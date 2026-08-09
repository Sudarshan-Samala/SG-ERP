from datetime import datetime
from typing import Literal
from uuid import UUID
from fastapi import APIRouter,Depends,HTTPException,status
from pydantic import BaseModel,Field
from sqlalchemy.orm import Session
from app.api.deps import get_current_user,require_permission
from app.core.database import get_db
from app.models.base import Notification,User
from app.services.audit.audit_service import log_action
router=APIRouter()
NotificationCategory=Literal['GENERAL','ACADEMIC','FINANCE','ATTENDANCE','HR','SYSTEM']
class NotificationCreate(BaseModel):
 user_id:UUID;title:str=Field(min_length=2,max_length=160);message:str=Field(min_length=2,max_length=2000);category:NotificationCategory='GENERAL';link:str|None=Field(default=None,max_length=500)
def _serialize(item):return {'id':item.id,'title':item.title,'message':item.message,'category':item.category,'link':item.link,'is_read':item.is_read,'created_at':item.created_at}
@router.get('/')
def list_notifications(unread_only:bool=False,limit:int=50,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
 q=db.query(Notification).filter(Notification.organization_id==current_user.organization_id,Notification.user_id==current_user.id)
 if unread_only:q=q.filter(Notification.is_read.is_(False))
 safe_limit=min(max(limit,1),100)
 return [_serialize(x) for x in q.order_by(Notification.created_at.desc()).limit(safe_limit).all()]
@router.get('/summary')
def notification_summary(db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
 q=db.query(Notification).filter(Notification.organization_id==current_user.organization_id,Notification.user_id==current_user.id);total=q.count();unread=q.filter(Notification.is_read.is_(False)).count();return {'total':total,'unread':unread,'read':total-unread}
@router.post('/',status_code=status.HTTP_201_CREATED)
def create_notification(payload:NotificationCreate,db:Session=Depends(get_db),current_user:User=Depends(require_permission('communication.manage'))):
 recipient=db.query(User).filter(User.id==payload.user_id,User.organization_id==current_user.organization_id,User.is_active.is_(True)).first()
 if not recipient:raise HTTPException(status_code=404,detail='Recipient not found')
 title=payload.title.strip();message=payload.message.strip();category=payload.category
 link=payload.link.strip() if payload.link else None
 if not title or not message:raise HTTPException(status_code=422,detail='Notification title and message are required')
 if link and not (link.startswith('/') or link.startswith('https://')):raise HTTPException(status_code=422,detail='Notification link must be an application path or HTTPS URL')
 item=Notification(organization_id=current_user.organization_id,user_id=recipient.id,title=title,message=message,category=category,link=link,is_read=False)
 try:
  db.add(item);db.flush();log_action(db,current_user.organization_id,current_user.id,'CREATE','NOTIFICATION',item.id,new_values=f'user_id={recipient.id};category={category}');db.commit();db.refresh(item);return _serialize(item)
 except Exception:db.rollback();raise
@router.patch('/{notification_id}/read')
def mark_read(notification_id:UUID,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
 try:
  item=db.query(Notification).filter(Notification.id==notification_id,Notification.organization_id==current_user.organization_id,Notification.user_id==current_user.id).with_for_update().first()
  if not item:raise HTTPException(status_code=404,detail='Notification not found')
  if not item.is_read:item.is_read=True;item.read_at=datetime.utcnow();db.commit();db.refresh(item)
  return _serialize(item)
 except HTTPException:db.rollback();raise
 except Exception:db.rollback();raise
@router.post('/read-all')
def mark_all_read(db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
 try:
  now=datetime.utcnow();updated=db.query(Notification).filter(Notification.organization_id==current_user.organization_id,Notification.user_id==current_user.id,Notification.is_read.is_(False)).update({Notification.is_read:True,Notification.read_at:now},synchronize_session=False);db.commit();return {'status':'ok','updated':updated}
 except Exception:db.rollback();raise
