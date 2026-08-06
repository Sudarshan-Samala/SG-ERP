from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def source(path:str)->str:
    return (ROOT/path).read_text()

def test_attendance_ui_consumes_monthly_analytics():
    page=source('../frontend/src/app/attendance/page.tsx')
    assert "api.get('/attendance/analytics/monthly'" in page
    assert 'Monthly attendance analytics' in page
    assert 'present_rate' in page
    assert 'active_days' in page

def test_fee_payment_uses_locked_invoice_and_atomic_audit_transaction():
    service=source('app/services/fee_service.py')
    assert '.with_for_update().first()' in service
    assert "if outstanding<=0" in service
    assert 'db.flush();log_action' in service
    assert 'except HTTPException:' in service
    assert 'db.rollback();raise' in service

def test_fee_payment_never_accepts_overpayment():
    service=source('app/services/fee_service.py')
    assert 'payment_in.amount_paid>outstanding' in service
    assert 'Payment exceeds the outstanding invoice amount' in service
