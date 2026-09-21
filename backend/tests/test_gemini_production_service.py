"""
Unit & Integration Tests for Gemini Production Intelligence Service (Phase I.2)
Covers all 22 required test conditions, user-intent cases (A, B, C, D),
deterministic fallback behavior, schema validations, and DB model mapping.
"""

import asyncio
import uuid
from unittest.mock import AsyncMock, patch
import pytest
from pydantic import ValidationError

from app.models.specification import (
    ProductionGemstone,
    ProductionMaterial,
    ProductionSpecification,
    ProductionStep,
)
from app.schemas.production_intelligence import (
    ComplexityRatingEnum,
    JewelleryCategoryEnum,
    ProductionGemstoneEstimate,
    ProductionIntelligenceInput,
    ProductionMaterialEstimate,
    ProductionSpecificationAIResponse,
    ProductionStepEstimate,
    ProductionStructureObservation,
    ProvenanceOrigin,
)
from app.services.gemini_production_service import (
    CATEGORY_BENCHMARKS,
    GeminiProductionService,
    get_gemini_production_service,
    map_ai_response_to_production_specification,
)


@pytest.fixture
def sample_input_ring() -> ProductionIntelligenceInput:
    return ProductionIntelligenceInput(
        design_id=uuid.uuid4(),
        render_id=uuid.uuid4(),
        category="ring",
        user_prompt="Solitaire diamond engagement ring in 18k white gold",
        enhanced_prompt="A stunning 18k white gold solitaire ring with round brilliant diamond center stone",
        structured_state={
            "material": {"metal": "gold", "purity": "18k", "color": "white"},
            "gemstones": [{"gemstone_type": "diamond", "cut": "round"}],
        },
    )


@pytest.fixture
def sample_gemini_ring_json():
    return {
        "category": "ring",
        "specification_summary": "Classic solitaire engagement ring in 18k white gold with 1.0ct round brilliant diamond.",
        "materials": [
            {
                "metal_type": "gold",
                "metal_purity": "18k",
                "metal_color": "white",
                "metal_finish": "high_polish",
                "plating": "rhodium",
                "estimated_weight_grams": 5.4,
                "casting_loss_percentage": 10.0,
            }
        ],
        "gemstones": [
            {
                "gemstone_type": "diamond",
                "cut_shape": "round",
                "stone_count": 1,
                "estimated_carat_weight": 1.0,
                "approximate_dimensions_mm": "6.5mm",
                "setting_type": "prong",
                "is_center_stone": True,
            }
        ],
        "structure": {
            "component_breakdown": ["shank", "four_prong_head"],
            "estimated_dimensions": "US Size 6.5 (16.9mm internal diameter)",
            "minimum_thickness": "1.6mm at base of shank",
            "fabrication_notes": "Cast head integrated with shank or solder two-piece assembly.",
        },
        "routing": [
            {
                "step_number": 1,
                "stage_name": "CAD & 3D Wax Modeling",
                "required_skill": "cad_design",
                "required_machine_type": "3d_wax_printer",
                "base_hours": 1.5,
                "per_unit_hours": 0.2,
                "description": "Model and print castable wax.",
                "quality_checkpoint": "Check prong thickness.",
            },
            {
                "step_number": 2,
                "stage_name": "Investment Casting",
                "required_skill": "casting",
                "required_machine_type": "casting_furnace",
                "base_hours": 2.0,
                "per_unit_hours": 0.5,
                "description": "Vacuum investment casting in 18k white gold.",
                "quality_checkpoint": "Zero porosity under magnification.",
            },
            {
                "step_number": 3,
                "stage_name": "Stone Setting",
                "required_skill": "stone_setting",
                "required_machine_type": None,
                "base_hours": 1.0,
                "per_unit_hours": 0.75,
                "description": "Seat and tighten round brilliant center diamond.",
                "quality_checkpoint": "Stone secure and level.",
            },
            {
                "step_number": 4,
                "stage_name": "Rhodium Plating & Polish",
                "required_skill": "polishing",
                "required_machine_type": "ultrasonic_cleaner",
                "base_hours": 0.5,
                "per_unit_hours": 0.25,
                "description": "Mirror polish and rhodium electroplating.",
                "quality_checkpoint": "Uniform bright white finish.",
            },
        ],
        "estimated_rough_metal_weight_grams": 6.2,
        "estimated_finished_metal_weight_grams": 5.4,
        "estimated_total_bench_hours": 4.5,
        "complexity_rating": "moderate",
        "ai_confidence_score": 0.92,
        "warnings": ["Ensure ring size is verified with client before casting."],
        "assumptions": ["Lost-wax investment casting path assumed."],
    }


