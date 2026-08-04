from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.base import User
from app.schemas.user import Token
from app.services.auth import create_access_token, verify_password
from app.services.session_service import (
    InvalidSession,
    RefreshReplayDetected,
    create_session,
    revoke_all_sessions,
    revoke_session,
    rotate_refresh_token,
)
from app.services.user_service import get_user_by_email

router = APIRouter()


class SessionToken(Token):
    refresh_token: str
    session_id: UUID


class RefreshRequest(BaseModel):
    session_id: UUID
    organization_id: UUID
    refresh_token: str


class LogoutRequest(BaseModel):
    session_id: UUID


@router.post("/login", response_model=SessionToken)
def login(
    db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
):
    user = get_user_by_email(db, email=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")

    issued = create_session(db, user_id=user.id, organization_id=user.organization_id)
    access_token = create_access_token(
        subject=user.id,
        organization_id=user.organization_id,
        session_id=issued.session.id,
    )
    return {
        "access_token": access_token,
        "refresh_token": issued.refresh_token,
        "session_id": issued.session.id,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=SessionToken)
def refresh(request: RefreshRequest, db: Session = Depends(get_db)):
    try:
        issued = rotate_refresh_token(
            db,
            session_id=request.session_id,
            organization_id=request.organization_id,
            refresh_token=request.refresh_token,
        )
    except RefreshReplayDetected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session revoked")
    except InvalidSession:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")

    user = db.query(User).filter(
        User.id == issued.session.user_id,
        User.organization_id == issued.session.organization_id,
    ).first()
    if user is None or not user.is_active:
        revoke_session(
            db,
            session_id=issued.session.id,
            user_id=issued.session.user_id,
            organization_id=issued.session.organization_id,
            reason="user_inactive",
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")

    access_token = create_access_token(
        subject=user.id,
        organization_id=user.organization_id,
        session_id=issued.session.id,
    )
    return {
        "access_token": access_token,
        "refresh_token": issued.refresh_token,
        "session_id": issued.session.id,
        "token_type": "bearer",
    }


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: LogoutRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    revoke_session(
        db,
        session_id=request.session_id,
        user_id=current_user.id,
        organization_id=current_user.organization_id,
    )


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
def logout_all(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    revoke_all_sessions(
        db,
        user_id=current_user.id,
        organization_id=current_user.organization_id,
    )


@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "organization_id": current_user.organization_id,
        "is_active": current_user.is_active,
        "is_superuser": current_user.is_superuser,
    }
