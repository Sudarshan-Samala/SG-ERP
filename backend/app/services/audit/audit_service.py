from sqlalchemy.orm import Session
from app.models.base import AuditLog
from uuid import UUID

def log_action(db: Session, organization_id: UUID, user_id: UUID, action: str, entity_type: str, entity_id: UUID, previous_values: str = None, new_values: str = None):
    log = AuditLog(
        organization_id=organization_id,
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        previous_values=previous_values,
        new_values=new_values
    )
    db.add(log)
    db.commit()
