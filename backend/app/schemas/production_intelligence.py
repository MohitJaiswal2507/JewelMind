"""
Production Intelligence & Manufacturing Schemas
Defines input contracts, output structures, BOM estimates, routing steps,
provenance origins, and validation constraints for AI manufacturing reasoning.
"""

import uuid
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProvenanceOrigin(str, Enum):
    """Origin tracking for manufacturing data points."""
    AI_ESTIMATE = "AI_ESTIMATE"
    ARTISAN_OVERRIDE = "ARTISAN_OVERRIDE"
    SYSTEM_DERIVED = "SYSTEM_DERIVED"
    BENCH_MEASURED = "BENCH_MEASURED"


class JewelleryCategoryEnum(str, Enum):
    """Authoritative jewellery categories in JewelMind."""
    RING = "ring"
    EARRING = "earring"
    PENDANT = "pendant"
    NECKLACE = "necklace"
    BRACELET = "bracelet"
    BANGLE = "bangle"
    BROOCH = "brooch"
    OTHER_JEWELLERY = "other_jewellery"


class ComplexityRatingEnum(str, Enum):
    """Manufacturing complexity classification."""
    SIMPLE = "simple"
    MODERATE = "moderate"
    INTRICATE = "intricate"
    MASTERPIECE = "masterpiece"


# ---------------------------------------------------------------------------
# Input Contract
# ---------------------------------------------------------------------------

class ProductionIntelligenceInput(BaseModel):
    """
    Input payload provided to the GeminiProductionService.
    Captures only real, existing project information without fabricating 3D solid metrics.
    """
    design_id: uuid.UUID = Field(..., description="Parent jewellery design ID")
    render_id: uuid.UUID = Field(..., description="Approved DesignRender ID")
    category: str = Field(..., description="Authoritative jewellery category")
    image_url: Optional[str] = Field(None, description="Accessible URL of the approved render")
    image_bytes: Optional[bytes] = Field(None, description="Raw binary bytes of approved render visual")
    image_base64: Optional[str] = Field(None, description="Base64 encoded string of approved render visual")
    image_mime_type: str = Field(default="image/png", description="MIME type of the visual asset")
    structured_state: Optional[Dict[str, Any]] = Field(
        None, description="Structured visual state dictionary from DesignRender"
    )
    user_prompt: Optional[str] = Field(None, description="Original user prompt or artisan instruction")
    enhanced_prompt: Optional[str] = Field(None, description="Natural enhanced prompt generated during synthesis")
    material_hint: Optional[str] = Field(None, description="Explicit metal requirement hint if known")
    gemstone_hint: Optional[str] = Field(None, description="Explicit gemstone requirement hint if known")

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        clean = v.strip().lower().replace(" ", "_")
        canonical_map = {
            "ring": "ring",
            "rings": "ring",
            "earring": "earring",
            "earrings": "earring",
            "pendant": "pendant",
            "pendants": "pendant",
            "necklace": "necklace",
            "necklaces": "necklace",
            "bracelet": "bracelet",
            "bracelets": "bracelet",
            "bangle": "bangle",
            "bangles": "bangle",
            "brooch": "brooch",
            "brooches": "brooch",
            "other": "other_jewellery",
            "other_jewellery": "other_jewellery",
        }
        if clean in canonical_map:
            return canonical_map[clean]
        return "other_jewellery"


# ---------------------------------------------------------------------------
# Line Items & Output Sub-Models
# ---------------------------------------------------------------------------

class ProductionMaterialEstimate(BaseModel):
    """BOM metal alloy specification and rough cast weight estimation."""
    metal_type: str = Field(..., description="Primary metal (gold, platinum, silver, etc.)")
    metal_purity: str = Field(..., description="Alloy purity grade (18k, 14k, 950, 925, etc.)")
    metal_color: Optional[str] = Field(None, description="Metal color hue (yellow, white, rose, etc.)")
    metal_finish: Optional[str] = Field(None, description="Surface finish (high_polish, matte, satin, etc.)")
    plating: Optional[str] = Field(None, description="Surface electroplating (rhodium, gold_vermeil, none)")
    estimated_weight_grams: Optional[float] = Field(
        None, ge=0.0, description="Estimated finished metal weight in grams (approximate)"
    )
    casting_loss_percentage: Optional[float] = Field(
        default=10.0, ge=0.0, description="Estimated casting sprue and polishing metal loss factor"
    )
    origin: ProvenanceOrigin = Field(
        default=ProvenanceOrigin.AI_ESTIMATE, description="Provenance classification of this material specification"
    )

    @field_validator("estimated_weight_grams", "casting_loss_percentage")
    @classmethod
    def round_sensible_precision(cls, v: Optional[float]) -> Optional[float]:
        if v is not None:
            if v < 0:
                raise ValueError("Weight or loss factor cannot be negative.")
            return round(v, 2)
        return v


