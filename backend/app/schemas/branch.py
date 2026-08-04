from pydantic import BaseModel
from typing import Optional
from uuid import UUID

class BranchBase(BaseModel):
    name: str
    code: str
    is_active: bool = True

class BranchCreate(BranchBase):
    pass

class Branch(BranchBase):
    id: UUID
    organization_id: UUID

    class Config:
        from_attributes = True
