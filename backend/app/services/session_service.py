import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.auth_refresh_token import AuthRefreshToken
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
    now = datetime.utcnow()
    refresh_token = generate_refresh_token()
    token_hash = hash_refresh_token(refresh_token)
    session = AuthSession(
        user_id=user_id,
        organization_id=organization_id,
        token_family_id=uuid.uuid4(),
        refresh_token_hash=token_hash,
        expires_at=now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    try:
        db.add(session)
        db.flush()
        db.add(
            AuthRefreshToken(
                session_id=session.id,
                token_family_id=session.token_family_id,
                token_hash=token_hash,
                issued_at=now,
                expires_at=session.expires_at,
            )
        )
        db.commit()
        db.refresh(session)
        return IssuedSession(session=session, refresh_token=refresh_token)
    except Exception:
        db.rollback()
        raise


def list_active_sessions(db: Session, *, user_id, organization_id) -> list[AuthSession]:
    return (
        db.query(AuthSession)
        .filter(
            AuthSession.user_id == user_id,
            AuthSession.organization_id == organization_id,
            AuthSession.revoked_at.is_(None),
            AuthSession.expires_at > datetime.utcnow(),
        )
        .order_by(AuthSession.created_at.desc())
        .all()
    )


def rotate_refresh_token(db: Session, *, refresh_token: str) -> IssuedSession:
    try:
        now = datetime.utcnow()
        presented_hash = hash_refresh_token(refresh_token)
        token_record = (
            db.query(AuthRefreshToken)
            .filter(AuthRefreshToken.token_hash == presented_hash)
            .with_for_update()
            .one_or_none()
        )
        if token_record is None:
            raise InvalidSession("Session is invalid")

        session = (
            db.query(AuthSession)
            .filter(
                AuthSession.id == token_record.session_id,
                AuthSession.token_family_id == token_record.token_family_id,
            )
            .with_for_update()
            .one_or_none()
        )
        if session is None or session.revoked_at is not None or session.expires_at <= now:
            raise InvalidSession("Session is invalid")
        if token_record.revoked_at is not None or token_record.expires_at <= now:
            raise InvalidSession("Session is invalid")

        if token_record.consumed_at is not None:
            session.revoked_at = now
            session.revocation_reason = "refresh_replay"
            db.query(AuthRefreshToken).filter(
                AuthRefreshToken.session_id == session.id,
                AuthRefreshToken.revoked_at.is_(None),
            ).update({"revoked_at": now}, synchronize_session=False)
            db.commit()
            raise RefreshReplayDetected("Refresh credential replay detected")

        new_token = generate_refresh_token()
        new_hash = hash_refresh_token(new_token)
        token_record.consumed_at = now
        db.add(
            AuthRefreshToken(
                session_id=session.id,
                token_family_id=session.token_family_id,
                token_hash=new_hash,
                issued_at=now,
                expires_at=session.expires_at,
            )
        )
        session.previous_refresh_token_hash = token_record.token_hash
        session.refresh_token_hash = new_hash
        session.last_used_at = now
        db.commit()
        db.refresh(session)
        return IssuedSession(session=session, refresh_token=new_token)
    except RefreshReplayDetected:
        raise
    except InvalidSession:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise


def revoke_session(db: Session, *, session_id, user_id, organization_id, reason: str = "logout") -> bool:
    try:
        session = (
            db.query(AuthSession)
            .filter(
                AuthSession.id == session_id,
                AuthSession.user_id == user_id,
                AuthSession.organization_id == organization_id,
            )
            .with_for_update()
            .one_or_none()
        )
        if session is None:
            return False
        if session.revoked_at is None:
            now = datetime.utcnow()
            session.revoked_at = now
            session.revocation_reason = reason[:120]
            db.query(AuthRefreshToken).filter(
                AuthRefreshToken.session_id == session.id,
                AuthRefreshToken.revoked_at.is_(None),
            ).update({"revoked_at": now}, synchronize_session=False)
            db.commit()
        return True
    except Exception:
        db.rollback()
        raise


def revoke_all_sessions(db: Session, *, user_id, organization_id, reason: str = "logout_all") -> int:
    try:
        now = datetime.utcnow()
        sessions = (
            db.query(AuthSession)
            .filter(
                AuthSession.user_id == user_id,
                AuthSession.organization_id == organization_id,
                AuthSession.revoked_at.is_(None),
            )
            .with_for_update()
            .all()
        )
        for session in sessions:
            session.revoked_at = now
            session.revocation_reason = reason[:120]
            db.query(AuthRefreshToken).filter(
                AuthRefreshToken.session_id == session.id,
                AuthRefreshToken.revoked_at.is_(None),
            ).update({"revoked_at": now}, synchronize_session=False)
        if sessions:
            db.commit()
        return len(sessions)
    except Exception:
        db.rollback()
        raise