class ProductionGemstoneEstimate(BaseModel):
    """BOM gemstone specification item."""
    gemstone_type: str = Field(..., description="Gemstone species (diamond, emerald, sapphire, ruby, etc.)")
    cut_shape: Optional[str] = Field(None, description="Cut shape (round, cushion, oval, pear, etc.)")
    stone_count: int = Field(default=1, ge=0, description="Number of stones of this type and cut")
    estimated_carat_weight: Optional[float] = Field(
        None, ge=0.0, description="Estimated total carat weight for these stones"
    )
    approximate_dimensions_mm: Optional[str] = Field(
        None, description="Estimated dimensional bracket (e.g. '6.5mm', '1.3mm pavé')"
    )
    setting_type: Optional[str] = Field(
        None, description="Bench setting technique (prong, bezel, channel, pave, etc.)"
    )
    is_center_stone: bool = Field(default=False, description="Whether this item is the primary focal center stone")
    origin: ProvenanceOrigin = Field(
        default=ProvenanceOrigin.AI_ESTIMATE, description="Provenance classification"
    )

    @field_validator("stone_count")
    @classmethod
    def validate_count_non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Stone count cannot be negative.")
        return v

    @field_validator("estimated_carat_weight")
    @classmethod
    def round_carat(cls, v: Optional[float]) -> Optional[float]:
        if v is not None:
            if v < 0:
                raise ValueError("Carat weight cannot be negative.")
            return round(v, 3)
        return v


class ProductionStructureObservation(BaseModel):
    """Manufacturing and structural observations extracted from render & blueprint."""
    component_breakdown: List[str] = Field(
        default_factory=list, description="List of identifiable sub-assemblies (e.g. shank, center collet, bail)"
    )
    estimated_dimensions: Optional[str] = Field(
        None, description="Rough planning dimensions (e.g. 'US Size 7', '45cm chain')"
    )
    minimum_thickness: Optional[str] = Field(
        None, description="Minimum recommended wall/shank thickness for casting integrity"
    )
    fabrication_notes: Optional[str] = Field(
        None, description="Artisan fabrication observations and warnings"
    )
    origin: ProvenanceOrigin = Field(
        default=ProvenanceOrigin.AI_ESTIMATE, description="Provenance classification"
    )


class ProductionStepEstimate(BaseModel):
    """Tailored sequential manufacturing routing stage."""
    step_number: int = Field(..., gt=0, description="Sequential stage order number (1-indexed)")
    stage_name: str = Field(..., min_length=2, max_length=255, description="Manufacturing stage title")
    required_skill: str = Field(
        ..., description="Primary artisan skill needed (cad_design, casting, stone_setting, polishing, engraving, general)"
    )
    required_machine_type: Optional[str] = Field(
        None, description="Optional required workshop equipment (casting_furnace, 3d_wax_printer, etc.)"
    )
    base_hours: float = Field(default=0.0, ge=0.0, description="Setup or fixed operation duration in hours")
    per_unit_hours: float = Field(default=0.0, ge=0.0, description="Variable duration in hours per unit batch")
    description: Optional[str] = Field(None, description="Detailed stage procedure instructions")
    quality_checkpoint: Optional[str] = Field(None, description="Inspection criteria required before advancing")
    origin: ProvenanceOrigin = Field(
        default=ProvenanceOrigin.AI_ESTIMATE, description="Provenance classification"
    )

    @field_validator("step_number")
    @classmethod
    def validate_step_number(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Step number must be greater than zero.")
        return v

    @field_validator("base_hours", "per_unit_hours")
    @classmethod
    def round_hours(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Hours cannot be negative.")
        return round(v, 2)


# ---------------------------------------------------------------------------
# Top-Level AI Output Schema
# ---------------------------------------------------------------------------

class ProductionSpecificationAIResponse(BaseModel):
    """
    Authoritative structured output produced by GeminiProductionService.
    Directly compatible with Phase I.1 ProductionSpecification database models.
    """
    design_id: Optional[uuid.UUID] = Field(None, description="Parent design ID")
    render_id: Optional[uuid.UUID] = Field(None, description="Approved render ID")
    category: str = Field(..., description="Authoritative jewellery category")
    specification_summary: str = Field(..., description="Comprehensive manufacturing summary for the workshop")
    materials: List[ProductionMaterialEstimate] = Field(default_factory=list)
    gemstones: List[ProductionGemstoneEstimate] = Field(default_factory=list)
    structure: ProductionStructureObservation = Field(default_factory=ProductionStructureObservation)
    routing: List[ProductionStepEstimate] = Field(default_factory=list)
    estimated_rough_metal_weight_grams: Optional[float] = Field(
        None, ge=0.0, description="Approximate gross casting weight including sprues"
    )
    estimated_finished_metal_weight_grams: Optional[float] = Field(
        None, ge=0.0, description="Approximate finished piece net weight"
    )
    estimated_total_bench_hours: Optional[float] = Field(
        None, ge=0.0, description="Total estimated workshop bench time across all stages"
    )
    complexity_rating: str = Field(
        default="moderate", description="Manufacturing difficulty: simple, moderate, intricate, masterpiece"
    )
    ai_confidence_score: float = Field(
        default=0.85, ge=0.0, le=1.0, description="Confidence rating in the analysis"
    )
    warnings: List[str] = Field(
        default_factory=list, description="Manufacturing caveats, dimensional uncertainties, and conflict notices"
    )
    assumptions: List[str] = Field(
        default_factory=list, description="Assumptions made in the absence of physical caliper/scale data"
    )
    fallback_applied: bool = Field(
        default=False, description="True if deterministic domain rules were applied instead of Gemini API"
    )
    provenance_summary: Dict[str, str] = Field(
        default_factory=dict, description="Summary map of field provenance classifications"
    )

    model_config = ConfigDict(from_attributes=True)

    @field_validator("ai_confidence_score")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        if v < 0.0 or v > 1.0:
            raise ValueError("AI confidence score must be between 0.0 and 1.0.")
        return round(v, 2)

    @field_validator("complexity_rating")
    @classmethod
    def validate_complexity(cls, v: str) -> str:
        clean = v.strip().lower()
        if clean not in ("simple", "moderate", "intricate", "masterpiece"):
            return "moderate"
        return clean
