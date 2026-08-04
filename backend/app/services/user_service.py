from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.base import User
from app.schemas.user import UserCreate
from app.services.auth import get_password_hash


def get_user_by_email(db: Session, email: str):
    normalized_email = (email or "").strip().lower()
    if not normalized_email:
        return None
    return db.query(User).filter(func.lower(User.email) == normalized_email).first()


def create_user(db: Session, user_in: UserCreate):
    user = User(
        email=user_in.email.strip().lower(),
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        organization_id=user_in.organization_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
