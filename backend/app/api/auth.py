from datetime import datetime
from uuid import UUID
import re

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.base import Organization, Role, User
from app.schemas.user import Token
from app.services.auth import create_access_token, get_password_hash, verify_password
from app.services.auth_audit import record_auth_event
from app.services.csrf import clear_csrf_cookie, generate_csrf_token, require_csrf, set_csrf_cookie
from app.services.rate_limit import SlidingWindowRateLimiter
from app.services.session_service import InvalidSession, RefreshReplayDetected, create_session, list_active_sessions, revoke_all_sessions, revoke_session, rotate_refresh_token
from app.services.user_service import get_user_by_email

router = APIRouter()
login_limiter = SlidingWindowRateLimiter(settings.AUTH_LOGIN_RATE_LIMIT, settings.AUTH_RATE_LIMIT_WINDOW_SECONDS)
refresh_limiter = SlidingWindowRateLimiter(settings.AUTH_REFRESH_RATE_LIMIT, settings.AUTH_RATE_LIMIT_WINDOW_SECONDS)
signup_limiter = SlidingWindowRateLimiter(settings.AUTH_SIGNUP_RATE_LIMIT, settings.AUTH_RATE_LIMIT_WINDOW_SECONDS)

class SessionToken(Token): session_id: UUID
class RefreshRequest(BaseModel): session_id: UUID; organization_id: UUID
class LogoutRequest(BaseModel): session_id: UUID
class SessionView(BaseModel): id: UUID; created_at: datetime; last_used_at: datetime | None; expires_at: datetime
class SignupRequest(BaseModel):
    organization_name: str = Field(min_length=2, max_length=120)
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)


def _client_metadata(request: Request) -> tuple[str | None, str | None]: return (request.client.host if request.client else None, request.headers.get("user-agent"))
def _rate_key(request: Request, scope: str) -> str:
    ip, _ = _client_metadata(request); return f"{scope}:{ip or 'unknown'}"
def _set_refresh_cookie(response: Response, token: str) -> None: response.set_cookie(key=settings.REFRESH_COOKIE_NAME,value=token,max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS*86400,httponly=True,secure=settings.REFRESH_COOKIE_SECURE,samesite=settings.REFRESH_COOKIE_SAMESITE,path="/api/v1/auth")
def _clear_refresh_cookie(response: Response) -> None: response.delete_cookie(key=settings.REFRESH_COOKIE_NAME,path="/api/v1/auth",secure=settings.REFRESH_COOKIE_SECURE,httponly=True,samesite=settings.REFRESH_COOKIE_SAMESITE)
def _password_is_strong(password: str) -> bool: return bool(re.search(r"[a-z]",password) and re.search(r"[A-Z]",password) and re.search(r"\d",password) and re.search(r"[^A-Za-z0-9]",password))

