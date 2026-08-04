from pydantic import BaseModel, EmailStr
from typing import Optional, List
from uuid import UUID

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True

class UserCreate(UserBase):
    password: str
    organization_id: UUID
    branch_ids: Optional[List[UUID]] = None
    role_ids: Optional[List[UUID]] = None

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None

class User(UserBase):
    id: UUID
    organization_id: UUID

    class Config:
        from_attributes = True
