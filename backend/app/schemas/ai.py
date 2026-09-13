"""JewelMind AI & Gemini Multimodal Design Understanding Schemas.

Defines Pydantic models for structured jewellery design understanding,
user intent preservation, YOLO V2 category grounding, and prompt compilation.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class JewelleryCategory(str, Enum):
    """Supported 8-class taxonomy matching YOLO V2 production detector."""
    RING = "ring"
    EARRING = "earring"
    PENDANT = "pendant"
    NECKLACE = "necklace"
    BRACELET = "bracelet"
    BANGLE = "bangle"
    BROOCH = "brooch"
    OTHER_JEWELLERY = "other_jewellery"


class MaterialSpec(BaseModel):
    """Precious metal and alloy specifications."""
    model_config = ConfigDict(extra="ignore")

    primary_metal: str = Field(
        default="18k yellow gold",
        description="Primary precious metal (e.g. '18k yellow gold', '950 platinum', '925 sterling silver')",
    )
    finish: str = Field(
        default="polished high-shine",
        description="Surface finish (e.g. 'polished high-shine', 'matte brushed', 'satin', 'hammered')",
    )
    accent_metal: Optional[str] = Field(
        default=None,
        description="Secondary or accent metal alloy if bi-color or multi-metal design",
    )
    material_notes: Optional[str] = Field(
        default=None,
        description="Additional metallurgical or craftsmanship details",
    )


class GemstoneItem(BaseModel):
    """Detailed specification for an individual gemstone or stone grouping."""
    model_config = ConfigDict(extra="ignore")

    gemstone_type: str = Field(
        default="diamond",
        description="Gemstone variety (e.g. 'diamond', 'blue sapphire', 'emerald', 'ruby', 'pearl')",
    )
    cut: str = Field(
        default="round brilliant",
        description="Facet cut shape (e.g. 'round brilliant', 'oval', 'cushion', 'emerald cut', 'pear')",
    )
    estimated_count: int = Field(
        default=1,
        ge=0,
        description="Estimated quantity visible in the design",
    )
    setting_type: str = Field(
        default="prong setting",
        description="Mounting/setting mechanism (e.g. '4-prong basket', 'bezel setting', 'micro-pavé', 'channel')",
    )
    color_or_clarity: Optional[str] = Field(
        default=None,
        description="Color hue or optical characteristic (e.g. 'colorless D-F', 'royal velvet blue')",
    )


class GemstoneSpec(BaseModel):
    """Comprehensive gemstone assembly specifications."""
    model_config = ConfigDict(extra="ignore")

    has_gemstones: bool = Field(
        default=True,
        description="Whether gemstones are present in the design",
    )
    primary_gemstone: Optional[GemstoneItem] = Field(
        default=None,
        description="Main center stone or focal gemstone",
    )
    secondary_gemstones: List[GemstoneItem] = Field(
        default_factory=list,
        description="Accent, halo, side, or pavé stones",
    )
    gemstone_details: Optional[str] = Field(
        default=None,
        description="Overall stone layout summary and arrangement description",
    )


class StructuralSpec(BaseModel):
    """Geometric and architectural elements of the jewellery piece."""
    model_config = ConfigDict(extra="ignore")

    silhouette: str = Field(
        default="classic balanced silhouette",
        description="Overall profile contour and geometry",
    )
    symmetry: str = Field(
        default="radial symmetry",
        description="Symmetry type (e.g. 'bilateral symmetry', 'asymmetrical organic', 'radial')",
    )
    setting_style: str = Field(
        default="elevated basket setting",
        description="Head and mounting architecture",
    )
    stone_arrangement: str = Field(
        default="solitaire",
        description="Stone layout (e.g. 'solitaire', 'halo cluster', 'three-stone trinity', 'eternity band', 'pave')",
    )
    band_or_body_structure: str = Field(
        default="tapered comfort-fit band",
        description="Shank, chain, link, or bangle body structure",
    )
    decorative_elements: List[str] = Field(
        default_factory=list,
        description="Artisanal embellishments (e.g. 'milgrain borders', 'vintage filigree', 'engraved gallery')",
    )
    edge_details: Optional[str] = Field(
        default=None,
        description="Edge profile (e.g. 'knife-edge', 'beveled edge', 'rounded dome')",
    )
    surface_details: Optional[str] = Field(
        default=None,
        description="Surface texturing or gallery openwork",
    )
    clasp_or_findings: Optional[str] = Field(
        default=None,
        description="Fastening hardware (e.g. 'lobster claw clasp', 'post and butterfly back', 'box clasp with safety')",
    )


class StructuredDesignUnderstanding(BaseModel):
    """Complete semantic model of a jewellery piece synthesized by Gemini Vision."""
    model_config = ConfigDict(extra="ignore")

    jewellery_category: str = Field(
        ...,
        description="Identified jewellery category (ring, earring, pendant, necklace, bracelet, bangle, brooch, other_jewellery)",
    )
    category_confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Gemini confidence score in category classification",
    )
    design_summary: str = Field(
        ...,
        description="Concise 1-2 sentence artisan description of the jewellery design",
    )
    material: MaterialSpec = Field(
        default_factory=MaterialSpec,
        description="Precious metal alloy and surface finish specifications",
    )
    gemstones: GemstoneSpec = Field(
        default_factory=GemstoneSpec,
        description="Gemstone mounting, cuts, and arrangements",
    )
    structure: StructuralSpec = Field(
        default_factory=StructuralSpec,
        description="Physical construction, symmetry, and architectural layout",
    )
    design_motifs: List[str] = Field(
        default_factory=list,
        description="Aesthetic influences (e.g. 'Art Deco', 'Modern Minimalist', 'Floral Victorian', 'Bridal Solitaire')",
    )
    user_intent_preserved: bool = Field(
        default=True,
        description="Flags whether all explicit user constraints were strictly locked and preserved",
    )
    user_constraints_applied: List[str] = Field(
        default_factory=list,
        description="List of locked attributes directly derived from user input (Tier 1 Precedence)",
    )


class YoloGroundingContext(BaseModel):
    """Grounding evidence provided by JewelMind's local YOLO V2 detector."""
    model_config = ConfigDict(extra="ignore")

    detected_category: str = Field(
        ...,
        description="Class predicted by local YOLO V2 detector",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Detection confidence from YOLO V2",
    )
    bounding_box: Optional[List[float]] = Field(
        default=None,
        description="Normalized coordinates [x1, y1, x2, y2] if available",
    )


