"""add attendance correction workflow
Revision ID: b1f4a1d8c901
Revises: a2508051730
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision='b1f4a1d8c901'
down_revision='a2508051730'
branch_labels=None
depends_on=None

def upgrade():
    op.create_table(
        'attendance_corrections',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('attendance_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('attendance.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('requested_status', sa.String(), nullable=False),
        sa.Column('reason', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='PENDING'),
        sa.Column('requested_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('reviewed_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_attendance_corrections_org', 'attendance_corrections', ['organization_id'])
    op.create_index('ix_attendance_corrections_attendance', 'attendance_corrections', ['attendance_id'])
    op.create_index('ix_attendance_corrections_status', 'attendance_corrections', ['status'])

def downgrade():
    op.drop_table('attendance_corrections')
