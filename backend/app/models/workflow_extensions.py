import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base

class HelpdeskAssignment(Base):
    __tablename__='helpdesk_assignments'
    id=Column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
    organization_id=Column(UUID(as_uuid=True),ForeignKey('organizations.id'),nullable=False,index=True)
    ticket_id=Column(UUID(as_uuid=True),ForeignKey('tickets.id',ondelete='CASCADE'),nullable=False,unique=True,index=True)
    assignee_id=Column(UUID(as_uuid=True),ForeignKey('users.id'),nullable=True,index=True)
    sla_due_at=Column(DateTime,nullable=True,index=True)
    updated_by=Column(UUID(as_uuid=True),ForeignKey('users.id'),nullable=False)
    updated_at=Column(DateTime,default=datetime.utcnow,onupdate=datetime.utcnow,nullable=False)

class CommunicationTarget(Base):
    __tablename__='communication_targets'
    id=Column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
    organization_id=Column(UUID(as_uuid=True),ForeignKey('organizations.id'),nullable=False,index=True)
    communication_id=Column(UUID(as_uuid=True),ForeignKey('communications.id',ondelete='CASCADE'),nullable=False,unique=True,index=True)
    branch_id=Column(UUID(as_uuid=True),ForeignKey('branches.id'),nullable=True,index=True)
    grade_id=Column(UUID(as_uuid=True),ForeignKey('grades.id'),nullable=True,index=True)

class InventoryReorderPolicy(Base):
    __tablename__='inventory_reorder_policies'
    id=Column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
    organization_id=Column(UUID(as_uuid=True),ForeignKey('organizations.id'),nullable=False,index=True)
    item_id=Column(UUID(as_uuid=True),ForeignKey('inventory_items.id',ondelete='CASCADE'),nullable=False,unique=True,index=True)
    reorder_level=Column(Integer,nullable=False,default=5)
    updated_at=Column(DateTime,default=datetime.utcnow,onupdate=datetime.utcnow,nullable=False)
    __table_args__=(UniqueConstraint('organization_id','item_id',name='uq_inventory_reorder_org_item'),)
