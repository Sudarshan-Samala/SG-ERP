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

def _can_manage(user: User) -> bool:
    return user.is_superuser or any(permission.name == "helpdesk.manage" for role in user.roles for permission in role.permissions)

@router.get("/", response_model=List[Ticket])
def read_tickets(db: Session = Depends(get_db), current_user: User = Depends(require_permission("helpdesk.read"))):
    return get_tickets(db, current_user.organization_id, None if _can_manage(current_user) else current_user.id)

@router.get("/summary")
def ticket_summary(db: Session = Depends(get_db), current_user: User = Depends(require_permission("helpdesk.read"))):
    tickets = get_tickets(db, current_user.organization_id, None if _can_manage(current_user) else current_user.id)
    return {"total": len(tickets), "open": sum(t.status == "OPEN" for t in tickets), "in_progress": sum(t.status == "IN_PROGRESS" for t in tickets), "resolved": sum(t.status == "RESOLVED" for t in tickets), "closed": sum(t.status == "CLOSED" for t in tickets), "high_priority": sum(t.priority == "HIGH" and t.status != "CLOSED" for t in tickets)}

@router.post("/", response_model=Ticket)
def create_ticket_endpoint(ticket_in: TicketCreate, db: Session = Depends(get_db), current_user: User = Depends(require_permission("helpdesk.ticket.create"))):
    return create_ticket(db, ticket_in, current_user.organization_id, current_user.id)

@router.patch("/{ticket_id}/status/{new_status}", response_model=Ticket)
def change_ticket_status(ticket_id: UUID, new_status: str, db: Session = Depends(get_db), current_user: User = Depends(require_permission("helpdesk.manage"))):
    ticket = update_ticket_status(db, ticket_id, new_status.upper(), current_user.organization_id)
    if not ticket: raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket
