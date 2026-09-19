"""Comprehensive Test Suite for Gemini Design Understanding & Prompt Compilation.

Tests cover:
1. GEMINI_MODEL configurability and absence of hard-coded obsolete models
2. Structured design understanding richness (no artificial 65-token restriction)
3. Renderer prompt compilation and Tier-1 user intent preservation
4. Negative prompt compilation
5. YOLO V2 category grounding & conflict representation
6. Case A: Text-only prompt fallback when Gemini is unavailable
7. Case B: Image/sketch fallback when Gemini is unavailable (no visual claim, no fabricated attributes)
8. Mocked Gemini Vision API calls (success, error handling)
9. FastAPI endpoints integration (/api/v1/ai/gemini/analyze-design and /enhance-prompt)
"""

import asyncio
import json
import re
from unittest.mock import AsyncMock, patch
import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token
from app.models.user import User
from app.schemas.auth import UserCreate
from app.services.user_service import user_service
from app.schemas.ai import (
    AnalyzeDesignRequest,
    AnalyzeDesignResponse,
    DesignState,
    EnhancePromptRequest,
    EnhancePromptResponse,
    GemstoneItem,
    GemstoneSpec,
    JewelleryCategory,
    MaterialSpec,
    StructuralSpec,
    StructuredDesignUnderstanding,
    YoloGroundingContext,
)
from app.services.gemini_design_service import GeminiDesignService, get_gemini_design_service
from app.services.jewellery_prompt_compiler import JewelleryPromptCompiler, JEWELLERY_NEGATIVE_PROMPT


def create_test_user(db: Session, email: str = "gemini_tester@jewelmind.com") -> User:
    """Helper to create a test user."""
    return user_service.create(
        db,
        UserCreate(
            email=email,
            password="SecurePassword123!",
            full_name="Gemini Artisan Tester",
        ),
    )


def get_auth_headers(user: User) -> dict:
    """Helper to generate JWT Bearer headers for a user."""
    token = create_access_token(
        subject=user.id,
        extra_claims={"email": user.email, "role": user.role},
    )
    return {"Authorization": f"Bearer {token}"}


# ------------------------------------------------------------------------------
# 1. Model Configuration Tests
# ------------------------------------------------------------------------------

def test_gemini_model_is_configurable():
    """Verify GEMINI_MODEL is environment-driven and can be configured without hardcoding."""
    # Test custom model via constructor
    custom_service = GeminiDesignService(api_key="test-key", model_name="gemini-2.5-pro")
    assert custom_service.model_name == "gemini-2.5-pro"

    # Test modern default from settings
    default_service = GeminiDesignService(api_key="test-key")
    assert default_service.model_name == settings.GEMINI_MODEL
    # Verify it does not hardcode an obsolete model
    assert default_service.model_name != "gemini-1.0-pro"

    # Verify custom model is used in the URL constructed for API call
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_payload = {
            "candidates": [{
                "content": {"parts": [{"text": json.dumps({
                    "jewellery_category": "ring",
                    "category_confidence": 0.95,
                    "design_summary": "Test ring",
                    "material": {"primary_metal": "platinum", "finish": "polished"},
                    "gemstones": {"has_gemstones": False},
                    "structure": {"band_or_body_structure": "band"},
                    "design_motifs": [],
                    "user_intent_preserved": True,
                    "user_constraints_applied": [],
                })}]}
            }]
        }
        mock_post.return_value = httpx.Response(200, json=mock_payload)
        asyncio.run(custom_service._call_gemini_api("test prompt"))
        called_url = mock_post.call_args[0][0]
        assert "gemini-2.5-pro:generateContent" in called_url


# ------------------------------------------------------------------------------
# 2. Rich Structured Understanding (No 65-Token Restriction)
# ------------------------------------------------------------------------------

