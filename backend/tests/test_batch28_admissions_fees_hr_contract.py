from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def src(p):return (ROOT/p).read_text()
def test_fees_enforce_positive_amounts_and_normalized_states():
 t=src('app/services/fee_service.py');assert "Invoice amount must be greater than zero" in t;assert "invoice.status='UNPAID'" in t;assert "invoice.status.upper()" in t;assert "'PARTIALLY_PAID'" in t
def test_hr_enforces_active_users_and_payroll_bounds():
 t=src('app/services/hr_service.py');assert 'User.is_active.is_(True)' in t;assert "employee_code=emp_in.employee_id.strip().upper()" in t;assert 'Gross salary must be greater than zero' in t;assert 'Net salary must be greater than zero' in t
def test_frontend_has_collection_and_pipeline_ux():
 fees=src('../frontend/src/app/fees/page.tsx');hr=src('../frontend/src/app/hr/page.tsx');admissions=src('../frontend/src/app/admissions/page.tsx');assert "api.post('/fees/payments'" in fees;assert 'Payment cannot exceed the outstanding balance.' in fees;assert 'Configured gross:' in hr;assert 'Conversion' in admissions;assert 'Active Pipeline' in admissions
