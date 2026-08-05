from datetime import datetime
from typing import Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.base import Account, JournalEntry
from app.schemas.finance import AccountCreate, JournalEntryCreate
from app.services.audit.audit_service import log_action

def get_accounts(db: Session, organization_id: UUID): return db.query(Account).filter(Account.organization_id == organization_id).order_by(Account.name).all()
def create_account(db: Session, account_in: AccountCreate, organization_id: UUID, user_id: UUID):
    name=account_in.name.strip();duplicate=db.query(Account).filter(Account.organization_id==organization_id,Account.name==name).first()
    if duplicate:raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="An account with this name already exists")
    payload=account_in.model_dump();payload["name"]=name;acc=Account(**payload,organization_id=organization_id);db.add(acc);db.commit();db.refresh(acc);log_action(db,organization_id,user_id,"CREATE","ACCOUNT",acc.id,new_values=str(payload));return acc

def _journal_query(db: Session, organization_id: UUID, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None):
    if start_date and end_date and end_date < start_date: raise HTTPException(status_code=400, detail="end_date cannot be before start_date")
    query=db.query(JournalEntry).filter(JournalEntry.organization_id==organization_id)
    if start_date: query=query.filter(JournalEntry.date >= start_date)
    if end_date: query=query.filter(JournalEntry.date <= end_date)
    return query

def get_journal_entries(db: Session, organization_id: UUID, account_id: Optional[UUID] = None, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None):
    query=_journal_query(db,organization_id,start_date,end_date)
    if account_id:
        if not db.query(Account.id).filter(Account.id==account_id,Account.organization_id==organization_id).first():raise HTTPException(status_code=404,detail="Account not found")
        query=query.filter(JournalEntry.account_id==account_id)
    return query.order_by(JournalEntry.date.desc()).all()
def get_finance_summary(db:Session,organization_id:UUID,start_date:Optional[datetime]=None,end_date:Optional[datetime]=None):
    base=_journal_query(db,organization_id,start_date,end_date)
    rows=base.with_entities(JournalEntry.type,func.coalesce(func.sum(JournalEntry.amount),0)).group_by(JournalEntry.type).all();totals={str(k).upper():float(v) for k,v in rows};debit=totals.get("DEBIT",0.0);credit=totals.get("CREDIT",0.0)
    return {"accounts":db.query(func.count(Account.id)).filter(Account.organization_id==organization_id).scalar() or 0,"entries":base.count(),"total_debit":debit,"total_credit":credit,"difference":debit-credit}
def create_journal_entry(db: Session, entry_in: JournalEntryCreate, organization_id: UUID, user_id: UUID):
    account=db.query(Account).filter(Account.id==entry_in.account_id,Account.organization_id==organization_id).first()
    if not account:raise HTTPException(status_code=400,detail="Account does not belong to this organization")
    payload=entry_in.model_dump();payload["description"]=entry_in.description.strip();je=JournalEntry(**payload,organization_id=organization_id);db.add(je);db.commit();db.refresh(je);log_action(db,organization_id,user_id,"CREATE","JOURNAL_ENTRY",je.id,new_values=str(payload));return je
