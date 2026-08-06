from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def source(path:str)->str:
    return (ROOT/path).read_text()

def test_monthly_attendance_analytics_is_permission_and_branch_scoped():
    api=source('app/api/attendance.py')
    assert "@router.get('/analytics/monthly')" in api
    assert "require_permission('attendance.read')" in api
    assert 'enforce_branch_access(current_user, branch_id)' in api
    assert "'present_rate'" in api
    assert "'daily'" in api

def test_fee_statement_and_receipt_are_tenant_branch_scoped():
    api=source('app/api/fees.py')
    assert "@router.get('/students/{student_id}/statement')" in api
    assert "@router.get('/payments/{payment_id}/receipt')" in api
    assert "require_permission('fees.read')" in api
    assert 'enforce_branch_access(current_user' in api
    assert 'PaymentModel.organization_id==current_org.id' in api

def test_fee_frontend_integrates_statement_and_receipt_workflows():
    page=source('../frontend/src/app/fees/page.tsx')
    assert '/statement`' in page
    assert '/receipt`' in page
    assert 'Student Fee Statement' in page
    assert 'Payment Receipt' in page
    assert 'Print / Save PDF' in page
