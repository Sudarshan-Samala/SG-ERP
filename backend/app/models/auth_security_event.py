import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class AuthSecurityEvent(Base):
    __tablename__ = "auth_security_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("auth_sessions.id", ondelete="SET NULL"), nullable=True)
    event_type = Column(String(64), nullable=False)
    outcome = Column(String(32), nullable=False)
    correlation_id = Column(String(64), nullable=True)
    email_fingerprint = Column(String(64), nullable=True)
    ip_address = Column(String(64), nullable=True)
    user_agent = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_auth_security_events_org_created", "organization_id", "created_at"),
        Index("ix_auth_security_events_user_created", "user_id", "created_at"),
        Index("ix_auth_security_events_type_created", "event_type", "created_at"),
        Index("ix_auth_security_events_correlation", "correlation_id"),
    )
