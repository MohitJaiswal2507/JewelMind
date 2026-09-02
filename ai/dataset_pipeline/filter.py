"""Quality, dimension, corruption, and background validation filter."""

import io
from typing import Tuple, Optional
import numpy as np
from PIL import Image

from ai.dataset_pipeline.schemas import FilterResult


class ImageQualityFilter:
    """Validates downloaded image candidates against strict quality requirements."""

    def __init__(
        self,
        min_width: int = 512,
        min_height: int = 512,
        min_foreground_ratio: float = 0.08,
        max_foreground_ratio: float = 0.95,
    ):
        self.min_width = min_width
        self.min_height = min_height
        self.min_foreground_ratio = min_foreground_ratio
        self.max_foreground_ratio = max_foreground_ratio

    def validate(self, image_bytes: bytes) -> Tuple[FilterResult, Optional[Image.Image]]:
        """Validate raw image bytes. Returns FilterResult and PIL Image if passed."""
        # 1. Corruption Detection & Format Validation
        try:
            img = Image.open(io.BytesIO(image_bytes))
            img.load()  # Force decoding to catch truncation/corruption
        except Exception as err:
            return FilterResult(
                passed=False,
                rejection_reason=f"CORRUPT_OR_UNREADABLE_IMAGE: {str(err)}",
            ), None

        w, h = img.size
        orig_dims = (w, h)

        # 2. Minimum Dimension Constraint
        if w < self.min_width or h < self.min_height:
            return FilterResult(
                passed=False,
                rejection_reason=f"BELOW_MIN_RESOLUTION: {w}x{h} < {self.min_width}x{self.min_height}",
                original_dimensions=orig_dims,
            ), None

        # 3. Channel Normalization
        if img.mode not in ("RGB", "RGBA"):
            try:
                img = img.convert("RGB")
            except Exception as err:
                return FilterResult(
                    passed=False,
                    rejection_reason=f"INVALID_IMAGE_MODE: Cannot convert {img.mode} to RGB: {str(err)}",
                    original_dimensions=orig_dims,
                ), None

        # Convert to numpy array for image-level heuristic checks
        arr = np.array(img.convert("RGB"), dtype=np.float32)

        # 4. Background Sanity & Foreground Estimation
        # Sample four 25x25 corner patches to estimate background properties
        patch_size = min(25, w // 8, h // 8)
        top_left = arr[:patch_size, :patch_size]
        top_right = arr[:patch_size, -patch_size:]
        bottom_left = arr[-patch_size:, :patch_size]
        bottom_right = arr[-patch_size:, -patch_size:]

        corners = np.concatenate([
            top_left.reshape(-1, 3),
            top_right.reshape(-1, 3),
            bottom_left.reshape(-1, 3),
            bottom_right.reshape(-1, 3),
        ], axis=0)

        corner_mean = corners.mean(axis=0)
        corner_std = corners.std()

        # Background brightness (0 to 255)
        bg_brightness = float(corner_mean.mean())

        # If corners have extreme variance (>60 standard deviation), the background is heavily cluttered
        if corner_std > 65.0:
            return FilterResult(
                passed=False,
                rejection_reason=f"EXCESSIVE_BACKGROUND_CLUTTER: Corner variance std={corner_std:.1f} > 65.0",
                original_dimensions=orig_dims,
                background_brightness=bg_brightness,
            ), None

        # 5. Subject Size Sanity Check
        # Compute color distance of each pixel from estimated background color
        color_diff = np.linalg.norm(arr - corner_mean, axis=2)
        # Foreground threshold: distance > 25 indicates jewellery object
        foreground_mask = color_diff > 25.0
        foreground_ratio = float(foreground_mask.sum() / (w * h))

        if foreground_ratio < self.min_foreground_ratio:
            return FilterResult(
                passed=False,
                rejection_reason=f"FOREGROUND_TOO_SMALL: Subject occupies {foreground_ratio*100:.1f}% of canvas (< {self.min_foreground_ratio*100:.1f}%)",
                original_dimensions=orig_dims,
                foreground_ratio=foreground_ratio,
                background_brightness=bg_brightness,
            ), None

        if foreground_ratio > self.max_foreground_ratio:
            return FilterResult(
                passed=False,
                rejection_reason=f"FOREGROUND_TOO_LARGE: Subject occupies {foreground_ratio*100:.1f}% of canvas (> {self.max_foreground_ratio*100:.1f}%)",
                original_dimensions=orig_dims,
                foreground_ratio=foreground_ratio,
                background_brightness=bg_brightness,
            ), None

        return FilterResult(
            passed=True,
            original_dimensions=orig_dims,
            foreground_ratio=foreground_ratio,
            background_brightness=bg_brightness,
        ), img
