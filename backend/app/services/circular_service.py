from sqlalchemy.orm import Session
from app.models.base import Circular
from uuid import UUID

def create_circular(db: Session, circ_in, organization_id: UUID):
    circ = Circular(**circ_in.dict(), organization_id=organization_id)
    db.add(circ)
    db.commit()
    db.refresh(circ)
    return circ
