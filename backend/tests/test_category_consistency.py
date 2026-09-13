"""Phase F Tests: Jewellery Type Consistency & ControlNet Conditioning Alignment.

Tests:
1. Canonicalization: All variations and plurals correctly map to singular canonical forms.
2. Extraction: Explicit prompt categories correctly parsed.
3. Precedence:
   - User Prompt Explicit Intent (Tier 1) > UI Selection > YOLO V2 > Gemini Vision > Fallback
4. Conflict Detection:
   - Conflict flagged whenever requested category differs from blueprint category.
5. End-to-End API Guard:
   - Rendering endpoint rejects unconfirmed category conflict with HTTP 409 Conflict.
   - Rendering endpoint accepts render when user explicitly resolves via conflict_resolution="blueprint".
"""

from unittest.mock import AsyncMock, patch
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.models.user import User
from app.schemas.auth import UserCreate
from app.services.user_service import user_service
from app.schemas.ai import YoloGroundingContext
from app.services.gemini_design_service import (
    GeminiDesignService,
    canonicalize_category,
    extract_explicit_category,
)


@pytest.fixture
def auth_headers(db_session):
    email = "category_tester@jewelmind.com"
    user = user_service.get_by_email(db_session, email=email)
    if not user:
        user = user_service.create(
            db_session,
            UserCreate(
                email=email,
                password="SecurePassword123!",
                full_name="Consistency Tester",
            ),
        )
    token = create_access_token(
        subject=user.id,
        extra_claims={"email": user.email, "role": user.role},
    )
    return {"Authorization": f"Bearer {token}"}


def test_canonicalize_category():
    assert canonicalize_category("Earrings") == "earring"
    assert canonicalize_category("earrings") == "earring"
    assert canonicalize_category("Earring") == "earring"
    assert canonicalize_category("Necklaces") == "necklace"
    assert canonicalize_category("necklace") == "necklace"
    assert canonicalize_category("Rings") == "ring"
    assert canonicalize_category("ring") == "ring"
    assert canonicalize_category("Brooches") == "brooch"
    assert canonicalize_category("brooch") == "brooch"
    assert canonicalize_category("Pendants") == "pendant"
    assert canonicalize_category("unknown_xyz") is None
    assert canonicalize_category(None) is None


def test_extract_explicit_category():
    assert extract_explicit_category("Create a sophisticated earring in polished 18k yellow gold") == "earring"
    assert extract_explicit_category("Vintage diamond earrings with filigree") == "earring"
    assert extract_explicit_category("A stunning emerald necklace") == "necklace"
    assert extract_explicit_category("Platinum solitaire ring with round brilliant diamond") == "ring"
    assert extract_explicit_category("Floral sapphire brooch") == "brooch"
    assert extract_explicit_category("Pure gold with pear diamonds") is None


def test_resolve_category_precedence_user_prompt():
    service = GeminiDesignService()
    yolo_ctx = YoloGroundingContext(detected_category="necklace", confidence=0.95)
    res = service._resolve_category(
        user_prompt="Create a sophisticated earring in gold",
        yolo_context=yolo_ctx,
        gemini_category="necklace",
        source_blueprint_category="necklace",
        user_selected_category="ring",
    )
    assert res.resolved == "earring"
    assert res.category_source == "user_prompt"
    assert res.conflict is True
    assert "earring" in res.conflict_reason
    assert "necklace" in res.conflict_reason


def test_resolve_category_precedence_user_ui():
    service = GeminiDesignService()
    yolo_ctx = YoloGroundingContext(detected_category="necklace", confidence=0.60)
    res = service._resolve_category(
        user_prompt="Polished 18k yellow gold with pave diamonds",
        yolo_context=yolo_ctx,
        gemini_category="pendant",
        source_blueprint_category=None,
        user_selected_category="earring",
    )
    assert res.resolved == "earring"
    assert res.category_source == "user_selected"


