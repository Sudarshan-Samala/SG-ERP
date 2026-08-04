from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.base import InventoryItem, Asset
from app.schemas.inventory_assets import InventoryItemCreate, InventoryItemUpdate, AssetCreate, AssetUpdate
from uuid import UUID
from typing import Optional, List

# Inventory
def get_inventory_items(db: Session, organization_id: UUID) -> List[InventoryItem]:
    return db.query(InventoryItem).filter(InventoryItem.organization_id == organization_id).all()

def get_inventory_item(db: Session, organization_id: UUID, item_id: UUID) -> Optional[InventoryItem]:
    return db.query(InventoryItem).filter(InventoryItem.organization_id == organization_id, InventoryItem.id == item_id).first()

def create_inventory_item(db: Session, item_in: InventoryItemCreate, organization_id: UUID) -> InventoryItem:
    item = InventoryItem(**item_in.model_dump(), organization_id=organization_id)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

def update_inventory_item(db: Session, item_id: UUID, item_in: InventoryItemUpdate, organization_id: UUID) -> Optional[InventoryItem]:
    item = get_inventory_item(db, organization_id, item_id)
    if not item:
        return None
    for field, value in item_in.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item

def delete_inventory_item(db: Session, item_id: UUID, organization_id: UUID) -> bool:
    item = get_inventory_item(db, organization_id, item_id)
    if not item:
        return False
    db.delete(item)
    db.commit()
    return True

# Assets
def get_assets(db: Session, organization_id: UUID) -> List[Asset]:
    return db.query(Asset).filter(Asset.organization_id == organization_id).all()

def get_asset(db: Session, organization_id: UUID, asset_id: UUID) -> Optional[Asset]:
    return db.query(Asset).filter(Asset.organization_id == organization_id, Asset.id == asset_id).first()

def create_asset(db: Session, asset_in: AssetCreate, organization_id: UUID) -> Optional[Asset]:
    try:
        asset = Asset(**asset_in.model_dump(), organization_id=organization_id)
        db.add(asset)
        db.commit()
        db.refresh(asset)
        return asset
    except IntegrityError:
        db.rollback()
        return None

def update_asset(db: Session, asset_id: UUID, asset_in: AssetUpdate, organization_id: UUID) -> Optional[Asset]:
    asset = get_asset(db, organization_id, asset_id)
    if not asset:
        return None
    for field, value in asset_in.model_dump(exclude_unset=True).items():
        setattr(asset, field, value)
    db.commit()
    db.refresh(asset)
    return asset

def delete_asset(db: Session, asset_id: UUID, organization_id: UUID) -> bool:
    asset = get_asset(db, organization_id, asset_id)
    if not asset:
        return False
    db.delete(asset)
    db.commit()
    return True
