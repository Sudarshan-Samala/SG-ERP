from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def src(path):return (ROOT/path).read_text()

def test_admission_workflow_is_controlled_and_branch_protected():
    service=src('app/services/admission_service.py');api=src('app/api/admissions.py')
    assert 'ADMISSION_TRANSITIONS' in service
    assert 'with_for_update()' in service
    assert 'Invalid admission status transition' in service
    assert 'enforce_branch_access(current_user, enquiry.branch_id)' in api

def test_helpdesk_requesters_only_see_their_tickets_unless_managers():
    api=src('app/api/helpdesk.py');service=src('app/services/helpdesk_service.py')
    assert 'None if can_manage else current_user.id' in api
    assert 'query.filter(Ticket.user_id == user_id)' in service
    assert 'with_for_update()' in service

def test_exam_results_are_branch_isolated():
    api=src('app/api/exams.py');service=src('app/services/exam_service.py')
    assert 'accessible_branch_ids(current_user)' in api
    assert 'enforce_branch_access(current_user, student.branch_id)' in api
    assert 'Student.branch_id.in_(branch_ids)' in service
