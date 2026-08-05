from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def src(p): return (ROOT/p).read_text()

def test_inventory_summary_and_lifecycle_contract():
    api=src('app/api/inventory_assets.py'); service=src('app/services/inventory_assets_service.py')
    assert '@router.get("/summary")' in api and 'require_permission("inventory.read")' in api
    assert 'with_for_update()' in service and 'Stock adjustment would make inventory negative' in service
    assert 'Only disposed assets can be permanently deleted' in service

def test_helpdesk_summary_respects_requester_scope():
    api=src('app/api/helpdesk.py'); service=src('app/services/helpdesk_service.py')
    assert '@router.get("/summary")' in api and 'None if _can_manage(current_user) else current_user.id' in api
    assert 'ALLOWED_TRANSITIONS' in service and 'with_for_update()' in service

def test_transport_summary_and_tenant_validation():
    api=src('app/api/transport.py'); service=src('app/services/transport_service.py')
    assert '@router.get("/summary")' in api and 'require_permission("transport.read")' in api
    assert 'Vehicle does not belong to this organization' in service
    assert 'Vehicle is already assigned to another route' in service

def test_frontend_operational_workspaces_exist():
    inventory=src('../frontend/src/app/inventory/page.tsx'); helpdesk=src('../frontend/src/app/helpdesk/page.tsx'); transport=src('../frontend/src/app/transport/page.tsx')
    assert 'Stock Movement' in inventory and 'Dispose' in inventory
    assert 'Change status' in helpdesk and 'New Ticket' in helpdesk
    assert 'Manage vehicles, routes and drivers' in transport and 'Available' in transport