# ===========================================================================
# 1. Valid Gemini Production Response
# ===========================================================================

def test_01_valid_gemini_production_response(sample_input_ring, sample_gemini_ring_json):
    service = GeminiProductionService()
    with patch.object(service, "is_available", return_value=True), \
         patch.object(service, "_call_gemini_manufacturing_api", new_callable=AsyncMock) as mock_api:
        mock_api.return_value = sample_gemini_ring_json

        res = asyncio.run(service.analyze_production(sample_input_ring))

        assert isinstance(res, ProductionSpecificationAIResponse)
        assert res.category == "ring"
        assert res.fallback_applied is False
        assert len(res.materials) == 1
        assert res.materials[0].metal_type == "gold"
        assert res.materials[0].metal_purity == "18k"
        assert res.materials[0].metal_color == "white"
        assert len(res.gemstones) == 1
        assert res.gemstones[0].gemstone_type == "diamond"
        assert res.gemstones[0].stone_count == 1
        assert res.estimated_finished_metal_weight_grams == 5.4
        assert res.complexity_rating == "moderate"
        assert res.ai_confidence_score == 0.92


# ===========================================================================
# 2. Strict Schema Validation
# ===========================================================================

def test_02_strict_schema_validation():
    # Valid model construction
    valid_mat = ProductionMaterialEstimate(
        metal_type="platinum",
        metal_purity="950",
        metal_color="white",
        estimated_weight_grams=8.5,
        casting_loss_percentage=12.0,
        origin=ProvenanceOrigin.AI_ESTIMATE,
    )
    assert valid_mat.metal_type == "platinum"
    assert valid_mat.estimated_weight_grams == 8.5

    # Invalid origin
    with pytest.raises(ValidationError):
        ProductionMaterialEstimate(
            metal_type="gold",
            metal_purity="18k",
            origin="INVALID_ORIGIN",  # type: ignore
        )


# ===========================================================================
# 3. User Material Preserved
# ===========================================================================

def test_03_user_material_preserved(sample_gemini_ring_json):
    service = GeminiProductionService()
    # User specifically requested platinum
    input_data = ProductionIntelligenceInput(
        design_id=uuid.uuid4(),
        render_id=uuid.uuid4(),
        category="ring",
        user_prompt="Custom platinum ring with sapphire",
    )
    # Gemini incorrectly returned 18k yellow gold
    sample_gemini_ring_json["materials"][0] = {
        "metal_type": "gold",
        "metal_purity": "18k",
        "metal_color": "yellow",
        "estimated_weight_grams": 5.0,
    }

    with patch.object(service, "is_available", return_value=True), \
         patch.object(service, "_call_gemini_manufacturing_api", new_callable=AsyncMock) as mock_api:
        mock_api.return_value = sample_gemini_ring_json

        res = asyncio.run(service.analyze_production(input_data))
        # Material must be restored to platinum
        assert res.materials[0].metal_type == "platinum"
        assert res.materials[0].metal_purity == "950"


# ===========================================================================
# 4. User Gemstone Preserved
# ===========================================================================

def test_04_user_gemstone_preserved(sample_gemini_ring_json):
    service = GeminiProductionService()
    # User specifically requested emerald
    input_data = ProductionIntelligenceInput(
        design_id=uuid.uuid4(),
        render_id=uuid.uuid4(),
        category="pendant",
        user_prompt="Solitaire emerald pendant in yellow gold",
    )
    # Gemini incorrectly substituted diamond
    sample_gemini_ring_json["category"] = "pendant"
    sample_gemini_ring_json["gemstones"][0]["gemstone_type"] = "diamond"

    with patch.object(service, "is_available", return_value=True), \
         patch.object(service, "_call_gemini_manufacturing_api", new_callable=AsyncMock) as mock_api:
        mock_api.return_value = sample_gemini_ring_json

        res = asyncio.run(service.analyze_production(input_data))
        assert res.gemstones[0].gemstone_type == "emerald"


# ===========================================================================
# 5. User Category Preserved
# ===========================================================================

def test_05_user_category_preserved(sample_gemini_ring_json):
    service = GeminiProductionService()
    # Authoritative category is earring
    input_data = ProductionIntelligenceInput(
        design_id=uuid.uuid4(),
        render_id=uuid.uuid4(),
        category="earring",
        user_prompt="Drop earrings with diamonds",
    )
    # Gemini visual reasoning claims it looks like a pendant
    sample_gemini_ring_json["category"] = "pendant"

    with patch.object(service, "is_available", return_value=True), \
         patch.object(service, "_call_gemini_manufacturing_api", new_callable=AsyncMock) as mock_api:
        mock_api.return_value = sample_gemini_ring_json

        res = asyncio.run(service.analyze_production(input_data))
        assert res.category == "earring"


# ===========================================================================
# 6. Category Conflict Warning
# ===========================================================================

def test_06_category_conflict_warning(sample_gemini_ring_json):
    service = GeminiProductionService()
    input_data = ProductionIntelligenceInput(
        design_id=uuid.uuid4(),
        render_id=uuid.uuid4(),
        category="necklace",
        user_prompt="Collar necklace with emeralds",
    )
    sample_gemini_ring_json["category"] = "bracelet"

    with patch.object(service, "is_available", return_value=True), \
         patch.object(service, "_call_gemini_manufacturing_api", new_callable=AsyncMock) as mock_api:
        mock_api.return_value = sample_gemini_ring_json

        res = asyncio.run(service.analyze_production(input_data))
        assert res.category == "necklace"
        assert any("Visual analysis suggested category 'bracelet'" in w for w in res.warnings)


# ===========================================================================
# 7. Material Conflict Warning
# ===========================================================================

def test_07_material_conflict_warning(sample_gemini_ring_json):
    service = GeminiProductionService()
    input_data = ProductionIntelligenceInput(
        design_id=uuid.uuid4(),
        render_id=uuid.uuid4(),
        category="ring",
        user_prompt="18k rose gold signet ring",
    )
    sample_gemini_ring_json["materials"][0] = {
        "metal_type": "platinum",
        "metal_purity": "950",
        "metal_color": "white",
    }

    with patch.object(service, "is_available", return_value=True), \
         patch.object(service, "_call_gemini_manufacturing_api", new_callable=AsyncMock) as mock_api:
        mock_api.return_value = sample_gemini_ring_json

        res = asyncio.run(service.analyze_production(input_data))
        assert res.materials[0].metal_color == "rose"
        assert any("Material conflict detected" in w for w in res.warnings)


# ===========================================================================
# 8. Gemstone Conflict Warning
# ===========================================================================

def test_08_gemstone_conflict_warning(sample_gemini_ring_json):
    service = GeminiProductionService()
    input_data = ProductionIntelligenceInput(
        design_id=uuid.uuid4(),
        render_id=uuid.uuid4(),
        category="ring",
        user_prompt="Ruby halo ring in yellow gold",
    )
    sample_gemini_ring_json["gemstones"][0]["gemstone_type"] = "diamond"

    with patch.object(service, "is_available", return_value=True), \
         patch.object(service, "_call_gemini_manufacturing_api", new_callable=AsyncMock) as mock_api:
        mock_api.return_value = sample_gemini_ring_json

        res = asyncio.run(service.analyze_production(input_data))
        assert res.gemstones[0].gemstone_type == "ruby"
        assert any("Gemstone conflict detected" in w for w in res.warnings)


# ===========================================================================
# 9. No-Gemstone Routing
# ===========================================================================

def test_09_no_gemstone_routing():
    service = GeminiProductionService()
    # Explicit no gemstones requirement
    input_data = ProductionIntelligenceInput(
        design_id=uuid.uuid4(),
        render_id=uuid.uuid4(),
        category="ring",
        user_prompt="Plain 18k yellow gold wedding band with no gemstones",
    )
    with patch.object(service, "is_available", return_value=False):
        res = asyncio.run(service.analyze_production(input_data))

        assert len(res.gemstones) == 0
        stage_names = [s.stage_name.lower() for s in res.routing]
        assert not any("stone setting" in s for s in stage_names)


# ===========================================================================
# 10. Gemstone Routing
# ===========================================================================

def test_10_gemstone_routing():
    service = GeminiProductionService()
    input_data = ProductionIntelligenceInput(
        design_id=uuid.uuid4(),
        render_id=uuid.uuid4(),
        category="ring",
        user_prompt="Sapphire three-stone ring",
    )
    with patch.object(service, "is_available", return_value=False):
        res = asyncio.run(service.analyze_production(input_data))

        assert len(res.gemstones) > 0
        stage_names = [s.stage_name.lower() for s in res.routing]
        assert any("stone setting" in s for s in stage_names)


