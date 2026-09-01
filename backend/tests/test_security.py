"""
Tests for security utilities (bcrypt password hashing and JWT token handling)
"""

from datetime import timedelta
import pytest
from app.core.exceptions import AppException
from app.core.security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)


def test_password_hashing_and_verification():
    password = "SuperSecretPassword123!"
    hashed = get_password_hash(password)
    
    assert hashed != password
    assert hashed.startswith("$2b$") or hashed.startswith("$2a$")
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword123!", hashed) is False


def test_jwt_creation_and_decoding():
    user_id = "e0a2936a-2d4e-4b47-bcfc-63b7bca06121"
    token = create_access_token(
        subject=user_id,
        extra_claims={"email": "designer@jewelmind.com", "role": "artisan"},
    )
    
    payload = decode_access_token(token)
    assert payload["sub"] == user_id
    assert payload["email"] == "designer@jewelmind.com"
    assert payload["role"] == "artisan"
    assert payload["type"] == "access"
    assert "exp" in payload


def test_jwt_expired_token():
    user_id = "e0a2936a-2d4e-4b47-bcfc-63b7bca06121"
    # Create token expired 5 minutes ago
    token = create_access_token(
        subject=user_id,
        expires_delta=timedelta(minutes=-5),
    )
    
    with pytest.raises(AppException) as exc_info:
        decode_access_token(token)
    assert exc_info.value.code == "TOKEN_EXPIRED"
    assert exc_info.value.status_code == 401


def test_jwt_invalid_token():
    with pytest.raises(AppException) as exc_info:
        decode_access_token("not.a.valid.jwt.token")
    assert exc_info.value.code == "INVALID_TOKEN"
    assert exc_info.value.status_code == 401
