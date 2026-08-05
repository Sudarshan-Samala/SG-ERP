"""Add authentication security events.

Revision ID: c0011a002001
Revises: c0011a001001
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "c0011a002001"
down_revision = "c0011a001001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "auth_security_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("outcome", sa.String(length=32), nullable=False),
        sa.Column("email_fingerprint", sa.String(length=64), nullable=True),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["session_id"], ["auth_sessions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_auth_security_events_org_created", "auth_security_events", ["organization_id", "created_at"])
    op.create_index("ix_auth_security_events_user_created", "auth_security_events", ["user_id", "created_at"])
    op.create_index("ix_auth_security_events_type_created", "auth_security_events", ["event_type", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_auth_security_events_type_created", table_name="auth_security_events")
    op.drop_index("ix_auth_security_events_user_created", table_name="auth_security_events")
    op.drop_index("ix_auth_security_events_org_created", table_name="auth_security_events")
    op.drop_table("auth_security_events")
