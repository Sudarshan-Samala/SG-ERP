from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.base import Account, JournalEntry
from app.schemas.finance import AccountCreate, JournalEntryCreate
from app.services.audit.audit_service import log_action


def get_accounts(db: Session, organization_id: UUID):
    return db.query(Account).filter(Account.organization_id == organization_id).all()


def create_account(db: Session, account_in: AccountCreate, organization_id: UUID, user_id: UUID):
    acc = Account(**account_in.model_dump(), organization_id=organization_id)
    db.add(acc)
    db.commit()
    db.refresh(acc)
    log_action(db, organization_id, user_id, "CREATE", "ACCOUNT", acc.id, new_values=str(account_in.model_dump()))
    return acc


def get_journal_entries(db: Session, organization_id: UUID, account_id: Optional[UUID] = None):
    query = db.query(JournalEntry).filter(JournalEntry.organization_id == organization_id)
    if account_id:
        query = query.filter(JournalEntry.account_id == account_id)
    return query.all()


def create_journal_entry(db: Session, entry_in: JournalEntryCreate, organization_id: UUID, user_id: UUID):
    account = db.query(Account).filter(Account.id == entry_in.account_id, Account.organization_id == organization_id).first()
    if not account:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Account does not belong to this organization")

    je = JournalEntry(**entry_in.model_dump(), organization_id=organization_id)
    db.add(je)
    db.commit()
    db.refresh(je)
    log_action(db, organization_id, user_id, "CREATE", "JOURNAL_ENTRY", je.id, new_values=str(entry_in.model_dump()))
    return je
