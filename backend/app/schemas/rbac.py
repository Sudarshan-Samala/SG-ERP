from pydantic import BaseModel
from typing import Optional
from uuid import UUID

class PermissionBase(BaseModel):
    name: str
    description: Optional[str] = None

class PermissionCreate(PermissionBase):
    pass

class Permission(PermissionBase):
    id: UUID

    class Config:
        from_attributes = True

class RoleBase(BaseModel):
    name: str
    organization_id: Optional[UUID] = None # Global if None

class RoleCreate(RoleBase):
    pass

class Role(RoleBase):
    id: UUID

    class Config:
        from_attributes = True
