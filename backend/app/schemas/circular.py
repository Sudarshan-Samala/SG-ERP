from pydantic import BaseModel
from typing import Optional
from uuid import UUID

class CircularBase(BaseModel):
    title: str
    content: str
    is_active: bool = True

class Circular(CircularBase):
    id: UUID
    organization_id: UUID

    class Config:
        from_attributes = True
