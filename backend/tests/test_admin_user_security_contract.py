from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def src(path):return (ROOT/path).read_text()

def test_user_admin_is_tenant_and_permission_scoped():
    api=src('app/api/users.py');service=src('app/services/user_management_service.py')
    assert "require_permission('users.manage')" in api
    assert 'User.organization_id==organization_id' in service
    assert 'Branch.organization_id==organization_id' in service
    assert 'Role.organization_id==organization_id' in service

def test_user_mutations_are_locked_audited_and_rollback_safe():
    service=src('app/services/user_management_service.py')
    assert '.with_for_update().first()' in service
    assert "log_action(db,organization_id,actor_id,'CREATE','USER'" in service
    assert "log_action(db,organization_id,actor_id,'UPDATE','USER'" in service
    assert 'except Exception:db.rollback();raise' in service

def test_user_security_prevents_weak_password_and_self_deactivation():
    service=src('app/services/user_management_service.py')
    assert 'Password must include uppercase, lowercase, number and special character' in service
    assert "user.id==actor_id and user_in.is_active is False" in service
    assert 'revoke_all_sessions' in service

def test_user_api_never_trusts_client_organization_id():
    api=src('app/api/users.py')
    assert 'create_user(db,user_in,current_org.id,current_user.id)' in api
    assert 'user_in.organization_id = current_org.id' not in api
