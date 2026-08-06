from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEPS = ROOT / "app" / "api" / "deps.py"
ORGANIZATIONS = ROOT / "app" / "api" / "organizations.py"
SIGNUP = ROOT / "app" / "api" / "signup.py"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_platform_authority_is_explicit_not_a_permission_bypass():
    source = _read(DEPS)

    assert "def require_platform_admin" in source
    assert "if not current_user.is_superuser" in source

    permission_block = source.split("def require_permission", 1)[1].split(
        "def accessible_branch_ids", 1
    )[0]
    assert "current_user.is_superuser" not in permission_block

    branch_block = source.split("def enforce_branch_access", 1)[1]
    assert "current_user.is_superuser" not in branch_block
    assert "accessible_branch_ids(current_user)" in branch_block


def test_platform_organization_endpoints_use_platform_dependency():
    source = _read(ORGANIZATIONS)

    assert "from app.api.deps import require_platform_admin" in source
    assert source.count("Depends(require_platform_admin)") == 4
    assert "Depends(get_current_user)" not in source
    assert "if not current_user.is_superuser" not in source


def test_public_school_signup_does_not_create_platform_superuser():
    source = _read(SIGNUP)

    # School registration creates a tenant administrator, never a SaaS platform
    # administrator. Keep this invariant explicit because a regression here would
    # turn public signup into a platform privilege-escalation path.
    assert "is_superuser=False" in source
    assert "is_superuser=True" not in source


def test_role_permissions_are_limited_to_tenant_or_global_roles():
    source = _read(DEPS)
    permission_block = source.split("def require_permission", 1)[1].split(
        "def accessible_branch_ids", 1
    )[0]

    assert "role.organization_id in (None, current_user.organization_id)" in permission_block


def test_branch_assignments_are_filtered_to_authenticated_tenant():
    source = _read(DEPS)
    branch_block = source.split("def accessible_branch_ids", 1)[1].split(
        "def enforce_branch_access", 1
    )[0]

    assert "branch.organization_id == current_user.organization_id" in branch_block
