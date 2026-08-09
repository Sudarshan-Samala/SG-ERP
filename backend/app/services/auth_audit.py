import hashlib
import hmac

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.auth_security_event import AuthSecurityEvent


def email_fingerprint(email: str | None) -> str | None:
    if not email:
        return None
    normalized = email.strip().lower()
    return hmac.new(settings.SECRET_KEY.encode(), normalized.encode(), hashlib.sha256).hexdigest()


def record_auth_event(
    db: Session,
    *,
    event_type: str,
    outcome: str,
    organization_id=None,
    user_id=None,
    session_id=None,
    correlation_id: str | None = None,
    email: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> None:
    """Persist sanitized authentication telemetry without credentials or token material."""
    event = AuthSecurityEvent(
        event_type=event_type[:64],
        outcome=outcome[:32],
        organization_id=organization_id,
        user_id=user_id,
        session_id=session_id,
        correlation_id=(correlation_id or "")[:64] or None,
        email_fingerprint=email_fingerprint(email),
        ip_address=(ip_address or "")[:64] or None,
        user_agent=(user_agent or "")[:255] or None,
    )
    db.add(event)
    db.commit()
