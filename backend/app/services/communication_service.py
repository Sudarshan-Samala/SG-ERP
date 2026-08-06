from uuid import UUID
from fastapi import HTTPException,status
from sqlalchemy.orm import Session
from app.models.base import Communication
from app.services.audit.audit_service import log_action
ALLOWED_TRANSITIONS={'DRAFT':{'QUEUED','CANCELLED'},'QUEUED':{'SENT','FAILED','CANCELLED'},'FAILED':{'QUEUED','CANCELLED'},'SENT':set(),'CANCELLED':set()}
def create_communication(db:Session,comm_in,organization_id:UUID,user_id:UUID):
 try:
  comm=Communication(**comm_in.model_dump(),organization_id=organization_id,status='DRAFT');db.add(comm);db.flush();log_action(db,organization_id,user_id,'CREATE','COMMUNICATION',comm.id,new_values=f'audience={comm.recipient_type};channel={comm.channel};status=DRAFT');db.commit();db.refresh(comm);return comm
 except Exception:db.rollback();raise
def get_communications(db:Session,organization_id:UUID):return db.query(Communication).filter(Communication.organization_id==organization_id).order_by(Communication.id.desc()).all()
def update_communication_status(db:Session,communication_id:UUID,new_status:str,organization_id:UUID,user_id:UUID):
 try:
  comm=db.query(Communication).filter(Communication.id==communication_id,Communication.organization_id==organization_id).with_for_update().first()
  if not comm:return None
  old=comm.status
  if new_status not in ALLOWED_TRANSITIONS.get(old,set()):raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail=f'Invalid communication status transition: {old} -> {new_status}')
  comm.status=new_status;db.flush();log_action(db,organization_id,user_id,'UPDATE','COMMUNICATION',comm.id,old_values=f'status={old}',new_values=f'status={new_status}');db.commit();db.refresh(comm);return comm
 except HTTPException:db.rollback();raise
 except Exception:db.rollback();raise
