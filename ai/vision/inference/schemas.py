"""JewelMind Component Detection Output Schemas.

Defines the stable JSON output contract for jewellery component detection and
instance segmentation across backend APIs, CAD workflows, and design canvas.
"""

from typing import List, Optional, Tuple
from pydantic import BaseModel, Field


class ComponentDetection(BaseModel):
    """Single detected jewellery component with bounding box and segmentation mask."""

    class_id: int = Field(..., description="Integer class ID from taxonomy (0-6)")
    class_name: str = Field(..., description="Semantic name (e.g. gemstone, ring_shank)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence score")
    bbox: List[float] = Field(
        ...,
        min_length=4,
        max_length=4,
        description="Bounding box [x1, y1, x2, y2] in pixel coordinates",
    )
    mask: List[List[float]] = Field(
        default_factory=list,
        description="Polygon contour vertices [[x1, y1], [x2, y2], ...] in pixel coordinates",
    )
    normalized_mask: Optional[List[List[float]]] = Field(
        default_factory=list,
        description="Polygon contour vertices normalized to [0, 1] relative to image dimensions",
    )
    area: Optional[float] = Field(None, description="Contour pixel area")


class DetectionResult(BaseModel):
    """Overall detection response containing all detected components for an image."""

    model_version: str = Field(..., description="Model identifier and checkpoint version")
    image_size: List[int] = Field(
        ...,
        min_length=2,
        max_length=2,
        description="Source image dimensions [width, height] in pixels",
    )
    inference_time_ms: float = Field(..., ge=0.0, description="Model inference latency in milliseconds")
    device_used: str = Field(..., description="Hardware device used for inference (e.g. cuda:0, cpu)")
    detections: List[ComponentDetection] = Field(
        default_factory=list,
        description="List of detected jewellery components",
    )
    total_detections: int = Field(..., description="Count of detected components")
