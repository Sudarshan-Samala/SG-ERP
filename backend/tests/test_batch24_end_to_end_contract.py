from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def src(path: str) -> str:
    return (ROOT / path).read_text()

def test_exam_workspace_has_schedule_and_result_entry():
    page = src('../frontend/src/app/exams/page.tsx')
    assert "api.post('/exams/schedules'" in page
    assert "api.post('/exams/results'" in page
    assert "exam.schedule.manage" in page
    assert "exam.result.create" in page

def test_finance_supports_period_scoped_reporting():
    api = src('app/api/finance.py')
    service = src('app/services/finance_service.py')
    page = src('../frontend/src/app/finance/page.tsx')
    assert 'start_date' in api and 'end_date' in api
    assert 'JournalEntry.date >=' in service and 'JournalEntry.date <=' in service
    assert 'type="date"' in page

def test_inventory_ui_supports_item_creation_and_variable_movements():
    page = src('../frontend/src/app/inventory/page.tsx')
    assert "api.post('/inventory-assets/inventory'" in page
    assert '/adjust' in page
    assert 'movementQty' in page