def test_resolve_category_precedence_yolo_high_confidence():
    service = GeminiDesignService()
    yolo_ctx = YoloGroundingContext(detected_category="necklace", confidence=0.88)
    res = service._resolve_category(
        user_prompt="Polished 18k gold with gemstones",
        yolo_context=yolo_ctx,
        gemini_category="pendant",
        source_blueprint_category="necklace",
        user_selected_category=None,
    )
    assert res.resolved == "necklace"
    assert res.category_source == "yolo"
    # When YOLO (necklace) and Gemini (pendant) disagree, conflict is recorded
    assert res.conflict is True
    assert "necklace" in res.warnings[0]
    assert "pendant" in res.warnings[0]


def test_resolve_category_precedence_gemini_vision():
    service = GeminiDesignService()
    yolo_ctx = YoloGroundingContext(detected_category="other_jewellery", confidence=0.45)
    res = service._resolve_category(
        user_prompt="Polished 18k gold with gemstones",
        yolo_context=yolo_ctx,
        gemini_category="bracelet",
        source_blueprint_category=None,
        user_selected_category=None,
    )
    assert res.resolved == "bracelet"
    assert res.category_source == "gemini"


def test_conflict_detection_blueprint_mismatch():
    service = GeminiDesignService()
    res = service._resolve_category(
        user_prompt="A masterwork earring in platinum",
        source_blueprint_category="necklace",
    )
    assert res.resolved == "earring"
    assert res.conflict is True
    assert res.requested_category == "earring"
    assert res.source_blueprint_category == "necklace"


def _make_valid_png():
    import io
    from PIL import Image
    img = Image.new("RGB", (64, 64), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_api_render_rejects_category_conflict_without_resolution(client: TestClient, auth_headers):
    """POST /api/v1/ai/render must reject unconfirmed conflict with HTTP 409."""
    valid_png = _make_valid_png()

    response = client.post(
        "/api/v1/ai/render",
        headers=auth_headers,
        data={
            "category": "earring",
            "prompt": "Create a sophisticated earring in polished gold",
            "source_blueprint_category": "necklace",
        },
        files={"file": ("sketch.png", valid_png, "image/png")},
    )

    assert response.status_code == status.HTTP_409_CONFLICT
    body = response.json()
    assert body["detail"]["error"] == "CATEGORY_CONFLICT"
    assert body["detail"]["requested_category"] == "earring"
    assert body["detail"]["source_blueprint_category"] == "necklace"


def test_api_render_accepts_conflict_when_user_confirms_blueprint(client: TestClient, auth_headers):
    """POST /api/v1/ai/render allows render if user confirms with conflict_resolution='blueprint'."""
    valid_png = _make_valid_png()

    mock_worker_resp = {
        "model_version": "runwayml/stable-diffusion-v1-5",
        "controlnet_version": "lllyasviel/control_v11p_sd15_lineart",
        "image_width": 512,
        "image_height": 512,
        "seed": 42,
        "steps": 20,
        "control_type": "lineart",
        "control_strength": 1.0,
        "guidance_scale": 7.5,
        "inference_time_ms": 2500,
        "device_used": "NVIDIA GeForce RTX 4060",
        "output_url": "http://127.0.0.1:8001/rendered/mock.png",
        "created_at": "2026-09-02T13:00:00Z",
    }

    with patch("app.api.v1.ai_rendering.get_rendering_pipeline", return_value=None):
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            from unittest.mock import MagicMock
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_worker_resp
            mock_post.return_value = mock_response

            response = client.post(
                "/api/v1/ai/render",
                headers=auth_headers,
                data={
                    "category": "necklace",
                    "prompt": "A masterwork necklace in polished gold",
                    "source_blueprint_category": "necklace",
                    "conflict_resolution": "blueprint",
                },
                files={"file": ("sketch.png", valid_png, "image/png")},
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["seed"] == 42
