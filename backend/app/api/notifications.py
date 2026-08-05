from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.base import Notification, User

router = APIRouter()


class NotificationCreate(BaseModel):
    user_id: UUID
    title: str = Field(min_length=2, max_length=160)
    message: str = Field(min_length=2, max_length=2000)
    category: str = Field(default="GENERAL", max_length=40)
    link: str | None = Field(default=None, max_length=500)


def _serialize(item: Notification):
    return {
        "id": item.id,
        "title": item.title,
        "message": item.message,
        "category": item.category,
        "link": item.link,
        "is_read": item.is_read,
        "created_at": item.created_at,
    }


@router.get("/")
def list_notifications(unread_only: bool = False, limit: int = 50, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    limit = min(max(limit, 1), 100)
    query = db.query(Notification).filter(Notification.organization_id == current_user.organization_id, Notification.user_id == current_user.id)
    if unread_only:
        query = query.filter(Notification.is_read.is_(False))
    return [_serialize(item) for item in query.order_by(Notification.created_at.desc()).limit(limit).all()]


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_notification(payload: NotificationCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    permission_names = {permission.name for role in current_user.roles for permission in role.permissions}
    if not current_user.is_superuser and "communication.manage" not in permission_names:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permission")
    recipient = db.query(User).filter(User.id == payload.user_id, User.organization_id == current_user.organization_id, User.is_active.is_(True)).first()
    if not recipient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipient not found")
    item = Notification(
        organization_id=current_user.organization_id,
        user_id=recipient.id,
        title=payload.title.strip(),
        message=payload.message.strip(),
        category=payload.category.strip().upper() or "GENERAL",
        link=payload.link.strip() if payload.link else None,
        is_read=False,
    )
    db.add(item); db.commit(); db.refresh(item)
    return _serialize(item)


@router.patch("/{notification_id}/read")
def mark_read(notification_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = db.query(Notification).filter(Notification.id == notification_id, Notification.organization_id == current_user.organization_id, Notification.user_id == current_user.id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    item.is_read = True
    item.read_at = datetime.utcnow()
    db.commit(); db.refresh(item)
    return _serialize(item)


@router.post("/read-all")
def mark_all_read(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    now = datetime.utcnow()
    db.query(Notification).filter(Notification.organization_id == current_user.organization_id, Notification.user_id == current_user.id, Notification.is_read.is_(False)).update({Notification.is_read: True, Notification.read_at: now}, synchronize_session=False)
    db.commit()
    return {"status": "ok"}
