from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT.parent / "frontend"


def backend(path: str) -> str:
    return (ROOT / path).read_text()


def frontend(path: str) -> str:
    return (FRONTEND / path).read_text()


def test_transport_enforces_operational_integrity():
    service = backend("app/services/transport_service.py")
    page = frontend("src/app/transport/page.tsx")
    assert 'Vehicle is already assigned to another route' in service
    assert 'license_number.strip().upper()' in service
    assert "can('transport.manage')" in page
    assert "api.get('/transport/routes')" in page
    assert "api.get('/transport/drivers')" in page


def test_exam_schedule_rejects_grade_time_conflicts():
    service = backend("app/services/exam_service.py")
    assert "ExamSchedule.grade_id==schedule_in.grade_id" in service
    assert "ExamSchedule.date==schedule_in.date" in service
    assert "This grade already has an exam scheduled at this date and time" in service
    assert "order_by(ExamResult.exam_id,ExamResult.student_id,ExamResult.subject_id)" in service


def test_asset_lifecycle_is_permission_aware_in_ui():
    page = frontend("src/app/inventory/page.tsx")
    service = backend("app/services/inventory_assets_service.py")
    assert "can('assets.manage')" in page
    assert "api.put(`/inventory-assets/assets/${asset.id}`" in page
    assert "api.delete(`/inventory-assets/assets/${asset.id}`" in page
    assert '"DISPOSED":{"DISPOSED"}' in service
    assert 'Only disposed assets can be permanently deleted' in service
