from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_helpdesk_persists_requester_and_rolls_back_status_failures():
    service = read("app/services/helpdesk_service.py")
    schema = read("app/schemas/helpdesk.py")
    assert "requester_id=user_id" in service
    assert "Ticket.requester_id == user_id" in service
    assert "db.rollback()" in service
    assert "requester_id: UUID | None" in schema


def test_helpdesk_frontend_has_authoritative_summary_and_operational_states():
    page = read("../frontend/src/app/helpdesk/page.tsx")
    assert "'/helpdesk/summary'" in page
    assert "Loading tickets" in page
    assert "No tickets found" in page
    assert 'role="alert"' in page
    assert "SLA OVERDUE" in page


def test_notifications_remain_tenant_and_recipient_scoped():
    api = read("app/api/notifications.py")
    assert "Notification.organization_id==current_user.organization_id" in api
    assert "Notification.user_id==current_user.id" in api
    assert "with_for_update()" in api
    assert "Notification link must be an application path or HTTPS URL" in api


def test_dashboard_scopes_branch_sensitive_metrics():
    api = read("app/api/dashboard.py")
    assert "accessible_branch_ids(current_user)" in api
    assert "Student.branch_id.in_(branch_ids)" in api
    assert "Attendance.branch_id.in_(branch_ids)" in api
    assert "Student.branch_id.in_(branch_ids)" in api
