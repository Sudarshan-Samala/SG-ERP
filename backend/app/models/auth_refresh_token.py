import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class AuthRefreshToken(Base):
    """One-way refresh-token ledger used for rotation and replay detection."""

    __tablename__ = "auth_refresh_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("auth_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    token_family_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    token_hash = Column(String(64), nullable=False, unique=True)
    issued_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    consumed_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    revoked_at = Column(DateTime, nullable=True)

    session = relationship("AuthSession")

    __table_args__ = (
        Index("ix_auth_refresh_tokens_session_family", "session_id", "token_family_id"),
    )
