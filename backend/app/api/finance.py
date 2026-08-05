from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.core.database import get_db
from app.api.deps import get_current_organization, require_permission
from app.services.finance_service import get_accounts, create_account, get_journal_entries, get_finance_summary, create_journal_entry
from app.schemas.finance import Account, AccountCreate, JournalEntry, JournalEntryCreate
from app.models.base import Organization, User
router=APIRouter()
@router.get("/accounts",response_model=List[Account])
def read_accounts(db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),_:User=Depends(require_permission("finance.read"))):return get_accounts(db,current_org.id)
@router.post("/accounts",response_model=Account)
def create_account_endpoint(account_in:AccountCreate,db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),current_user:User=Depends(require_permission("finance.manage"))):return create_account(db,account_in,current_org.id,current_user.id)
@router.get("/journal",response_model=List[JournalEntry])
def read_journal_entries(db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),account_id:Optional[UUID]=None,start_date:Optional[datetime]=None,end_date:Optional[datetime]=None,_:User=Depends(require_permission("finance.read"))):return get_journal_entries(db,current_org.id,account_id,start_date,end_date)
@router.get("/summary")
def read_finance_summary(db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),start_date:Optional[datetime]=None,end_date:Optional[datetime]=None,_:User=Depends(require_permission("finance.read"))):return get_finance_summary(db,current_org.id,start_date,end_date)
@router.post("/journal",response_model=JournalEntry)
def create_journal_endpoint(entry_in:JournalEntryCreate,db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),current_user:User=Depends(require_permission("finance.manage"))):return create_journal_entry(db,entry_in,current_org.id,current_user.id)
