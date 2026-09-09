"""JewelMind Generative Rendering V2 Training Infrastructure.

Provides dataset loaders, training pipelines, evaluation suites, and configurations
for fine-tuning multi-category ControlNet models on the JewelMind 8-category taxonomy.
"""

from ai.rendering.training.rendering_v2_dataset import (
    RenderingV2Dataset,
    get_rendering_v2_dataloader,
)

__all__ = [
    "RenderingV2Dataset",
    "get_rendering_v2_dataloader",
]
