"""student permanent identity and lifecycle

Revision ID: a2608071200
Revises: a2508051730
"""
from alembic import op
import sqlalchemy as sa

revision = "a2608071200"
down_revision = "a2508051730"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("students", sa.Column("student_number", sa.Integer(), nullable=True))
    op.add_column("students", sa.Column("status", sa.String(length=24), nullable=False, server_default="ACTIVE"))
    op.add_column("students", sa.Column("status_changed_at", sa.DateTime(), nullable=True))

    # Backfill stable six-digit-or-longer numbers independently for each school.
    # Existing rows are ordered by creation time/id so the migration is deterministic.
    op.execute("""
        WITH ranked AS (
            SELECT id, organization_id,
                   99999 + ROW_NUMBER() OVER (PARTITION BY organization_id ORDER BY created_at, id) AS n
            FROM students
        )
        UPDATE students s SET student_number = ranked.n
        FROM ranked WHERE ranked.id = s.id
    """)
    op.alter_column("students", "student_number", nullable=False)

    # Admission numbers were historically globally unique. SaaS schools must be
    # independent, so replace that with tenant-scoped uniqueness.
    op.execute("ALTER TABLE students DROP CONSTRAINT IF EXISTS students_admission_number_key")
    op.create_unique_constraint("uq_students_org_admission_number", "students", ["organization_id", "admission_number"])
    op.create_unique_constraint("uq_students_org_student_number", "students", ["organization_id", "student_number"])
    op.create_index("ix_students_organization_id", "students", ["organization_id"])
    op.create_index("ix_students_branch_id", "students", ["branch_id"])
    op.create_index("ix_students_status", "students", ["status"])


def downgrade():
    op.drop_index("ix_students_status", table_name="students")
    op.drop_index("ix_students_branch_id", table_name="students")
    op.drop_index("ix_students_organization_id", table_name="students")
    op.drop_constraint("uq_students_org_student_number", "students", type_="unique")
    op.drop_constraint("uq_students_org_admission_number", "students", type_="unique")
    # Downgrade cannot safely restore global admission uniqueness if two schools
    # now share a number. Refuse destructive downgrade rather than deleting data.
    op.drop_column("students", "status_changed_at")
    op.drop_column("students", "status")
    op.drop_column("students", "student_number")
