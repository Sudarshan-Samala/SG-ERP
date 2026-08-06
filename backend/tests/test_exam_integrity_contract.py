from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def source(path:str)->str:return (ROOT/path).read_text()
def test_exam_writes_are_atomic_and_audited():
    service=source('app/services/exam_service.py')
    assert 'db.flush();log_action' in service
    assert 'db.rollback();raise' in service
    assert "'CREATE','EXAM_SCHEDULE'" in service
    assert "'CREATE','EXAM_RESULT'" in service
def test_exam_result_creation_locks_exam_and_validates_marks():
    service=source('app/services/exam_service.py')
    assert "'Exam',lock=True" in service
    assert 'result_in.marks_obtained<0' in service
    assert 'result_in.marks_obtained>schedule.max_marks' in service
def test_result_reads_support_explicit_branch_isolation():
    api=source('app/api/exams.py')
    assert 'branch_id:Optional[UUID]=None' in api
    assert 'enforce_branch_access(current_user,branch_id)' in api
    assert 'allowed={branch_id}' in api
def test_bulk_results_are_all_or_nothing_with_audits():
    api=source('app/api/exams.py');service=source('app/services/exam_service.py')
    assert 'create_exam_result(db,result,current_org.id,current_user.id,commit=False)' in api
    assert 'except Exception:db.rollback();raise' in api
    assert "log_action(db,organization_id,user_id,'CREATE','EXAM_RESULT'" in service
