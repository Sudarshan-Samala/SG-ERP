import json
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from app.models.base import Asset, AuditLog, InventoryItem


def get_inventory_items(db, organization_id): return db.query(InventoryItem).filter(InventoryItem.organization_id == organization_id).order_by(InventoryItem.name).all()
def get_inventory_item(db, organization_id, item_id): return db.query(InventoryItem).filter(InventoryItem.organization_id == organization_id, InventoryItem.id == item_id).first()
def get_inventory_movements(db, organization_id, item_id=None, limit=100):
    q=db.query(AuditLog).filter(AuditLog.organization_id==organization_id,AuditLog.entity_type=="inventory_item",AuditLog.action=="stock_adjustment")
    if item_id:q=q.filter(AuditLog.entity_id==item_id)
    return q.order_by(AuditLog.created_at.desc()).limit(min(max(limit,1),250)).all()
def _audit(db,organization_id,user_id,action,entity_type,entity_id,previous=None,new=None):db.add(AuditLog(organization_id=organization_id,user_id=user_id,action=action,entity_type=entity_type,entity_id=entity_id,previous_values=json.dumps(previous) if previous is not None else None,new_values=json.dumps(new) if new is not None else None))
def _validate_quantity(data):
    quantity=data.get("quantity")
    if quantity is not None and quantity < 0: raise HTTPException(status_code=400, detail="Inventory quantity cannot be negative")
def create_inventory_item(db,item_in,organization_id,user_id=None):
    data=item_in.model_dump();_validate_quantity(data);data["name"]=data["name"].strip()
    if db.query(InventoryItem).filter(InventoryItem.organization_id==organization_id,InventoryItem.name==data["name"]).first():raise HTTPException(status_code=409,detail="Inventory item name already exists")
    try:
        item=InventoryItem(**data,organization_id=organization_id);db.add(item);db.flush();_audit(db,organization_id,user_id,"CREATE","inventory_item",item.id,new=data);db.commit();db.refresh(item);return item
    except HTTPException:db.rollback();raise
    except IntegrityError as exc:db.rollback();raise HTTPException(status_code=409,detail="Inventory item already exists") from exc
    except Exception:db.rollback();raise
def update_inventory_item(db,item_id,item_in,organization_id,user_id=None):
    item=db.query(InventoryItem).filter(InventoryItem.organization_id==organization_id,InventoryItem.id==item_id).with_for_update().first()
    if not item:return None
    data=item_in.model_dump(exclude_unset=True);_validate_quantity(data);before={"name":item.name,"quantity":item.quantity,"category":item.category,"unit":item.unit}
    if "name" in data:
        data["name"]=data["name"].strip()
        if db.query(InventoryItem).filter(InventoryItem.organization_id==organization_id,InventoryItem.name==data["name"],InventoryItem.id!=item_id).first():raise HTTPException(status_code=409,detail="Inventory item name already exists")
    try:
        for field,value in data.items():setattr(item,field,value)
        _audit(db,organization_id,user_id,"UPDATE","inventory_item",item.id,previous=before,new=data);db.commit();db.refresh(item);return item
    except HTTPException:db.rollback();raise
    except Exception:db.rollback();raise
def adjust_inventory_quantity(db,item_id,delta,organization_id,user_id=None):
    if delta == 0: raise HTTPException(status_code=400,detail="Stock adjustment cannot be zero")
    item=db.query(InventoryItem).filter(InventoryItem.organization_id==organization_id,InventoryItem.id==item_id).with_for_update().first()
    if not item:return None
    old_quantity=item.quantity;new_quantity=old_quantity+delta
    if new_quantity<0:db.rollback();raise HTTPException(status_code=409,detail="Stock adjustment would make inventory negative")
    try:item.quantity=new_quantity;_audit(db,organization_id,user_id,"stock_adjustment","inventory_item",item.id,{"quantity":old_quantity},{"quantity":new_quantity,"delta":delta});db.commit();db.refresh(item);return item
    except Exception:db.rollback();raise
def delete_inventory_item(db,item_id,organization_id):
    item=get_inventory_item(db,organization_id,item_id)
    if not item:return False
    if item.quantity>0: raise HTTPException(status_code=409,detail="Inventory with remaining stock cannot be deleted")
    db.delete(item);db.commit();return True
def get_assets(db,organization_id):return db.query(Asset).filter(Asset.organization_id==organization_id).order_by(Asset.asset_tag).all()
def get_asset(db,organization_id,asset_id):return db.query(Asset).filter(Asset.organization_id==organization_id,Asset.id==asset_id).first()
def create_asset(db,asset_in,organization_id,user_id=None):
    data=asset_in.model_dump();data["name"]=data["name"].strip();data["asset_tag"]=data["asset_tag"].strip().upper()
    try:asset=Asset(**data,organization_id=organization_id);db.add(asset);db.flush();_audit(db,organization_id,user_id,"CREATE","asset",asset.id,new=data);db.commit();db.refresh(asset);return asset
    except IntegrityError as exc:db.rollback();raise HTTPException(status_code=409,detail="Asset tag already exists") from exc
    except Exception:db.rollback();raise
def update_asset(db,asset_id,asset_in,organization_id,user_id=None):
    asset=db.query(Asset).filter(Asset.organization_id==organization_id,Asset.id==asset_id).with_for_update().first()
    if not asset:return None
    data=asset_in.model_dump(exclude_unset=True);requested=data.get("status");allowed={"DEPLOYED":{"DEPLOYED","REPAIR","DISPOSED"},"REPAIR":{"REPAIR","DEPLOYED","DISPOSED"},"DISPOSED":{"DISPOSED"}}
    if requested and requested not in allowed.get(asset.status,{asset.status}):raise HTTPException(status_code=409,detail=f"Invalid asset status transition from {asset.status} to {requested}")
    if "name" in data:data["name"]=data["name"].strip()
    before={"name":asset.name,"status":asset.status,"assigned_to":asset.assigned_to}
    try:
        for field,value in data.items():setattr(asset,field,value)
        _audit(db,organization_id,user_id,"UPDATE","asset",asset.id,previous=before,new=data);db.commit();db.refresh(asset);return asset
    except IntegrityError as exc:db.rollback();raise HTTPException(status_code=409,detail="Asset tag already exists") from exc
    except Exception:db.rollback();raise
def delete_asset(db,asset_id,organization_id):
    asset=get_asset(db,organization_id,asset_id)
    if not asset:return False
    if asset.status!="DISPOSED":raise HTTPException(status_code=409,detail="Only disposed assets can be permanently deleted")
    db.delete(asset);db.commit();return True
