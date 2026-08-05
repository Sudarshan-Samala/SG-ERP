from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def src(p):return (ROOT/p).read_text()
def test_admission_conversion_is_locked_and_branch_scoped():
 t=src('app/api/admissions.py');assert "with_for_update()" in t;assert "enforce_branch_access(current_user,enquiry.branch_id)" in t;assert "enquiry.status.upper()!='SELECTED'" in t;assert "enquiry.status='ADMITTED'" in t;assert "require_permission('students.create')" in t
def test_fee_statement_and_receipt_are_branch_scoped():
 t=src('app/api/fees.py');assert "@router.get('/students/{student_id}/statement')" in t;assert "@router.get('/payments/{payment_id}/receipt')" in t;assert t.count('enforce_branch_access(current_user')>=6;assert "require_permission('fees.read')" in t
def test_payroll_reporting_is_tenant_scoped_and_exportable():
 t=src('app/api/hr.py');assert "PayrollModel.organization_id==org_id" in t;assert "@router.get('/payroll-summary')" in t;assert "@router.get('/payroll-export.csv')" in t;assert "require_permission('hr.payroll.read')" in t;assert "text/csv" in t
def test_admissions_frontend_uses_conversion_api():
 t=src('../frontend/src/app/admissions/page.tsx');assert "can('students.create')" in t;assert '/convert`' in t;assert 'Admit student' in t;assert 'Create student record' in t