class AnalyzeDesignRequest(BaseModel):
    """Payload for analyzing a jewellery design sketch or image."""
    model_config = ConfigDict(extra="ignore")

    image_base64: Optional[str] = Field(
        default=None,
        description="Base64-encoded image string (data URL or raw base64)",
    )
    image_url: Optional[str] = Field(
        default=None,
        description="Publicly accessible image URL or Supabase storage URL",
    )
    user_prompt: Optional[str] = Field(
        default=None,
        description="Optional custom text prompt or artisan notes",
    )
    yolo_category: Optional[str] = Field(
        default=None,
        description="Optional YOLO V2 category classification for grounding",
    )
    yolo_confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Optional YOLO V2 detection confidence",
    )
    source_blueprint_category: Optional[str] = Field(
        default=None,
        description="Category of the source blueprint sketch/image if known",
    )
    user_selected_category: Optional[str] = Field(
        default=None,
        description="Explicit category chosen manually by the user in the UI",
    )


class AnalyzeDesignResponse(BaseModel):
    """Standardized response from the Gemini design understanding pipeline."""
    model_config = ConfigDict(extra="ignore")

    success: bool = Field(
        default=True,
        description="Whether analysis succeeded without fatal error",
    )
    design_understanding: StructuredDesignUnderstanding = Field(
        ...,
        description="Semantic structured design breakdown",
    )
    renderer_prompt: str = Field(
        ...,
        description="Diffusion-optimized positive prompt compiled for ControlNet + SD1.5 rendering pipeline",
    )
    negative_prompt: str = Field(
        ...,
        description="Diffusion-optimized negative prompt preventing common jewellery rendering artifacts",
    )
    original_prompt: Optional[str] = Field(
        default=None,
        description="Raw user-supplied input prompt if provided",
    )
    enhanced_prompt: Optional[str] = Field(
        default=None,
        description="Polished natural language design description for artisan review",
    )
    yolo_category: Optional[str] = Field(
        default=None,
        description="Category grounded by local YOLO V2 detector",
    )
    gemini_category: Optional[str] = Field(
        default=None,
        description="Category visually classified by Gemini Vision if visual analysis was performed",
    )
    source_blueprint_category: Optional[str] = Field(
        default=None,
        description="Category of the source blueprint sketch/image",
    )
    requested_category: Optional[str] = Field(
        default=None,
        description="Category requested explicitly by the user or inferred from intent",
    )
    resolved_category: str = Field(
        ...,
        description="Final consolidated category adhering to precedence rules",
    )
    category_source: str = Field(
        default="default",
        description="Authority source: 'user_prompt', 'user_selected', 'yolo', 'gemini', or 'default'",
    )
    category_conflict: bool = Field(
        default=False,
        description="Flags whether blueprint category and requested category disagree",
    )
    category_conflict_reason: Optional[str] = Field(
        default=None,
        description="Reason for category conflict if detected",
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Notices regarding category disagreements, fallback triggers, or missing attributes",
    )
    fallback_applied: bool = Field(
        default=False,
        description="True if Gemini was unavailable and fallback was utilized",
    )


