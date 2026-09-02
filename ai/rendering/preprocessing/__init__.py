"""JewelMind Sketch Preprocessing Module."""

from typing import Union
from ai.rendering.preprocessing.base import ConditioningProcessor
from ai.rendering.preprocessing.lineart import LineArtProcessor
from ai.rendering.preprocessing.canny import CannyProcessor


def get_conditioning_processor(
    control_type: str,
    target_width: int = 512,
    target_height: int = 512,
) -> ConditioningProcessor:
    """Factory function to instantiate the requested conditioning processor."""
    normalized = control_type.strip().lower()
    if normalized == "lineart":
        return LineArtProcessor(target_width=target_width, target_height=target_height)
    elif normalized == "canny":
        return CannyProcessor(target_width=target_width, target_height=target_height)
    else:
        raise ValueError(
            f"Unsupported conditioning control type: '{control_type}'. Supported options: 'lineart', 'canny'."
        )


__all__ = [
    "ConditioningProcessor",
    "LineArtProcessor",
    "CannyProcessor",
    "get_conditioning_processor",
]
