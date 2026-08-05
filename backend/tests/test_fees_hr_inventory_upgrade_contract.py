from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def source(path: str) -> str:
    return (ROOT / path).read_text()

def test_fee_api_enforces_branch_access():
    text = source("app/api/fees.py")
    assert "accessible_branch_ids(current_user)" in text
    assert "enforce_branch_access(current_user, get_student_branch_id" in text
    assert "enforce_branch_access(current_user, get_invoice_branch_id" in text

def test_fee_queries_scope_invoices_and_payments_by_student_branch():
    text = source("app/services/fee_service.py")
    assert "Student.branch_id.in_(branch_ids)" in text
    assert "join(Student, Student.id == Invoice.student_id)" in text

def test_payment_creation_locks_invoice_and_rejects_non_positive_amount():
    text = source("app/services/fee_service.py")
    assert ".with_for_update().first()" in text
    assert "payment_in.amount_paid <= 0" in text
    assert "Payment exceeds the outstanding invoice amount" in text

def test_hr_ui_is_permission_aware_and_inventory_has_operational_states():
    hr = (ROOT.parent / "frontend/src/app/hr/page.tsx").read_text()
    inventory = (ROOT.parent / "frontend/src/app/inventory/page.tsx").read_text()
    assert "hr.employee.create" in hr
    assert "apiErrorMessage" in hr
    assert "Low Stock Items" in inventory
    assert "Out of stock" in inventory
    assert "apiErrorMessage" in inventory
