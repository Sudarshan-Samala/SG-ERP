from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

class SchoolEventBase(BaseModel):
    name: str
    date: datetime
    description: Optional[str] = None

class SchoolEvent(SchoolEventBase):
    id: UUID
    organization_id: UUID

    class Config:
        from_attributes = True
