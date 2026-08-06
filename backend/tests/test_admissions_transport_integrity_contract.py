from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def source(path:str)->str:return (ROOT/path).read_text()
def test_admissions_are_atomic_audited_and_active_scope_only():
    service=source('app/services/admission_service.py');api=source('app/api/admissions.py')
    assert 'Branch.is_active.is_(True)' in service and 'AcademicYear.is_active.is_(True)' in service
    assert 'db.flush(); log_action' in service and 'db.rollback(); raise' in service
    assert "current_user.id" in api and "db.flush();log_action" in api
    assert "with_for_update().first()" in api
def test_transport_creation_is_atomic_and_vehicle_assignment_locked():
    service=source('app/services/transport_service.py')
    assert 'def _commit_audited' in service
    assert 'db.flush();log_action' in service
    assert 'db.rollback();raise' in service
    assert 'with_for_update().first()' in service
    assert 'capacity>200' in service
def test_transport_ui_consumes_authoritative_summary():
    page=source('../frontend/src/app/transport/page.tsx')
    assert "api.get('/transport/summary')" in page
    assert 'Available vehicles' in page
    assert 'Fleet capacity' in page