# ===========================================================================
# 11. Plating Routing
# ===========================================================================

def test_11_plating_routing():
    service = GeminiProductionService()
    input_data = ProductionIntelligenceInput(
        design_id=uuid.uuid4(),
        render_id=uuid.uuid4(),
        category="necklace",
        user_prompt="Silver chain with rhodium plating",
    )
    with patch.object(service, "is_available", return_value=False):
        res = asyncio.run(service.analyze_production(input_data))

        stage_names = [s.stage_name.lower() for s in res.routing]
        assert any("plating" in s for s in stage_names)


# ===========================================================================
# 12. Fallback When API Key Unavailable
# ===========================================================================

def test_12_fallback_when_api_key_unavailable(sample_input_ring):
    service = GeminiProductionService()
    with patch.object(service, "is_available", return_value=False):
        res = asyncio.run(service.analyze_production(sample_input_ring))

        assert res.fallback_applied is True
        assert any("Gemini API key is not configured" in w for w in res.warnings)
        assert len(res.routing) > 0
        assert res.estimated_finished_metal_weight_grams > 0


# ===========================================================================
# 13. Fallback When Gemini Request Fails
# ===========================================================================

def test_13_fallback_when_gemini_request_fails(sample_input_ring):
    service = GeminiProductionService()
    with patch.object(service, "is_available", return_value=True), \
         patch.object(service, "_call_gemini_manufacturing_api", side_effect=RuntimeError("Connection timeout")):
        res = asyncio.run(service.analyze_production(sample_input_ring))

        assert res.fallback_applied is True
        assert any("Gemini manufacturing analysis error" in w for w in res.warnings)


# ===========================================================================
# 14. Fallback When Gemini JSON is Malformed
# ===========================================================================

def test_14_fallback_when_gemini_json_is_malformed(sample_input_ring):
    service = GeminiProductionService()
    with patch.object(service, "is_available", return_value=True), \
         patch.object(service, "_call_gemini_manufacturing_api", side_effect=ValueError("Invalid JSON formatting")):
        res = asyncio.run(service.analyze_production(sample_input_ring))

        assert res.fallback_applied is True
        assert any("Gemini manufacturing analysis error" in w for w in res.warnings)


# ===========================================================================
# 15. Invalid Negative Weight Rejected
# ===========================================================================

def test_15_invalid_negative_weight_rejected():
    with pytest.raises(ValidationError):
        ProductionMaterialEstimate(
            metal_type="gold",
            metal_purity="18k",
            estimated_weight_grams=-2.5,
        )


# ===========================================================================
# 16. Invalid Negative Hours Rejected
# ===========================================================================

def test_16_invalid_negative_hours_rejected():
    with pytest.raises(ValidationError):
        ProductionStepEstimate(
            step_number=1,
            stage_name="Casting",
            required_skill="casting",
            base_hours=-1.5,
        )


# ===========================================================================
# 17. Confidence Validation
# ===========================================================================

def test_17_confidence_validation():
    # Negative confidence
    with pytest.raises(ValidationError):
        ProductionSpecificationAIResponse(
            category="ring",
            specification_summary="Test",
            ai_confidence_score=-0.1,
        )

    # Confidence > 1.0
    with pytest.raises(ValidationError):
        ProductionSpecificationAIResponse(
            category="ring",
            specification_summary="Test",
            ai_confidence_score=1.5,
        )

    # Valid boundary confidence
    res = ProductionSpecificationAIResponse(
        category="ring",
        specification_summary="Test",
        ai_confidence_score=1.0,
    )
    assert res.ai_confidence_score == 1.0


# ===========================================================================
# 18. Empty Routing Rejected / Fallback
# ===========================================================================

def test_18_empty_routing_rejected(sample_input_ring, sample_gemini_ring_json):
    service = GeminiProductionService()
    sample_gemini_ring_json["routing"] = []  # AI returns empty routing

    with patch.object(service, "is_available", return_value=True), \
         patch.object(service, "_call_gemini_manufacturing_api", new_callable=AsyncMock) as mock_api:
        mock_api.return_value = sample_gemini_ring_json

        res = asyncio.run(service.analyze_production(sample_input_ring))
        # Should have generated default category routing
        assert len(res.routing) > 0
        assert any("Gemini provided empty routing" in w for w in res.warnings)


