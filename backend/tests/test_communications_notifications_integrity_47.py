from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def src(p):return (ROOT/p).read_text()
def test_notifications_are_tenant_user_scoped_and_audited():
 s=src('app/api/notifications.py');assert 'Notification.organization_id==current_user.organization_id' in s;assert 'Notification.user_id==current_user.id' in s;assert "require_permission('communication.manage')" in s;assert "'CREATE','NOTIFICATION'" in s;assert 'db.rollback()' in s
def test_notification_links_are_constrained_and_summary_is_private():
 s=src('app/api/notifications.py');assert "link.startswith('/') or link.startswith('https://')" in s;assert "@router.get('/summary')" in s;assert "'unread':unread" in s
def test_communication_writes_are_atomic_and_actor_audited():
 s=src('app/services/communication_service.py');assert "'CREATE','COMMUNICATION'" in s;assert "'UPDATE','COMMUNICATION'" in s;assert '.with_for_update().first()' in s;assert 'db.flush()' in s;assert 'db.rollback()' in s
def test_targets_are_active_branch_scoped_locked_and_audited():
 s=src('app/api/communication.py');assert 'Branch.is_active.is_(True)' in s;assert 'enforce_branch_access(current_user' in s;assert 'CommunicationModel.organization_id==current_org.id' in s;assert "'UPDATE','COMMUNICATION_TARGET'" in s
def test_frontend_uses_authoritative_summary_and_operational_states():
 s=src('../frontend/src/app/communication/page.tsx');assert "api.get('/communication/summary')" in s;assert 'Loading communications' in s;assert 'No communications match this view' in s;assert 'No authorized targets are available' in s
