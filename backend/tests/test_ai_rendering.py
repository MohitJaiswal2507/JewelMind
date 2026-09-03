"""Tests for AI Generative Jewellery Rendering API Endpoints.

POST /api/v1/ai/render
GET  /api/v1/ai/render/outputs/{filename}
"""

import io
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.api.deps import get_current_active_user
from app.main import app
from app.models.user import User


@pytest.fixture
def mock_user():
    return User(
        id="test-user-ai-002",
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


def create_mock_png_bytes(width=64, height=64):
    """Create minimal valid PNG image in bytes using PIL."""
    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_render_unauthorized(unauth_client):
    """Ensure unauthenticated requests are rejected with 401."""
    png_bytes = create_mock_png_bytes()
    response = unauth_client.post(
        "/api/v1/ai/render",
        files={"file": ("sketch.png", io.BytesIO(png_bytes), "image/png")},
    )
    assert response.status_code == 401


def test_render_invalid_mime_type(auth_client):
    """Ensure unsupported file formats return 422."""
    response = auth_client.post(
        "/api/v1/ai/render",
        files={"file": ("cad.dxf", io.BytesIO(b"0\nSECTION\n"), "application/dxf")},
    )
    assert response.status_code == 422
    assert "Unsupported file type" in response.json()["detail"]


def test_render_empty_file(auth_client):
    """Ensure zero-byte uploads return 400."""
    response = auth_client.post(
        "/api/v1/ai/render",
        files={"file": ("empty.png", io.BytesIO(b""), "image/png")},
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_render_invalid_resolution(auth_client):
    """Ensure non-multiples of 8 return 422."""
    png_bytes = create_mock_png_bytes()
    response = auth_client.post(
        "/api/v1/ai/render",
        files={"file": ("sketch.png", io.BytesIO(png_bytes), "image/png")},
        data={"width": "515", "height": "512"},
    )
    assert response.status_code == 422
    assert "divisible by 8" in response.json()["detail"]


@patch("app.api.v1.ai_rendering.get_rendering_pipeline")
def test_render_success_mock(mock_get_pipeline, auth_client):
    """Ensure valid render request invokes pipeline and returns structured RenderResult."""
    mock_pipeline = MagicMock()
    mock_result = {
        "model_version": "runwayml/stable-diffusion-v1-5",
        "controlnet_version": "lllyasviel/control_v11p_sd15_lineart",
        "image_width": 512,
        "image_height": 512,
        "seed": 42,
        "control_type": "lineart",
        "control_strength": 1.0,
        "steps": 20,
        "guidance_scale": 7.5,
        "inference_time_ms": 3210.5,
        "device_used": "cuda:0",
        "output_url": "/api/v1/ai/render/outputs/render_test_42.png",
        "created_at": "2026-09-02T13:00:00Z",
    }
    mock_pipeline.render.return_value = (Image.new("RGB", (512, 512)), mock_result)
    mock_get_pipeline.return_value = mock_pipeline

    png_bytes = create_mock_png_bytes()
    response = auth_client.post(
        "/api/v1/ai/render",
        files={"file": ("ring_sketch.png", io.BytesIO(png_bytes), "image/png")},
        data={
            "category": "ring",
            "material": "18k yellow gold",
            "gemstone": "round brilliant diamond",
            "control_type": "lineart",
            "steps": "20",
            "seed": "42",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["model_version"] == "runwayml/stable-diffusion-v1-5"
    assert data["control_strength"] == 1.0
    assert data["seed"] == 42
    assert data["output_url"].startswith("/api/v1/ai/render/outputs/")
    # Ensure default control_strength of 1.0 is passed to pipeline request
    call_req = mock_pipeline.render.call_args.kwargs["request"]
    assert call_req.control_strength == 1.0
    # Ensure no local filesystem paths are leaked
    assert "C:\\" not in str(data)
    assert "/Users/" not in str(data)


def test_render_invalid_category_rejected(auth_client):
    """Ensure unsupported category returns 422."""
    png_bytes = create_mock_png_bytes()
    response = auth_client.post(
        "/api/v1/ai/render",
        files={"file": ("sketch.png", io.BytesIO(png_bytes), "image/png")},
        data={"category": "invalid_jewellery_type"},
    )
    assert response.status_code == 422
    assert "Invalid render parameters" in response.json()["detail"]