class EnhancePromptRequest(BaseModel):
    """Payload for standalone natural-language prompt enhancement."""
    model_config = ConfigDict(extra="ignore")

    user_prompt: str = Field(
        ...,
        min_length=1,
        description="Artisan text prompt describing jewellery design",
    )
    image_base64: Optional[str] = Field(
        default=None,
        description="Optional accompanying sketch/image to ground the text enhancement",
    )
    image_url: Optional[str] = Field(
        default=None,
        description="Optional image URL to ground the text enhancement",
    )
    yolo_category: Optional[str] = Field(
        default=None,
        description="Optional YOLO category for grounding",
    )
    yolo_confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Optional YOLO detection confidence",
    )
    source_blueprint_category: Optional[str] = Field(
        default=None,
        description="Category of the source blueprint sketch/image if known",
    )
    user_selected_category: Optional[str] = Field(
        default=None,
        description="Explicit category chosen manually by the user in the UI",
    )


class EnhancePromptResponse(BaseModel):
    """Response containing enhanced prompt and structured design specifications."""
    model_config = ConfigDict(extra="ignore")

    success: bool = Field(
        default=True,
        description="Whether enhancement succeeded",
    )
    original_prompt: str = Field(
        ...,
        description="Original unedited user prompt",
    )
    enhanced_prompt: str = Field(
        ...,
        description="Polished natural-language design description for UI display and editing",
    )
    design_understanding: StructuredDesignUnderstanding = Field(
        ...,
        description="Extracted structured design understanding",
    )
    renderer_prompt: str = Field(
        ...,
        description="Compiled prompt formatted specifically for Stable Diffusion + ControlNet",
    )
    negative_prompt: str = Field(
        ...,
        description="Jewellery-specific negative prompt",
    )
    yolo_category: Optional[str] = Field(
        default=None,
        description="YOLO V2 category grounding if provided",
    )
    gemini_category: Optional[str] = Field(
        default=None,
        description="Category interpreted by Gemini if visual understanding was executed",
    )
    source_blueprint_category: Optional[str] = Field(
        default=None,
        description="Category of the source blueprint sketch/image",
    )
    requested_category: Optional[str] = Field(
        default=None,
        description="Category requested explicitly by the user or inferred from intent",
    )
    resolved_category: str = Field(
        ...,
        description="Final resolved category",
    )
    category_source: str = Field(
        default="default",
        description="Authority source: 'user_prompt', 'user_selected', 'yolo', 'gemini', or 'default'",
    )
    category_conflict: bool = Field(
        default=False,
        description="True if blueprint category and requested category disagree",
    )
    category_conflict_reason: Optional[str] = Field(
        default=None,
        description="Reason for category conflict if detected",
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Diagnostic warnings",
    )
    fallback_applied: bool = Field(
        default=False,
        description="True if local fallback builder was used",
    )
