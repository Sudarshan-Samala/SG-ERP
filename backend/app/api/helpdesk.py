from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.core.database import get_db
from app.api.deps import require_permission
from app.services.helpdesk_service import create_ticket, get_tickets, update_ticket_status
from app.schemas.helpdesk import Ticket, TicketCreate
from app.models.base import User

router = APIRouter()

@router.get("/", response_model=List[Ticket])
def read_tickets(db: Session = Depends(get_db), current_user: User = Depends(require_permission("helpdesk.read"))):
    can_manage = current_user.is_superuser or any(permission.name == "helpdesk.manage" for role in current_user.roles for permission in role.permissions)
    return get_tickets(db, current_user.organization_id, None if can_manage else current_user.id)

@router.post("/", response_model=Ticket)
def create_ticket_endpoint(ticket_in: TicketCreate, db: Session = Depends(get_db), current_user: User = Depends(require_permission("helpdesk.ticket.create"))):
    return create_ticket(db, ticket_in, current_user.organization_id, current_user.id)

@router.patch("/{ticket_id}/status/{new_status}", response_model=Ticket)
def change_ticket_status(ticket_id: UUID, new_status: str, db: Session = Depends(get_db), current_user: User = Depends(require_permission("helpdesk.manage"))):
    ticket = update_ticket_status(db, ticket_id, new_status.upper(), current_user.organization_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket
