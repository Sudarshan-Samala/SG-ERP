from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def source(path:str)->str:
    return (ROOT/path).read_text()

def test_hr_writes_commit_business_record_and_audit_atomically():
    service=source('app/services/hr_service.py')
    assert "db.flush();log_action" in service
    assert "except Exception:db.rollback();raise" in service
    assert "_require_employee(db,struct_in.employee_id,organization_id,lock=True)" in service

def test_payroll_creation_locks_salary_and_employee_before_duplicate_check():
    service=source('app/services/hr_service.py')
    assert "_require_employee(db,payroll_in.employee_id,organization_id,lock=True)" in service
    assert "SalaryStructure.employee_id==payroll_in.employee_id).with_for_update().first()" in service
    assert "Payroll already exists for this employee and period" in service

def test_payroll_reporting_validates_and_filters_period_server_side():
    api=source('app/api/hr.py')
    assert "def _validate_period" in api
    assert "get_payrolls(db,current_org.id,employee_id,month,year)" in api
    assert "Month must be between 1 and 12" in api
    assert "Year must be between 2000 and 2200" in api

def test_payslip_is_permission_and_tenant_scoped():
    api=source('app/api/hr.py')
    assert "@router.get('/payroll/{payroll_id}/payslip')" in api
    assert "require_permission('hr.payroll.read')" in api
    assert "PayrollModel.organization_id==current_org.id" in api
    assert "EmployeeModel.organization_id==current_org.id" in api
    assert "User.organization_id==current_org.id" in api

def test_frontend_uses_period_filtered_payroll_and_authoritative_payslip():
    page=source('../frontend/src/app/hr/page.tsx')
    assert "api.get('/hr/payroll',{params:selected})" in page
    assert "api.get(`/hr/payroll/${id}/payslip`)" in page
    assert "No payroll records for this period." in page
    assert "Print / Save PDF" in page
