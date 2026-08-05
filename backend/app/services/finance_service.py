from typing import Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.base import Account, JournalEntry
from app.schemas.finance import AccountCreate, JournalEntryCreate
from app.services.audit.audit_service import log_action


def get_accounts(db: Session, organization_id: UUID):
    return db.query(Account).filter(Account.organization_id == organization_id).order_by(Account.name).all()


def create_account(db: Session, account_in: AccountCreate, organization_id: UUID, user_id: UUID):
    name = account_in.name.strip()
    duplicate = db.query(Account).filter(Account.organization_id == organization_id, Account.name == name).first()
    if duplicate:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this name already exists")
    payload = account_in.model_dump(); payload["name"] = name
    acc = Account(**payload, organization_id=organization_id)
    db.add(acc); db.commit(); db.refresh(acc)
    log_action(db, organization_id, user_id, "CREATE", "ACCOUNT", acc.id, new_values=str(payload))
    return acc


def get_journal_entries(db: Session, organization_id: UUID, account_id: Optional[UUID] = None):
    query = db.query(JournalEntry).filter(JournalEntry.organization_id == organization_id)
    if account_id:
        account = db.query(Account.id).filter(Account.id == account_id, Account.organization_id == organization_id).first()
        if not account:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
        query = query.filter(JournalEntry.account_id == account_id)
    return query.order_by(JournalEntry.date.desc()).all()


def create_journal_entry(db: Session, entry_in: JournalEntryCreate, organization_id: UUID, user_id: UUID):
    account = db.query(Account).filter(Account.id == entry_in.account_id, Account.organization_id == organization_id).first()
    if not account:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Account does not belong to this organization")
    payload = entry_in.model_dump(); payload["description"] = entry_in.description.strip()
    je = JournalEntry(**payload, organization_id=organization_id)
    db.add(je); db.commit(); db.refresh(je)
    log_action(db, organization_id, user_id, "CREATE", "JOURNAL_ENTRY", je.id, new_values=str(payload))
    return je
