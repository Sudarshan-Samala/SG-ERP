from sqlalchemy.orm import Session
from app.models.base import Role, Permission
from app.schemas.rbac import RoleCreate, PermissionCreate
from uuid import UUID

def get_roles(db: Session, organization_id: UUID = None):
    query = db.query(Role)
    if organization_id:
        query = query.filter((Role.organization_id == organization_id) | (Role.organization_id == None))
    return query.all()

def create_role(db: Session, role_in: RoleCreate):
    role = Role(**role_in.dict())
    db.add(role)
    db.commit()
    db.refresh(role)
    return role

def get_permissions(db: Session):
    return db.query(Permission).all()

def create_permission(db: Session, perm_in: PermissionCreate):
    perm = Permission(**perm_in.dict())
    db.add(perm)
    db.commit()
    db.refresh(perm)
    return perm
