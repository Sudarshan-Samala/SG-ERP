import uuid
from datetime import datetime
from sqlalchemy import Column,DateTime,ForeignKey,String
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base

class TicketComment(Base):
    __tablename__='ticket_comments'
    id=Column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
    organization_id=Column(UUID(as_uuid=True),ForeignKey('organizations.id'),nullable=False,index=True)
    ticket_id=Column(UUID(as_uuid=True),ForeignKey('tickets.id',ondelete='CASCADE'),nullable=False,index=True)
    author_id=Column(UUID(as_uuid=True),ForeignKey('users.id'),nullable=False)
    content=Column(String,nullable=False)
    created_at=Column(DateTime,default=datetime.utcnow,nullable=False)
