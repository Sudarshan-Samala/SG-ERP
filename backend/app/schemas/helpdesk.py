from pydantic import BaseModel
from typing import Optional
from uuid import UUID

class TicketBase(BaseModel):
    subject: str
    description: str
    priority: str # LOW, MEDIUM, HIGH

class TicketCreate(TicketBase):
    pass

class Ticket(TicketBase):
    id: UUID
    organization_id: UUID
    user_id: UUID
    status: str # OPEN, IN_PROGRESS, CLOSED

    class Config:
        from_attributes = True
