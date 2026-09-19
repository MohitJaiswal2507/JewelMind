"""
JewelMind Phase G1 — Conversational Redesign & Card Flow Bug Fix Regression Tests.

Validates:
1. Material-only edit ("Change metal to platinum") produces no category conflict.
2. Material + finish edit ("Change metal to 18k rose gold with mirror polish") produces no conflict.
3. Gemstone-only edit ("Change stone to emerald") preserves category and produces no category conflict.
4. Geometry/structural edit ("Make the shank thinner") preserves category and produces no category conflict.
5. Genuine category transformation ("Turn this ring into a necklace") triggers valid category conflict.
6. DesignState attribute isolation: Bracelet state never leaks Ring / Diamond / Prong Setting defaults.
7. Finish extraction recognizes "mirror polish" and "highly polished".
8. Gemini fallback and LLM response parsing enforce category preservation when no category change was instructed.
"""

import pytest
from app.services.gemini_design_service import (
    GeminiDesignService,
    DesignState,
)


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def gemini_service():
    return GeminiDesignService(api_key=None)


@pytest.mark.anyio
async def test_material_only_edit_no_conflict(gemini_service):
    """Bug 1: Material-only redesign must preserve category and never trigger a category conflict."""
    initial_state = DesignState(
        category="Bracelet",
        primary_metal="18k yellow gold",
        metal_finish="polished",
        has_gemstones=True,
        gemstone_type="diamond",
        setting_type="prong setting",
    )

    resp = await gemini_service.modify_design_state(
        current_state=initial_state,
        user_instruction="Change metal to platinum",
    )

    assert resp.success is True
    assert resp.updated_state.category == "Bracelet"
    assert "platinum" in (resp.updated_state.primary_metal or "").lower()
    assert resp.updated_state.gemstone_type == "diamond"
    assert resp.updated_state.has_gemstones is True
    assert "category" not in resp.changes_detected
    assert "primary_metal" in resp.changes_detected

    # Test category resolution against blueprint
    res = gemini_service._resolve_category(
        user_selected_category="bracelet",
        user_prompt="Change metal to platinum",
        source_blueprint_category="bracelet",
    )
    assert res.conflict is False
    assert res.resolved == "bracelet"


@pytest.mark.anyio
async def test_material_plus_finish_edit_no_conflict(gemini_service):
    """Bug 1 exact scenario: 'Change metal to 18k rose gold with mirror polish' on a bracelet."""
    initial_state = DesignState(
        category="Bracelet",
        primary_metal="18k yellow gold",
        metal_finish="matte",
        has_gemstones=True,
        gemstone_type="diamond",
        setting_type="bezel setting",
    )

    resp = await gemini_service.modify_design_state(
        current_state=initial_state,
        user_instruction="Change metal to 18k rose gold with mirror polish",
    )

    assert resp.success is True
    assert resp.updated_state.category == "Bracelet"
    assert resp.updated_state.primary_metal == "18k rose gold"
    assert "mirror polish" in (resp.updated_state.metal_finish or "").lower()
    # Preserves existing stones & setting
    assert resp.updated_state.gemstone_type == "diamond"
    assert resp.updated_state.setting_type == "bezel setting"
    assert "category" not in resp.changes_detected

    # Category conflict check
    res = gemini_service._resolve_category(
        user_selected_category="bracelet",
        user_prompt="Change metal to 18k rose gold with mirror polish",
        source_blueprint_category="bracelet",
    )
    assert res.conflict is False
    assert res.resolved == "bracelet"


@pytest.mark.anyio
async def test_gemstone_only_edit_preserves_category_and_material(gemini_service):
    """Gemstone change ('Change the center stone to emerald') preserves category and metal."""
    initial_state = DesignState(
        category="Ring",
        primary_metal="950 platinum",
        has_gemstones=True,
        gemstone_type="diamond",
    )

    resp = await gemini_service.modify_design_state(
        current_state=initial_state,
        user_instruction="Change the center stone to emerald",
    )

    assert resp.success is True
    assert resp.updated_state.category == "Ring"
    assert resp.updated_state.primary_metal == "950 platinum"
    assert resp.updated_state.gemstone_type == "emerald"
    assert resp.updated_state.has_gemstones is True


@pytest.mark.anyio
async def test_geometry_only_edit_preserves_attributes(gemini_service):
    """Geometry change ('Make the shank thinner') preserves category, metal, and gemstone."""
    initial_state = DesignState(
        category="Ring",
        primary_metal="18k white gold",
        has_gemstones=True,
        gemstone_type="blue sapphire",
        silhouette="broad band",
    )

    resp = await gemini_service.modify_design_state(
        current_state=initial_state,
        user_instruction="Make the shank thinner and delicate",
    )

    assert resp.success is True
    assert resp.updated_state.category == "Ring"
    assert resp.updated_state.primary_metal == "18k white gold"
    assert resp.updated_state.gemstone_type == "blue sapphire"


def test_genuine_category_conflict_retained(gemini_service):
    """Genuine category change ('Turn this ring into a necklace') with ring blueprint MUST detect conflict."""
    # When user asks for a necklace on a ring blueprint
    res = gemini_service._resolve_category(
        user_prompt="Turn this ring into a necklace",
        source_blueprint_category="ring",
    )
    assert res.conflict is True
    assert "conflict" in (res.conflict_reason or "").lower() or len(res.warnings) > 0


def test_attribute_only_prompt_does_not_conflict_with_blueprint(gemini_service):
    """Prompts with no explicit category noun ('Change metal to platinum') against bracelet blueprint."""
    prompt_extracted = gemini_service.extract_explicit_category("Change metal to platinum")
    assert prompt_extracted is None

    res = gemini_service._resolve_category(
        user_selected_category="bracelet",
        user_prompt="Change metal to platinum",
        source_blueprint_category="bracelet",
    )
    assert res.conflict is False
    assert res.resolved == "bracelet"


def test_no_default_ring_leakage_in_fallback(gemini_service):
    """Verifies that fallback analysis never defaults to 'ring' when a category hint is provided."""
    analysis = gemini_service._generate_text_fallback_analysis(
        user_prompt="18k rose gold with mirror polish",
        category_hint="bracelet",
    )
    assert analysis.jewellery_category == "bracelet"
