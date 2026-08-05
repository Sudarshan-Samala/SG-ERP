from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.base import Asset, InventoryItem
from app.schemas.inventory_assets import AssetCreate, AssetUpdate, InventoryItemCreate, InventoryItemUpdate


def get_inventory_items(db, organization_id): return db.query(InventoryItem).filter(InventoryItem.organization_id == organization_id).order_by(InventoryItem.name).all()
def get_inventory_item(db, organization_id, item_id): return db.query(InventoryItem).filter(InventoryItem.organization_id == organization_id, InventoryItem.id == item_id).first()


def _validate_quantity(data):
    quantity = data.get("quantity")
    if quantity is not None and quantity < 0: raise HTTPException(status_code=400, detail="Inventory quantity cannot be negative")


def create_inventory_item(db, item_in, organization_id):
    data = item_in.model_dump(); _validate_quantity(data)
    item = InventoryItem(**data, organization_id=organization_id); db.add(item); db.commit(); db.refresh(item); return item


def update_inventory_item(db, item_id, item_in, organization_id):
    item = get_inventory_item(db, organization_id, item_id)
    if not item: return None
    data = item_in.model_dump(exclude_unset=True); _validate_quantity(data)
    for field, value in data.items(): setattr(item, field, value)
    db.commit(); db.refresh(item); return item


def delete_inventory_item(db, item_id, organization_id):
    item = get_inventory_item(db, organization_id, item_id)
    if not item: return False
    db.delete(item); db.commit(); return True


def get_assets(db, organization_id): return db.query(Asset).filter(Asset.organization_id == organization_id).order_by(Asset.asset_tag).all()
def get_asset(db, organization_id, asset_id): return db.query(Asset).filter(Asset.organization_id == organization_id, Asset.id == asset_id).first()


def create_asset(db, asset_in, organization_id):
    try:
        asset = Asset(**asset_in.model_dump(), organization_id=organization_id); db.add(asset); db.commit(); db.refresh(asset); return asset
    except IntegrityError as exc: db.rollback(); raise HTTPException(status_code=409, detail="Asset tag already exists") from exc


def update_asset(db, asset_id, asset_in, organization_id):
    asset = get_asset(db, organization_id, asset_id)
    if not asset: return None
    if asset.status == "DISPOSED" and asset_in.status and asset_in.status != "DISPOSED": raise HTTPException(status_code=409, detail="Disposed assets cannot be reactivated")
    for field, value in asset_in.model_dump(exclude_unset=True).items(): setattr(asset, field, value)
    try: db.commit(); db.refresh(asset)
    except IntegrityError as exc: db.rollback(); raise HTTPException(status_code=409, detail="Asset tag already exists") from exc
    return asset


def delete_asset(db, asset_id, organization_id):
    asset = get_asset(db, organization_id, asset_id)
    if not asset: return False
    if asset.status == "DEPLOYED": raise HTTPException(status_code=409, detail="Deployed assets cannot be deleted")
    db.delete(asset); db.commit(); return True
