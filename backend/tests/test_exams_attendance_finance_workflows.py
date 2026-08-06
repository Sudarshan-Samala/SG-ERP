from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def src(p):
    return (ROOT / p).read_text()


def test_attendance_bulk_and_exceptions_are_branch_secured():
    t = src('app/api/attendance.py')
    assert "@router.post('/bulk')" in t
    assert "@router.get('/exceptions')" in t
    assert "enforce_branch_access(current_user,payload.branch_id)" in t
    assert "require_permission('attendance.mark')" in t


def test_exam_bulk_results_are_atomic_and_branch_secured():
    api = src('app/api/exams.py')
    service = src('app/services/exam_service.py')
    assert "@router.post('/results/bulk')" in api
    assert "require_permission('exam.result.create')" in api
    assert 'Student.organization_id == current_org.id' in api
    assert 'enforce_branch_access(current_user, student_by_id[result.student_id].branch_id)' in api
    assert 'create_exam_result(db, result, current_org.id, current_user.id, commit=False)' in api
    assert 'db.rollback()' in api
    assert 'db.commit()' in api
    assert 'commit: bool = True' in service
    assert 'db.flush()' in service


def test_exam_bulk_result_ui_uses_atomic_endpoint_and_scheduled_subjects():
    t = src('../frontend/src/app/exams/page.tsx')
    assert "api.post('/exams/results/bulk',{results:rows})" in t
    assert 'Bulk Result Entry' in t
    assert 'schedules.some(x=>x.exam_id===bulkExam&&x.subject_id===s.id)' in t
    assert 'No partial batch was retained.' in t


def test_exam_summary_keeps_result_read_permission():
    t = src('app/api/exams.py')
    assert "@router.get('/results/summary')" in t
    assert "require_permission('exam.result.read')" in t
    assert 'accessible_branch_ids(current_user)' in t


def test_finance_reconciliation_and_export_are_tenant_scoped():
    t = src('app/api/finance.py')
    assert "@router.get('/reconciliation')" in t
    assert "@router.get('/journal/export')" in t
    assert 'get_finance_summary(db,current_org.id' in t
    assert 'get_journal_entries(db,current_org.id' in t
    assert "require_permission('finance.read')" in t
