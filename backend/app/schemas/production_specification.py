"""
Production Specification API Schemas
Defines request and response schemas for Production Specification generation,
retrieval, artisan review/override updates, approval, and nested BOM line items.
"""

import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ProductionSpecificationGenerateRequest(BaseModel):
    """
    Client request payload for generating a production specification.
    Client specifies the target approved render and optional artisan hints.
    All ownership, design linkage, versioning, and AI metadata are strictly server-controlled.
    """
    render_id: uuid.UUID = Field(..., description="Target approved DesignRender ID")
    user_prompt: Optional[str] = Field(
        None, description="Optional custom artisan manufacturing instructions or notes"
    )
    material_hint: Optional[str] = Field(
        None, description="Optional explicit metal alloy requirement (e.g. '18k yellow gold')"
    )
    gemstone_hint: Optional[str] = Field(
        None, description="Optional explicit gemstone species requirement (e.g. 'emerald')"
    )

    # Disallow client injection of server-controlled fields
    model_config = ConfigDict(extra="forbid")


# ---------------------------------------------------------------------------
# Artisan Update / Override Schemas
# ---------------------------------------------------------------------------

class ProductionMaterialUpdate(BaseModel):
    """Artisan update payload for a material item."""
    id: Optional[uuid.UUID] = Field(None, description="Existing material ID to update; null to create new item")
    metal_type: str = Field(..., description="Alloy metal family (gold, platinum, silver, etc.)")
    metal_purity: str = Field(..., description="Alloy purity grade (18k, 14k, 950, 925, etc.)")
    metal_color: Optional[str] = Field(None, description="Metal color hue")
    metal_finish: Optional[str] = Field(None, description="Surface finish")
    plating: Optional[str] = Field(None, description="Surface electroplating")
    estimated_weight_grams: Optional[float] = Field(None, ge=0.0, description="Finished net weight in grams")
    casting_loss_percentage: Optional[float] = Field(10.0, ge=0.0, description="Casting and finishing loss factor")


class ProductionGemstoneUpdate(BaseModel):
    """Artisan update payload for a gemstone item."""
    id: Optional[uuid.UUID] = Field(None, description="Existing gemstone ID to update; null to create new item")
    gemstone_type: str = Field(..., description="Gemstone species")
    cut_shape: Optional[str] = Field(None, description="Cut shape")
    stone_count: int = Field(1, ge=0, description="Number of stones")
    estimated_carat_weight: Optional[float] = Field(None, ge=0.0, description="Carat weight total")
    approximate_dimensions_mm: Optional[str] = Field(None, description="Approximate nominal dimensions")
    setting_type: Optional[str] = Field(None, description="Bench setting technique")
    is_center_stone: bool = Field(False, description="Whether this is the center focal stone")


class ProductionStepUpdate(BaseModel):
    """Artisan update payload for a manufacturing routing stage."""
    id: Optional[uuid.UUID] = Field(None, description="Existing step ID to update; null to create new step")
    step_number: int = Field(..., gt=0, description="Sequential stage order number (1-indexed)")
    stage_name: str = Field(..., min_length=2, description="Stage name")
    required_skill: str = Field(..., description="Primary artisan skill needed")
    required_machine_type: Optional[str] = Field(None, description="Required workshop machinery")
    base_hours: float = Field(0.0, ge=0.0, description="Base/setup duration in hours")
    per_unit_hours: float = Field(0.0, ge=0.0, description="Duration per unit batch in hours")
    description: Optional[str] = Field(None, description="Stage instructions")
    quality_checkpoint: Optional[str] = Field(None, description="Inspection checkpoint")


