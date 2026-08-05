from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.base import User
from app.schemas.user import Token
from app.services.auth import create_access_token, verify_password
from app.services.auth_audit import record_auth_event
from app.services.csrf import clear_csrf_cookie, generate_csrf_token, require_csrf, set_csrf_cookie
from app.services.rate_limit import SlidingWindowRateLimiter
from app.services.session_service import InvalidSession, RefreshReplayDetected, create_session, list_active_sessions, revoke_all_sessions, revoke_session, rotate_refresh_token
from app.services.user_service import get_user_by_email

router = APIRouter()
login_limiter = SlidingWindowRateLimiter(settings.AUTH_LOGIN_RATE_LIMIT, settings.AUTH_RATE_LIMIT_WINDOW_SECONDS)
refresh_limiter = SlidingWindowRateLimiter(settings.AUTH_REFRESH_RATE_LIMIT, settings.AUTH_RATE_LIMIT_WINDOW_SECONDS)

class SessionToken(Token):
    session_id: UUID

class RefreshRequest(BaseModel):
    session_id: UUID
    organization_id: UUID

class LogoutRequest(BaseModel):
    session_id: UUID

class SessionView(BaseModel):
    id: UUID
    created_at: datetime
    last_used_at: datetime | None
    expires_at: datetime


def _client_metadata(request: Request) -> tuple[str | None, str | None]:
    return (request.client.host if request.client else None, request.headers.get("user-agent"))


def _rate_key(request: Request, scope: str) -> str:
    ip, _ = _client_metadata(request)
    return f"{scope}:{ip or 'unknown'}"


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(key=settings.REFRESH_COOKIE_NAME, value=token, max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400, httponly=True, secure=settings.REFRESH_COOKIE_SECURE, samesite=settings.REFRESH_COOKIE_SAMESITE, path="/api/v1/auth")


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=settings.REFRESH_COOKIE_NAME, path="/api/v1/auth", secure=settings.REFRESH_COOKIE_SECURE, httponly=True, samesite=settings.REFRESH_COOKIE_SAMESITE)


@router.post("/login", response_model=SessionToken)
def login(request: Request, response: Response, db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    login_limiter.check(_rate_key(request, "login"))
    ip, ua = _client_metadata(request)
    user = get_user_by_email(db, email=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        record_auth_event(db, event_type="login", outcome="failure", email=form_data.username, ip_address=ip, user_agent=ua)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    if not user.is_active:
        record_auth_event(db, event_type="login", outcome="inactive", organization_id=user.organization_id, user_id=user.id, email=user.email, ip_address=ip, user_agent=ua)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    issued = create_session(db, user_id=user.id, organization_id=user.organization_id)
    access_token = create_access_token(subject=user.id, organization_id=user.organization_id, session_id=issued.session.id)
    _set_refresh_cookie(response, issued.refresh_token)
    set_csrf_cookie(response, generate_csrf_token())
    record_auth_event(db, event_type="login", outcome="success", organization_id=user.organization_id, user_id=user.id, session_id=issued.session.id, email=user.email, ip_address=ip, user_agent=ua)
    return {"access_token": access_token, "session_id": issued.session.id, "token_type": "bearer"}


@router.post("/refresh", response_model=SessionToken)
def refresh(request_body: RefreshRequest, request: Request, response: Response, db: Session = Depends(get_db), refresh_token: str | None = Cookie(default=None, alias=settings.REFRESH_COOKIE_NAME)):
    refresh_limiter.check(_rate_key(request, "refresh"))
    require_csrf(request)
    ip, ua = _client_metadata(request)
    if not refresh_token:
        record_auth_event(db, event_type="refresh", outcome="missing", organization_id=request_body.organization_id, session_id=request_body.session_id, ip_address=ip, user_agent=ua)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")
    try:
        issued = rotate_refresh_token(db, session_id=request_body.session_id, organization_id=request_body.organization_id, refresh_token=refresh_token)
    except RefreshReplayDetected:
        record_auth_event(db, event_type="refresh", outcome="replay", organization_id=request_body.organization_id, session_id=request_body.session_id, ip_address=ip, user_agent=ua)
        _clear_refresh_cookie(response); clear_csrf_cookie(response)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")
    except InvalidSession:
        record_auth_event(db, event_type="refresh", outcome="failure", organization_id=request_body.organization_id, session_id=request_body.session_id, ip_address=ip, user_agent=ua)
        _clear_refresh_cookie(response); clear_csrf_cookie(response)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")
    user = db.query(User).filter(User.id == issued.session.user_id, User.organization_id == issued.session.organization_id, User.is_active.is_(True)).first()
    if user is None:
        revoke_session(db, session_id=issued.session.id, user_id=issued.session.user_id, organization_id=issued.session.organization_id, reason="user_inactive")
        record_auth_event(db, event_type="refresh", outcome="inactive", organization_id=issued.session.organization_id, user_id=issued.session.user_id, session_id=issued.session.id, ip_address=ip, user_agent=ua)
        _clear_refresh_cookie(response); clear_csrf_cookie(response)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")
    access_token = create_access_token(subject=user.id, organization_id=user.organization_id, session_id=issued.session.id)
    _set_refresh_cookie(response, issued.refresh_token)
    record_auth_event(db, event_type="refresh", outcome="success", organization_id=user.organization_id, user_id=user.id, session_id=issued.session.id, ip_address=ip, user_agent=ua)
    return {"access_token": access_token, "session_id": issued.session.id, "token_type": "bearer"}


@router.get("/sessions", response_model=list[SessionView])
def sessions(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return list_active_sessions(db, user_id=current_user.id, organization_id=current_user.organization_id)


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(session_id: UUID, request: Request, response: Response, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    require_csrf(request)
    ip, ua = _client_metadata(request)
    revoked = revoke_session(db, session_id=session_id, user_id=current_user.id, organization_id=current_user.organization_id, reason="user_revoked")
    if not revoked:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    record_auth_event(db, event_type="session_revoke", outcome="success", organization_id=current_user.organization_id, user_id=current_user.id, session_id=session_id, ip_address=ip, user_agent=ua)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request_body: LogoutRequest, request: Request, response: Response, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    require_csrf(request)
    ip, ua = _client_metadata(request)
    revoked = revoke_session(db, session_id=request_body.session_id, user_id=current_user.id, organization_id=current_user.organization_id)
    record_auth_event(db, event_type="logout", outcome="success" if revoked else "not_found", organization_id=current_user.organization_id, user_id=current_user.id, session_id=request_body.session_id, ip_address=ip, user_agent=ua)
    _clear_refresh_cookie(response); clear_csrf_cookie(response)


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
def logout_all(request: Request, response: Response, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    require_csrf(request)
    ip, ua = _client_metadata(request)
    revoke_all_sessions(db, user_id=current_user.id, organization_id=current_user.organization_id)
    record_auth_event(db, event_type="logout_all", outcome="success", organization_id=current_user.organization_id, user_id=current_user.id, ip_address=ip, user_agent=ua)
    _clear_refresh_cookie(response); clear_csrf_cookie(response)


@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    permissions = sorted({permission.name for role in current_user.roles for permission in role.permissions})
    branches = sorted(
        ({"id": branch.id, "name": branch.name, "code": branch.code} for branch in current_user.branches if branch.organization_id == current_user.organization_id),
        key=lambda branch: branch["name"].lower(),
    )
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "organization_id": current_user.organization_id,
        "is_active": current_user.is_active,
        "is_superuser": current_user.is_superuser,
        "permissions": permissions,
        "branches": branches,
    }
