from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.auth_session import AuthSession
from app.models.base import Organization, User
from app.schemas.user import Token
from app.services.auth import create_access_token, hash_refresh_token, verify_password
from app.services.auth_audit import record_auth_event
from app.services.csrf import clear_csrf_cookie, generate_csrf_token, require_csrf, set_csrf_cookie
from app.services.rate_limit import SlidingWindowRateLimiter
from app.services.session_service import (
    InvalidSession,
    RefreshReplayDetected,
    create_session,
    list_active_sessions,
    revoke_all_sessions,
    revoke_session,
    rotate_refresh_token,
)


router = APIRouter()
login_ip_limiter = SlidingWindowRateLimiter(settings.AUTH_LOGIN_RATE_LIMIT, settings.AUTH_RATE_LIMIT_WINDOW_SECONDS)
login_account_limiter = SlidingWindowRateLimiter(settings.AUTH_LOGIN_RATE_LIMIT, settings.AUTH_RATE_LIMIT_WINDOW_SECONDS)
refresh_ip_limiter = SlidingWindowRateLimiter(settings.AUTH_REFRESH_RATE_LIMIT, settings.AUTH_RATE_LIMIT_WINDOW_SECONDS)
refresh_session_limiter = SlidingWindowRateLimiter(settings.AUTH_REFRESH_RATE_LIMIT, settings.AUTH_RATE_LIMIT_WINDOW_SECONDS)


class SessionToken(Token):
    session_id: UUID
    csrf_token: str


class SessionView(BaseModel):
    id: UUID
    created_at: datetime
    last_used_at: datetime | None
    expires_at: datetime


def _client_metadata(request: Request):
    return (request.client.host if request.client else None, request.headers.get("user-agent"))


def _correlation_id(request: Request) -> str | None:
    return getattr(request.state, "correlation_id", None)


def _set_refresh_cookie(response: Response, token: str):
    response.set_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        value=token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        httponly=True,
        secure=settings.REFRESH_COOKIE_SECURE,
        samesite=settings.REFRESH_COOKIE_SAMESITE,
        path="/api/v1/auth",
    )


def _clear_refresh_cookie(response: Response):
    response.delete_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        path="/api/v1/auth",
        secure=settings.REFRESH_COOKIE_SECURE,
        httponly=True,
        samesite=settings.REFRESH_COOKIE_SAMESITE,
    )


def _rate_key(request: Request, prefix: str):
    ip, _ = _client_metadata(request)
    return f"{prefix}:{ip or 'unknown'}"


def _login_account_key(email: str):
    return f"login-account:{email.strip().lower()[:160]}"


@router.get("/csrf")
def csrf(response: Response):
    """Bootstrap a CSRF token for browser clients hosted on a different origin."""
    token = generate_csrf_token()
    set_csrf_cookie(response, token)
    return {"csrf_token": token}


