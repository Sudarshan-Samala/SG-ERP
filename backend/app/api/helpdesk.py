from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel,Field
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.core.database import get_db
from app.api.deps import require_permission
from app.services.helpdesk_service import create_ticket,get_tickets,update_ticket_status
from app.schemas.helpdesk import Ticket,TicketCreate
from app.models.base import User
from app.models.helpdesk_comment import TicketComment
router=APIRouter()
class CommentCreate(BaseModel):content:str=Field(min_length=2,max_length=2000)
def _can_manage(user:User)->bool:return user.is_superuser or any(p.name=='helpdesk.manage' for r in user.roles for p in r.permissions)
def _visible_ticket(db:Session,ticket_id:UUID,user:User):
 tickets=get_tickets(db,user.organization_id,None if _can_manage(user) else user.id);return next((t for t in tickets if t.id==ticket_id),None)
@router.get('/',response_model=List[Ticket])
def read_tickets(db:Session=Depends(get_db),current_user:User=Depends(require_permission('helpdesk.read'))):return get_tickets(db,current_user.organization_id,None if _can_manage(current_user) else current_user.id)
@router.get('/summary')
def ticket_summary(db:Session=Depends(get_db),current_user:User=Depends(require_permission('helpdesk.read'))):
 tickets=get_tickets(db,current_user.organization_id,None if _can_manage(current_user) else current_user.id);return {'total':len(tickets),'open':sum(t.status=='OPEN' for t in tickets),'in_progress':sum(t.status=='IN_PROGRESS' for t in tickets),'resolved':sum(t.status=='RESOLVED' for t in tickets),'closed':sum(t.status=='CLOSED' for t in tickets),'high_priority':sum(t.priority=='HIGH' and t.status!='CLOSED' for t in tickets)}
@router.post('/',response_model=Ticket)
def create_ticket_endpoint(ticket_in:TicketCreate,db:Session=Depends(get_db),current_user:User=Depends(require_permission('helpdesk.ticket.create'))):return create_ticket(db,ticket_in,current_user.organization_id,current_user.id)
@router.get('/{ticket_id}/comments')
def read_comments(ticket_id:UUID,db:Session=Depends(get_db),current_user:User=Depends(require_permission('helpdesk.read'))):
 if not _visible_ticket(db,ticket_id,current_user):raise HTTPException(status_code=404,detail='Ticket not found')
 rows=db.query(TicketComment).filter(TicketComment.organization_id==current_user.organization_id,TicketComment.ticket_id==ticket_id).order_by(TicketComment.created_at).all();return [{'id':x.id,'author_id':x.author_id,'content':x.content,'created_at':x.created_at} for x in rows]
@router.post('/{ticket_id}/comments',status_code=201)
def add_comment(ticket_id:UUID,payload:CommentCreate,db:Session=Depends(get_db),current_user:User=Depends(require_permission('helpdesk.read'))):
 if not _visible_ticket(db,ticket_id,current_user):raise HTTPException(status_code=404,detail='Ticket not found')
 row=TicketComment(organization_id=current_user.organization_id,ticket_id=ticket_id,author_id=current_user.id,content=payload.content.strip());db.add(row);db.commit();db.refresh(row);return {'id':row.id,'author_id':row.author_id,'content':row.content,'created_at':row.created_at}
@router.patch('/{ticket_id}/status/{new_status}',response_model=Ticket)
def change_ticket_status(ticket_id:UUID,new_status:str,db:Session=Depends(get_db),current_user:User=Depends(require_permission('helpdesk.manage'))):
 ticket=update_ticket_status(db,ticket_id,new_status.upper(),current_user.organization_id)
 if not ticket:raise HTTPException(status_code=404,detail='Ticket not found')
 return ticket
