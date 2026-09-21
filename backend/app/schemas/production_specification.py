"""
Production Specification API Schemas
Defines request and response schemas for Production Specification generation,
retrieval, and nested BOM line items.
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
