from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def source(path: str) -> str:
    return (ROOT / path).read_text()


def test_auth_me_exposes_authorization_context():
    text = source("app/api/auth.py")
    assert '"permissions": permissions' in text
    assert '"branches": branches' in text
    assert 'permission.name for role in current_user.roles' in text


def test_admissions_are_branch_scoped_and_default_deny():
    api = source("app/api/admissions.py")
    service = source("app/services/admission_service.py")
    assert "accessible_branch_ids(current_user)" in api
    assert "enforce_branch_access(current_user, enquiry_in.branch_id)" in api
    assert "AdmissionEnquiry.branch_id.in_(branch_ids)" in service
    assert "if not branch_ids:" in service


def test_admission_contact_is_normalized_before_duplicate_check():
    text = source("app/services/admission_service.py")
    assert ".strip().lower()" in text
    assert "normalized_phone = enquiry_in.phone.strip()" in text