# ===========================================================================
# 19. Production Response -> DB Model Mapping
# ===========================================================================

def test_19_production_response_to_db_model_mapping(sample_gemini_ring_json):
    user_id = uuid.uuid4()
    design_id = uuid.uuid4()
    render_id = uuid.uuid4()

    ai_resp = ProductionSpecificationAIResponse.model_validate({
        **sample_gemini_ring_json,
        "design_id": design_id,
        "render_id": render_id,
    })

    db_spec = map_ai_response_to_production_specification(
        ai_response=ai_resp,
        user_id=user_id,
        design_id=design_id,
        render_id=render_id,
        version_number=1,
        status="draft",
    )

    assert isinstance(db_spec, ProductionSpecification)
    assert db_spec.user_id == user_id
    assert db_spec.design_id == design_id
    assert db_spec.render_id == render_id
    assert db_spec.category == "ring"
    assert db_spec.status == "draft"
    assert db_spec.estimated_finished_metal_weight_grams == 5.4
    assert db_spec.total_gemstone_count == 1
    assert len(db_spec.materials) == 1
    assert isinstance(db_spec.materials[0], ProductionMaterial)
    assert db_spec.materials[0].metal_type == "gold"
    assert len(db_spec.gemstones) == 1
    assert isinstance(db_spec.gemstones[0], ProductionGemstone)
    assert db_spec.gemstones[0].gemstone_type == "diamond"
    assert len(db_spec.steps) == 4
    assert isinstance(db_spec.steps[0], ProductionStep)
    assert db_spec.steps[0].stage_name == "CAD & 3D Wax Modeling"


# ===========================================================================
# 20. Provenance Labels
# ===========================================================================

def test_20_provenance_labels(sample_input_ring, sample_gemini_ring_json):
    service = GeminiProductionService()
    with patch.object(service, "is_available", return_value=True), \
         patch.object(service, "_call_gemini_manufacturing_api", new_callable=AsyncMock) as mock_api:
        mock_api.return_value = sample_gemini_ring_json

        res = asyncio.run(service.analyze_production(sample_input_ring))
        assert res.materials[0].origin == ProvenanceOrigin.AI_ESTIMATE
        assert res.gemstones[0].origin == ProvenanceOrigin.AI_ESTIMATE
        assert res.routing[0].origin == ProvenanceOrigin.AI_ESTIMATE


# ===========================================================================
# 21. Uncertain Values Produce Warnings/Sensible Precision
# ===========================================================================

def test_21_sensible_precision_and_rounding():
    mat = ProductionMaterialEstimate(
        metal_type="gold",
        metal_purity="18k",
        estimated_weight_grams=5.4876291,  # Fake 7-decimal float
        casting_loss_percentage=10.1234,
    )
    # Should be rounded to sensible 2 decimals
    assert mat.estimated_weight_grams == 5.49
    assert mat.casting_loss_percentage == 10.12


# ===========================================================================
# 22. All Eight Jewellery Categories
# ===========================================================================

def test_22_all_eight_jewellery_categories():
    service = GeminiProductionService()
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

    with patch.object(service, "is_available", return_value=False):
        for cat in categories:
            inp = ProductionIntelligenceInput(
                design_id=uuid.uuid4(),
                render_id=uuid.uuid4(),
                category=cat,
                user_prompt=f"A beautiful bespoke {cat} crafted in 18k yellow gold",
            )
            res = asyncio.run(service.analyze_production(inp))
            assert res.category == cat
            assert len(res.materials) >= 1
            assert len(res.routing) >= 4
            assert res.estimated_finished_metal_weight_grams > 0
            assert res.estimated_total_bench_hours > 0


# ===========================================================================
# USER INTENT TEST CASES (A, B, C, D)
# ===========================================================================

def test_case_a_emerald_pendant_with_7_stones():
    """
    CASE A: "18k yellow gold emerald pendant with 7 emerald stones"
    Expected: pendant, 18k, yellow gold, emerald, ~7 stones, no silent diamond substitution.
    """
    service = GeminiProductionService()
    inp = ProductionIntelligenceInput(
        design_id=uuid.uuid4(),
        render_id=uuid.uuid4(),
        category="pendant",
        user_prompt="18k yellow gold emerald pendant with 7 emerald stones",
    )
    with patch.object(service, "is_available", return_value=False):
        res = asyncio.run(service.analyze_production(inp))

        assert res.category == "pendant"
        assert res.materials[0].metal_type == "gold"
        assert res.materials[0].metal_purity == "18k"
        assert res.materials[0].metal_color == "yellow"
        assert len(res.gemstones) >= 1
        assert res.gemstones[0].gemstone_type == "emerald"
        assert res.gemstones[0].stone_count == 7
        assert not any(g.gemstone_type == "diamond" for g in res.gemstones)


