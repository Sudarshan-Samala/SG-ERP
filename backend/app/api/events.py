from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_organization
from app.services.event_service import create_event
from app.schemas.event import SchoolEvent
from app.models.base import Organization

router = APIRouter()

@router.post("/", response_model=SchoolEvent)
def create_event_endpoint(event_in, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization)):
    return create_event(db, event_in, current_org.id)