def test_structured_design_understanding_unconstrained_richness():
    """Verify StructuredDesignUnderstanding holds deep, rich semantic attributes
    without being artificially truncated or restricted to a 65-token ceiling.
    """
    rich_summary = (
        "An opulent Edwardian-inspired masterwork high-jewellery ring featuring an intricately "
        "pierced under-gallery, double French-set pavé shoulders, delicate milgrain bordering along "
        "the cathedral arches, and a prominent cushion-cut royal blue sapphire haloed by brilliant diamonds."
    )
    rich_decorative = [
        "Edwardian openwork filigree under-gallery",
        "Hand-applied triple milgrain borders along outer shank rims",
        "Engraved chevron feathering along interior comfort-fit band",
        "French pavé bead setting across split shoulders",
    ]
    secondary_gems = [
        GemstoneItem(gemstone_type="diamond", cut="round brilliant", estimated_count=18, setting_type="French pavé"),
        GemstoneItem(gemstone_type="diamond", cut="trapezoid", estimated_count=2, setting_type="channel setting"),
        GemstoneItem(gemstone_type="diamond", cut="tapered baguette", estimated_count=4, setting_type="bar setting"),
    ]

    design = StructuredDesignUnderstanding(
        jewellery_category="ring",
        category_confidence=0.99,
        design_summary=rich_summary,
        material=MaterialSpec(primary_metal="950 platinum", finish="mirror polish", accent_metal="18k yellow gold filigree"),
        gemstones=GemstoneSpec(
            has_gemstones=True,
            primary_gemstone=GemstoneItem(gemstone_type="royal blue sapphire", cut="cushion", estimated_count=1, setting_type="double-prong basket"),
            secondary_gemstones=secondary_gems,
            gemstone_details="Center cushion sapphire flanked by trapezoids with dual French-set pavé diamond halos",
        ),
        structure=StructuralSpec(
            silhouette="architectural cathedral dome",
            symmetry="bilateral symmetry",
            setting_style="elevated cathedral basket with filigree gallery",
            stone_arrangement="halo cluster with side accents",
            band_or_body_structure="split-shank tapering to solid comfort-fit base",
            decorative_elements=rich_decorative,
            edge_details="knife-edge shoulder transition",
            surface_details="openwork gallery scrollwork",
        ),
        design_motifs=["Edwardian Revival", "Cathedral Solitaire", "Artisan Filigree"],
        user_intent_preserved=True,
        user_constraints_applied=["metal: 950 platinum", "gemstone: royal blue sapphire"],
    )

    # Validate that all rich attributes are preserved without schema truncation
    assert len(design.gemstones.secondary_gemstones) == 3
    assert len(design.structure.decorative_elements) == 4
    assert len(design.design_summary.split()) > 30  # Substantial rich text

    # Verify that the prompt compiler successfully converts this rich representation into a concise renderer prompt
    compiled_prompt = JewelleryPromptCompiler.compile_renderer_prompt(design)
    assert "platinum" in compiled_prompt.lower()
    assert "sapphire" in compiled_prompt.lower()
    assert "studio lighting" in compiled_prompt.lower()


# ------------------------------------------------------------------------------
# 3. User Intent Preservation & Prompt Compiler Tests
# ------------------------------------------------------------------------------

def test_user_intent_preservation_rule():
    """Test the mandatory rule: 'platinum round brilliant diamond thin shank'
    must retain platinum, diamond, and thin shank, and NOT output gold, emerald, or thick shank.
    """
    design = StructuredDesignUnderstanding(
        jewellery_category="ring",
        design_summary="A bespoke platinum solitaire ring.",
        material=MaterialSpec(primary_metal="platinum", finish="polished"),
        gemstones=GemstoneSpec(
            has_gemstones=True,
            primary_gemstone=GemstoneItem(
                gemstone_type="round brilliant diamond",
                cut="round brilliant",
                estimated_count=1,
                setting_type="prong setting",
            ),
        ),
        structure=StructuralSpec(
            band_or_body_structure="thin shank",
            setting_style="prong setting",
        ),
        user_constraints_applied=["metal: platinum", "gemstone: diamond", "structure: thin shank"],
    )

    compiled_prompt = JewelleryPromptCompiler.compile_renderer_prompt(
        design=design,
        user_constraints=["metal: platinum", "gemstone: diamond", "structure: thin shank"],
    )

    lower_prompt = compiled_prompt.lower()

    # Must contain explicit user requirements
    assert "platinum" in lower_prompt
    assert "diamond" in lower_prompt
    assert "thin shank" in lower_prompt

    # Must NOT produce conflicting attributes
    assert "gold" not in lower_prompt
    assert "emerald" not in lower_prompt
    assert "thick shank" not in lower_prompt


