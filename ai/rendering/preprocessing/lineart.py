"""LineArt Conditioning Processor for fine jewellery sketches."""

from typing import Tuple, Union
import cv2
import numpy as np
from PIL import Image

from ai.rendering.preprocessing.base import ConditioningProcessor
from ai.rendering.schemas import ConditioningMetadata


class LineArtProcessor(ConditioningProcessor):
    """Generates clean lineart conditioning maps for ControlNet v1.1 LineArt."""

    def __init__(self, target_width: int = 512, target_height: int = 512):
        super().__init__(target_width=target_width, target_height=target_height)

    def process(
        self,
        image: Union[np.ndarray, Image.Image],
        target_width: int = 512,
        target_height: int = 512,
    ) -> Tuple[Image.Image, ConditioningMetadata]:
        """Process sketch into white-on-black lineart conditioning image."""
        orig_np = self.normalize_input(image)
        orig_h, orig_w = orig_np.shape[:2]

        # Step 1: Letterbox resize to target dimensions preserving aspect ratio with white border
        resized, padding = self.letterbox_resize(
            orig_np, target_w=target_width, target_h=target_height, pad_color=255
        )

        # Step 2: Convert to grayscale
        gray = cv2.cvtColor(resized, cv2.COLOR_RGB2GRAY)

        # Step 3: Bilateral smoothing to remove paper grain while preserving sharp jewellery edges
        smoothed = cv2.bilateralFilter(gray, d=5, sigmaColor=50, sigmaSpace=50)

        # Step 4: Detect background tone
        mean_val = float(np.mean(smoothed))
        if mean_val > 128:
            # Typical dark sketch on light paper/canvas -> invert to white lines on black background
            inverted = 255 - smoothed
        else:
            # Already bright strokes on dark background
            inverted = smoothed.copy()

        # Step 5: Normalize and enhance stroke contrast
        p2, p98 = np.percentile(inverted, (2, 98))
        if p98 > p2:
            enhanced = np.clip((inverted - p2) * (255.0 / (p98 - p2)), 0, 255).astype(np.uint8)
        else:
            enhanced = inverted

        # Zero-out low intensity noise floor (light shading / smudges)
        enhanced[enhanced < 30] = 0

        # Calculate edge/line density
        active_pixels = int(np.count_nonzero(enhanced > 30))
        total_pixels = enhanced.size
        density = round(active_pixels / total_pixels, 4)

        # ControlNet expects 3-channel RGB image
        rgb_lineart = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2RGB)
        pil_image = Image.fromarray(rgb_lineart)

        metadata = ConditioningMetadata(
            original_size=[orig_w, orig_h],
            processed_size=[target_width, target_height],
            control_type="lineart",
            padding=list(padding),
            edge_density=density,
        )

        return pil_image, metadata
