from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.api.deps import get_current_organization
from app.services.communication_service import create_communication, get_communications
from app.schemas.communication import Communication, CommunicationCreate
from app.models.base import Organization

router = APIRouter()

@router.get("/", response_model=List[Communication])
def read_communications(db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization)):
    return get_communications(db, current_org.id)

@router.post("/", response_model=Communication)
def create_communication_endpoint(comm_in: CommunicationCreate, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization)):
    return create_communication(db, comm_in, current_org.id)