def test_prompt_compiler_multi_category():
    """Test prompt compiler generates tailored prompts for necklace, earring, and bracelet."""
    for cat in ["necklace", "earring", "bracelet"]:
        design = StructuredDesignUnderstanding(
            jewellery_category=cat,
            design_summary=f"Artisan handcrafted {cat}.",
            material=MaterialSpec(primary_metal="18k yellow gold", finish="satin"),
            gemstones=GemstoneSpec(
                has_gemstones=True,
                primary_gemstone=GemstoneItem(
                    gemstone_type="emerald",
                    cut="cushion",
                    estimated_count=1,
                    setting_type="bezel setting",
                ),
            ),
            structure=StructuralSpec(
                band_or_body_structure=f"{cat} chain",
                setting_style="flush bezel",
            ),
        )
        prompt = JewelleryPromptCompiler.compile_renderer_prompt(design)
        assert cat in prompt.lower()
        assert "18k yellow gold" in prompt.lower()
        assert "emerald" in prompt.lower()
        assert "studio lighting" in prompt.lower()


def test_negative_prompt_compiler():
    """Verify negative prompt includes jewellery artifact suppressors."""
    neg = JewelleryPromptCompiler.compile_negative_prompt("oversaturated")
    assert "malformed jewellery" in neg
    assert "missing gemstones" in neg
    assert "oversaturated" in neg


# ------------------------------------------------------------------------------
# 4. YOLO V2 Grounding & Category Conflict Representation
# ------------------------------------------------------------------------------

def test_category_conflict_resolution():
    """Verify category conflict between YOLO V2 and Gemini is correctly flagged and resolved."""
    service = GeminiDesignService(api_key="mock-key")

    # Scenario 1: YOLO = necklace (conf: 0.92), Gemini = bracelet
    yolo_ctx = YoloGroundingContext(detected_category="necklace", confidence=0.92)
    resolved, conflict, warnings = service._resolve_category(
        gemini_category="bracelet",
        yolo_context=yolo_ctx,
        user_prompt=None,
    )
    assert conflict is True
    assert resolved == "necklace"  # High-confidence YOLO takes precedence
    assert any("Category conflict detected" in w for w in warnings)

    # Scenario 2: YOLO = necklace (conf: 0.40 - low), Gemini = bracelet
    low_yolo_ctx = YoloGroundingContext(detected_category="necklace", confidence=0.40)
    resolved2, conflict2, warnings2 = service._resolve_category(
        gemini_category="bracelet",
        yolo_context=low_yolo_ctx,
        user_prompt=None,
    )
    assert conflict2 is True
    assert resolved2 == "bracelet"  # Low-confidence YOLO falls back to Gemini Vision

    # Scenario 3: User explicitly wrote 'ring' in prompt
    resolved3, conflict3, _ = service._resolve_category(
        gemini_category="pendant",
        yolo_context=yolo_ctx,
        user_prompt="I want a custom engagement ring with diamonds",
    )
    assert resolved3 == "ring"  # User explicit intent has absolute priority


# ------------------------------------------------------------------------------
# 5. Case A & Case B Fallback Semantics
# ------------------------------------------------------------------------------

