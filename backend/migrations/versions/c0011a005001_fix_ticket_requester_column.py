"""Align the tickets requester column with the ORM model.

Revision ID: c0011a005001
Revises: c0011a004001

The original ticket migration created ``tickets.user_id`` while the current
Ticket model and helpdesk service use ``tickets.requester_id``. This migration
renames the existing column in-place so existing ticket data is preserved.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "c0011a005001"
down_revision: Union[str, Sequence[str], None] = "c0011a004001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "tickets" not in inspector.get_table_names():
        return

    columns = {column["name"]: column for column in inspector.get_columns("tickets")}

    if "requester_id" not in columns and "user_id" in columns:
        op.alter_column(
            "tickets",
            "user_id",
            new_column_name="requester_id",
            existing_type=postgresql.UUID(as_uuid=True),
            existing_nullable=columns["user_id"]["nullable"],
        )

    # The ORM model allows a ticket requester to be nullable.
    if "requester_id" in {column["name"] for column in inspector.get_columns("tickets")}:
        op.alter_column(
            "tickets",
            "requester_id",
            existing_type=postgresql.UUID(as_uuid=True),
            existing_nullable=True,
            nullable=True,
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "tickets" not in inspector.get_table_names():
        return

    columns = {column["name"]: column for column in inspector.get_columns("tickets")}

    if "user_id" not in columns and "requester_id" in columns:
        op.alter_column(
            "tickets",
            "requester_id",
            new_column_name="user_id",
            existing_type=postgresql.UUID(as_uuid=True),
            existing_nullable=True,
        )
