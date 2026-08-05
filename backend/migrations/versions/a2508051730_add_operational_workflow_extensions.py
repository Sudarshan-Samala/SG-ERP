"""add operational workflow extensions
Revision ID: a2508051730
Revises: a2508051530
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision='a2508051730';down_revision='a2508051530';branch_labels=None;depends_on=None

def upgrade():
 op.create_table('helpdesk_assignments',sa.Column('id',postgresql.UUID(as_uuid=True),primary_key=True),sa.Column('organization_id',postgresql.UUID(as_uuid=True),sa.ForeignKey('organizations.id'),nullable=False),sa.Column('ticket_id',postgresql.UUID(as_uuid=True),sa.ForeignKey('tickets.id',ondelete='CASCADE'),nullable=False,unique=True),sa.Column('assignee_id',postgresql.UUID(as_uuid=True),sa.ForeignKey('users.id'),nullable=True),sa.Column('sla_due_at',sa.DateTime(),nullable=True),sa.Column('updated_by',postgresql.UUID(as_uuid=True),sa.ForeignKey('users.id'),nullable=False),sa.Column('updated_at',sa.DateTime(),nullable=False,server_default=sa.func.now()))
 op.create_index('ix_helpdesk_assignments_org','helpdesk_assignments',['organization_id']);op.create_index('ix_helpdesk_assignments_ticket','helpdesk_assignments',['ticket_id']);op.create_index('ix_helpdesk_assignments_assignee','helpdesk_assignments',['assignee_id']);op.create_index('ix_helpdesk_assignments_sla','helpdesk_assignments',['sla_due_at'])
 op.create_table('communication_targets',sa.Column('id',postgresql.UUID(as_uuid=True),primary_key=True),sa.Column('organization_id',postgresql.UUID(as_uuid=True),sa.ForeignKey('organizations.id'),nullable=False),sa.Column('communication_id',postgresql.UUID(as_uuid=True),sa.ForeignKey('communications.id',ondelete='CASCADE'),nullable=False,unique=True),sa.Column('branch_id',postgresql.UUID(as_uuid=True),sa.ForeignKey('branches.id'),nullable=True),sa.Column('grade_id',postgresql.UUID(as_uuid=True),sa.ForeignKey('grades.id'),nullable=True))
 op.create_index('ix_communication_targets_org','communication_targets',['organization_id']);op.create_index('ix_communication_targets_comm','communication_targets',['communication_id'])
 op.create_table('inventory_reorder_policies',sa.Column('id',postgresql.UUID(as_uuid=True),primary_key=True),sa.Column('organization_id',postgresql.UUID(as_uuid=True),sa.ForeignKey('organizations.id'),nullable=False),sa.Column('item_id',postgresql.UUID(as_uuid=True),sa.ForeignKey('inventory_items.id',ondelete='CASCADE'),nullable=False,unique=True),sa.Column('reorder_level',sa.Integer(),nullable=False,server_default='5'),sa.Column('updated_at',sa.DateTime(),nullable=False,server_default=sa.func.now()),sa.UniqueConstraint('organization_id','item_id',name='uq_inventory_reorder_org_item'))
 op.create_index('ix_inventory_reorder_org','inventory_reorder_policies',['organization_id']);op.create_index('ix_inventory_reorder_item','inventory_reorder_policies',['item_id'])

def downgrade():
 op.drop_table('inventory_reorder_policies');op.drop_table('communication_targets');op.drop_table('helpdesk_assignments')
