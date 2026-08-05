from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.api.deps import get_current_organization, require_permission
from app.services.user_management_service import get_users, create_user
from app.schemas.user_management import User, UserCreate
from app.models.base import Organization

router = APIRouter()

@router.get("/", response_model=List[User])
def read_users(db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), _=Depends(require_permission("users.manage"))):
    return get_users(db, organization_id=current_org.id)

@router.post("/", response_model=User)
def create_user_endpoint(user_in: UserCreate, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), _=Depends(require_permission("users.manage"))):
    user_in.organization_id = current_org.id
    return create_user(db, user_in)