class ProductionSpecificationUpdateRequest(BaseModel):
    """
    Client request payload for updating/overriding a DRAFT Production Specification.
    Strictly forbids client modification of immutable and server-controlled fields
    (id, user_id, design_id, render_id, version_number, status, approved_at, ai_confidence_score, timestamps).
    """
    category: Optional[str] = Field(None, description="Authoritative jewellery category")
    estimated_rough_metal_weight_grams: Optional[float] = Field(None, ge=0.0, description="Estimated rough casting weight in grams")
    estimated_finished_metal_weight_grams: Optional[float] = Field(None, ge=0.0, description="Estimated finished piece weight in grams")
    total_gemstone_count: Optional[int] = Field(None, ge=0, description="Total count of gemstones")
    estimated_total_bench_hours: Optional[float] = Field(None, ge=0.0, description="Estimated workshop bench labor hours")
    complexity_rating: Optional[str] = Field(None, description="Manufacturing complexity classification")
    fabrication_notes: Optional[str] = Field(None, description="Artisan fabrication and engineering notes")

    materials: Optional[List[ProductionMaterialUpdate]] = Field(None, description="Updated BOM materials collection")
    gemstones: Optional[List[ProductionGemstoneUpdate]] = Field(None, description="Updated BOM gemstones collection")
    steps: Optional[List[ProductionStepUpdate]] = Field(None, description="Updated sequential routing stages")

    # Extra fields forbidden to prevent client injection of server-controlled attributes
    model_config = ConfigDict(extra="forbid")


# ---------------------------------------------------------------------------
# Response Models
# ---------------------------------------------------------------------------

class ProductionMaterialResponse(BaseModel):
    """BOM metal alloy specification item."""
    id: uuid.UUID
    specification_id: uuid.UUID
    metal_type: str
    metal_purity: str
    metal_color: Optional[str] = None
    metal_finish: Optional[str] = None
    plating: Optional[str] = None
    estimated_weight_grams: Optional[float] = None
    casting_loss_percentage: Optional[float] = None
    origin: str = Field(default="AI_ESTIMATE", description="Data provenance (AI_ESTIMATE, ARTISAN_OVERRIDE, SYSTEM_DERIVED)")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductionGemstoneResponse(BaseModel):
    """BOM gemstone specification item."""
    id: uuid.UUID
    specification_id: uuid.UUID
    gemstone_type: str
    cut_shape: Optional[str] = None
    stone_count: int = 1
    estimated_carat_weight: Optional[float] = None
    approximate_dimensions_mm: Optional[str] = None
    setting_type: Optional[str] = None
    is_center_stone: bool = False
    origin: str = Field(default="AI_ESTIMATE", description="Data provenance (AI_ESTIMATE, ARTISAN_OVERRIDE, SYSTEM_DERIVED)")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductionStepResponse(BaseModel):
    """Workshop sequential routing stage."""
    id: uuid.UUID
    specification_id: uuid.UUID
    step_number: int
    stage_name: str
    required_skill: str
    required_machine_type: Optional[str] = None
    base_hours: float = 0.0
    per_unit_hours: float = 0.0
    description: Optional[str] = None
    quality_checkpoint: Optional[str] = None
    origin: str = Field(default="AI_ESTIMATE", description="Data provenance (AI_ESTIMATE, ARTISAN_OVERRIDE, SYSTEM_DERIVED)")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductionSpecificationResponse(BaseModel):
    """Complete production specification including child materials, gemstones, and routing."""
    id: uuid.UUID
    user_id: uuid.UUID
    design_id: uuid.UUID
    render_id: uuid.UUID
    version_number: int
    status: str
    category: str
    estimated_rough_metal_weight_grams: Optional[float] = None
    estimated_finished_metal_weight_grams: Optional[float] = None
    total_gemstone_count: int = 0
    estimated_total_bench_hours: Optional[float] = None
    complexity_rating: Optional[str] = None
    fabrication_notes: Optional[str] = None
    ai_confidence_score: Optional[float] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    materials: List[ProductionMaterialResponse] = Field(default_factory=list)
    gemstones: List[ProductionGemstoneResponse] = Field(default_factory=list)
    steps: List[ProductionStepResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
