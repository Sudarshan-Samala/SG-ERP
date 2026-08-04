from dataclasses import dataclass
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.base import Organization, User
from app.services.auth import get_password_hash, verify_password


_BOOTSTRAP_LOCK_KEY = 734672001


@dataclass(frozen=True)
class BootstrapResult:
    created: bool
    reason: str
    user_id: Optional[str] = None


def bootstrap_super_admin(db: Session, email: str, password: str) -> BootstrapResult:
    """Create or synchronize the configured bootstrap super admin.

    Credentials are supplied from configuration/environment. The plaintext
    password is used only for verification/hashing and is never persisted or
    logged. Re-running bootstrap is idempotent and keeps the configured account
    usable when its bootstrap password changes.
    """
    email = (email or "").strip().lower()
    if not email:
        raise ValueError("BOOTSTRAP_ADMIN_EMAIL is required")
    if not password:
        raise ValueError("BOOTSTRAP_ADMIN_PASSWORD is required")

    # Serialize bootstrap attempts so concurrent deploy processes cannot race.
    db.execute(text("SELECT pg_advisory_xact_lock(:lock_key)"), {"lock_key": _BOOTSTRAP_LOCK_KEY})

    existing_email = db.query(User).filter(User.email == email).first()
    if existing_email is not None:
        if not existing_email.is_superuser:
            db.rollback()
            return BootstrapResult(
                created=False,
                reason="email_belongs_to_non_superuser",
                user_id=str(existing_email.id),
            )

        changed = False
        if not existing_email.is_active:
            existing_email.is_active = True
            changed = True

        if not verify_password(password, existing_email.hashed_password):
            existing_email.hashed_password = get_password_hash(password)
            changed = True

        if changed:
            db.commit()
            db.refresh(existing_email)
            return BootstrapResult(
                created=False,
                reason="super_admin_synchronized",
                user_id=str(existing_email.id),
            )

        db.rollback()
        return BootstrapResult(
            created=False,
            reason="super_admin_current",
            user_id=str(existing_email.id),
        )

    # Do not silently create a second super admin with a different email.
    existing_super_admin = db.query(User).filter(User.is_superuser.is_(True)).first()
    if existing_super_admin is not None:
        db.rollback()
        return BootstrapResult(
            created=False,
            reason="different_super_admin_exists",
            user_id=str(existing_super_admin.id),
        )

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
