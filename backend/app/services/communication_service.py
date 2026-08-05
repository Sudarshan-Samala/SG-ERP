from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.base import Communication

ALLOWED_TRANSITIONS = {
    "DRAFT": {"QUEUED", "CANCELLED"},
    "QUEUED": {"SENT", "FAILED", "CANCELLED"},
    "FAILED": {"QUEUED", "CANCELLED"},
    "SENT": set(),
    "CANCELLED": set(),
}


def create_communication(db: Session, comm_in, organization_id: UUID):
    # Creating a record must not falsely claim that an external provider delivered it.
    comm = Communication(**comm_in.model_dump(), organization_id=organization_id, status="DRAFT")
    db.add(comm); db.commit(); db.refresh(comm)
    return comm


def get_communications(db: Session, organization_id: UUID):
    return db.query(Communication).filter(Communication.organization_id == organization_id).all()


def update_communication_status(db: Session, communication_id: UUID, new_status: str, organization_id: UUID):
    comm = db.query(Communication).filter(Communication.id == communication_id, Communication.organization_id == organization_id).first()
    if not comm:
        return None
    if new_status not in ALLOWED_TRANSITIONS.get(comm.status, set()):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Invalid communication status transition: {comm.status} -> {new_status}")
    comm.status = new_status
    db.commit(); db.refresh(comm)
    return comm
