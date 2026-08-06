import csv,json
from io import StringIO
from fastapi import APIRouter,Depends,HTTPException,Response,status
from typing import List
from pydantic import BaseModel,Field
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_organization,require_permission
from app.services.inventory_assets_service import create_inventory_item,get_inventory_items,get_inventory_movements,update_inventory_item,adjust_inventory_quantity,delete_inventory_item,create_asset,get_assets,update_asset,delete_asset
from app.schemas.inventory_assets import InventoryItem,InventoryItemCreate,InventoryItemUpdate,Asset,AssetCreate,AssetUpdate
from app.models.base import Organization,User
from app.models.workflow_extensions import InventoryReorderPolicy
from uuid import UUID
router=APIRouter()
class StockAdjustment(BaseModel):delta:int=Field(ge=-1000000,le=1000000)
class ReorderUpdate(BaseModel):reorder_level:int=Field(ge=0,le=1000000)
def _policies(db,org_id):return {x.item_id:x.reorder_level for x in db.query(InventoryReorderPolicy).filter(InventoryReorderPolicy.organization_id==org_id).all()}
@router.get('/summary')
def inventory_summary(db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),_:User=Depends(require_permission('inventory.read'))):
 items=get_inventory_items(db,current_org.id);assets=get_assets(db,current_org.id);p=_policies(db,current_org.id);return {'inventory_items':len(items),'stock_quantity':sum(i.quantity for i in items),'low_stock_items':sum(i.quantity<=p.get(i.id,5) for i in items),'out_of_stock_items':sum(i.quantity==0 for i in items),'assets':len(assets),'assets_in_repair':sum(a.status=='REPAIR' for a in assets),'disposed_assets':sum(a.status=='DISPOSED' for a in assets)}
@router.get('/inventory',response_model=List[InventoryItem])
def read_inventory(db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),_:User=Depends(require_permission('inventory.read'))):return get_inventory_items(db,current_org.id)
@router.get('/inventory/reorder-policies')
def reorder_policies(db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),_:User=Depends(require_permission('inventory.read'))):return [{'item_id':k,'reorder_level':v} for k,v in _policies(db,current_org.id).items()]
@router.put('/inventory/{item_id}/reorder-policy')
def set_reorder_policy(item_id:UUID,payload:ReorderUpdate,db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),_:User=Depends(require_permission('inventory.manage'))):
 if not next((i for i in get_inventory_items(db,current_org.id) if i.id==item_id),None):raise HTTPException(status_code=404,detail='Item not found')
 row=db.query(InventoryReorderPolicy).filter(InventoryReorderPolicy.organization_id==current_org.id,InventoryReorderPolicy.item_id==item_id).with_for_update().first()
 if not row:row=InventoryReorderPolicy(organization_id=current_org.id,item_id=item_id,reorder_level=payload.reorder_level);db.add(row)
 else:row.reorder_level=payload.reorder_level
 db.commit();db.refresh(row);return {'item_id':row.item_id,'reorder_level':row.reorder_level}
@router.get('/inventory/movements')
def inventory_movements(item_id:UUID|None=None,limit:int=100,db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),_:User=Depends(require_permission('inventory.read'))):return [{'id':x.id,'item_id':x.entity_id,'user_id':x.user_id,'previous':json.loads(x.previous_values or '{}'),'change':json.loads(x.new_values or '{}'),'created_at':x.created_at} for x in get_inventory_movements(db,current_org.id,item_id,min(max(limit,1),1000))]
@router.get('/inventory/movements.csv')
def inventory_movements_csv(item_id:UUID|None=None,db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),_:User=Depends(require_permission('inventory.read'))):
 items={i.id:i.name for i in get_inventory_items(db,current_org.id)};out=StringIO();w=csv.writer(out);w.writerow(['item','delta','before','after','actor_id','timestamp'])
 for x in get_inventory_movements(db,current_org.id,item_id,1000):
  before=json.loads(x.previous_values or '{}');after=json.loads(x.new_values or '{}');w.writerow([items.get(x.entity_id,'Inventory item'),after.get('delta',''),before.get('quantity',''),after.get('quantity',''),x.user_id or '',x.created_at.isoformat()])
 return Response(out.getvalue(),media_type='text/csv',headers={'Content-Disposition':'attachment; filename="inventory-movements.csv"'})
@router.post('/inventory',response_model=InventoryItem)
def create_inventory(item_in:InventoryItemCreate,db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),current_user:User=Depends(require_permission('inventory.manage'))):return create_inventory_item(db,item_in,current_org.id,current_user.id)
@router.put('/inventory/{item_id}',response_model=InventoryItem)
def update_inventory(item_id:UUID,item_in:InventoryItemUpdate,db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),current_user:User=Depends(require_permission('inventory.manage'))):
 item=update_inventory_item(db,item_id,item_in,current_org.id,current_user.id)
 if not item:raise HTTPException(status_code=404,detail='Item not found')
 return item
@router.post('/inventory/{item_id}/adjust',response_model=InventoryItem)
def adjust_inventory(item_id:UUID,adjustment:StockAdjustment,db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),current_user:User=Depends(require_permission('inventory.manage'))):
 item=adjust_inventory_quantity(db,item_id,adjustment.delta,current_org.id,current_user.id)
 if not item:raise HTTPException(status_code=404,detail='Item not found')
 return item
@router.delete('/inventory/{item_id}',status_code=status.HTTP_204_NO_CONTENT)
def delete_inventory(item_id:UUID,db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),_:User=Depends(require_permission('inventory.manage'))):
 if not delete_inventory_item(db,item_id,current_org.id):raise HTTPException(status_code=404,detail='Item not found')
@router.get('/assets',response_model=List[Asset])
def read_assets(db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),_:User=Depends(require_permission('assets.read'))):return get_assets(db,current_org.id)
@router.post('/assets',response_model=Asset)
def create_asset_endpoint(asset_in:AssetCreate,db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),current_user:User=Depends(require_permission('assets.manage'))):return create_asset(db,asset_in,current_org.id,current_user.id)
@router.put('/assets/{asset_id}',response_model=Asset)
def update_asset_endpoint(asset_id:UUID,asset_in:AssetUpdate,db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),current_user:User=Depends(require_permission('assets.manage'))):
 asset=update_asset(db,asset_id,asset_in,current_org.id,current_user.id)
 if not asset:raise HTTPException(status_code=404,detail='Asset not found')
 return asset
@router.delete('/assets/{asset_id}',status_code=status.HTTP_204_NO_CONTENT)
def delete_asset_endpoint(asset_id:UUID,db:Session=Depends(get_db),current_org:Organization=Depends(get_current_organization),_:User=Depends(require_permission('assets.manage'))):
 if not delete_asset(db,asset_id,current_org.id):raise HTTPException(status_code=404,detail='Asset not found')
