"""Tests for AI Jewellery Component Detection Endpoint:

POST /api/v1/ai/components/detect
"""

import io
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_active_user
from app.main import app
from app.models.user import User


@pytest.fixture
def mock_user():
    return User(
        id="test-user-ai-001",
        email="artisan@jewelmind.com",
        full_name="Artisan Jeweller",
        is_active=True,
        hashed_password="hash",
    )


@pytest.fixture
def auth_client(mock_user):
    app.dependency_overrides[get_current_active_user] = lambda: mock_user
    client = TestClient(app)
    yield client
    app.dependency_overrides.pop(get_current_active_user, None)


@pytest.fixture
def unauth_client():
    return TestClient(app)


def create_mock_png_bytes():
    """Create minimal valid 64x64 PNG image in bytes."""
    import cv2
    import numpy as np
    img = np.full((64, 64, 3), 240, dtype=np.uint8)
    cv2.circle(img, (32, 32), 20, (30, 30, 30), 2)
    success, encoded = cv2.imencode(".png", img)
    return encoded.tobytes()


def test_detect_unauthorized(unauth_client):
    """Ensure unauthenticated requests are rejected with 401."""
    png_bytes = create_mock_png_bytes()
    response = unauth_client.post(
        "/api/v1/ai/components/detect",
        files={"file": ("sketch.png", io.BytesIO(png_bytes), "image/png")},
    )
    assert response.status_code == 401


def test_detect_invalid_file_type(auth_client):
    """Ensure invalid MIME types (e.g. text/plain, pdf) return 422."""
    response = auth_client.post(
        "/api/v1/ai/components/detect",
        files={"file": ("notes.txt", io.BytesIO(b"ring description"), "text/plain")},
    )
    assert response.status_code == 422
    assert "Unsupported file type" in response.json()["detail"]


def test_detect_empty_file(auth_client):
    """Ensure zero-byte uploads return 400 Bad Request."""
    response = auth_client.post(
        "/api/v1/ai/components/detect",
        files={"file": ("empty.png", io.BytesIO(b""), "image/png")},
    )
    assert response.status_code == 400


def test_detect_success(auth_client):
    """Ensure valid image upload returns structured detection results."""
    png_bytes = create_mock_png_bytes()
    response = auth_client.post(
        "/api/v1/ai/components/detect?conf=0.20",
        files={"file": ("ring_blueprint.png", io.BytesIO(png_bytes), "image/png")},
    )
    assert response.status_code == 200
    data = response.json()

    assert "model_version" in data
    assert "image_size" in data
    assert "inference_time_ms" in data
    assert "detections" in data
    assert "total_detections" in data
    assert isinstance(data["detections"], list)
