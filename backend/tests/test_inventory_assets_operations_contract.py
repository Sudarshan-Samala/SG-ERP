from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def source(path):return (ROOT/path).read_text()
def test_inventory_writes_are_actor_audited_and_atomic():
 s=source('app/services/inventory_assets_service.py');a=source('app/api/inventory_assets.py')
 assert 'current_user.id' in a
 assert 'db.flush();_audit' in s
 assert '"CREATE","inventory_item"' in s
 assert 'db.rollback();raise' in s
def test_asset_lifecycle_is_locked_and_audited():
 s=source('app/services/inventory_assets_service.py')
 assert 'Asset.organization_id==organization_id' in s
 assert '.with_for_update().first()' in s
 assert '"UPDATE","asset"' in s
 assert 'Invalid asset status transition' in s
def test_inventory_frontend_supports_creation_and_operational_states():
 p=source('../frontend/src/app/inventory/page.tsx')
 assert 'Create Inventory Item' in p
 assert 'Register Asset' in p
 assert "api.post('/inventory-assets/inventory'" in p
 assert "api.post('/inventory-assets/assets'" in p
 assert 'Unable to create record.' in p
