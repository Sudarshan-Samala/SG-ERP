from sqlalchemy.orm import Session
from app.models.base import Communication
from app.schemas.communication import CommunicationCreate
from uuid import UUID

def create_communication(db: Session, comm_in: CommunicationCreate, organization_id: UUID):
    comm = Communication(**comm_in.model_dump(), organization_id=organization_id, status="SENT")
    db.add(comm)
    db.commit()
    db.refresh(comm)
    return comm

def get_communications(db: Session, organization_id: UUID):
    return db.query(Communication).filter(Communication.organization_id == organization_id).all()
