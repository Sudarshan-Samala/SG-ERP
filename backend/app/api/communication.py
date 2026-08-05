from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.core.database import get_db
from app.api.deps import get_current_organization,require_permission
from app.services.communication_service import create_communication,get_communications,update_communication_status
from app.schemas.communication import Communication,CommunicationCreate
from app.models.base import Organization,User,Branch,Grade
from app.models.workflow_extensions import CommunicationTarget
router=APIRouter()
class TargetUpdate(BaseModel):branch_id:UUID|None=None;grade_id:UUID|None=None
@router.get('/',response_model=List[Communication])
def read_communications(db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),_:User=Depends(require_permission('communication.read'))):return get_communications(db,current_org.id)
@router.get('/summary')
def communication_summary(db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),_:User=Depends(require_permission('communication.read'))):
 items=get_communications(db,current_org.id);return {'total':len(items),'draft':sum(x.status=='DRAFT' for x in items),'queued':sum(x.status=='QUEUED' for x in items),'sent':sum(x.status=='SENT' for x in items),'failed':sum(x.status=='FAILED' for x in items),'cancelled':sum(x.status=='CANCELLED' for x in items)}
@router.post('/',response_model=Communication)
def create_communication_endpoint(comm_in:CommunicationCreate,db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),_:User=Depends(require_permission('communication.create'))):
 if comm_in.recipient_type.upper() not in {'ALL','STAFF','STUDENTS','PARENTS','BRANCH','GRADE'}:raise HTTPException(status_code=400,detail='Unsupported communication audience')
 if comm_in.channel.upper() not in {'IN_APP','SMS','EMAIL'}:raise HTTPException(status_code=400,detail='Unsupported communication channel')
 if not comm_in.content.strip():raise HTTPException(status_code=400,detail='Communication content is required')
 return create_communication(db,comm_in,current_org.id)
@router.get('/{communication_id}/target')
def read_target(communication_id:UUID,db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),_:User=Depends(require_permission('communication.read'))):
 if not db.query(CommunicationTarget).filter(CommunicationTarget.organization_id==current_org.id,CommunicationTarget.communication_id==communication_id).first():return {'branch_id':None,'grade_id':None}
 t=db.query(CommunicationTarget).filter(CommunicationTarget.organization_id==current_org.id,CommunicationTarget.communication_id==communication_id).first();return {'branch_id':t.branch_id,'grade_id':t.grade_id}
@router.put('/{communication_id}/target')
def set_target(communication_id:UUID,payload:TargetUpdate,db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),_:User=Depends(require_permission('communication.create'))):
 communication=next((x for x in get_communications(db,current_org.id) if x.id==communication_id),None)
 if not communication:raise HTTPException(status_code=404,detail='Communication not found')
 if communication.status!='DRAFT':raise HTTPException(status_code=409,detail='Audience target can only be changed while draft')
 audience=communication.recipient_type.upper()
 if audience=='BRANCH':
  if not payload.branch_id or payload.grade_id:raise HTTPException(status_code=400,detail='Branch audience requires only branch_id')
  if not db.query(Branch).filter(Branch.id==payload.branch_id,Branch.organization_id==current_org.id).first():raise HTTPException(status_code=400,detail='Branch not found in this organization')
 elif audience=='GRADE':
  if not payload.grade_id or payload.branch_id:raise HTTPException(status_code=400,detail='Grade audience requires only grade_id')
  if not db.query(Grade).filter(Grade.id==payload.grade_id,Grade.organization_id==current_org.id).first():raise HTTPException(status_code=400,detail='Grade not found in this organization')
 else:
  if payload.branch_id or payload.grade_id:raise HTTPException(status_code=400,detail='This audience does not accept a concrete target')
 t=db.query(CommunicationTarget).filter(CommunicationTarget.organization_id==current_org.id,CommunicationTarget.communication_id==communication_id).with_for_update().first()
 if not t:t=CommunicationTarget(organization_id=current_org.id,communication_id=communication_id);db.add(t)
 t.branch_id=payload.branch_id;t.grade_id=payload.grade_id;db.commit();db.refresh(t);return {'branch_id':t.branch_id,'grade_id':t.grade_id}
@router.patch('/{communication_id}/status/{new_status}',response_model=Communication)
def change_communication_status(communication_id:UUID,new_status:str,db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),_:User=Depends(require_permission('communication.manage'))):
 communication=next((x for x in get_communications(db,current_org.id) if x.id==communication_id),None)
 if not communication:raise HTTPException(status_code=404,detail='Communication not found')
 if new_status.upper()=='QUEUED' and communication.recipient_type.upper() in {'BRANCH','GRADE'}:
  target=db.query(CommunicationTarget).filter(CommunicationTarget.organization_id==current_org.id,CommunicationTarget.communication_id==communication_id).first()
  if not target or (communication.recipient_type.upper()=='BRANCH' and not target.branch_id) or (communication.recipient_type.upper()=='GRADE' and not target.grade_id):raise HTTPException(status_code=409,detail='Select a concrete audience target before queueing')
 communication=update_communication_status(db,communication_id,new_status.upper(),current_org.id)
 if not communication:raise HTTPException(status_code=404,detail='Communication not found')
 return communication
