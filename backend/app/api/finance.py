from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.core.database import get_db
from app.api.deps import get_current_organization, get_current_user
from app.services.finance_service import (
    get_accounts, create_account,
    get_journal_entries, create_journal_entry
)
from app.schemas.finance import (
    Account,
    AccountCreate,
    JournalEntry,
    JournalEntryCreate,
)
from app.models.base import Organization, User

router = APIRouter()

# Accounts
@router.get("/accounts", response_model=List[Account])
def read_accounts(db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization)):
    return get_accounts(db, current_org.id)

@router.post("/accounts", response_model=Account)
def create_account_endpoint(account_in: AccountCreate, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), current_user: User = Depends(get_current_user)):
    return create_account(db, account_in, current_org.id, current_user.id)

# Journal Entries
@router.get("/journal", response_model=List[JournalEntry])
def read_journal_entries(db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), account_id: Optional[UUID] = None):
    return get_journal_entries(db, current_org.id, account_id)

@router.post("/journal", response_model=JournalEntry)
def create_journal_endpoint(entry_in: JournalEntryCreate, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), current_user: User = Depends(get_current_user)):
    return create_journal_entry(db, entry_in, current_org.id, current_user.id)
