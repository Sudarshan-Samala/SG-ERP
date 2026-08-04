from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.api.deps import get_current_user
from app.services.rbac_service import get_roles, create_role
from app.schemas.rbac import Role, RoleCreate
from app.models.base import User

router = APIRouter()

@router.get("/", response_model=List[Role])
def read_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Superuser can see all, regular users see org-scoped
    if current_user.is_superuser:
        return get_roles(db)
    return get_roles(db, organization_id=current_user.organization_id)

@router.post("/", response_model=Role)
def create_role_endpoint(
    role_in: RoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Only superusers or specific admin roles (to be defined) can create roles
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return create_role(db, role_in)
