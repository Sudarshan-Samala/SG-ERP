from sqlalchemy.orm import Session
from app.models.base import SchoolEvent
from uuid import UUID

def create_event(db: Session, event_in, organization_id: UUID):
    ev = SchoolEvent(**event_in.dict(), organization_id=organization_id)
    db.add(ev)
    db.commit()
    db.refresh(ev)
    return ev
