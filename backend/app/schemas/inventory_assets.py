from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID

class InventoryItemBase(BaseModel):
    name: str = Field(..., min_length=1)
    quantity: int = Field(..., ge=0)

class InventoryItemCreate(InventoryItemBase):
    pass

class InventoryItemUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1)
    quantity: Optional[int] = Field(None, ge=0)

class InventoryItem(InventoryItemBase):
    id: UUID
    organization_id: UUID

    class Config:
        from_attributes = True

class AssetBase(BaseModel):
    name: str = Field(..., min_length=1)
    asset_tag: str = Field(..., min_length=1)
    status: str = Field(..., pattern="^(DEPLOYED|REPAIR|DISPOSED)$")

class AssetCreate(AssetBase):
    pass

class AssetUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1)
    status: Optional[str] = Field(None, pattern="^(DEPLOYED|REPAIR|DISPOSED)$")

class Asset(AssetBase):
    id: UUID
    organization_id: UUID

    class Config:
        from_attributes = True
