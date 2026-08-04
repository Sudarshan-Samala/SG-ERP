from sqlalchemy.orm import Session
from app.models.base import User, Role, Branch
from app.schemas.user_management import UserCreate
from app.services.auth import get_password_hash
from uuid import UUID

def get_users(db: Session, organization_id: UUID):
    return db.query(User).filter(User.organization_id == organization_id).all()

def create_user(db: Session, user_in: UserCreate):
    user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        organization_id=user_in.organization_id,
        is_active=user_in.is_active
    )
    
    if user_in.branch_ids:
        user.branches = db.query(Branch).filter(Branch.id.in_(user_in.branch_ids)).all()
        
    if user_in.role_ids:
        user.roles = db.query(Role).filter(Role.id.in_(user_in.role_ids)).all()
        
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
