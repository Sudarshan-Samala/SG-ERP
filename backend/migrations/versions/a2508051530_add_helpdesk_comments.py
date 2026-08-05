"""add helpdesk ticket comments
Revision ID: a2508051530
Revises: a2508051300
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision='a2508051530';down_revision='a2508051300';branch_labels=None;depends_on=None
def upgrade():
 op.create_table('ticket_comments',sa.Column('id',postgresql.UUID(as_uuid=True),primary_key=True),sa.Column('organization_id',postgresql.UUID(as_uuid=True),sa.ForeignKey('organizations.id'),nullable=False),sa.Column('ticket_id',postgresql.UUID(as_uuid=True),sa.ForeignKey('tickets.id',ondelete='CASCADE'),nullable=False),sa.Column('author_id',postgresql.UUID(as_uuid=True),sa.ForeignKey('users.id'),nullable=False),sa.Column('content',sa.String(),nullable=False),sa.Column('created_at',sa.DateTime(),nullable=False,server_default=sa.func.now()))
 op.create_index('ix_ticket_comments_organization_id','ticket_comments',['organization_id']);op.create_index('ix_ticket_comments_ticket_id','ticket_comments',['ticket_id'])
def downgrade():
 op.drop_index('ix_ticket_comments_ticket_id',table_name='ticket_comments');op.drop_index('ix_ticket_comments_organization_id',table_name='ticket_comments');op.drop_table('ticket_comments')
