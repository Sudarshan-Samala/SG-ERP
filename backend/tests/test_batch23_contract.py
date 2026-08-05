from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def src(path):return (ROOT/path).read_text()
def test_inventory_adjustment_is_locked_and_rbac_protected():
    service=src('app/services/inventory_assets_service.py');api=src('app/api/inventory_assets.py')
    assert '.with_for_update()' in service
    assert 'Stock adjustment would make inventory negative' in service
    assert 'inventory/{item_id}/adjust' in api
    assert 'require_permission("inventory.manage")' in api
def test_finance_summary_is_tenant_scoped_and_read_protected():
    service=src('app/services/finance_service.py');api=src('app/api/finance.py')
    assert 'JournalEntry.organization_id==organization_id' in service
    assert 'Account.organization_id==organization_id' in service
    assert '"/summary"' in api
    assert 'require_permission("finance.read")' in api
def test_exam_results_require_valid_schedule_and_marks():
    text=src('app/services/exam_service.py')
    assert 'No exam schedule exists for this subject' in text
    assert 'Marks obtained cannot exceed maximum marks' in text
    assert 'Exam schedule is outside the configured exam window' in text
