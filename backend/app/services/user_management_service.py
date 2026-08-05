from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.models.base import User, Role, Branch
from app.schemas.user_management import UserCreate
from app.services.auth import get_password_hash
from uuid import UUID


def get_users(db: Session, organization_id: UUID):
    return db.query(User).filter(User.organization_id == organization_id).order_by(User.email).all()


def create_user(db: Session, user_in: UserCreate):
    branch_ids = set(user_in.branch_ids or [])
    role_ids = set(user_in.role_ids or [])
    branches = db.query(Branch).filter(Branch.organization_id == user_in.organization_id, Branch.id.in_(branch_ids)).all() if branch_ids else []
    roles = db.query(Role).filter(Role.organization_id == user_in.organization_id, Role.id.in_(role_ids)).all() if role_ids else []
    if len(branches) != len(branch_ids):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or cross-tenant branch")
    if len(roles) != len(role_ids):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or cross-tenant role")
    user = User(email=user_in.email.lower(), hashed_password=get_password_hash(user_in.password), full_name=user_in.full_name, organization_id=user_in.organization_id, is_active=user_in.is_active, branches=branches, roles=roles)
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User email already exists")
    db.refresh(user)
    return user
