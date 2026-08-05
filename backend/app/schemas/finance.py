from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class AccountBase(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    type: Literal["ASSET", "LIABILITY", "INCOME", "EXPENSE", "EQUITY"]

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
    description: str = Field(min_length=2, max_length=500)
    amount: int = Field(gt=0)
    type: Literal["DEBIT", "CREDIT"]

class JournalEntryCreate(JournalEntryBase):
    pass

class JournalEntry(JournalEntryBase):
    id: UUID
    organization_id: UUID
    class Config:
        from_attributes = True
