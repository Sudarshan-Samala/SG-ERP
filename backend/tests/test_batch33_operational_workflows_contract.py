from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def src(p):return (ROOT/p).read_text()

def test_helpdesk_assignment_is_tenant_safe_and_manager_only():
 t=src('app/api/helpdesk.py')
 assert "require_permission('helpdesk.manage')" in t
 assert 'TicketModel.organization_id==current_user.organization_id' in t
 assert 'User.organization_id==current_user.organization_id' in t
 assert '.with_for_update().first()' in t
 assert "'sla_overdue'" in t

def test_communication_target_enforces_branch_scope_and_draft_lock():
 t=src('app/api/communication.py')
 assert 'enforce_branch_access(current_user,payload.branch_id)' in t
 assert 'enforce_branch_access(current_user,grade.branch_id)' in t
 assert "communication.status!='DRAFT'" in t
 assert "Select a concrete audience target before queueing" in t
 assert 'accessible_branch_ids(current_user)' in t

def test_inventory_reorder_and_export_are_tenant_scoped():
 t=src('app/api/inventory_assets.py')
 assert 'InventoryReorderPolicy.organization_id==current_org.id' in t
 assert "@router.put('/inventory/{item_id}/reorder-policy')" in t
 assert "@router.get('/inventory/movements.csv')" in t
 assert "require_permission('inventory.read')" in t
 assert '.with_for_update().first()' in t

def test_frontend_integrates_all_three_workflows():
 h=src('../frontend/src/app/helpdesk/page.tsx');c=src('../frontend/src/app/communication/page.tsx');i=src('../frontend/src/app/inventory/page.tsx')
 assert '/assignment`' in h and 'SLA & Assignment' in h
 assert '/communication/target-options' in c and '/target`' in c
 assert '/reorder-policy`' in i and '/inventory/movements.csv' in i

def test_migration_covers_extension_tables():
 t=src('migrations/versions/a2508051730_add_operational_workflow_extensions.py')
 for table in ('helpdesk_assignments','communication_targets','inventory_reorder_policies'):assert table in t
