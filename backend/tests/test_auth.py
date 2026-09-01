"""
End-to-end integration tests for Authentication API endpoints
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.models.user import User


def test_user_registration_success(client: TestClient, db_session: Session):
    payload = {
        "email": "Artisan@JewelMind.com",  # Mixed case to test normalization
        "full_name": "Elena Rostova",
        "password": "MasterCraftsman2026!",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "artisan@jewelmind.com"
    assert data["user"]["full_name"] == "Elena Rostova"
    assert "password" not in data["user"]
    assert "hashed_password" not in data["user"]

    # Verify stored password in DB is hashed
    db_user = db_session.query(User).filter_by(email="artisan@jewelmind.com").first()
    assert db_user is not None
    assert db_user.hashed_password != payload["password"]
    assert db_user.hashed_password.startswith("$2b$")


def test_user_registration_duplicate_email(client: TestClient):
    payload = {
        "email": "duplicate@jewelmind.com",
        "full_name": "First User",
        "password": "ValidPassword123!",
    }
    # First registration
    res1 = client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    # Second registration with duplicate email
    res2 = client.post("/api/v1/auth/register", json=payload)
    assert res2.status_code == 409
    data = res2.json()
    assert data["error"]["code"] == "EMAIL_ALREADY_EXISTS"
    assert "already exists" in data["error"]["message"]


def test_user_registration_short_password(client: TestClient):
    payload = {
        "email": "shortpass@jewelmind.com",
        "full_name": "Short Pass",
        "password": "123",  # Less than 8 chars
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_user_registration_invalid_email(client: TestClient):
    payload = {
        "email": "not-an-email-address",
        "full_name": "Invalid Email",
        "password": "ValidPassword123!",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_user_login_success(client: TestClient):
    # Register user first
    reg_payload = {
        "email": "login_user@jewelmind.com",
        "full_name": "Login Tester",
        "password": "CorrectPassword123!",
    }
    client.post("/api/v1/auth/register", json=reg_payload)

    # Login
    login_payload = {
        "email": "login_user@jewelmind.com",
        "password": "CorrectPassword123!",
    }
    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "login_user@jewelmind.com"


def test_user_login_invalid_password(client: TestClient):
    # Register user
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "wrongpass@jewelmind.com",
            "full_name": "Tester",
            "password": "CorrectPassword123!",
        },
    )

    # Attempt login with wrong password
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "wrongpass@jewelmind.com",
            "password": "IncorrectPassword999!",
        },
    )
    assert response.status_code == 401
    data = response.json()
    assert data["error"]["code"] == "INVALID_CREDENTIALS"


def test_user_login_unknown_email(client: TestClient):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "nonexistent@jewelmind.com",
            "password": "SomePassword123!",
        },
    )
    assert response.status_code == 401
    data = response.json()
    assert data["error"]["code"] == "INVALID_CREDENTIALS"


def test_get_current_user_me_authenticated(client: TestClient):
    # Register and get token
    reg_res = client.post(
        "/api/v1/auth/register",
        json={
            "email": "me_test@jewelmind.com",
            "full_name": "Me Tester",
            "password": "Password12345!",
        },
    )
    token = reg_res.json()["access_token"]

    # Call /me with Bearer token
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "me_test@jewelmind.com"
    assert data["full_name"] == "Me Tester"
    assert "id" in data


def test_get_current_user_me_unauthenticated(client: TestClient):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    data = response.json()
    assert data["error"]["code"] == "NOT_AUTHENTICATED"


def test_get_current_user_me_invalid_token(client: TestClient):
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid.token.payload"},
    )
    assert response.status_code == 401
    data = response.json()
    assert data["error"]["code"] == "INVALID_TOKEN"


def test_logout_endpoint(client: TestClient):
    response = client.post("/api/v1/auth/logout")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "discarded" in data["message"].lower()
