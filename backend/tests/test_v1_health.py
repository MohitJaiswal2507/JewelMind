"""
Tests for Versioned API V1 Health endpoints
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_v1_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "JewelMind API"
    assert "version" in data
    assert "environment" in data
    assert "database_configured" in data


def test_request_id_header_injected():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert "X-Process-Time-Ms" in response.headers
