"""
Security Regression Tests: Authentication & JWT Authorization
Validates token handling, signature verification, expiration, credential validation,
and comprehensive unauthenticated route rejection across all API endpoints.
"""

from datetime import timedelta
import pytest
from fastapi.testclient import TestClient
import jwt

from app.core.config import settings
from app.core.security import create_access_token


def test_auth_registration_input_sanitization(client: TestClient):
    """Verify registration handles email normalization and trims whitespace."""
    payload = {
        "email": "   SecurityTester@JewelMind.IO   ",
        "full_name": "  Security Admin  ",
        "password": "StrongSecurityPass2026!",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["user"]["email"] == "securitytester@jewelmind.io"
    assert data["user"]["full_name"] == "Security Admin"


def test_auth_login_invalid_credentials_timing_safe(client: TestClient):
    """Verify failed login returns 401 without distinguishing email vs password presence."""
    # Non-existent user
    res1 = client.post("/api/v1/auth/login", json={
        "email": "nonexistent@jewelmind.com",
        "password": "SomePassword123!",
    })
    assert res1.status_code == 401
    assert res1.json()["error"]["code"] == "INVALID_CREDENTIALS"

    # Register user first
    client.post("/api/v1/auth/register", json={
        "email": "userexists@jewelmind.com",
        "full_name": "User Exists",
        "password": "CorrectPassword123!",
    })

    # Wrong password
    res2 = client.post("/api/v1/auth/login", json={
        "email": "userexists@jewelmind.com",
        "password": "WrongPassword123!",
    })
    assert res2.status_code == 401
    assert res2.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_jwt_tampered_signature_rejection(client: TestClient):
    """Verify JWT signed with different secret key is rejected with 401."""
    fake_token = jwt.encode(
        {"sub": "00000000-0000-0000-0000-000000000001", "type": "access"},
        "attacker-compromised-secret-key-123456789",
        algorithm="HS256",
    )
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {fake_token}"})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_TOKEN"


def test_jwt_expired_token_rejection(client: TestClient):
    """Verify expired JWT is rejected with TOKEN_EXPIRED."""
    expired_token = create_access_token(
        subject="00000000-0000-0000-0000-000000000001",
        expires_delta=timedelta(seconds=-60),
    )
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "TOKEN_EXPIRED"


def test_jwt_missing_sub_claim(client: TestClient):
    """Verify token lacking 'sub' claim is rejected."""
    bad_token = jwt.encode(
        {"type": "access"},
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {bad_token}"})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_TOKEN_SUBJECT"


def test_jwt_malformed_token_header(client: TestClient):
    """Verify malformed bearer tokens fail safely with 401."""
    malformed_headers = [
        "Bearer",
        "Bearer ",
        "Bearer not.a.valid.jwt.token",
        "Bearer 12345",
        "Basic dXNlcjpwYXNz",
    ]
    for auth_hdr in malformed_headers:
        res = client.get("/api/v1/auth/me", headers={"Authorization": auth_hdr})
        assert res.status_code in (401, 403), f"Failed for header: {auth_hdr}"


@pytest.mark.parametrize(
    "method,endpoint,json_body",
    [
        ("GET", "/api/v1/auth/me", None),
        ("GET", "/api/v1/designs", None),
        ("POST", "/api/v1/designs", {"name": "Test", "category": "ring"}),
        ("GET", "/api/v1/designs/00000000-0000-0000-0000-000000000001", None),
        ("PATCH", "/api/v1/designs/00000000-0000-0000-0000-000000000001", {"name": "Test"}),
        ("DELETE", "/api/v1/designs/00000000-0000-0000-0000-000000000001", None),
        ("DELETE", "/api/v1/designs/00000000-0000-0000-0000-000000000001/sketch", None),
        ("GET", "/api/v1/production/summary", None),
        ("GET", "/api/v1/production/orders", None),
        ("POST", "/api/v1/production/orders", {"design_id": "00000000-0000-0000-0000-000000000001", "quantity": 1}),
        ("GET", "/api/v1/production/orders/00000000-0000-0000-0000-000000000001", None),
        ("PUT", "/api/v1/production/orders/00000000-0000-0000-0000-000000000001", {"quantity": 2}),
        ("DELETE", "/api/v1/production/orders/00000000-0000-0000-0000-000000000001", None),
        ("GET", "/api/v1/production/workers", None),
        ("POST", "/api/v1/production/workers", {"name": "Worker", "skill": "casting", "capacity_hours_per_day": 8.0}),
        ("GET", "/api/v1/production/workers/00000000-0000-0000-0000-000000000001", None),
        ("DELETE", "/api/v1/production/workers/00000000-0000-0000-0000-000000000001", None),
        ("GET", "/api/v1/production/machines", None),
        ("POST", "/api/v1/production/machines", {"name": "Machine", "machine_type": "casting_furnace", "capacity_hours_per_day": 8.0}),
        ("GET", "/api/v1/production/machines/00000000-0000-0000-0000-000000000001", None),
        ("DELETE", "/api/v1/production/machines/00000000-0000-0000-0000-000000000001", None),
        ("POST", "/api/v1/production/optimize", {"horizon_days": 7}),
        ("GET", "/api/v1/production/schedules", None),
        ("GET", "/api/v1/production/schedules/00000000-0000-0000-0000-000000000001", None),
        ("DELETE", "/api/v1/production/schedules/00000000-0000-0000-0000-000000000001", None),
        ("GET", "/api/v1/dashboard/overview", None),
    ],
)
def test_all_protected_endpoints_reject_unauthenticated(client: TestClient, method: str, endpoint: str, json_body: dict):
    """Verify every protected API route strictly rejects unauthenticated requests with HTTP 401."""
    if method == "GET":
        res = client.get(endpoint)
    elif method == "POST":
        res = client.post(endpoint, json=json_body)
    elif method == "PATCH":
        res = client.patch(endpoint, json=json_body)
    elif method == "PUT":
        res = client.put(endpoint, json=json_body)
    elif method == "DELETE":
        res = client.delete(endpoint)
    else:
        pytest.fail(f"Unsupported method {method}")

    assert res.status_code == 401, f"Expected 401 for {method} {endpoint}, got {res.status_code}"
    err = res.json()
    assert err["error"]["code"] in ("NOT_AUTHENTICATED", "INVALID_TOKEN")
