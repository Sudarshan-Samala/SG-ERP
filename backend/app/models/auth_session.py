import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class AuthSession(Base):
    """Server-tracked authentication session bound to one user and tenant.

    Only a one-way digest of the current refresh credential is persisted.
    Plaintext access/refresh tokens must never be stored in this table.
    """

    __tablename__ = "auth_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_family_id = Column(UUID(as_uuid=True), nullable=False, default=uuid.uuid4)
    refresh_token_hash = Column(String(64), nullable=False, unique=True)
    previous_refresh_token_hash = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_used_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    revocation_reason = Column(String(120), nullable=True)

    user = relationship("User")
    organization = relationship("Organization")

    __table_args__ = (
        Index("ix_auth_sessions_user_org", "user_id", "organization_id"),
        Index("ix_auth_sessions_family", "token_family_id"),
        Index("ix_auth_sessions_expires_at", "expires_at"),
    )
