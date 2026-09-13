"""JewelMind Phase E.1: Prompt Fidelity Hardening Regression Tests.

Verifies strict Tier-1 user intent preservation across all 12 mandatory test cases
from Section 10 of the Phase E.1 specification:
TEST 1: platinum round brilliant diamond thin shank ring
TEST 2: 18k yellow gold emerald oval stone pendant
TEST 3: rose gold minimalist necklace with small diamonds
TEST 4: silver hoop earring with three diamonds
TEST 5: platinum brooch with blue sapphire
TEST 6: yellow gold bangle with engraved floral pattern
TEST 7: white gold tennis bracelet with round diamonds
TEST 8: art deco geometric brooch in sterling silver featuring baguette cut diamonds and black onyx inlays
TEST 9: vintage floral pendant in rose gold with an oval blue sapphire center and petal diamond accents
TEST 10: User prompt platinum ring with emerald + edit to pear shaped
TEST 11: Gemini unavailable with oval sapphire pendant in platinum
TEST 12: No user gemstone specified (platinum minimalist ring)
Additionally verifies negative prompt safety (Section 11).
"""

import asyncio
import pytest

from app.schemas.ai import (
    GemstoneItem,
    GemstoneSpec,
    MaterialSpec,
    StructuralSpec,
    StructuredDesignUnderstanding,
    YoloGroundingContext,
)
from app.services.gemini_design_service import GeminiDesignService
from app.services.jewellery_prompt_compiler import JewelleryPromptCompiler, JEWELLERY_NEGATIVE_PROMPT
from ai.rendering.prompts import build_jewellery_prompt, build_negative_prompt


@pytest.fixture
def gemini_service():
    """GeminiDesignService instance with no API key (testing deterministic fallback & constraints)."""
    return GeminiDesignService(api_key=None)


# ------------------------------------------------------------------------------
# TEST 1: platinum round brilliant diamond thin shank ring
# ------------------------------------------------------------------------------
def test_1_platinum_round_brilliant_diamond_thin_shank_ring(gemini_service):
    prompt_text = "platinum round brilliant diamond thin shank ring"
    resp = asyncio.run(gemini_service.analyze_design(user_prompt=prompt_text))
    assert resp.success is True

    compiled = resp.renderer_prompt.lower()
    assert "platinum" in compiled
    assert "round brilliant" in compiled
    assert "diamond" in compiled
    assert "thin shank" in compiled
    assert "ring" in compiled

    # Must NOT contain conflicting substitutions
    assert "gold" not in compiled
    assert "emerald" not in compiled
    assert "sapphire" not in compiled
    assert "thick shank" not in compiled
    assert "wide shank" not in compiled


# ------------------------------------------------------------------------------
# TEST 2: 18k yellow gold emerald oval stone pendant
# ------------------------------------------------------------------------------
def test_2_18k_yellow_gold_emerald_oval_stone_pendant(gemini_service):
    prompt_text = "18k yellow gold emerald oval stone pendant"
    resp = asyncio.run(gemini_service.analyze_design(user_prompt=prompt_text))
    assert resp.success is True

    compiled = resp.renderer_prompt.lower()
    assert "18k yellow gold" in compiled
    assert "emerald" in compiled
    assert "oval" in compiled
    assert "pendant" in compiled

    # Must NOT silently become diamond or round brilliant
    assert "diamond" not in compiled
    assert "round brilliant" not in compiled


# ------------------------------------------------------------------------------
# TEST 3: rose gold minimalist necklace with small diamonds
# ------------------------------------------------------------------------------
def test_3_rose_gold_minimalist_necklace_small_diamonds(gemini_service):
    prompt_text = "rose gold minimalist necklace with small diamonds"
    resp = asyncio.run(gemini_service.analyze_design(user_prompt=prompt_text))
    assert resp.success is True

    compiled = resp.renderer_prompt.lower()
    assert "rose gold" in compiled
    assert "minimalist" in compiled
    assert "necklace" in compiled
    assert "diamond" in compiled


# ------------------------------------------------------------------------------
# TEST 4: silver hoop earring with three diamonds
# ------------------------------------------------------------------------------
def test_4_silver_hoop_earring_three_diamonds(gemini_service):
    prompt_text = "silver hoop earring with three diamonds"
    resp = asyncio.run(gemini_service.analyze_design(user_prompt=prompt_text))
    assert resp.success is True

    compiled = resp.renderer_prompt.lower()
    assert "silver" in compiled
    assert "hoop" in compiled
    assert "earring" in compiled
    assert "diamond" in compiled


