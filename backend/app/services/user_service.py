from sqlalchemy.orm import Session
from app.models.base import User
from app.schemas.user import UserCreate
from app.services.auth import get_password_hash

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, user_in: UserCreate):
    user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        organization_id=user_in.organization_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
