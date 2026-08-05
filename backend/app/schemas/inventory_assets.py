from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class InventoryItemBase(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    quantity: int = Field(ge=0)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("name must not be blank")
        return value

class InventoryItemCreate(InventoryItemBase):
    pass

class InventoryItemUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    quantity: Optional[int] = Field(None, ge=0)

class InventoryItem(InventoryItemBase):
    id: UUID
    organization_id: UUID
    class Config:
        from_attributes = True

class AssetBase(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    asset_tag: str = Field(min_length=1, max_length=100)
    status: Literal["DEPLOYED", "REPAIR", "DISPOSED"]

    @field_validator("name", "asset_tag")
    @classmethod
    def normalize_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("value must not be blank")
        return value

class AssetCreate(AssetBase):
    pass

class AssetUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    status: Optional[Literal["DEPLOYED", "REPAIR", "DISPOSED"]] = None

class Asset(AssetBase):
    id: UUID
    organization_id: UUID
    class Config:
        from_attributes = True