# ------------------------------------------------------------------------------
# TEST 5: platinum brooch with blue sapphire
# ------------------------------------------------------------------------------
def test_5_platinum_brooch_blue_sapphire(gemini_service):
    prompt_text = "platinum brooch with blue sapphire"
    resp = asyncio.run(gemini_service.analyze_design(user_prompt=prompt_text))
    assert resp.success is True

    compiled = resp.renderer_prompt.lower()
    assert "platinum" in compiled
    assert "brooch" in compiled
    assert "blue sapphire" in compiled

    # Must NOT become diamond
    assert "diamond" not in compiled


# ------------------------------------------------------------------------------
# TEST 6: yellow gold bangle with engraved floral pattern
# ------------------------------------------------------------------------------
def test_6_yellow_gold_bangle_engraved_floral_pattern(gemini_service):
    prompt_text = "yellow gold bangle with engraved floral pattern"
    resp = asyncio.run(gemini_service.analyze_design(user_prompt=prompt_text))
    assert resp.success is True

    compiled = resp.renderer_prompt.lower()
    assert "yellow gold" in compiled
    assert "bangle" in compiled
    assert "engraved floral pattern" in compiled or ("engraved" in compiled and "floral" in compiled)

    # Must NOT invent gemstones
    assert "diamond" not in compiled
    assert "sapphire" not in compiled


# ------------------------------------------------------------------------------
# TEST 7: white gold tennis bracelet with round diamonds
# ------------------------------------------------------------------------------
def test_7_white_gold_tennis_bracelet_round_diamonds(gemini_service):
    prompt_text = "white gold tennis bracelet with round diamonds"
    resp = asyncio.run(gemini_service.analyze_design(user_prompt=prompt_text))
    assert resp.success is True

    compiled = resp.renderer_prompt.lower()
    assert "white gold" in compiled
    assert "tennis bracelet" in compiled
    assert "diamond" in compiled
    assert "round" in compiled


# ------------------------------------------------------------------------------
# TEST 8: art deco geometric brooch in sterling silver featuring baguette cut diamonds and black onyx inlays
# ------------------------------------------------------------------------------
def test_8_art_deco_geometric_brooch_baguette_diamonds_black_onyx(gemini_service):
    prompt_text = "art deco geometric brooch in sterling silver featuring baguette cut diamonds and black onyx inlays"
    resp = asyncio.run(gemini_service.analyze_design(user_prompt=prompt_text))
    assert resp.success is True

    compiled = resp.renderer_prompt.lower()
    assert "sterling silver" in compiled
    assert "brooch" in compiled
    assert "baguette" in compiled
    assert "diamond" in compiled
    assert "black onyx" in compiled
    assert "art deco" in compiled or "geometric" in compiled

    # Must NOT become round brilliant as a replacement or lose onyx
    assert "round brilliant" not in compiled


# ------------------------------------------------------------------------------
# TEST 9: vintage floral pendant in rose gold with an oval blue sapphire center and petal diamond accents
# ------------------------------------------------------------------------------
def test_9_vintage_floral_pendant_oval_sapphire_petal_diamond_accents(gemini_service):
    prompt_text = "vintage floral pendant in rose gold with an oval blue sapphire center and petal diamond accents"
    resp = asyncio.run(gemini_service.analyze_design(user_prompt=prompt_text))
    assert resp.success is True

    compiled = resp.renderer_prompt.lower()
    assert "rose gold" in compiled
    assert "oval" in compiled
    assert "blue sapphire" in compiled
    assert "diamond" in compiled
    assert "pendant" in compiled
    assert "vintage" in compiled or "floral" in compiled

    # Must NOT replace sapphire with diamond center
    assert "round brilliant diamond" not in compiled


# ------------------------------------------------------------------------------
# TEST 10: User prompt: "platinum ring with emerald", User edit: "make the emerald pear shaped"
# ------------------------------------------------------------------------------
def test_10_user_edited_prompt_pear_shaped_emerald(gemini_service):
    initial_prompt = "platinum ring with emerald"
    edited_prompt = "platinum ring with pear shaped emerald"

    resp = asyncio.run(gemini_service.analyze_design(user_prompt=edited_prompt))
    assert resp.success is True

    compiled = resp.renderer_prompt.lower()
    assert "platinum" in compiled
    assert "emerald" in compiled
    assert "pear" in compiled

    # Must NOT revert to round brilliant diamond
    assert "diamond" not in compiled
    assert "round brilliant" not in compiled


