import re
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.base import Organization, Permission, Role, User
from app.schemas.user import Token
from app.services.auth import create_access_token, get_password_hash
from app.services.auth_audit import record_auth_event
from app.services.csrf import generate_csrf_token, set_csrf_cookie
from app.services.rate_limit import SlidingWindowRateLimiter
from app.services.session_service import create_session
from app.services.user_service import get_user_by_email

router = APIRouter()
signup_limiter = SlidingWindowRateLimiter(settings.AUTH_SIGNUP_RATE_LIMIT, settings.AUTH_RATE_LIMIT_WINDOW_SECONDS)


class SignupRequest(BaseModel):
    organization_name: str = Field(min_length=2, max_length=120)
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)


class SignupToken(Token):
    session_id: UUID


def _strong(password: str) -> bool:
    return bool(
        re.search(r"[a-z]", password)
        and re.search(r"[A-Z]", password)
        and re.search(r"\d", password)
        and re.search(r"[^A-Za-z0-9]", password)
    )


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        value=token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        httponly=True,
        secure=settings.REFRESH_COOKIE_SECURE,
        samesite=settings.REFRESH_COOKIE_SAMESITE,
        path="/api/v1/auth",
    )


@router.post("/signup", response_model=SignupToken, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    ip = request.client.host if request.client else "unknown"
    signup_limiter.check(f"signup:{ip}")
    email = str(payload.email).strip().lower()
    org_name = " ".join(payload.organization_name.split())
    full_name = " ".join(payload.full_name.split())
    if not _strong(payload.password):
        raise HTTPException(status_code=400, detail="Password must include uppercase, lowercase, number and special character")
    if get_user_by_email(db, email):
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    if db.query(Organization).filter(func.lower(Organization.name) == org_name.lower()).first():
        raise HTTPException(status_code=409, detail="An organization with this name already exists")
    try:
        organization = Organization(name=org_name, is_active=True)
        db.add(organization)
        db.flush()
        role = Role(name="Organization Administrator", organization_id=organization.id, permissions=db.query(Permission).all())
        db.add(role)
        db.flush()
        user = User(
            email=email,
            hashed_password=get_password_hash(payload.password),
            full_name=full_name,
            organization_id=organization.id,
            is_active=True,
            is_superuser=False,
            roles=[role],
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Account or organization already exists")
    issued = create_session(db, user_id=user.id, organization_id=user.organization_id)
    token = create_access_token(subject=user.id, organization_id=user.organization_id, session_id=issued.session.id)
    _set_refresh_cookie(response, issued.refresh_token)
    set_csrf_cookie(response, generate_csrf_token())
    record_auth_event(
        db,
        event_type="signup",
        outcome="success",
        organization_id=user.organization_id,
        user_id=user.id,
        session_id=issued.session.id,
        correlation_id=getattr(request.state, "correlation_id", None),
        email=user.email,
        ip_address=ip,
        user_agent=request.headers.get("user-agent"),
    )
    return {"access_token": token, "session_id": issued.session.id, "token_type": "bearer"}
