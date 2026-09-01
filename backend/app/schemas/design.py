"""
Pydantic Schemas for Jewellery Design Management
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class DesignCategory(str, Enum):
    RING = "Ring"
    NECKLACE = "Necklace"
    EARRINGS = "Earrings"
    BRACELET = "Bracelet"
    BANGLE = "Bangle"
    PENDANT = "Pendant"
    OTHER = "Other"


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

    model_config = ConfigDict(from_attributes=True)


class DesignListResponse(BaseModel):
    items: List[DesignResponse]
    total: int
    page: int
    page_size: int
    pages: int
