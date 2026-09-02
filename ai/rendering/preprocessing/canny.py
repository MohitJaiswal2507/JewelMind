"""Canny Edge Conditioning Processor for jewellery sketches."""

from typing import Tuple, Union
import cv2
import numpy as np
from PIL import Image

from ai.rendering.preprocessing.base import ConditioningProcessor
from ai.rendering.schemas import ConditioningMetadata


class CannyProcessor(ConditioningProcessor):
    """Generates OpenCV Canny edge conditioning maps for ControlNet v1.1 Canny."""

    def __init__(
        self,
        target_width: int = 512,
        target_height: int = 512,
        low_threshold: int = 100,
        high_threshold: int = 200,
    ):
        super().__init__(target_width=target_width, target_height=target_height)
        self.low_threshold = low_threshold
        self.high_threshold = high_threshold

    def process(
        self,
        image: Union[np.ndarray, Image.Image],
        target_width: int = 512,
        target_height: int = 512,
    ) -> Tuple[Image.Image, ConditioningMetadata]:
        """Process sketch into Canny edge conditioning image."""
        orig_np = self.normalize_input(image)
        orig_h, orig_w = orig_np.shape[:2]

        # Step 1: Letterbox resize to target dimensions with white border
        resized, padding = self.letterbox_resize(
            orig_np, target_w=target_width, target_h=target_height, pad_color=255
        )

        # Step 2: Convert to grayscale
        gray = cv2.cvtColor(resized, cv2.COLOR_RGB2GRAY)

        # Step 3: Subtle Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Step 4: Canny edge detection
        edges = cv2.Canny(blurred, self.low_threshold, self.high_threshold)

        # Calculate edge density
        active_pixels = int(np.count_nonzero(edges))
        total_pixels = edges.size
        density = round(active_pixels / total_pixels, 4)

        # Step 5: Convert single channel to 3-channel RGB
        rgb_edges = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)
        pil_image = Image.fromarray(rgb_edges)

        metadata = ConditioningMetadata(
            original_size=[orig_w, orig_h],
            processed_size=[target_width, target_height],
            control_type="canny",
            padding=list(padding),
            edge_density=density,
        )

        return pil_image, metadata
