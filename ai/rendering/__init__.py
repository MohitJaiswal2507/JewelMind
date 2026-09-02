"""JewelMind Generative AI Jewellery Rendering Module."""

from ai.rendering.config import RenderingConfig, rendering_config
from ai.rendering.schemas import ConditioningMetadata, RenderRequest, RenderResult

try:
    from ai.rendering.model_manager import DiffusionModelManager, get_model_manager
    from ai.rendering.pipeline import JewelleryRenderingPipeline, RenderingOutOfMemoryError
    from ai.rendering.preprocessing import get_conditioning_processor
except ImportError:
    DiffusionModelManager = None
    get_model_manager = None
    JewelleryRenderingPipeline = None
    RenderingOutOfMemoryError = RuntimeError
    get_conditioning_processor = None

__all__ = [
    "RenderingConfig",
    "rendering_config",
    "ConditioningMetadata",
    "RenderRequest",
    "RenderResult",
    "DiffusionModelManager",
    "get_model_manager",
    "JewelleryRenderingPipeline",
    "RenderingOutOfMemoryError",
    "get_conditioning_processor",
]
