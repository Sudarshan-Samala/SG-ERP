from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.core.database import get_db
from app.api.deps import get_current_organization, require_permission
from app.services.rbac_service import get_roles, create_role, get_permissions, assign_user_roles
from app.schemas.rbac import Role, RoleCreate, Permission, UserRoleAssignment
from app.models.base import Organization, User

router = APIRouter()

@router.get("/", response_model=List[Role])
def read_roles(db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), _: User = Depends(require_permission("rbac.manage"))):
    return get_roles(db, current_org.id)

@router.get("/permissions", response_model=List[Permission])
def read_permissions(db: Session = Depends(get_db), _: User = Depends(require_permission("rbac.manage"))):
    return get_permissions(db)

@router.post("/", response_model=Role)
def create_role_endpoint(role_in: RoleCreate, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), _: User = Depends(require_permission("rbac.manage"))):
    return create_role(db, role_in, current_org.id)

@router.put("/users/{user_id}/roles", response_model=List[Role])
def replace_user_roles(user_id: UUID, assignment: UserRoleAssignment, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), _: User = Depends(require_permission("rbac.manage"))):
    return assign_user_roles(db, user_id, assignment.role_ids, current_org.id)