def test_case_a_text_only_fallback():
    """CASE A: User prompt only + Gemini unavailable.
    Deterministic heuristic text fallback should operate cleanly from the user prompt text.
    """
    service = GeminiDesignService(api_key=None)
    assert service.is_available() is False

    resp = asyncio.run(
        service.analyze_design(
            image_bytes=None,  # No image
            user_prompt="18k yellow gold solitaire ring with round diamond and thin shank",
            yolo_context=YoloGroundingContext(detected_category="ring", confidence=0.95),
        )
    )

    assert resp.success is True
    assert resp.fallback_applied is True
    assert resp.gemini_category is None  # Does NOT claim Gemini categorized it
    assert resp.resolved_category == "ring"
    assert "yellow gold" in resp.renderer_prompt.lower()
    assert "diamond" in resp.renderer_prompt.lower()
    assert "thin shank" in resp.renderer_prompt.lower()
    assert any("text-derived" in w.lower() for w in resp.warnings)


def test_case_b_image_unavailable_fallback():
    """CASE B: Image/sketch + Gemini unavailable.
    Must NOT claim to visually understand the image.
    Must NOT fabricate visual attributes from the image using regex.
    Must preserve baseline information for rendering continuity.
    """
    service = GeminiDesignService(api_key=None)
    assert service.is_available() is False

    # Image provided WITHOUT user prompt
    resp = asyncio.run(
        service.analyze_design(
            image_bytes=b"fake-image-bytes-sketch",
            user_prompt=None,
            yolo_context=YoloGroundingContext(detected_category="pendant", confidence=0.88),
        )
    )

    assert resp.success is True
    assert resp.fallback_applied is True
    assert resp.gemini_category is None  # Explicitly None: visual analysis was not performed
    assert resp.resolved_category == "pendant"  # Grounded on YOLO context
    assert resp.design_understanding.gemstones.has_gemstones is False  # Did NOT fabricate stones from image!
    assert "visual feature extraction was not performed" in resp.warnings[0].lower() or "visual analysis unavailable" in resp.warnings[0].lower()
    assert "pendant" in resp.renderer_prompt.lower()  # Rendering workflow remains usable


# ------------------------------------------------------------------------------
# 6. Mocked Gemini Vision API Call Tests
# ------------------------------------------------------------------------------

