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
