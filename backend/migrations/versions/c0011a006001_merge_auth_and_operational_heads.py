"""Merge the authentication and operational ERP migration heads.

Revision ID: c0011a006001
Revises: b1f4a1d8c901, c0011a005001

The repository previously merged the ERP and authentication branches at
c0011a003001, but subsequent work continued on both branches independently:
- the operational ERP branch reached b1f4a1d8c901;
- the authentication hardening branch reached c0011a005001.

This merge revision performs no schema operations. It restores a single
Alembic head so `alembic upgrade head` is deterministic on fresh and existing
databases.
"""

from typing import Sequence, Union

revision: str = "c0011a006001"
down_revision: Union[str, Sequence[str], None] = (
    "b1f4a1d8c901",
    "c0011a005001",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Merge migration branches without changing the database schema."""
    pass


def downgrade() -> None:
    """Split back to the two parent heads without changing the schema."""
    pass
