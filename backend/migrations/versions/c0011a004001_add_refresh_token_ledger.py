"""Add refresh-token ledger for complete rotation and replay detection.

Revision ID: c0011a004001
Revises: c0011a003001
"""
from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "c0011a004001"
down_revision: Union[str, Sequence[str], None] = "c0011a003001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "auth_refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_family_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("issued_at", sa.DateTime(), nullable=False),
        sa.Column("consumed_at", sa.DateTime(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["session_id"], ["auth_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash", name="uq_auth_refresh_tokens_token_hash"),
    )
    op.create_index("ix_auth_refresh_tokens_session_id", "auth_refresh_tokens", ["session_id"])
    op.create_index("ix_auth_refresh_tokens_token_family_id", "auth_refresh_tokens", ["token_family_id"])
    op.create_index("ix_auth_refresh_tokens_expires_at", "auth_refresh_tokens", ["expires_at"])
    op.create_index(
        "ix_auth_refresh_tokens_session_family",
        "auth_refresh_tokens",
        ["session_id", "token_family_id"],
    )

    bind = op.get_bind()
    rows = bind.execute(
        sa.text(
            "SELECT id, token_family_id, refresh_token_hash, created_at, expires_at, revoked_at "
            "FROM auth_sessions"
        )
    ).mappings().all()
    for row in rows:
        bind.execute(
            sa.text(
                "INSERT INTO auth_refresh_tokens "
                "(id, session_id, token_family_id, token_hash, issued_at, consumed_at, expires_at, revoked_at) "
                "VALUES (:id, :session_id, :family, :hash, :issued, NULL, :expires, :revoked)"
            ),
            {
                "id": uuid.uuid4(),
                "session_id": row["id"],
                "family": row["token_family_id"],
                "hash": row["refresh_token_hash"],
                "issued": row["created_at"],
                "expires": row["expires_at"],
                "revoked": row["revoked_at"],
            },
        )


def downgrade() -> None:
    op.drop_index("ix_auth_refresh_tokens_session_family", table_name="auth_refresh_tokens")
    op.drop_index("ix_auth_refresh_tokens_expires_at", table_name="auth_refresh_tokens")
    op.drop_index("ix_auth_refresh_tokens_token_family_id", table_name="auth_refresh_tokens")
    op.drop_index("ix_auth_refresh_tokens_session_id", table_name="auth_refresh_tokens")
    op.drop_table("auth_refresh_tokens")
