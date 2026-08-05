from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.base import Role, Permission, User
from app.schemas.rbac import RoleCreate
from uuid import UUID


def get_roles(db: Session, organization_id: UUID):
    return db.query(Role).filter(Role.organization_id == organization_id).order_by(Role.name).all()


def create_role(db: Session, role_in: RoleCreate, organization_id: UUID):
    if role_in.organization_id is not None and role_in.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cross-tenant role creation denied")
    name = role_in.name.strip()
    if len(name) < 2:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role name must contain at least 2 characters")
    existing = db.query(Role).filter(Role.organization_id == organization_id, Role.name.ilike(name)).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Role already exists")
    permission_names = set(role_in.permission_names)
    permissions = db.query(Permission).filter(Permission.name.in_(permission_names)).all() if permission_names else []
    if len(permissions) != len(permission_names):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown permission")
    role = Role(name=name, organization_id=organization_id, permissions=permissions)
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


def delete_role(db: Session, role_id: UUID, organization_id: UUID):
    role = db.query(Role).filter(Role.id == role_id, Role.organization_id == organization_id).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    if role.users:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Remove this role from all users before deleting it")
    db.delete(role)
    db.commit()


def assign_user_roles(db: Session, user_id: UUID, role_ids: list[UUID], organization_id: UUID):
    user = db.query(User).filter(User.id == user_id, User.organization_id == organization_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Superuser role assignment is not allowed")
    unique_ids = set(role_ids)
    roles = db.query(Role).filter(Role.id.in_(unique_ids), Role.organization_id == organization_id).all() if unique_ids else []
    if len(roles) != len(unique_ids):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or cross-tenant role")
    user.roles = roles
    db.commit()
    db.refresh(user)
    return user.roles


def get_permissions(db: Session):
    return db.query(Permission).order_by(Permission.name).all()
