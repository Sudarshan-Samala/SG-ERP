from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_platform_authority_does_not_bypass_tenant_permissions():
    source = read("app/api/deps.py")
    permission_block = source.split("def require_permission", 1)[1].split("def accessible_branch_ids", 1)[0]
    branch_block = source.split("def enforce_branch_access", 1)[1]
    assert "current_user.is_superuser" not in permission_block
    assert "current_user.is_superuser" not in branch_block
    assert "def require_platform_admin" in source


def test_organization_api_uses_explicit_platform_authority():
    source = read("app/api/organizations.py")
    assert source.count("Depends(require_platform_admin)") == 4
    assert "Depends(get_current_user)" not in source


def test_student_list_is_tenant_and_branch_scoped():
    api = read("app/api/students.py")
    service = read("app/services/student_service.py")
    assert "accessible_branch_ids(current_user)" in api
    assert "Student.organization_id == organization_id" in service
    assert "Student.branch_id.in_(branch_ids)" in service
    assert "if not branch_ids:" in service


def test_student_profile_sensitive_sections_require_explicit_permissions():
    source = read("app/api/students.py")
    assert 'if "attendance.read" in permissions:' in source
    assert 'if "fees.read" in permissions:' in source
    assert 'if "exams.read" in permissions:' in source
    assert 'current_user.is_superuser or "attendance.read"' not in source
    assert 'current_user.is_superuser or "fees.read"' not in source
    assert 'current_user.is_superuser or "exams.read"' not in source


def test_student_create_and_update_validate_school_scope():
    source = read("app/services/student_service.py")
    assert "Branch.organization_id == organization_id" in source
    assert "AcademicYear.organization_id == organization_id" in source
    assert "Student.organization_id == organization_id" in source
