from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class TicketBase(BaseModel):
    subject: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=5, max_length=5000)
    priority: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]

    @field_validator("subject", "description")
    @classmethod
    def normalize_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("value must not be blank")
        return value


class TicketCreate(TicketBase):
    pass


class Ticket(TicketBase):
    id: UUID
    organization_id: UUID
    requester_id: UUID | None
    status: Literal["OPEN", "IN_PROGRESS", "RESOLVED", "CLOSED"]

    class Config:
        from_attributes = True
