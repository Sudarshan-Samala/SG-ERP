from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_organization
from app.services.circular_service import create_circular
from app.schemas.circular import Circular
from app.models.base import Organization

router = APIRouter()

@router.post("/", response_model=Circular)
def create_circular_endpoint(circ_in, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization)):
    return create_circular(db, circ_in, current_org.id)
