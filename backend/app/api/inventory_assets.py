from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_organization, require_permission
from app.services.inventory_assets_service import create_inventory_item, get_inventory_items, update_inventory_item, adjust_inventory_quantity, delete_inventory_item, create_asset, get_assets, update_asset, delete_asset
from app.schemas.inventory_assets import InventoryItem, InventoryItemCreate, InventoryItemUpdate, Asset, AssetCreate, AssetUpdate
from app.models.base import Organization, User
from uuid import UUID

router = APIRouter()
class StockAdjustment(BaseModel): delta: int = Field(ge=-1000000, le=1000000)

@router.get("/inventory", response_model=List[InventoryItem])
def read_inventory(db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), _: User = Depends(require_permission("inventory.read"))): return get_inventory_items(db, current_org.id)
@router.post("/inventory", response_model=InventoryItem)
def create_inventory(item_in: InventoryItemCreate, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), _: User = Depends(require_permission("inventory.manage"))): return create_inventory_item(db, item_in, current_org.id)
@router.put("/inventory/{item_id}", response_model=InventoryItem)
def update_inventory(item_id: UUID, item_in: InventoryItemUpdate, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), _: User = Depends(require_permission("inventory.manage"))):
    item = update_inventory_item(db, item_id, item_in, current_org.id)
    if not item: raise HTTPException(status_code=404, detail="Item not found")
    return item
@router.post("/inventory/{item_id}/adjust", response_model=InventoryItem)
def adjust_inventory(item_id: UUID, adjustment: StockAdjustment, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), _: User = Depends(require_permission("inventory.manage"))):
    item=adjust_inventory_quantity(db,item_id,adjustment.delta,current_org.id)
    if not item: raise HTTPException(status_code=404,detail="Item not found")
    return item
@router.delete("/inventory/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_inventory(item_id: UUID, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), _: User = Depends(require_permission("inventory.manage"))):
    if not delete_inventory_item(db, item_id, current_org.id): raise HTTPException(status_code=404, detail="Item not found")

@router.get("/assets", response_model=List[Asset])
def read_assets(db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), _: User = Depends(require_permission("assets.read"))): return get_assets(db, current_org.id)
@router.post("/assets", response_model=Asset)
def create_asset_endpoint(asset_in: AssetCreate, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), _: User = Depends(require_permission("assets.manage"))): return create_asset(db, asset_in, current_org.id)
@router.put("/assets/{asset_id}", response_model=Asset)
def update_asset_endpoint(asset_id: UUID, asset_in: AssetUpdate, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), _: User = Depends(require_permission("assets.manage"))):
    asset = update_asset(db, asset_id, asset_in, current_org.id)
    if not asset: raise HTTPException(status_code=404, detail="Asset not found")
    return asset
@router.delete("/assets/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_asset_endpoint(asset_id: UUID, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization), _: User = Depends(require_permission("assets.manage"))):
    if not delete_asset(db, asset_id, current_org.id): raise HTTPException(status_code=404, detail="Asset not found")
