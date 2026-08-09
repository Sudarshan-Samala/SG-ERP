import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from starlette.requests import Request

from app.main import app
from app.core.database import Base, get_db
from app.core.config import settings
from app.services.csrf import generate_csrf_token, require_csrf

# Override settings for tests
settings.DATABASE_URL = "postgresql:///sg_erp_test"

engine = create_engine(settings.DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


def test_login_fail():
    response = client.post("/api/v1/auth/login", data={"username": "test@example.com", "password": "wrongpassword"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


def test_csrf_bootstrap():
    response = client.get("/api/v1/auth/csrf")
    assert response.status_code == 200
    token = response.json()["csrf_token"]
    assert isinstance(token, str)
    assert len(token) >= 32
    assert settings.CSRF_COOKIE_NAME in response.cookies


def _request_with_csrf(token: str) -> Request:
    return Request({
        "type": "http",
        "method": "POST",
        "path": "/api/v1/auth/refresh",
        "headers": [(b"x-csrf-token", token.encode("utf-8"))],
    })


def test_csrf_accepts_valid_header_without_cookie():
    token = generate_csrf_token()
    require_csrf(_request_with_csrf(token))


def test_csrf_rejects_invalid_header():
    with pytest.raises(HTTPException) as exc_info:
        require_csrf(_request_with_csrf("not-a-valid-csrf-token"))
    assert exc_info.value.status_code == 403