@router.post("/login", response_model=SessionToken)
def login(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    email = form_data.username.strip().lower()
    login_ip_limiter.check(_rate_key(request, "login-ip"))
    login_account_limiter.check(_login_account_key(email))
    ip, user_agent = _client_metadata(request)
    user = db.query(User).filter(User.email == email).first()
    generic_failure = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    if not user or not verify_password(form_data.password, user.hashed_password):
        record_auth_event(db, event_type="login", outcome="failure", correlation_id=_correlation_id(request), email=email, ip_address=ip, user_agent=user_agent)
        raise generic_failure

    if not user.is_active or not user.organization or not user.organization.is_active:
        record_auth_event(db, event_type="login", outcome="failure", organization_id=user.organization_id, user_id=user.id, correlation_id=_correlation_id(request), email=user.email, ip_address=ip, user_agent=user_agent)
        raise generic_failure

    issued = create_session(db, user_id=user.id, organization_id=user.organization_id)
    access_token = create_access_token(subject=user.id, organization_id=user.organization_id, session_id=issued.session.id)
    csrf_token = generate_csrf_token()
    _set_refresh_cookie(response, issued.refresh_token)
    set_csrf_cookie(response, csrf_token)
    record_auth_event(db, event_type="login", outcome="success", organization_id=user.organization_id, user_id=user.id, session_id=issued.session.id, correlation_id=_correlation_id(request), email=user.email, ip_address=ip, user_agent=user_agent)
    return {"access_token": access_token, "session_id": issued.session.id, "token_type": "bearer", "csrf_token": csrf_token}


@router.post("/refresh", response_model=SessionToken)
def refresh(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    refresh_token: str | None = Cookie(default=None, alias=settings.REFRESH_COOKIE_NAME),
):
    refresh_ip_limiter.check(_rate_key(request, "refresh-ip"))
    require_csrf(request)
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")

    presented_hash = hash_refresh_token(refresh_token)
    refresh_session_limiter.check(f"refresh-session:{presented_hash}")
    token_context = db.query(AuthSession).filter(AuthSession.refresh_token_hash == presented_hash).first()
    try:
        issued = rotate_refresh_token(db, refresh_token=refresh_token)
    except RefreshReplayDetected:
        record_auth_event(db, event_type="refresh_replay", outcome="failure", organization_id=token_context.organization_id if token_context else None, user_id=token_context.user_id if token_context else None, session_id=token_context.id if token_context else None, correlation_id=_correlation_id(request))
        _clear_refresh_cookie(response)
        clear_csrf_cookie(response)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")
    except InvalidSession:
        record_auth_event(db, event_type="refresh", outcome="failure", organization_id=token_context.organization_id if token_context else None, user_id=token_context.user_id if token_context else None, session_id=token_context.id if token_context else None, correlation_id=_correlation_id(request))
        _clear_refresh_cookie(response)
        clear_csrf_cookie(response)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")

    user = (
        db.query(User)
        .join(Organization, Organization.id == User.organization_id)
        .filter(User.id == issued.session.user_id, User.organization_id == issued.session.organization_id, User.is_active.is_(True), Organization.is_active.is_(True))
        .first()
    )
    if not user:
        revoke_session(db, session_id=issued.session.id, user_id=issued.session.user_id, organization_id=issued.session.organization_id, reason="account_inactive")
        record_auth_event(db, event_type="refresh", outcome="failure", organization_id=issued.session.organization_id, user_id=issued.session.user_id, session_id=issued.session.id, correlation_id=_correlation_id(request))
        _clear_refresh_cookie(response)
        clear_csrf_cookie(response)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")

    access_token = create_access_token(subject=user.id, organization_id=user.organization_id, session_id=issued.session.id)
    csrf_token = generate_csrf_token()
    _set_refresh_cookie(response, issued.refresh_token)
    set_csrf_cookie(response, csrf_token)
    ip, user_agent = _client_metadata(request)
    record_auth_event(db, event_type="refresh", outcome="success", organization_id=user.organization_id, user_id=user.id, session_id=issued.session.id, correlation_id=_correlation_id(request), email=user.email, ip_address=ip, user_agent=user_agent)
    return {"access_token": access_token, "session_id": issued.session.id, "token_type": "bearer", "csrf_token": csrf_token}


@router.get("/sessions", response_model=list[SessionView])
def sessions(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return [
        SessionView(id=session.id, created_at=session.created_at, last_used_at=session.last_used_at, expires_at=session.expires_at)
        for session in list_active_sessions(db, user_id=current_user.id, organization_id=current_user.organization_id)
    ]


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(session_id: UUID, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    require_csrf(request)
    if not revoke_session(db, session_id=session_id, user_id=current_user.id, organization_id=current_user.organization_id, reason="user_revoked"):
        raise HTTPException(status_code=404, detail="Session not found")
    ip, user_agent = _client_metadata(request)
    record_auth_event(db, event_type="session_revocation", outcome="success", organization_id=current_user.organization_id, user_id=current_user.id, session_id=session_id, correlation_id=_correlation_id(request), email=current_user.email, ip_address=ip, user_agent=user_agent)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request, response: Response, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    require_csrf(request)
    session_id = getattr(request.state, "session_id", None)
    if session_id is not None:
        revoke_session(db, session_id=session_id, user_id=current_user.id, organization_id=current_user.organization_id, reason="logout")
        ip, user_agent = _client_metadata(request)
        record_auth_event(db, event_type="logout", outcome="success", organization_id=current_user.organization_id, user_id=current_user.id, session_id=session_id, correlation_id=_correlation_id(request), email=current_user.email, ip_address=ip, user_agent=user_agent)
    _clear_refresh_cookie(response)
    clear_csrf_cookie(response)


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
def logout_all(request: Request, response: Response, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    require_csrf(request)
    revoke_all_sessions(db, user_id=current_user.id, organization_id=current_user.organization_id)
    ip, user_agent = _client_metadata(request)
    record_auth_event(db, event_type="logout_all", outcome="success", organization_id=current_user.organization_id, user_id=current_user.id, correlation_id=_correlation_id(request), email=current_user.email, ip_address=ip, user_agent=user_agent)
    _clear_refresh_cookie(response)
    clear_csrf_cookie(response)


@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    permissions = sorted({permission.name for role in current_user.roles for permission in role.permissions})
    branches = sorted(({"id": branch.id, "name": branch.name, "code": branch.code} for branch in current_user.branches if branch.organization_id == current_user.organization_id), key=lambda branch: branch["name"].lower())
    return {"id": current_user.id, "email": current_user.email, "full_name": current_user.full_name, "organization_id": current_user.organization_id, "is_active": current_user.is_active, "is_superuser": current_user.is_superuser, "permissions": permissions, "branches": branches}
