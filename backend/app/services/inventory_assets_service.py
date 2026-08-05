from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.base import Asset, InventoryItem
from app.schemas.inventory_assets import AssetCreate, AssetUpdate, InventoryItemCreate, InventoryItemUpdate


def get_inventory_items(db: Session, organization_id: UUID) -> List[InventoryItem]:
    return db.query(InventoryItem).filter(InventoryItem.organization_id == organization_id).all()


def get_inventory_item(db: Session, organization_id: UUID, item_id: UUID) -> Optional[InventoryItem]:
    return db.query(InventoryItem).filter(InventoryItem.organization_id == organization_id, InventoryItem.id == item_id).first()


def create_inventory_item(db: Session, item_in: InventoryItemCreate, organization_id: UUID) -> InventoryItem:
    item = InventoryItem(**item_in.model_dump(), organization_id=organization_id)
    db.add(item); db.commit(); db.refresh(item)
    return item


def update_inventory_item(db: Session, item_id: UUID, item_in: InventoryItemUpdate, organization_id: UUID) -> Optional[InventoryItem]:
    item = get_inventory_item(db, organization_id, item_id)
    if not item: return None
    for field, value in item_in.model_dump(exclude_unset=True).items(): setattr(item, field, value)
    db.commit(); db.refresh(item)
    return item


def delete_inventory_item(db: Session, item_id: UUID, organization_id: UUID) -> bool:
    item = get_inventory_item(db, organization_id, item_id)
    if not item: return False
    db.delete(item); db.commit()
    return True


def get_assets(db: Session, organization_id: UUID) -> List[Asset]:
    return db.query(Asset).filter(Asset.organization_id == organization_id).all()


def get_asset(db: Session, organization_id: UUID, asset_id: UUID) -> Optional[Asset]:
    return db.query(Asset).filter(Asset.organization_id == organization_id, Asset.id == asset_id).first()


def create_asset(db: Session, asset_in: AssetCreate, organization_id: UUID) -> Asset:
    try:
        asset = Asset(**asset_in.model_dump(), organization_id=organization_id)
        db.add(asset); db.commit(); db.refresh(asset)
        return asset
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Asset tag already exists") from exc


def update_asset(db: Session, asset_id: UUID, asset_in: AssetUpdate, organization_id: UUID) -> Optional[Asset]:
    asset = get_asset(db, organization_id, asset_id)
    if not asset: return None
    if asset.status == "DISPOSED" and asset_in.status and asset_in.status != "DISPOSED":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Disposed assets cannot be reactivated")
    for field, value in asset_in.model_dump(exclude_unset=True).items(): setattr(asset, field, value)
    db.commit(); db.refresh(asset)
    return asset


def delete_asset(db: Session, asset_id: UUID, organization_id: UUID) -> bool:
    asset = get_asset(db, organization_id, asset_id)
    if not asset: return False
    if asset.status == "DEPLOYED":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Deployed assets cannot be deleted")
    db.delete(asset); db.commit()
    return True
