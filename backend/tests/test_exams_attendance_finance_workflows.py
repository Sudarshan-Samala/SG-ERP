from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def src(p):return (ROOT/p).read_text()
def test_attendance_bulk_and_exceptions_are_branch_secured():
 t=src('app/api/attendance.py');assert "@router.post('/bulk')" in t;assert "@router.get('/exceptions')" in t;assert "enforce_branch_access(current_user,payload.branch_id)" in t;assert "require_permission('attendance.mark')" in t
def test_exam_bulk_results_and_summary_keep_result_permissions():
 t=src('app/api/exams.py');assert "@router.post('/results/bulk')" in t;assert "@router.get('/results/summary')" in t;assert "require_permission('exam.result.create')" in t;assert 'enforce_branch_access(current_user,student.branch_id)' in t
def test_finance_reconciliation_and_export_are_tenant_scoped():
 t=src('app/api/finance.py');assert "@router.get('/reconciliation')" in t;assert "@router.get('/journal/export')" in t;assert 'get_finance_summary(db,current_org.id' in t;assert 'get_journal_entries(db,current_org.id' in t;assert "require_permission('finance.read')" in t
