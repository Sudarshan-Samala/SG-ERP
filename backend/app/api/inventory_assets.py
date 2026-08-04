from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_organization
from app.services.inventory_assets_service import (
    create_inventory_item, get_inventory_items, get_inventory_item, update_inventory_item, delete_inventory_item,
    create_asset, get_assets, get_asset, update_asset, delete_asset
)
from app.schemas.inventory_assets import (
    InventoryItem, InventoryItemCreate, InventoryItemUpdate,
    Asset, AssetCreate, AssetUpdate
)
from app.models.base import Organization
from uuid import UUID

router = APIRouter()

# Inventory
@router.get("/inventory", response_model=List[InventoryItem])
def read_inventory(db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization)):
    return get_inventory_items(db, current_org.id)

@router.post("/inventory", response_model=InventoryItem)
def create_inventory(item_in: InventoryItemCreate, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization)):
    return create_inventory_item(db, item_in, current_org.id)

@router.put("/inventory/{item_id}", response_model=InventoryItem)
def update_inventory(item_id: UUID, item_in: InventoryItemUpdate, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization)):
    item = update_inventory_item(db, item_id, item_in, current_org.id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@router.delete("/inventory/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_inventory(item_id: UUID, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization)):
    if not delete_inventory_item(db, item_id, current_org.id):
        raise HTTPException(status_code=404, detail="Item not found")
    return None

# Assets
@router.get("/assets", response_model=List[Asset])
def read_assets(db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization)):
    return get_assets(db, current_org.id)

@router.post("/assets", response_model=Asset)
def create_asset_endpoint(asset_in: AssetCreate, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization)):
    asset = create_asset(db, asset_in, current_org.id)
    if not asset:
        raise HTTPException(status_code=400, detail="Asset tag already exists or invalid data")
    return asset

@router.put("/assets/{asset_id}", response_model=Asset)
def update_asset_endpoint(asset_id: UUID, asset_in: AssetUpdate, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization)):
    asset = update_asset(db, asset_id, asset_in, current_org.id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset

@router.delete("/assets/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_asset_endpoint(asset_id: UUID, db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization)):
    if not delete_asset(db, asset_id, current_org.id):
        raise HTTPException(status_code=404, detail="Asset not found")
    return None
