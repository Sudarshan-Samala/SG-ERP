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
from app.services.csrf import clear_csrf_cookie, generate_csrf_token, require_csrf, set_csrf_cookie
from app.services.session_service import InvalidSession, RefreshReplayDetected, create_session, revoke_all_sessions, revoke_session, rotate_refresh_token
from app.services.user_service import get_user_by_email

router = APIRouter()

class SessionToken(Token):
    session_id: UUID

class RefreshRequest(BaseModel):
    session_id: UUID
    organization_id: UUID

class LogoutRequest(BaseModel):
    session_id: UUID


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(key=settings.REFRESH_COOKIE_NAME, value=token, max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400, httponly=True, secure=settings.REFRESH_COOKIE_SECURE, samesite=settings.REFRESH_COOKIE_SAMESITE, path="/api/v1/auth")


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=settings.REFRESH_COOKIE_NAME, path="/api/v1/auth", secure=settings.REFRESH_COOKIE_SECURE, httponly=True, samesite=settings.REFRESH_COOKIE_SAMESITE)


@router.post("/login", response_model=SessionToken)
def login(response: Response, db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    user = get_user_by_email(db, email=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    issued = create_session(db, user_id=user.id, organization_id=user.organization_id)
    access_token = create_access_token(subject=user.id, organization_id=user.organization_id, session_id=issued.session.id)
    _set_refresh_cookie(response, issued.refresh_token)
    set_csrf_cookie(response, generate_csrf_token())
    return {"access_token": access_token, "session_id": issued.session.id, "token_type": "bearer"}


@router.post("/refresh", response_model=SessionToken)
def refresh(request_body: RefreshRequest, request: Request, response: Response, db: Session = Depends(get_db), refresh_token: str | None = Cookie(default=None, alias=settings.REFRESH_COOKIE_NAME)):
    require_csrf(request)
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")
    try:
        issued = rotate_refresh_token(db, session_id=request_body.session_id, organization_id=request_body.organization_id, refresh_token=refresh_token)
    except (RefreshReplayDetected, InvalidSession):
        _clear_refresh_cookie(response)
        clear_csrf_cookie(response)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")
    user = db.query(User).filter(User.id == issued.session.user_id, User.organization_id == issued.session.organization_id, User.is_active.is_(True)).first()
    if user is None:
        revoke_session(db, session_id=issued.session.id, user_id=issued.session.user_id, organization_id=issued.session.organization_id, reason="user_inactive")
        _clear_refresh_cookie(response)
        clear_csrf_cookie(response)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")
    access_token = create_access_token(subject=user.id, organization_id=user.organization_id, session_id=issued.session.id)
    _set_refresh_cookie(response, issued.refresh_token)
    return {"access_token": access_token, "session_id": issued.session.id, "token_type": "bearer"}


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request_body: LogoutRequest, request: Request, response: Response, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    require_csrf(request)
    revoke_session(db, session_id=request_body.session_id, user_id=current_user.id, organization_id=current_user.organization_id)
    _clear_refresh_cookie(response)
    clear_csrf_cookie(response)


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
def logout_all(request: Request, response: Response, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    require_csrf(request)
    revoke_all_sessions(db, user_id=current_user.id, organization_id=current_user.organization_id)
    _clear_refresh_cookie(response)
    clear_csrf_cookie(response)


@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return {"id": current_user.id, "email": current_user.email, "full_name": current_user.full_name, "organization_id": current_user.organization_id, "is_active": current_user.is_active, "is_superuser": current_user.is_superuser}
