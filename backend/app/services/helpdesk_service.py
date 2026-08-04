from sqlalchemy.orm import Session
from app.models.base import Ticket
from app.schemas.helpdesk import TicketCreate
from uuid import UUID

def create_ticket(db: Session, ticket_in: TicketCreate, organization_id: UUID, user_id: UUID):
    ticket = Ticket(
        **ticket_in.model_dump(),
        organization_id=organization_id,
        user_id=user_id,
        status="OPEN"
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket

def get_tickets(db: Session, organization_id: UUID):
    return db.query(Ticket).filter(Ticket.organization_id == organization_id).all()
