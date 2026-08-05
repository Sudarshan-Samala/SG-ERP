"""Merge CORE-001.1 authentication migrations with the existing ERP migration head.

Revision ID: c0011a003001
Revises: 06533392cbfc, c0011a002001

This is an Alembic merge revision only. It intentionally performs no schema
operations; it joins the two valid migration branches so `alembic upgrade head`
has a single deterministic target again.
"""
from typing import Sequence, Union

revision: str = "c0011a003001"
down_revision: Union[str, Sequence[str], None] = (
    "06533392cbfc",
    "c0011a002001",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Merge migration branches without changing schema."""
    pass


def downgrade() -> None:
    """Split back to the two parent migration heads without changing schema."""
    pass
