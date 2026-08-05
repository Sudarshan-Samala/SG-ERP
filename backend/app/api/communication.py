from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.core.database import get_db
from app.api.deps import get_current_organization, require_permission
from app.services.communication_service import create_communication, get_communications, update_communication_status
from app.schemas.communication import Communication, CommunicationCreate
from app.models.base import Organization, User

router = APIRouter()

@router.get("/", response_model=List[Communication])
def read_communications(db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), _: User = Depends(require_permission("communication.read"))):
    return get_communications(db, current_org.id)

@router.post("/", response_model=Communication)
def create_communication_endpoint(comm_in: CommunicationCreate, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), _: User = Depends(require_permission("communication.create"))):
    return create_communication(db, comm_in, current_org.id)

@router.patch("/{communication_id}/status/{new_status}", response_model=Communication)
def change_communication_status(communication_id: UUID, new_status: str, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), _: User = Depends(require_permission("communication.manage"))):
    communication = update_communication_status(db, communication_id, new_status.upper(), current_org.id)
    if not communication:
        raise HTTPException(status_code=404, detail="Communication not found")
    return communication
