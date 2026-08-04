import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.auth_session import AuthSession
from app.services.auth import generate_refresh_token, hash_refresh_token


class SessionError(Exception):
    pass


class InvalidSession(SessionError):
    pass


class RefreshReplayDetected(SessionError):
    pass


@dataclass(frozen=True)
class IssuedSession:
    session: AuthSession
    refresh_token: str


def create_session(db: Session, *, user_id, organization_id) -> IssuedSession:
    refresh_token = generate_refresh_token()
    session = AuthSession(
        user_id=user_id,
        organization_id=organization_id,
        token_family_id=uuid.uuid4(),
        refresh_token_hash=hash_refresh_token(refresh_token),
        expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return IssuedSession(session=session, refresh_token=refresh_token)


def rotate_refresh_token(db: Session, *, session_id, organization_id, refresh_token: str) -> IssuedSession:
    """Rotate once under a row lock; reuse of the immediately previous token revokes the session."""
    session = (
        db.query(AuthSession)
        .filter(AuthSession.id == session_id, AuthSession.organization_id == organization_id)
        .with_for_update()
        .one_or_none()
    )
    now = datetime.utcnow()
    if session is None or session.revoked_at is not None or session.expires_at <= now:
        raise InvalidSession("Session is invalid")

    presented_hash = hash_refresh_token(refresh_token)
    if session.previous_refresh_token_hash and presented_hash == session.previous_refresh_token_hash:
        session.revoked_at = now
        session.revocation_reason = "refresh_replay"
        db.commit()
        raise RefreshReplayDetected("Refresh credential replay detected")

    if presented_hash != session.refresh_token_hash:
        raise InvalidSession("Session is invalid")

    new_token = generate_refresh_token()
    session.previous_refresh_token_hash = session.refresh_token_hash
    session.refresh_token_hash = hash_refresh_token(new_token)
    session.last_used_at = now
    db.commit()
    db.refresh(session)
    return IssuedSession(session=session, refresh_token=new_token)


def revoke_session(db: Session, *, session_id, user_id, organization_id, reason: str = "logout") -> bool:
    session = (
        db.query(AuthSession)
        .filter(
            AuthSession.id == session_id,
            AuthSession.user_id == user_id,
            AuthSession.organization_id == organization_id,
        )
        .one_or_none()
    )
    if session is None:
        return False
    if session.revoked_at is None:
        session.revoked_at = datetime.utcnow()
        session.revocation_reason = reason[:120]
        db.commit()
    return True


def revoke_all_sessions(db: Session, *, user_id, organization_id, reason: str = "logout_all") -> int:
    now = datetime.utcnow()
    sessions = (
        db.query(AuthSession)
        .filter(
            AuthSession.user_id == user_id,
            AuthSession.organization_id == organization_id,
            AuthSession.revoked_at.is_(None),
        )
        .all()
    )
    for session in sessions:
        session.revoked_at = now
        session.revocation_reason = reason[:120]
    if sessions:
        db.commit()
    return len(sessions)
