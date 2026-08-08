from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.base import Ticket, User

ALLOWED_TRANSITIONS = {"OPEN": {"IN_PROGRESS", "CLOSED"}, "IN_PROGRESS": {"RESOLVED", "CLOSED"}, "RESOLVED": {"CLOSED", "IN_PROGRESS"}, "CLOSED": set()}


def create_ticket(db: Session, ticket_in, organization_id: UUID, user_id: UUID):
    user = db.query(User).filter(User.id == user_id, User.organization_id == organization_id, User.is_active.is_(True)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ticket requester does not belong to this organization")
    ticket = Ticket(
        **ticket_in.model_dump(),
        organization_id=organization_id,
        requester_id=user_id,
        status="OPEN",
    )
    try:
        db.add(ticket)
        db.flush()
        db.commit()
        db.refresh(ticket)
        return ticket
    except Exception:
        db.rollback()
        raise


def get_tickets(db: Session, organization_id: UUID, user_id: UUID | None = None):
    query = db.query(Ticket).filter(Ticket.organization_id == organization_id)
    if user_id is not None:
        query = query.filter(Ticket.requester_id == user_id)
    return query.order_by(Ticket.created_at.desc()).all()


def get_ticket(db: Session, ticket_id: UUID, organization_id: UUID):
    return db.query(Ticket).filter(Ticket.id == ticket_id, Ticket.organization_id == organization_id).first()


def update_ticket_status(db: Session, ticket_id: UUID, new_status: str, organization_id: UUID):
    ticket = (
        db.query(Ticket)
        .filter(Ticket.id == ticket_id, Ticket.organization_id == organization_id)
        .with_for_update()
        .first()
    )
    if not ticket:
        return None
    if new_status not in ALLOWED_TRANSITIONS.get(ticket.status, set()):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Invalid ticket status transition: {ticket.status} -> {new_status}",
        )
    ticket.status = new_status
    try:
        db.flush()
        db.commit()
        db.refresh(ticket)
        return ticket
    except Exception:
        db.rollback()
        raise
