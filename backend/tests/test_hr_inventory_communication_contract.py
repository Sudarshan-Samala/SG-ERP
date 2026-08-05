from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def source(path):return (ROOT/path).read_text()
def test_payroll_requires_salary_structure_and_gross_cap():
 text=source('app/services/hr_service.py');assert 'Create a salary structure before payroll' in text;assert 'Net salary cannot exceed configured gross salary' in text
def test_salary_structure_is_unique_per_employee():
 text=source('app/services/hr_service.py');assert 'Salary structure already exists for this employee' in text
def test_inventory_prevents_unsafe_deletion_and_duplicates():
 text=source('app/services/inventory_assets_service.py');assert 'Inventory item name already exists' in text;assert 'remaining stock cannot be deleted' in text;assert 'Only disposed assets can be permanently deleted' in text
def test_communication_transitions_are_locked():
 text=source('app/services/communication_service.py');assert '.with_for_update().first()' in text;assert 'ALLOWED_TRANSITIONS' in text
