from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

class AccountBase(BaseModel):
    name: str
    type: str # ASSET, LIABILITY, INCOME, EXPENSE

class AccountCreate(AccountBase):
    pass

class Account(AccountBase):
    id: UUID
    organization_id: UUID

    class Config:
        from_attributes = True

class JournalEntryBase(BaseModel):
    account_id: UUID
    date: datetime
    description: str
    amount: int
    type: str # DEBIT, CREDIT

class JournalEntryCreate(JournalEntryBase):
    pass

class JournalEntry(JournalEntryBase):
    id: UUID
    organization_id: UUID

    class Config:
        from_attributes = True
