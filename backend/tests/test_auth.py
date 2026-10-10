import pytest
from unittest.mock import patch, AsyncMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from app.main import app
from app.db.database import get_db
from app.db.models import Base, User

@pytest.fixture(autouse=True)
def setup_test_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
            
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.pop(get_db, None)

client = TestClient(app)

def test_whitelisted_test_user_allowed():
    # harisankar@sentellent.com
    res = client.post("/api/auth/google", json={"email": "harisankar@sentellent.com"})
    assert res.status_code == 200
    data = res.json()
    assert data["user"]["email"] == "harisankar@sentellent.com"
    assert data["user"]["is_test_user"] is True
    assert "access_token" in data

    # naga@sentellent.com
    res = client.post("/api/auth/google", json={"email": "naga@sentellent.com"})
    assert res.status_code == 200
    data = res.json()
    assert data["user"]["email"] == "naga@sentellent.com"
    assert data["user"]["is_test_user"] is True

def test_arbitrary_unverified_email_strictly_rejected():
    # Any random unverified email without a Google OAuth token MUST be rejected with 401
    res = client.post("/api/auth/google", json={"email": "randomuser@gmail.com"})
    assert res.status_code == 401
    assert "strictly restricted to Sentellent test users" in res.json()["detail"]

    res = client.post("/api/auth/google", json={"email": "attacker@evil.com"})
    assert res.status_code == 401

def test_invalid_google_token_rejected():
    res = client.post("/api/auth/google", json={"id_token": "fake_invalid_token_12345"})
    assert res.status_code == 401
    assert "Google OAuth verification failed" in res.json()["detail"]

@pytest.mark.asyncio
async def test_verified_google_token_accepted():
    mock_google_info = {
        "email": "verified_investor@gmail.com",
        "email_verified": "true",
        "name": "Verified Google Investor",
        "picture": "https://lh3.googleusercontent.com/test.jpg"
    }
    with patch("app.api.auth.verify_google_id_token", new=AsyncMock(return_value=mock_google_info)):
        res = client.post("/api/auth/google", json={"id_token": "valid_signed_google_jwt"})
        assert res.status_code == 200
        data = res.json()
        assert data["user"]["email"] == "verified_investor@gmail.com"
        assert data["user"]["name"] == "Verified Google Investor"
