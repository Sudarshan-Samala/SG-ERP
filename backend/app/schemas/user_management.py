from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from uuid import UUID

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = Field(default=None, max_length=120)
    is_active: bool = True

class UserCreate(UserBase):
    password: str = Field(min_length=12, max_length=128)
    organization_id: Optional[UUID] = None
    branch_ids: Optional[List[UUID]] = None
    role_ids: Optional[List[UUID]] = None

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(default=None, max_length=120)
    is_active: Optional[bool] = None
    branch_ids: Optional[List[UUID]] = None
    role_ids: Optional[List[UUID]] = None

class User(UserBase):
    id: UUID
    organization_id: UUID
    branch_ids: List[UUID] = []
    role_ids: List[UUID] = []

    @classmethod
    def from_model(cls, user):
        return cls(id=user.id,email=user.email,full_name=user.full_name,is_active=user.is_active,organization_id=user.organization_id,branch_ids=[b.id for b in user.branches],role_ids=[r.id for r in user.roles])

    class Config:
        from_attributes = True