# ------------------------------------------------------------------------------
# TEST 11: Gemini unavailable -> deterministic fallback preserves user attributes
# ------------------------------------------------------------------------------
def test_11_gemini_unavailable_preserves_user_attributes(gemini_service):
    assert gemini_service.is_available() is False
    prompt_text = "oval sapphire pendant in platinum"
    resp = asyncio.run(gemini_service.analyze_design(user_prompt=prompt_text))

    assert resp.success is True
    assert resp.fallback_applied is True
    assert resp.gemini_category is None  # No fabricated visual claim

    compiled = resp.renderer_prompt.lower()
    assert "platinum" in compiled
    assert "sapphire" in compiled
    assert "oval" in compiled
    assert "pendant" in compiled

    # No crash and no fabricated diamond
    assert "diamond" not in compiled


# ------------------------------------------------------------------------------
# TEST 12: No user gemstone specified -> MUST NOT invent a gemstone
# ------------------------------------------------------------------------------
def test_12_no_user_gemstone_specified_minimalist_ring(gemini_service):
    prompt_text = "platinum minimalist ring"
    resp = asyncio.run(gemini_service.analyze_design(user_prompt=prompt_text))
    assert resp.success is True

    compiled = resp.renderer_prompt.lower()
    assert "platinum" in compiled
    assert "ring" in compiled
    assert "minimalist" in compiled

    # MUST NOT invent a specific gemstone
    assert "diamond" not in compiled
    assert "round brilliant" not in compiled
    assert "sapphire" not in compiled
    assert "emerald" not in compiled


# ------------------------------------------------------------------------------
# SECTION 11: Negative Prompt Safety
# ------------------------------------------------------------------------------
def test_negative_prompt_safety_scrubs_user_requested_attributes():
    """Verify that user-requested positive attributes are never penalized in negative prompts."""
    # User requests emerald
    neg_emerald = JewelleryPromptCompiler.compile_negative_prompt(
        custom_negatives="emerald, green, oversaturated",
        user_constraints=["gemstone: emerald"],
    )
    assert "emerald" not in neg_emerald.lower()

    # User requests platinum
    neg_platinum = JewelleryPromptCompiler.compile_negative_prompt(
        custom_negatives="platinum, shiny metal",
        user_constraints=["metal: platinum"],
    )
    assert "platinum" not in neg_platinum.lower()

    # User requests baguette diamonds
    neg_baguette = JewelleryPromptCompiler.compile_negative_prompt(
        custom_negatives="baguette, diamond facets",
        user_constraints=["gemstone: diamond", "cut: baguette"],
    )
    assert "baguette" not in neg_baguette.lower()

    # Pipeline-level build_negative_prompt
    pipe_neg = build_negative_prompt(
        user_negative_prompt="blurry, emerald, platinum",
        positive_prompt="platinum ring with emerald",
    )
    assert "emerald" not in pipe_neg.lower()
    assert "platinum" not in pipe_neg.lower()


# ------------------------------------------------------------------------------
# Pipeline Prompt Builder Integration
# ------------------------------------------------------------------------------
def test_build_jewellery_prompt_fidelity():
    """Verify build_jewellery_prompt does not append conflicting defaults when given user prompts."""
    # Compiled prompt should remain intact without conflicting additions
    compiled = "photorealistic pendant fine jewellery product photograph, crafted in polished 18k yellow gold, embellished with featured oval emerald in prong setting, studio lighting, sharp focus, clean neutral background"
    res = build_jewellery_prompt(
        material="18k yellow gold",
        gemstone="round brilliant diamond",  # Default argument in caller
        category="pendant",
        user_prompt=compiled,
    )
    assert res == compiled
    assert "round brilliant diamond" not in res

    # Short artisan prompt with emerald should not have diamond added
    artisan = "18k yellow gold emerald oval stone pendant"
    res_artisan = build_jewellery_prompt(
        material="18k yellow gold",
        gemstone="round brilliant diamond",
        category="pendant",
        user_prompt=artisan,
    )
    assert "emerald" in res_artisan
    assert "round brilliant diamond" not in res_artisan
