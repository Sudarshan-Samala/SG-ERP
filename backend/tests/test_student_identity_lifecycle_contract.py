from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_student_identity_is_tenant_scoped_and_not_reusable():
    model = read("app/models/base.py")
    migration = read("migrations/versions/a2608071200_student_permanent_identity_lifecycle.py")
    service = read("app/services/student_service.py")
    assert 'UniqueConstraint("organization_id","student_number"' in model
    assert "uq_students_org_student_number" in migration
    assert "STUDENT_NUMBER_START = 100000" in service
    assert "Permanent student deletion is disabled" in service


def test_admission_number_is_tenant_scoped_not_globally_unique():
    model = read("app/models/base.py")
    migration = read("migrations/versions/a2608071200_student_permanent_identity_lifecycle.py")
    assert 'UniqueConstraint("organization_id","admission_number"' in model
    assert "students_admission_number_key" in migration


def test_student_number_cannot_be_edited_by_client_payload():
    schema = read("app/schemas/student.py")
    update_block = schema.split("class StudentUpdate", 1)[1].split("class StudentStatusUpdate", 1)[0]
    assert "student_number" not in update_block


def test_student_lifecycle_requires_reason_and_has_controlled_transitions():
    schema = read("app/schemas/student.py")
    service = read("app/services/student_service.py")
    assert "reason: str" in schema
    assert "ALLOWED_STATUS_TRANSITIONS" in service
    assert '"ARCHIVED": set()' in service


def test_student_actions_use_separate_permissions():
    api = read("app/api/students.py")
    permissions = read("app/core/permissions.py")
    for permission in ("students.read", "students.create", "students.edit", "students.status.manage", "students.archive", "students.delete"):
        assert permission in permissions
    assert 'require_permission("students.edit")' in api
    assert 'require_permission("students.status.manage")' in api
    assert 'require_permission("students.archive")' in api
    assert 'require_permission("students.delete")' in api


def test_student_number_lookup_is_tenant_and_branch_scoped():
    api = read("app/api/students.py")
    service = read("app/services/student_service.py")
    assert "get_student_by_number(db, student_number, current_org.id)" in api
    assert "enforce_branch_access(current_user, student.branch_id)" in api
    assert "Student.organization_id == organization_id" in service
