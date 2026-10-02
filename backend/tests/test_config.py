"""
Tests for settings configuration and environment parsing
"""

from app.core.config import Settings


def test_default_settings():
    settings = Settings()
    assert settings.PROJECT_NAME == "JewelMind API"
    assert settings.API_V1_STR == "/api/v1"
    assert "http://localhost:5173" in settings.CORS_ORIGINS


def test_cors_comma_separated_parsing():
    settings = Settings(CORS_ORIGINS="http://localhost:5173, https://jewelmind.com")
    assert isinstance(settings.CORS_ORIGINS, list)
    assert len(settings.CORS_ORIGINS) == 2
    assert "https://jewelmind.com" in settings.CORS_ORIGINS


def test_jwt_secret_and_environment_aliases(monkeypatch):
    # Test setting via JWT_SECRET and ENVIRONMENT aliases
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    settings = Settings(
        ENVIRONMENT="testing",
        JWT_SECRET="custom-secret-key-32-chars-long-abc",
        _env_file=None,
    )
    assert settings.APP_ENV == "testing"
    assert settings.JWT_SECRET_KEY == "custom-secret-key-32-chars-long-abc"


def test_production_jwt_secret_validation():
    import pytest
    from pydantic import ValidationError

    # Default dev secret in production must fail safely
    with pytest.raises(ValidationError):
        Settings(APP_ENV="production", JWT_SECRET_KEY="jewelmind-super-secret-jwt-key-minimum-32-chars-for-dev")

    # Short secret in production must fail safely
    with pytest.raises(ValidationError):
        Settings(APP_ENV="production", JWT_SECRET_KEY="short-secret")

    # Valid secret in production passes
    prod_settings = Settings(
        APP_ENV="production",
        JWT_SECRET_KEY="a-secure-production-secret-key-that-is-over-32-characters",
    )
    assert prod_settings.APP_ENV == "production"
    assert prod_settings.JWT_SECRET_KEY == "a-secure-production-secret-key-that-is-over-32-characters"

