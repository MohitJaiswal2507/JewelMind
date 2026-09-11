import sys
from pathlib import Path
import pytest

_ROOT = Path(__file__).resolve().parent.parent.parent
_BACKEND = _ROOT / "backend"
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from app.schemas.design import (
    DesignCategory,
    DesignCreate,
    DesignUpdate,
    to_ai_category,
    from_ai_category,
    BACKEND_TO_AI_CATEGORY_MAP,
    AI_TO_BACKEND_CATEGORY_MAP,
)
from ai.rendering.schemas import RenderRequest
from ai.rendering.prompts import build_jewellery_prompt


def test_backend_to_ai_category_conversion():
    """Verify that all 8 backend categories convert to the canonical AI category."""
    expected_mappings = {
        DesignCategory.RING: "ring",
        DesignCategory.EARRINGS: "earring",
        DesignCategory.PENDANT: "pendant",
        DesignCategory.NECKLACE: "necklace",
        DesignCategory.BRACELET: "bracelet",
        DesignCategory.BANGLE: "bangle",
        DesignCategory.BROOCH: "brooch",
        DesignCategory.OTHER: "other_jewellery",
    }

    for backend_cat, ai_cat in expected_mappings.items():
        assert to_ai_category(backend_cat) == ai_cat, f"Failed for {backend_cat} -> {ai_cat}"
        assert to_ai_category(backend_cat.value) == ai_cat, f"Failed for {backend_cat.value} -> {ai_cat}"


def test_ai_to_backend_category_conversion():
    """Verify that AI category strings map back to backend DesignCategory."""
    assert from_ai_category("ring") == DesignCategory.RING
    assert from_ai_category("earring") == DesignCategory.EARRINGS
    assert from_ai_category("earrings") == DesignCategory.EARRINGS
    assert from_ai_category("pendant") == DesignCategory.PENDANT
    assert from_ai_category("necklace") == DesignCategory.NECKLACE
    assert from_ai_category("bracelet") == DesignCategory.BRACELET
    assert from_ai_category("bangle") == DesignCategory.BANGLE
    assert from_ai_category("brooch") == DesignCategory.BROOCH
    assert from_ai_category("other_jewellery") == DesignCategory.OTHER
    assert from_ai_category("other") == DesignCategory.OTHER


def test_design_create_category_normalization():
    """Verify that DesignCreate accepts both title-case, lower-case, and AI singular forms."""
    # Standard enum
    d1 = DesignCreate(name="Gold Ring", category=DesignCategory.RING)
    assert d1.category == DesignCategory.RING

    # Brooch support
    d_brooch = DesignCreate(name="Vintage Brooch", category="Brooch")
    assert d_brooch.category == DesignCategory.BROOCH

    d_brooch_lower = DesignCreate(name="Vintage Brooch", category="brooch")
    assert d_brooch_lower.category == DesignCategory.BROOCH

    # Earring singular/plural normalization
    d_earring = DesignCreate(name="Diamond Studs", category="earring")
    assert d_earring.category == DesignCategory.EARRINGS

    d_earrings = DesignCreate(name="Diamond Studs", category="Earrings")
    assert d_earrings.category == DesignCategory.EARRINGS


def test_ai_rendering_schema_accepts_all_8_categories():
    """Verify that RenderRequest and PromptBuilder accept all 8 categories."""
    categories = [
        "ring",
        "earring",
        "pendant",
        "necklace",
        "bracelet",
        "bangle",
        "brooch",
        "other_jewellery",
    ]

    for cat in categories:
        req = RenderRequest(category=cat, prompt="luxury jewel")
        assert req.category == cat

        prompt = build_jewellery_prompt(category=cat, material="18k yellow gold", gemstone="diamond")
        assert len(prompt) > 20
        assert "18k yellow gold" in prompt
