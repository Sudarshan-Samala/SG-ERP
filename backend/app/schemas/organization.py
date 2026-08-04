from pydantic import BaseModel
from typing import Optional
from uuid import UUID

class OrganizationBase(BaseModel):
    name: str
    is_active: bool = True

class OrganizationCreate(OrganizationBase):
    pass

class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None

class Organization(OrganizationBase):
    id: UUID

    class Config:
        from_attributes = True
