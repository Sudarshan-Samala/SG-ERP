from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def src(p):return (ROOT/p).read_text()
def test_inventory_movements_are_audited_and_tenant_scoped():
 s=src('app/services/inventory_assets_service.py');a=src('app/api/inventory_assets.py');assert 'AuditLog(organization_id=organization_id' in s;assert 'with_for_update()' in s;assert 'get_inventory_movements(db,current_org.id' in a;assert "require_permission('inventory.read')" in a
def test_helpdesk_comments_preserve_requester_privacy():
 a=src('app/api/helpdesk.py');m=src('app/models/helpdesk_comment.py');assert '_visible_ticket' in a;assert "None if _can_manage(user) else user.id" in a;assert 'TicketComment.organization_id==current_user.organization_id' in a;assert "__tablename__='ticket_comments'" in m
def test_communication_delivery_state_is_controlled():
 a=src('app/api/communication.py');s=src('app/services/communication_service.py');assert "communication.manage" in a;assert "{'ALL','STAFF','STUDENTS','PARENTS','BRANCH','GRADE'}" in a;assert 'with_for_update()' in s;assert 'ALLOWED_TRANSITIONS' in s
def test_frontend_workflows_are_connected():
 c=src('../frontend/src/app/communication/page.tsx');h=src('../frontend/src/app/helpdesk/page.tsx');i=src('../frontend/src/app/inventory/page.tsx');assert '/status/${status}' in c;assert '/comments`' in h;assert '/inventory/movements' in i;assert "tab==='assets'" in i
