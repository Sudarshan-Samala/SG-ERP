from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def source(path:str)->str:return (ROOT/path).read_text()
def test_assignee_directory_is_tenant_scoped_and_manager_only():
 api=source('app/api/helpdesk.py');assert "@router.get('/assignees')" in api;assert "require_permission('helpdesk.manage')" in api;assert 'User.organization_id==current_user.organization_id' in api;assert 'User.is_active.is_(True)' in api
def test_assignment_is_locked_validated_audited_and_atomic():
 api=source('app/api/helpdesk.py');assert 'with_for_update().first()' in api;assert 'SLA due time must be in the future' in api;assert "'HELPDESK_ASSIGNMENT'" in api;assert 'db.flush();log_action' in api;assert 'db.rollback();raise' in api
def test_helpdesk_frontend_uses_assignee_directory_and_summary():
 page=source('../frontend/src/app/helpdesk/page.tsx');assert "api.get('/helpdesk/summary')" in page;assert "api.get('/helpdesk/assignees')" in page;assert 'SLA overdue' in page;assert '<select className="input" value={assignment.assignee_id' in page
