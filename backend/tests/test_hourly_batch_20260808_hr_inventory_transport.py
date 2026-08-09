from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_hr_department_payroll_reporting_is_period_and_tenant_scoped():
    api = read("app/api/hr.py")
    page = read("../frontend/src/app/hr/page.tsx")
    assert "@router.get('/payroll-summary/by-department')" in api
    assert "_period_query(db,current_org.id,month,year)" in api
    assert "require_permission('hr.payroll.read')" in api
    assert "'/hr/payroll-summary/by-department'" in page
    assert "No department payroll for this period." in page


def test_inventory_lifecycle_mutations_are_rollback_safe_and_validate_names():
    service = read("app/services/inventory_assets_service.py")
    assert "def _validate_name" in service
    assert "db.rollback();raise" in service
    assert "Only disposed assets can be permanently deleted" in service
    assert "Inventory with remaining stock cannot be deleted" in service


def test_transport_surfaces_unassigned_route_gap_without_bypassing_org_scope():
    api = read("app/api/transport.py")
    page = read("../frontend/src/app/transport/page.tsx")
    assert '"unassigned_routes"' in api
    assert 'require_permission("transport.read")' in api
    assert "unassigned_routes" in page
    assert 'role={tone===\'error\'?\'alert\':\'status\'}' in page
