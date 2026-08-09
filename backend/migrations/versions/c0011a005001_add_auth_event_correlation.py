"""Add correlation identifiers to authentication security events.

Revision ID: c0011a005001
Revises: c0011a004001
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "c0011a005001"
down_revision: Union[str, Sequence[str], None] = "c0011a004001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("auth_security_events", sa.Column("correlation_id", sa.String(length=64), nullable=True))
    op.create_index("ix_auth_security_events_correlation", "auth_security_events", ["correlation_id"])


def downgrade() -> None:
    op.drop_index("ix_auth_security_events_correlation", table_name="auth_security_events")
    op.drop_column("auth_security_events", "correlation_id")
