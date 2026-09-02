"""Pydantic schemas and contracts for JewelMind AI Rendering subsystem."""

from datetime import datetime, timezone
from typing import List, Literal, Optional
from pydantic import BaseModel, Field, field_validator


class ConditioningMetadata(BaseModel):
    """Metadata generated during sketch preprocessing."""

    original_size: List[int] = Field(..., description="Original [width, height]")
    processed_size: List[int] = Field(..., description="Letterboxed/scaled [width, height]")
    control_type: Literal["lineart", "canny"] = Field(..., description="Conditioning adapter applied")
    padding: List[int] = Field(
        default=[0, 0, 0, 0],
        description="Applied letterbox padding [pad_top, pad_bottom, pad_left, pad_right]",
    )
    edge_density: Optional[float] = Field(
        None,
        description="Fraction of active edge pixels in conditioning map",
    )


class RenderRequest(BaseModel):
    """Rendering parameters validated before inference execution."""

    prompt: Optional[str] = Field(
        default=None,
        max_length=500,
        description="User custom prompt addition (optional)",
    )
    negative_prompt: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Custom negative prompt overrides (optional)",
    )
    material: str = Field(
        default="18k yellow gold",
        description="Base jewellery metal (e.g. 18k yellow gold, platinum, rose gold, white gold)",
    )
    gemstone: str = Field(
        default="round brilliant diamond",
        description="Gemstone type (e.g. diamond, blue sapphire, emerald, ruby, amethyst)",
    )
    control_type: Literal["lineart", "canny"] = Field(
        default="lineart",
        description="Conditioning method for sketch guidance",
    )
    control_strength: float = Field(
        default=0.8,
        ge=0.1,
        le=1.0,
        description="ControlNet conditioning guidance scale",
    )
    steps: int = Field(
        default=20,
        ge=10,
        le=50,
        description="Diffusion denoising iterations",
    )
    guidance_scale: float = Field(
        default=7.5,
        ge=1.0,
        le=15.0,
        description="Classifier-Free Guidance (CFG) scale",
    )
    seed: Optional[int] = Field(
        default=None,
        ge=0,
        le=2147483647,
        description="Random seed for deterministic reproducibility",
    )
    width: int = Field(
        default=512,
        ge=256,
        le=768,
        description="Target image width in pixels",
    )
    height: int = Field(
        default=512,
        ge=256,
        le=768,
        description="Target image height in pixels",
    )

    @field_validator("width", "height")
    @classmethod
    def validate_multiples_of_8(cls, v: int) -> int:
        if v % 8 != 0:
            raise ValueError(f"Resolution dimension ({v}) must be a multiple of 8 for latent diffusion VAE.")
        return v


class RenderResult(BaseModel):
    """Stable JSON output response for completed jewellery renders."""

    model_version: str = Field(..., description="Base diffusion checkpoint identifier")
    controlnet_version: str = Field(..., description="ControlNet checkpoint identifier")
    image_width: int = Field(..., description="Rendered image width in pixels")
    image_height: int = Field(..., description="Rendered image height in pixels")
    seed: int = Field(..., description="Seed utilized for latent noise generation")
    control_type: str = Field(..., description="Conditioning type used (e.g. lineart, canny)")
    control_strength: float = Field(..., description="ControlNet scale applied")
    steps: int = Field(..., description="Denoising steps executed")
    guidance_scale: float = Field(..., description="CFG guidance scale applied")
    inference_time_ms: float = Field(..., ge=0.0, description="Inference execution duration in milliseconds")
    device_used: str = Field(..., description="Hardware device identifier (e.g. cuda:0, cpu)")
    output_url: str = Field(..., description="Public API URL endpoint to retrieve the rendered image")
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC creation timestamp",
    )
    conditioning_metadata: Optional[ConditioningMetadata] = Field(
        None,
        description="Sketch preprocessing and geometry metrics",
    )
