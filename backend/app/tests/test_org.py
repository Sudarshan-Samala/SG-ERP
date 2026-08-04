import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import Base, get_db
from app.core.config import settings
from app.models.base import User, Organization
from app.services.auth import get_password_hash

# Override settings for tests
settings.DATABASE_URL = "postgresql:///sg_erp_test"

engine = create_engine(settings.DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Recreate tables to ensure clean state
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture
def test_db():
    db = TestingSessionLocal()
    yield db
    db.close()

def test_create_org_as_superuser(test_db):
    # Setup Superuser
    org = Organization(name="Test Org")
    test_db.add(org)
    test_db.commit()
    
    user = User(
        email="admin@test.com", 
        hashed_password=get_password_hash("password"),
        is_superuser=True,
        organization_id=org.id
    )
    test_db.add(user)
    test_db.commit()

    # Login
    login_res = client.post("/api/v1/auth/login", data={"username": "admin@test.com", "password": "password"})
    token = login_res.json()["access_token"]
    
    # Create Org
    headers = {"Authorization": f"Bearer {token}"}
    res = client.post("/api/v1/organizations/", json={"name": "New Org"}, headers=headers)
    assert res.status_code == 200
    assert res.json()["name"] == "New Org"
