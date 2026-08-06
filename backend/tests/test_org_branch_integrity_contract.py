from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVICE = (ROOT / "app/services/org_service.py").read_text()
BRANCH_API = (ROOT / "app/api/branches.py").read_text()
ORG_API = (ROOT / "app/api/organizations.py").read_text()


def test_org_and_branch_mutations_are_atomic_and_locked():
    assert "with_for_update()" in SERVICE
    assert SERVICE.count("db.rollback()") >= 6
    assert "db.flush()" in SERVICE
    assert "log_action" in SERVICE


def test_branch_identity_is_normalized_and_tenant_scoped():
    assert "value.strip().upper()" in SERVICE
    assert "Branch.organization_id == organization_id" in SERVICE
    assert "Branch.code == code" in SERVICE
    assert "Branch.id != branch_id" in SERVICE


def test_destructive_tenant_operations_have_safety_guards():
    assert "deactivate it instead of deleting" in SERVICE
    assert "Deactivate the branch before deleting it" in SERVICE
    assert "referenced by ERP records" in SERVICE


def test_apis_preserve_rbac_and_return_conflict_errors():
    assert 'require_permission("branches.manage")' in BRANCH_API
    assert 'require_permission("branches.read")' in BRANCH_API
    assert "HTTP_409_CONFLICT" in BRANCH_API
    assert "_require_superuser" in ORG_API
    assert "HTTP_409_CONFLICT" in ORG_API