def test_mocked_gemini_vision_success():
    """Verify end-to-end analysis parsing with mocked successful Gemini API response."""
    service = GeminiDesignService(api_key="valid-test-key")

    mock_gemini_json = {
        "jewellery_category": "earring",
        "category_confidence": 0.98,
        "design_summary": "A pair of drop earrings with pear sapphires in white gold.",
        "material": {
            "primary_metal": "18k white gold",
            "finish": "high-polish",
            "accent_metal": None,
        },
        "gemstones": {
            "has_gemstones": True,
            "primary_gemstone": {
                "gemstone_type": "blue sapphire",
                "cut": "pear",
                "estimated_count": 2,
                "setting_type": "prong setting",
            },
            "secondary_gemstones": [],
        },
        "structure": {
            "silhouette": "drop silhouette",
            "symmetry": "bilateral",
            "setting_style": "articulated drop",
            "band_or_body_structure": "drop pendant body",
            "decorative_elements": ["milgrain edge"],
        },
        "design_motifs": ["Art Deco"],
        "user_intent_preserved": True,
        "user_constraints_applied": [],
    }

    with patch.object(service, "_call_gemini_api", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = mock_gemini_json

        resp = asyncio.run(
            service.analyze_design(
                image_bytes=b"fake-earring-bytes",
                user_prompt="drop earrings in white gold with blue sapphires",
                yolo_context=YoloGroundingContext(detected_category="earring", confidence=0.94),
            )
        )

        assert resp.success is True
        assert resp.fallback_applied is False
        assert resp.gemini_category == "earring"
        assert resp.resolved_category == "earring"
        assert "white gold" in resp.renderer_prompt.lower()
        assert "sapphire" in resp.renderer_prompt.lower()
        assert "milgrain" in resp.renderer_prompt.lower()


def test_gemini_error_graceful_fallback():
    """Verify service catches API errors (e.g. rate limit or timeout) and returns controlled fallback."""
    service = GeminiDesignService(api_key="valid-test-key")

    with patch.object(service, "_call_gemini_api", new_callable=AsyncMock) as mock_call:
        mock_call.side_effect = RuntimeError("Gemini free-tier rate limit exceeded.")

        resp = asyncio.run(
            service.analyze_design(
                image_bytes=b"fake-bytes",
                user_prompt="platinum ring with diamonds",
                yolo_context=YoloGroundingContext(detected_category="ring", confidence=0.90),
            )
        )

        assert resp.success is True
        assert resp.fallback_applied is True
        assert resp.gemini_category is None  # None because Gemini failed
        assert resp.resolved_category == "ring"
        assert "platinum" in resp.renderer_prompt.lower()
        assert any("unavailable" in w.lower() or "fallback" in w.lower() for w in resp.warnings)


# ------------------------------------------------------------------------------
# 7. FastAPI Router Endpoint Tests
# ------------------------------------------------------------------------------

def test_fastapi_gemini_endpoints_registered(client: TestClient, db_session: Session):
    """Verify new Gemini endpoints are registered and accessible via FastAPI."""
    user = create_test_user(db_session, "gemini_user_1@jewelmind.com")
    headers = get_auth_headers(user)

    # Test /api/v1/ai/gemini/enhance-prompt
    payload = {
        "user_prompt": "18k yellow gold solitaire ring with round diamond and thin shank",
        "yolo_category": "ring",
        "yolo_confidence": 0.95,
    }

    response = client.post("/api/v1/ai/gemini/enhance-prompt", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["resolved_category"] == "ring"
    assert "yellow gold" in data["renderer_prompt"].lower()
    assert "diamond" in data["renderer_prompt"].lower()
    assert "thin shank" in data["renderer_prompt"].lower()


def test_fastapi_gemini_analyze_multipart(client: TestClient, db_session: Session):
    """Verify /api/v1/ai/gemini/analyze-design endpoint accepts multipart file upload."""
    user = create_test_user(db_session, "gemini_user_2@jewelmind.com")
    headers = get_auth_headers(user)

    files = {
        "file": ("sketch.png", b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82", "image/png"),
    }
    data = {
        "user_prompt": "platinum ring with round brilliant diamond",
        "yolo_category": "ring",
        "yolo_confidence": "0.96",
    }

    response = client.post("/api/v1/ai/gemini/analyze-design", files=files, data=data, headers=headers)
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True
    assert res_data["resolved_category"] == "ring"
    assert "platinum" in res_data["renderer_prompt"].lower()
    assert "diamond" in res_data["renderer_prompt"].lower()


def test_modify_design_state_unit():
    """Verify GeminiDesignService.modify_design_state updates requested attributes and preserves unchanged ones."""
    from app.schemas.ai import DesignState

    service = GeminiDesignService(api_key=None)  # Use fallback
    initial_state = DesignState(
        category="Ring",
        primary_metal="18k yellow gold",
        metal_finish="polished high-shine",
        has_gemstones=True,
        gemstone_type="diamond",
        gemstone_cut="round brilliant",
        setting_type="prong setting",
    )

    # Change metal to rose gold and replace diamond with emerald
    instruction = "Change the metal to 18k rose gold and replace the center diamond with an emerald."
    res = asyncio.run(service.modify_design_state(initial_state, instruction))

    assert res.success is True
    assert res.updated_state.category == "Ring"  # Preserved!
    assert res.updated_state.primary_metal == "18k rose gold"  # Changed!
    assert res.updated_state.gemstone_type == "emerald"  # Changed!
    assert res.updated_state.gemstone_cut == "round brilliant"  # Preserved!
    assert "primary_metal" in res.changes_detected
    assert "gemstone_type" in res.changes_detected
    assert "rose gold" in res.renderer_prompt.lower()
    assert "emerald" in res.renderer_prompt.lower()
    assert res.fallback_applied is True


def test_design_state_defaults_do_not_hallucinate_gold_diamond_or_ring():
    """Verify that unspecified attributes in DesignState and natural language instructions
    never default to or hallucinate 18k yellow gold, diamond, or Ring.
    Tests the 5 mandatory cases from Directive 7:
    1. earring without gemstone
    2. platinum pendant
    3. silver bangle with no gemstone
    4. rose gold necklace
    5. sapphire brooch
    """
    service = GeminiDesignService()

    # Case 1: Earring without gemstone
    state_earring = DesignState(category="Earring")
    res1 = asyncio.run(service.modify_design_state(state_earring, "Earring without gemstone, pure metal design"))
    assert res1.updated_state.category == "Earring"
    assert res1.updated_state.has_gemstones is False
    assert res1.updated_state.gemstone_type is None
    assert "diamond" not in res1.renderer_prompt.lower()
    assert not re.search(r"\bring\b", res1.renderer_prompt.lower())

    # Case 2: Platinum pendant (no gemstone specified)
    state_pendant = DesignState()
    res2 = asyncio.run(service.modify_design_state(state_pendant, "A sculptural platinum pendant"))
    assert res2.updated_state.category == "Pendant"
    assert "platinum" in res2.updated_state.primary_metal.lower()
    assert res2.updated_state.gemstone_type is None
    assert "diamond" not in res2.renderer_prompt.lower()
    assert "gold" not in res2.renderer_prompt.lower()
    assert not re.search(r"\bring\b", res2.renderer_prompt.lower())

    # Case 3: Silver bangle with no gemstone
    state_bangle = DesignState()
    res3 = asyncio.run(service.modify_design_state(state_bangle, "Silver bangle with no gemstone, polished surface"))
    assert res3.updated_state.category == "Bangle"
    assert "silver" in res3.updated_state.primary_metal.lower()
    assert res3.updated_state.has_gemstones is False
    assert res3.updated_state.gemstone_type is None
    assert "diamond" not in res3.renderer_prompt.lower()
    assert "gold" not in res3.renderer_prompt.lower()
    assert not re.search(r"\bring\b", res3.renderer_prompt.lower())

    # Case 4: Rose gold necklace
    state_necklace = DesignState()
    res4 = asyncio.run(service.modify_design_state(state_necklace, "18k rose gold necklace"))
    assert res4.updated_state.category == "Necklace"
    assert "rose gold" in res4.updated_state.primary_metal.lower()
    assert res4.updated_state.gemstone_type is None
    assert "diamond" not in res4.renderer_prompt.lower()
    assert not re.search(r"\bring\b", res4.renderer_prompt.lower())

    # Case 5: Sapphire brooch
    state_brooch = DesignState()
    res5 = asyncio.run(service.modify_design_state(state_brooch, "Vintage brooch featuring a blue sapphire"))
    assert res5.updated_state.category == "Brooch"
    assert res5.updated_state.gemstone_type == "blue sapphire"
    assert "diamond" not in res5.renderer_prompt.lower()
    assert not re.search(r"\bring\b", res5.renderer_prompt.lower())


def test_clean_design_state_isolation_between_designs():
    """Verify Directive 6: Creating Design B after Design A does not leak attributes.
    Design A: Necklace, Gold, Diamond
    Design B: Earring, Platinum, Sapphire
    Verify Design B starts fresh and does not inherit Necklace, Gold, or Diamond.
    """
    service = GeminiDesignService()

    # Design A
    design_a = DesignState()
    res_a = asyncio.run(service.modify_design_state(design_a, "18k yellow gold necklace with solitaire diamond"))
    assert res_a.updated_state.category == "Necklace"
    assert "yellow gold" in res_a.updated_state.primary_metal.lower()
    assert res_a.updated_state.gemstone_type == "diamond"

    # Design B is created afresh (clean state)
    design_b = DesignState()
    res_b = asyncio.run(service.modify_design_state(design_b, "Platinum earring with blue sapphire"))
    assert res_b.updated_state.category == "Earring"
    assert "platinum" in res_b.updated_state.primary_metal.lower()
    assert res_b.updated_state.gemstone_type == "blue sapphire"

    # Ensure ZERO contamination from Design A into Design B
    assert res_b.updated_state.category != "Necklace"
    assert "gold" not in res_b.renderer_prompt.lower()
    assert "diamond" not in res_b.renderer_prompt.lower()
    assert "necklace" not in res_b.renderer_prompt.lower()


def test_fastapi_gemini_modify_design_endpoint(client: TestClient, db_session: Session):
    """Verify /api/v1/ai/gemini/modify-design endpoint accepts current state and applies instructions."""
    user = create_test_user(db_session, "gemini_user_modify@jewelmind.com")
    headers = get_auth_headers(user)

    payload = {
        "current_state": {
            "category": "Pendant",
            "primary_metal": "950 platinum",
            "metal_finish": "polished",
            "has_gemstones": True,
            "gemstone_type": "diamond",
            "gemstone_cut": "pear",
            "setting_type": "bezel setting",
        },
        "user_instruction": "Change metal to 18k yellow gold and stone to blue sapphire",
    }

    response = client.post("/api/v1/ai/gemini/modify-design", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["updated_state"]["category"] == "Pendant"
    assert data["updated_state"]["primary_metal"] == "18k yellow gold"
    assert data["updated_state"]["gemstone_type"] == "blue sapphire"
    assert "yellow gold" in data["renderer_prompt"].lower()
    assert "sapphire" in data["renderer_prompt"].lower()
    assert len(data["changes_detected"]) >= 2


def test_multi_turn_conversational_redesign_chain_modification():
    """Verify Directive 5: Multi-turn iterative conversational redesign.
    Turn 1: Platinum pendant with sapphire (V1)
    Turn 2: "Make the sapphire emerald" (V2)
    Turn 3: "Make the chain thinner" (V3)
    Verify that:
    - pendant remains pendant
    - platinum remains platinum until explicitly changed
    - emerald remains emerald
    - chain modification applies
    - previous design structure is preserved
    - no random unrelated jewellery appears
    """
    service = GeminiDesignService()

    # Turn 1: Initial state
    state_v1 = DesignState()
    res_v1 = asyncio.run(service.modify_design_state(state_v1, "Platinum pendant with sapphire and cable chain"))
    assert res_v1.updated_state.category == "Pendant"
    assert "platinum" in res_v1.updated_state.primary_metal.lower()
    assert res_v1.updated_state.gemstone_type == "sapphire"
    assert "pendant" in res_v1.renderer_prompt.lower()
    assert "platinum" in res_v1.renderer_prompt.lower()
    assert "sapphire" in res_v1.renderer_prompt.lower()

    # Turn 2: "Make the sapphire emerald"
    res_v2 = asyncio.run(service.modify_design_state(res_v1.updated_state, "Make the sapphire emerald"))
    assert res_v2.updated_state.category == "Pendant"  # Preserved!
    assert "platinum" in res_v2.updated_state.primary_metal.lower()  # Preserved!
    assert res_v2.updated_state.gemstone_type == "emerald"  # Changed!
    assert "emerald" in res_v2.renderer_prompt.lower()
    assert "platinum" in res_v2.renderer_prompt.lower()
    assert "sapphire" not in res_v2.renderer_prompt.lower()

    # Turn 3: "Make the chain thinner"
    res_v3 = asyncio.run(service.modify_design_state(res_v2.updated_state, "Make the chain thinner"))
    assert res_v3.updated_state.category == "Pendant"  # Preserved!
    assert "platinum" in res_v3.updated_state.primary_metal.lower()  # Preserved!
    assert res_v3.updated_state.gemstone_type == "emerald"  # Preserved!
    assert "thinner chain" in res_v3.updated_state.engraving_or_details.lower()  # Applied!
    assert "thinner chain" in res_v3.renderer_prompt.lower()
    assert "pendant" in res_v3.renderer_prompt.lower()
    assert "platinum" in res_v3.renderer_prompt.lower()
    assert "emerald" in res_v3.renderer_prompt.lower()
    assert not re.search(r"\bring\b", res_v3.renderer_prompt.lower())



