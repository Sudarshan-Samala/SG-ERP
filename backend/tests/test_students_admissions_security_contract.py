from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def source(path:str)->str:return (ROOT/path).read_text()
def test_student_directory_is_branch_scoped():
    api=source('app/api/students.py');service=source('app/services/student_service.py')
    assert 'accessible_branch_ids(current_user)' in api
    assert 'enforce_branch_access(current_user, branch_id)' in api
    assert 'Student.branch_id.in_(branch_ids)' in service
def test_student_writes_normalize_identity_and_audit_atomically():
    service=source('app/services/student_service.py')
    assert "admission_number.strip().upper()" in service
    assert "db.flush();log_action" in service
    assert 'except Exception:db.rollback();raise' in service
def test_admission_conversion_is_locked_scoped_and_atomic():
    api=source('app/api/admissions.py')
    assert '.with_for_update().first()' in api
    assert 'enforce_branch_access(current_user,enquiry.branch_id)' in api
    assert 'Branch.is_active==True' in api
    assert "db.flush();log_action" in api
    assert 'except HTTPException:db.rollback();raise' in api
def test_students_frontend_uses_server_branch_filter():
    page=source('../frontend/src/app/students/page.tsx')
    assert "{branch_id:branchFilter}" in page
    assert "api.get('/students/',{params})" in page
