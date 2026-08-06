from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.core.database import get_db
from app.api.deps import accessible_branch_ids,enforce_branch_access,get_current_organization,require_permission
from app.services.communication_service import create_communication,get_communications,update_communication_status
from app.schemas.communication import Communication,CommunicationCreate
from app.models.base import Organization,User,Branch,Grade
from app.models.workflow_extensions import CommunicationTarget
from app.services.audit.audit_service import log_action
router=APIRouter()
class TargetUpdate(BaseModel):branch_id:UUID|None=None;grade_id:UUID|None=None
@router.get('/',response_model=List[Communication])
def read_communications(db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),_:User=Depends(require_permission('communication.read'))):return get_communications(db,current_org.id)
@router.get('/summary')
def communication_summary(db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),_:User=Depends(require_permission('communication.read'))):
 items=get_communications(db,current_org.id);return {'total':len(items),'draft':sum(x.status=='DRAFT' for x in items),'queued':sum(x.status=='QUEUED' for x in items),'sent':sum(x.status=='SENT' for x in items),'failed':sum(x.status=='FAILED' for x in items),'cancelled':sum(x.status=='CANCELLED' for x in items)}
@router.get('/target-options')
def target_options(db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),current_user:User=Depends(require_permission('communication.create'))):
 branch_ids=accessible_branch_ids(current_user);bq=db.query(Branch).filter(Branch.organization_id==current_org.id,Branch.is_active.is_(True));gq=db.query(Grade).filter(Grade.organization_id==current_org.id)
 if not current_user.is_superuser:bq=bq.filter(Branch.id.in_(branch_ids)) if branch_ids else bq.filter(False);gq=gq.filter(Grade.branch_id.in_(branch_ids)) if branch_ids else gq.filter(False)
 return {'branches':[{'id':x.id,'name':x.name} for x in bq.order_by(Branch.name).all()],'grades':[{'id':x.id,'name':x.name,'branch_id':x.branch_id} for x in gq.order_by(Grade.name).all()]}
@router.post('/',response_model=Communication)
def create_communication_endpoint(comm_in:CommunicationCreate,db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),current_user:User=Depends(require_permission('communication.create'))):
 if comm_in.recipient_type.upper() not in {'ALL','STAFF','STUDENTS','PARENTS','BRANCH','GRADE'}:raise HTTPException(status_code=400,detail='Unsupported communication audience')
 if comm_in.channel.upper() not in {'IN_APP','SMS','EMAIL'}:raise HTTPException(status_code=400,detail='Unsupported communication channel')
 if not comm_in.content.strip():raise HTTPException(status_code=400,detail='Communication content is required')
 return create_communication(db,comm_in,current_org.id,current_user.id)
@router.get('/{communication_id}/target')
def read_target(communication_id:UUID,db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),_:User=Depends(require_permission('communication.read'))):
 t=db.query(CommunicationTarget).filter(CommunicationTarget.organization_id==current_org.id,CommunicationTarget.communication_id==communication_id).first();return {'branch_id':t.branch_id if t else None,'grade_id':t.grade_id if t else None}
@router.put('/{communication_id}/target')
def set_target(communication_id:UUID,payload:TargetUpdate,db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),current_user:User=Depends(require_permission('communication.create'))):
 try:
  communication=db.query(__import__('app.models.base',fromlist=['Communication']).Communication).filter_by(id=communication_id,organization_id=current_org.id).with_for_update().first()
  if not communication:raise HTTPException(status_code=404,detail='Communication not found')
  if communication.status!='DRAFT':raise HTTPException(status_code=409,detail='Audience target can only be changed while draft')
  audience=communication.recipient_type.upper()
  if audience=='BRANCH':
   if not payload.branch_id or payload.grade_id:raise HTTPException(status_code=400,detail='Branch audience requires only branch_id')
   enforce_branch_access(current_user,payload.branch_id)
   if not db.query(Branch).filter(Branch.id==payload.branch_id,Branch.organization_id==current_org.id,Branch.is_active.is_(True)).first():raise HTTPException(status_code=400,detail='Active branch not found in this organization')
  elif audience=='GRADE':
   if not payload.grade_id or payload.branch_id:raise HTTPException(status_code=400,detail='Grade audience requires only grade_id')
   grade=db.query(Grade).filter(Grade.id==payload.grade_id,Grade.organization_id==current_org.id).first()
   if not grade:raise HTTPException(status_code=400,detail='Grade not found in this organization')
   enforce_branch_access(current_user,grade.branch_id)
  elif payload.branch_id or payload.grade_id:raise HTTPException(status_code=400,detail='This audience does not accept a concrete target')
  t=db.query(CommunicationTarget).filter(CommunicationTarget.organization_id==current_org.id,CommunicationTarget.communication_id==communication_id).with_for_update().first()
  if not t:t=CommunicationTarget(organization_id=current_org.id,communication_id=communication_id);db.add(t)
  t.branch_id=payload.branch_id;t.grade_id=payload.grade_id;db.flush();log_action(db,current_org.id,current_user.id,'UPDATE','COMMUNICATION_TARGET',communication_id,new_values=f'branch_id={payload.branch_id};grade_id={payload.grade_id}');db.commit();db.refresh(t);return {'branch_id':t.branch_id,'grade_id':t.grade_id}
 except HTTPException:db.rollback();raise
 except Exception:db.rollback();raise
@router.patch('/{communication_id}/status/{new_status}',response_model=Communication)
def change_communication_status(communication_id:UUID,new_status:str,db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),current_user:User=Depends(require_permission('communication.manage'))):
 communication=next((x for x in get_communications(db,current_org.id) if x.id==communication_id),None)
 if not communication:raise HTTPException(status_code=404,detail='Communication not found')
 if new_status.upper()=='QUEUED' and communication.recipient_type.upper() in {'BRANCH','GRADE'}:
  target=db.query(CommunicationTarget).filter(CommunicationTarget.organization_id==current_org.id,CommunicationTarget.communication_id==communication_id).first()
  if not target or (communication.recipient_type.upper()=='BRANCH' and not target.branch_id) or (communication.recipient_type.upper()=='GRADE' and not target.grade_id):raise HTTPException(status_code=409,detail='Select a concrete audience target before queueing')
 communication=update_communication_status(db,communication_id,new_status.upper(),current_org.id,current_user.id)
 if not communication:raise HTTPException(status_code=404,detail='Communication not found')
 return communication
