from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def src(p):return (ROOT/p).read_text()

def test_attendance_export_is_permission_and_branch_scoped():
    api=src('app/api/attendance.py')
    assert "@router.get('/export.csv')" in api
    assert "require_permission('attendance.read')" in api
    assert 'accessible_branch_ids(current_user)' in api
    assert "Student.branch_id==payload.branch_id" in api
    assert "Student does not belong to the selected branch" in api

def test_reporting_ui_uses_authoritative_attendance_export():
    ui=src('../frontend/src/app/reports/page.tsx')
    assert "api.get('/attendance/export.csv'" in ui
    assert "responseType:'blob'" in ui
    assert 'server-generated attendance data' in ui
    assert "can('reports.read')" in ui

def test_payroll_reporting_ui_uses_scoped_summary_and_export():
    api=src('app/api/hr.py');ui=src('../frontend/src/app/hr/page.tsx')
    assert "require_permission('hr.payroll.read')" in api
    assert "PayrollModel.organization_id==org_id" in api
    assert "api.get('/hr/payroll-summary'" in ui
    assert "api.get('/hr/payroll-export.csv'" in ui
    assert "responseType:'blob'" in ui
    assert 'Payroll reporting' in ui
