from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.config import settings
from app.core.database import Base, get_db
from app.models.base import Branch, Organization, Permission, Role, Student, User, user_roles
from app.services.auth import get_password_hash
from app.services import rate_limit as rate_limit_module


engine = create_engine(settings.DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_auth_limiters():
    for name in (
        "login_ip_limiter",
        "login_account_limiter",
        "refresh_ip_limiter",
        "refresh_session_limiter",
    ):
        limiter = getattr(rate_limit_module, name, None)
        if limiter is not None:
            limiter.clear()
    yield


def _seed_user(*, branch_count=1):
    db = TestingSessionLocal()
    suffix = uuid4().hex[:10]
    org = Organization(name=f"E2E Org {suffix}")
    db.add(org)
    db.flush()

    branches = []
    for index in range(branch_count):
        branch = Branch(
            organization_id=org.id,
            name=f"E2E Branch {suffix}-{index}",
            code=f"E{suffix[:5]}{index}",
        )
        db.add(branch)
        branches.append(branch)
    db.flush()

    permission = Permission(name="students.read", description="E2E student read")
    role = Role(name=f"E2E Reader {suffix}", organization_id=org.id)
    role.permissions.append(permission)
    db.add_all([permission, role])
    db.flush()

    user = User(
        organization_id=org.id,
        email=f"e2e-{suffix}@example.test",
        hashed_password=get_password_hash("E2E-Password-123!"),
        full_name="E2E User",
        is_active=True,
        is_superuser=False,
    )
    user.roles.append(role)
    user.branches.append(branches[0])
    db.add(user)
    db.commit()
    db.refresh(user)
    for branch in branches:
        db.refresh(branch)

    data = {
        "organization_id": org.id,
        "user_id": user.id,
        "email": user.email,
        "branches": branches,
    }
    db.close()
    return data


def _login(client_instance, email):
    return client_instance.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "E2E-Password-123!"},
    )


def _csrf_headers(response):
    return {"X-CSRF-Token": response.json()["csrf_token"]}


def test_auth_login_refresh_rotation_and_replay_detection():
    seeded = _seed_user()
    login = _login(client, seeded["email"])
    assert login.status_code == 200
    body = login.json()
    assert body["access_token"]
    assert body["session_id"]
    assert body["csrf_token"]

    access_token = body["access_token"]
    old_refresh = client.cookies.get(settings.REFRESH_COOKIE_NAME)
    assert old_refresh

    sessions = client.get(
        "/api/v1/auth/sessions",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert sessions.status_code == 200
    assert len(sessions.json()) == 1

    refreshed = client.post("/api/v1/auth/refresh", headers=_csrf_headers(login))
    assert refreshed.status_code == 200
    new_refresh = client.cookies.get(settings.REFRESH_COOKIE_NAME)
    assert new_refresh and new_refresh != old_refresh

    replay = client.post(
        "/api/v1/auth/refresh",
        headers={"X-CSRF-Token": refreshed.json()["csrf_token"]},
        cookies={settings.REFRESH_COOKIE_NAME: old_refresh},
    )
    assert replay.status_code == 401

    revoked_access = refreshed.json()["access_token"]
    me_after_replay = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {revoked_access}"},
    )
    assert me_after_replay.status_code == 401


def test_csrf_is_required_for_state_changing_auth_operations():
    seeded = _seed_user()
    login = _login(client, seeded["email"])
    assert login.status_code == 200

    missing_csrf = client.post("/api/v1/auth/logout")
    assert missing_csrf.status_code == 403

    valid_csrf = client.post("/api/v1/auth/logout", headers=_csrf_headers(login))
    assert valid_csrf.status_code == 204


def test_login_rate_limit_returns_429_and_retry_after():
    seeded = _seed_user()
    responses = [
        _login(client, seeded["email"])
        for _ in range(settings.AUTH_LOGIN_RATE_LIMIT + 1)
    ]
    assert all(response.status_code == 401 for response in responses[:-1])
    assert responses[-1].status_code == 429
    assert responses[-1].headers.get("Retry-After")


def test_tenant_isolation_rejects_cross_organization_student_access():
    first = _seed_user()
    second = _seed_user()
    db = TestingSessionLocal()
    branch = first["branches"][0]
    student = Student(
        organization_id=second["organization_id"],
        branch_id=second["branches"][0].id,
        academic_year_id=uuid4(),
        admission_number=f"E2E-{uuid4().hex[:8]}",
        student_name="Tenant Boundary Student",
        date_of_birth=datetime(2015, 1, 1),
        gender="OTHER",
    )
    # Use a valid academic-year foreign key from the same tenant.
    from app.models.base import AcademicYear

    academic_year = AcademicYear(
        id=student.academic_year_id,
        organization_id=second["organization_id"],
        name=f"E2E AY {uuid4().hex[:8]}",
        start_date=datetime(2026, 4, 1),
        end_date=datetime(2027, 3, 31),
        is_active=True,
    )
    db.add_all([academic_year, student])
    db.commit()
    student_id = student.id
    db.close()

    login = _login(client, first["email"])
    assert login.status_code == 200
    token = login.json()["access_token"]
    response = client.get(
        f"/api/v1/students/{student_id}/profile",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


def test_branch_isolation_limits_student_listing_and_profile():
    seeded = _seed_user(branch_count=2)
    db = TestingSessionLocal()
    second_branch = seeded["branches"][1]
    from app.models.base import AcademicYear

    academic_year = AcademicYear(
        organization_id=seeded["organization_id"],
        name=f"E2E Branch AY {uuid4().hex[:8]}",
        start_date=datetime(2026, 4, 1),
        end_date=datetime(2027, 3, 31),
        is_active=True,
    )
    db.add(academic_year)
    db.flush()
    hidden_student = Student(
        organization_id=seeded["organization_id"],
        branch_id=second_branch.id,
        academic_year_id=academic_year.id,
        admission_number=f"E2E-BR-{uuid4().hex[:8]}",
        student_name="Hidden Branch Student",
        date_of_birth=datetime(2014, 5, 5),
        gender="OTHER",
    )
    db.add(hidden_student)
    db.commit()
    hidden_student_id = hidden_student.id
    db.close()

    login = _login(client, seeded["email"])
    assert login.status_code == 200
    token = login.json()["access_token"]
    auth = {"Authorization": f"Bearer {token}"}

    listing = client.get("/api/v1/students/", headers=auth)
    assert listing.status_code == 200
    assert all(row["id"] != str(hidden_student_id) for row in listing.json())

    hidden_profile = client.get(
        f"/api/v1/students/{hidden_student_id}/profile",
        headers=auth,
    )
    assert hidden_profile.status_code == 403
