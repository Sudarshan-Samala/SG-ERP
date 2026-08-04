from dataclasses import dataclass
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.base import Organization, User
from app.services.auth import get_password_hash


_BOOTSTRAP_LOCK_KEY = 734672001


@dataclass(frozen=True)
class BootstrapResult:
    created: bool
    reason: str
    user_id: Optional[str] = None


def bootstrap_super_admin(db: Session, email: str, password: str) -> BootstrapResult:
    """Create the initial super admin exactly once.

    The caller supplies credentials from configuration/environment. The plaintext
    password is used only as input to the project's password hashing utility and
    is never persisted or logged.
    """
    email = (email or "").strip().lower()
    if not email:
        raise ValueError("BOOTSTRAP_ADMIN_EMAIL is required")
    if not password:
        raise ValueError("BOOTSTRAP_ADMIN_PASSWORD is required")

    # The application uses PostgreSQL. Serialize bootstrap attempts so two
    # processes cannot create different first super admins concurrently.
    db.execute(text("SELECT pg_advisory_xact_lock(:lock_key)"), {"lock_key": _BOOTSTRAP_LOCK_KEY})

    existing_super_admin = db.query(User).filter(User.is_superuser.is_(True)).first()
    if existing_super_admin is not None:
        db.rollback()
        return BootstrapResult(created=False, reason="super_admin_exists")

    existing_email = db.query(User).filter(User.email == email).first()
    if existing_email is not None:
        db.rollback()
        return BootstrapResult(created=False, reason="email_already_exists")

    organization = db.query(Organization).order_by(Organization.created_at.asc()).first()
    if organization is None:
        organization = Organization(name="System")
        db.add(organization)
        db.flush()

    user = User(
        organization_id=organization.id,
        email=email,
        hashed_password=get_password_hash(password),
        full_name="Super Admin",
        is_active=True,
        is_superuser=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return BootstrapResult(created=True, reason="created", user_id=str(user.id))
