from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.api.deps import get_current_user, get_current_organization
from app.services.helpdesk_service import create_ticket, get_tickets
from app.schemas.helpdesk import Ticket, TicketCreate
from app.models.base import User, Organization

router = APIRouter()

@router.get("/", response_model=List[Ticket])
def read_tickets(db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization)):
    return get_tickets(db, current_org.id)

@router.post("/", response_model=Ticket)
def create_ticket_endpoint(ticket_in: TicketCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return create_ticket(db, ticket_in, current_user.organization_id, current_user.id)
