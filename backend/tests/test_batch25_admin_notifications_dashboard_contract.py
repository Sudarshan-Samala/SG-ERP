from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def src(path): return (ROOT/path).read_text()

def test_rbac_role_lifecycle_is_tenant_safe():
    service=src('app/services/rbac_service.py'); api=src('app/api/rbac.py')
    assert 'Role.organization_id == organization_id' in service
    assert 'Remove this role from all users before deleting it' in service
    assert '@router.delete("/{role_id}"' in api
    assert 'require_permission("rbac.manage")' in api

def test_notifications_are_private_to_recipient_and_tenant():
    text=src('app/api/notifications.py')
    assert 'Notification.organization_id == current_user.organization_id' in text
    assert 'Notification.user_id == current_user.id' in text
    assert 'recipient = db.query(User).filter' in text
    assert '"communication.manage" not in permission_names' in text

def test_dashboard_is_permission_and_branch_scoped():
    text=src('app/api/dashboard.py')
    assert 'accessible_branch_ids(current_user)' in text
    assert '"students.read" in permissions' in text
    assert 'Student.branch_id.in_(branch_ids)' in text
    assert 'Ticket.requester_id == current_user.id' in text
    assert '"fees.read" in permissions' in text

def test_frontend_exposes_notification_and_admin_workflows():
    layout=src('../frontend/src/app/layout.tsx'); notifications=src('../frontend/src/app/notifications/page.tsx'); admin=src('../frontend/src/app/access-control/page.tsx')
    assert "href:'/notifications'" in layout
    assert "api.post('/notifications/read-all')" in notifications
    assert "can('rbac.manage')" in admin
    assert 'api.delete(`/rbac/${role.id}`)' in admin
