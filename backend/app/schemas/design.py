"""
Pydantic Schemas for Jewellery Design Management
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field, field_validator


class DesignCategory(str, Enum):
    RING = "Ring"
    NECKLACE = "Necklace"
    EARRINGS = "Earrings"
    BRACELET = "Bracelet"
    BANGLE = "Bangle"
    PENDANT = "Pendant"
    BROOCH = "Brooch"
    OTHER = "Other"


# Authoritative Taxonomy Mappings between Backend DesignCategory and AI Pipeline Category
BACKEND_TO_AI_CATEGORY_MAP = {
    DesignCategory.RING: "ring",
    DesignCategory.EARRINGS: "earring",
    DesignCategory.PENDANT: "pendant",
    DesignCategory.NECKLACE: "necklace",
    DesignCategory.BRACELET: "bracelet",
    DesignCategory.BANGLE: "bangle",
    DesignCategory.BROOCH: "brooch",
    DesignCategory.OTHER: "other_jewellery",
}

AI_TO_BACKEND_CATEGORY_MAP = {
    "ring": DesignCategory.RING,
    "earring": DesignCategory.EARRINGS,
    "earrings": DesignCategory.EARRINGS,
    "pendant": DesignCategory.PENDANT,
    "necklace": DesignCategory.NECKLACE,
    "bracelet": DesignCategory.BRACELET,
    "bangle": DesignCategory.BANGLE,
    "brooch": DesignCategory.BROOCH,
    "other_jewellery": DesignCategory.OTHER,
    "other": DesignCategory.OTHER,
}


def to_ai_category(category: Optional[Union[str, DesignCategory]]) -> Optional[str]:
    """Convert a backend or human-facing category to canonical AI rendering category."""
    if category is None:
        return None
    if isinstance(category, DesignCategory):
        return BACKEND_TO_AI_CATEGORY_MAP.get(category, "other_jewellery")

    cleaned = str(category).strip().lower()
    return AI_TO_BACKEND_CATEGORY_MAP.get(cleaned, None) and BACKEND_TO_AI_CATEGORY_MAP.get(AI_TO_BACKEND_CATEGORY_MAP[cleaned], "other_jewellery")


def from_ai_category(category: Optional[str]) -> Optional[DesignCategory]:
    """Convert an AI category or raw string to canonical backend DesignCategory."""
    if category is None:
        return None
    cleaned = str(category).strip().lower()
    return AI_TO_BACKEND_CATEGORY_MAP.get(cleaned, None)


class DesignStatus(str, Enum):
    DRAFT = "draft"
    READY = "ready"
    RENDERING = "rendering"
    RENDERED = "rendered"
    ARCHIVED = "archived"


class DesignBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Name of the jewellery design")
    description: Optional[str] = Field(None, max_length=2000, description="Detailed design notes or description")
    category: DesignCategory = Field(..., description="Jewellery category")
    status: DesignStatus = Field(default=DesignStatus.DRAFT, description="Current lifecycle state")
    sketch_image_url: Optional[str] = Field(None, max_length=1024, description="URL or reference to original sketch")
    rendered_image_url: Optional[str] = Field(None, max_length=1024, description="URL or reference to AI rendered visual")
    ai_prompt: Optional[str] = Field(None, description="Prompt parameter used for AI generative workflows")

    @field_validator("name")
    @classmethod
    def validate_name_not_empty(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Design name cannot be blank or whitespace only.")
        return trimmed

    @field_validator("category", mode="before")
    @classmethod
    def normalize_category(cls, v: Union[str, DesignCategory]) -> DesignCategory:
        if isinstance(v, DesignCategory):
            return v
        if isinstance(v, str):
            res = from_ai_category(v)
            if res:
                return res
        raise ValueError(f"Unsupported jewellery category: '{v}'")


class DesignCreate(DesignBase):
    pass


class DesignUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    category: Optional[DesignCategory] = None
    status: Optional[DesignStatus] = None
    sketch_image_url: Optional[str] = Field(None, max_length=1024)
    rendered_image_url: Optional[str] = Field(None, max_length=1024)
    ai_prompt: Optional[str] = None

    @field_validator("name")
    @classmethod
    def validate_name_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            trimmed = v.strip()
            if not trimmed:
                raise ValueError("Design name cannot be blank or whitespace only.")
            return trimmed
        return v

    @field_validator("category", mode="before")
    @classmethod
    def normalize_category(cls, v: Optional[Union[str, DesignCategory]]) -> Optional[DesignCategory]:
        if v is None:
            return None
        if isinstance(v, DesignCategory):
            return v
        if isinstance(v, str):
            res = from_ai_category(v)
            if res:
                return res
        raise ValueError(f"Unsupported jewellery category: '{v}'")


class DesignRenderResponse(BaseModel):
    id: uuid.UUID
    design_id: uuid.UUID
    user_id: uuid.UUID
    version_number: int
    parent_render_id: Optional[uuid.UUID] = None
    source_asset_id: Optional[uuid.UUID] = None
    render_mode: str
    prompt: str
    enhanced_prompt: Optional[str] = None
    structured_state: Optional[dict] = None
    image_url: str
    thumbnail_url: Optional[str] = None
    control_type: str = "none"
    control_strength: float = 0.0
    seed: Optional[int] = None
    is_approved_for_production: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DesignRenderListResponse(BaseModel):
    renders: List[DesignRenderResponse]
    total: int


class DesignResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    description: Optional[str]
    category: DesignCategory
    status: DesignStatus
    sketch_image_url: Optional[str]
    rendered_image_url: Optional[str]
    ai_prompt: Optional[str]
    created_at: datetime
    updated_at: datetime
    renders: List[DesignRenderResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class DesignListResponse(BaseModel):
    items: List[DesignResponse]
    total: int
    page: int
    page_size: int
    pages: int