def test_case_b_platinum_ring_one_diamond():
    """
    CASE B: "platinum ring with one round brilliant diamond"
    Expected: platinum, ring, diamond, round, one center stone.
    """
    service = GeminiProductionService()
    inp = ProductionIntelligenceInput(
        design_id=uuid.uuid4(),
        render_id=uuid.uuid4(),
        category="ring",
        user_prompt="platinum ring with one round brilliant diamond",
    )
    with patch.object(service, "is_available", return_value=False):
        res = asyncio.run(service.analyze_production(inp))

        assert res.category == "ring"
        assert res.materials[0].metal_type == "platinum"
        assert res.materials[0].metal_purity == "950"
        assert len(res.gemstones) == 1
        assert res.gemstones[0].gemstone_type == "diamond"
        assert res.gemstones[0].cut_shape == "round"
        assert res.gemstones[0].stone_count == 1
        assert res.gemstones[0].is_center_stone is True


def test_case_c_silver_bracelet_no_gemstones():
    """
    CASE C: "silver bracelet with no gemstones"
    Expected: silver, bracelet, zero gemstone requirement, no Stone Setting stage.
    """
    service = GeminiProductionService()
    inp = ProductionIntelligenceInput(
        design_id=uuid.uuid4(),
        render_id=uuid.uuid4(),
        category="bracelet",
        user_prompt="silver bracelet with no gemstones",
    )
    with patch.object(service, "is_available", return_value=False):
        res = asyncio.run(service.analyze_production(inp))

        assert res.category == "bracelet"
        assert res.materials[0].metal_type == "silver"
        assert len(res.gemstones) == 0
        stages = [s.stage_name.lower() for s in res.routing]
        assert not any("stone setting" in s for s in stages)
        # Bracelet should include assembly
        assert any("assembly" in s or "clasp" in s for s in stages)


def test_case_d_rose_gold_necklace_rhodium_plating():
    """
    CASE D: "18k rose gold necklace with rhodium plating"
    Expected: rose gold, rhodium plating, plating-related manufacturing stage.
    """
    service = GeminiProductionService()
    inp = ProductionIntelligenceInput(
        design_id=uuid.uuid4(),
        render_id=uuid.uuid4(),
        category="necklace",
        user_prompt="18k rose gold necklace with rhodium plating",
    )
    with patch.object(service, "is_available", return_value=False):
        res = asyncio.run(service.analyze_production(inp))

        assert res.category == "necklace"
        assert res.materials[0].metal_color == "rose"
        assert res.materials[0].plating == "rhodium"
        stages = [s.stage_name.lower() for s in res.routing]
        assert any("plating" in s for s in stages)


# ===========================================================================
# 23. Database Persistence Integration with Session Fixture
# ===========================================================================

def test_23_db_session_integration(db_session, sample_gemini_ring_json):
    """
    Verifies that the mapped ProductionSpecification model can be persisted to SQLite,
    persists its children (materials, gemstones, steps), and cascades work as defined in Phase I.1.
    """
    user_id = uuid.uuid4()
    design_id = uuid.uuid4()
    render_id = uuid.uuid4()

    ai_resp = ProductionSpecificationAIResponse.model_validate({
        **sample_gemini_ring_json,
        "design_id": design_id,
        "render_id": render_id,
    })

    db_spec = map_ai_response_to_production_specification(
        ai_response=ai_resp,
        user_id=user_id,
        design_id=design_id,
        render_id=render_id,
    )

    db_session.add(db_spec)
    db_session.commit()

    # Query back
    loaded = db_session.query(ProductionSpecification).filter_by(id=db_spec.id).first()
    assert loaded is not None
    assert loaded.category == "ring"
    assert len(loaded.materials) == 1
    assert loaded.materials[0].metal_type == "gold"
    assert len(loaded.gemstones) == 1
    assert loaded.gemstones[0].gemstone_type == "diamond"
    assert len(loaded.steps) == 4
    assert loaded.steps[0].required_skill == "cad_design"