@router.post("/signup", response_model=SessionToken, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    signup_limiter.check(_rate_key(request,"signup")); ip,ua=_client_metadata(request)
    email=str(payload.email).strip().lower(); org_name=" ".join(payload.organization_name.split()); full_name=" ".join(payload.full_name.split())
    if not _password_is_strong(payload.password): raise HTTPException(status_code=400,detail="Password must include uppercase, lowercase, number and special character")
    if get_user_by_email(db,email): raise HTTPException(status_code=409,detail="An account with this email already exists")
    if db.query(Organization).filter(func.lower(Organization.name)==org_name.lower()).first(): raise HTTPException(status_code=409,detail="An organization with this name already exists")
    try:
        organization=Organization(name=org_name,is_active=True); db.add(organization); db.flush()
        role=Role(name="Organization Administrator",organization_id=organization.id,permissions=[]); db.add(role); db.flush()
        user=User(email=email,hashed_password=get_password_hash(payload.password),full_name=full_name,organization_id=organization.id,is_active=True,is_superuser=False,roles=[role]); db.add(user); db.commit(); db.refresh(user)
    except IntegrityError:
        db.rollback(); raise HTTPException(status_code=409,detail="Account or organization already exists")
    issued=create_session(db,user_id=user.id,organization_id=user.organization_id); access_token=create_access_token(subject=user.id,organization_id=user.organization_id,session_id=issued.session.id)
    _set_refresh_cookie(response,issued.refresh_token); set_csrf_cookie(response,generate_csrf_token()); record_auth_event(db,event_type="signup",outcome="success",organization_id=user.organization_id,user_id=user.id,session_id=issued.session.id,email=user.email,ip_address=ip,user_agent=ua)
    return {"access_token":access_token,"session_id":issued.session.id,"token_type":"bearer"}

@router.post("/login", response_model=SessionToken)
def login(request:Request,response:Response,db:Session=Depends(get_db),form_data:OAuth2PasswordRequestForm=Depends()):
    login_limiter.check(_rate_key(request,"login"));ip,ua=_client_metadata(request);user=get_user_by_email(db,email=form_data.username)
    if not user or not verify_password(form_data.password,user.hashed_password): record_auth_event(db,event_type="login",outcome="failure",email=form_data.username,ip_address=ip,user_agent=ua);raise HTTPException(status_code=401,detail="Incorrect email or password")
    if not user.is_active: record_auth_event(db,event_type="login",outcome="inactive",organization_id=user.organization_id,user_id=user.id,email=user.email,ip_address=ip,user_agent=ua);raise HTTPException(status_code=403,detail="Inactive user")
    issued=create_session(db,user_id=user.id,organization_id=user.organization_id);access_token=create_access_token(subject=user.id,organization_id=user.organization_id,session_id=issued.session.id);_set_refresh_cookie(response,issued.refresh_token);set_csrf_cookie(response,generate_csrf_token());record_auth_event(db,event_type="login",outcome="success",organization_id=user.organization_id,user_id=user.id,session_id=issued.session.id,email=user.email,ip_address=ip,user_agent=ua);return {"access_token":access_token,"session_id":issued.session.id,"token_type":"bearer"}

@router.post("/refresh",response_model=SessionToken)
def refresh(request_body:RefreshRequest,request:Request,response:Response,db:Session=Depends(get_db),refresh_token:str|None=Cookie(default=None,alias=settings.REFRESH_COOKIE_NAME)):
    refresh_limiter.check(_rate_key(request,"refresh"));require_csrf(request);ip,ua=_client_metadata(request)
    if not refresh_token: record_auth_event(db,event_type="refresh",outcome="missing",organization_id=request_body.organization_id,session_id=request_body.session_id,ip_address=ip,user_agent=ua);raise HTTPException(status_code=401,detail="Invalid session")
    try: issued=rotate_refresh_token(db,session_id=request_body.session_id,organization_id=request_body.organization_id,refresh_token=refresh_token)
    except RefreshReplayDetected: record_auth_event(db,event_type="refresh",outcome="replay",organization_id=request_body.organization_id,session_id=request_body.session_id,ip_address=ip,user_agent=ua);_clear_refresh_cookie(response);clear_csrf_cookie(response);raise HTTPException(status_code=401,detail="Invalid session")
    except InvalidSession: record_auth_event(db,event_type="refresh",outcome="failure",organization_id=request_body.organization_id,session_id=request_body.session_id,ip_address=ip,user_agent=ua);_clear_refresh_cookie(response);clear_csrf_cookie(response);raise HTTPException(status_code=401,detail="Invalid session")
    user=db.query(User).filter(User.id==issued.session.user_id,User.organization_id==issued.session.organization_id,User.is_active.is_(True)).first()
    if user is None: revoke_session(db,session_id=issued.session.id,user_id=issued.session.user_id,organization_id=issued.session.organization_id,reason="user_inactive");_clear_refresh_cookie(response);clear_csrf_cookie(response);raise HTTPException(status_code=401,detail="Invalid session")
    access_token=create_access_token(subject=user.id,organization_id=user.organization_id,session_id=issued.session.id);_set_refresh_cookie(response,issued.refresh_token);return {"access_token":access_token,"session_id":issued.session.id,"token_type":"bearer"}

@router.get("/sessions",response_model=list[SessionView])
def sessions(db:Session=Depends(get_db),current_user:User=Depends(get_current_user)): return list_active_sessions(db,user_id=current_user.id,organization_id=current_user.organization_id)
@router.delete("/sessions/{session_id}",status_code=204)
def delete_session(session_id:UUID,request:Request,response:Response,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    require_csrf(request);revoked=revoke_session(db,session_id=session_id,user_id=current_user.id,organization_id=current_user.organization_id,reason="user_revoked")
    if not revoked: raise HTTPException(status_code=404,detail="Session not found")
@router.post("/logout",status_code=204)
def logout(request_body:LogoutRequest,request:Request,response:Response,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)): require_csrf(request);revoke_session(db,session_id=request_body.session_id,user_id=current_user.id,organization_id=current_user.organization_id);_clear_refresh_cookie(response);clear_csrf_cookie(response)
@router.post("/logout-all",status_code=204)
def logout_all(request:Request,response:Response,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)): require_csrf(request);revoke_all_sessions(db,user_id=current_user.id,organization_id=current_user.organization_id);_clear_refresh_cookie(response);clear_csrf_cookie(response)
@router.get("/me")
def me(current_user:User=Depends(get_current_user)):
    permissions=sorted({p.name for r in current_user.roles for p in r.permissions});branches=sorted(({"id":b.id,"name":b.name,"code":b.code} for b in current_user.branches if b.organization_id==current_user.organization_id),key=lambda b:b["name"].lower());return {"id":current_user.id,"email":current_user.email,"full_name":current_user.full_name,"organization_id":current_user.organization_id,"is_active":current_user.is_active,"is_superuser":current_user.is_superuser,"permissions":permissions,"branches":branches}
