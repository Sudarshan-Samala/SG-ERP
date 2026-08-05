from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID

class PermissionBase(BaseModel):
    name: str
    description: Optional[str] = None

class PermissionCreate(PermissionBase): pass

class Permission(PermissionBase):
    id: UUID
    class Config: from_attributes = True

class RoleBase(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    organization_id: Optional[UUID] = None

class RoleCreate(RoleBase):
    permission_names: List[str] = Field(default_factory=list)

class Role(RoleBase):
    id: UUID
    permissions: List[Permission] = Field(default_factory=list)
    class Config: from_attributes = True

class UserRoleAssignment(BaseModel):
    role_ids: List[UUID] = Field(default_factory=list, max_length=50)
