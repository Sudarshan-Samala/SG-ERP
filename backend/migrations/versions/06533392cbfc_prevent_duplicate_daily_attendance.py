"""prevent duplicate daily attendance

Revision ID: 06533392cbfc
Revises: 0c0417af0dc9
Create Date: 2026-08-03 23:20:52.542240
"""

from typing import Sequence, Union

from alembic import op


revision: str = "06533392cbfc"
down_revision: Union[str, Sequence[str], None] = "0c0417af0dc9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE UNIQUE INDEX uq_attendance_student_daily
        ON attendance (
            organization_id,
            student_id,
            (date::date)
        )
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP INDEX IF EXISTS uq_attendance_student_daily
        """
    )
