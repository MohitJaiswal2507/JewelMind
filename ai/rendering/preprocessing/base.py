"""Base conditioning processor abstraction for sketch preprocessing."""

from abc import ABC, abstractmethod
from typing import Tuple, Union
import cv2
import numpy as np
from PIL import Image, ImageOps

from ai.rendering.schemas import ConditioningMetadata


class ConditioningProcessor(ABC):
    """Abstract base class for ControlNet conditioning processors."""

    def __init__(self, target_width: int = 512, target_height: int = 512):
        self.target_width = target_width
        self.target_height = target_height

    def normalize_input(self, image: Union[np.ndarray, Image.Image]) -> np.ndarray:
        """Validate, handle EXIF orientation, transparency, and return BGR/RGB numpy array."""
        if isinstance(image, Image.Image):
            # Transpose EXIF orientation if present
            image = ImageOps.exif_transpose(image)

            # Handle transparency (RGBA -> RGB on white background)
            if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
                canvas = Image.new("RGB", image.size, (255, 255, 255))
                # Convert palette to RGBA if needed
                rgba_img = image.convert("RGBA")
                canvas.paste(rgba_img, mask=rgba_img.split()[3])
                image = canvas
            elif image.mode != "RGB":
                image = image.convert("RGB")

            # Convert PIL to RGB numpy array
            np_img = np.array(image)
        elif isinstance(image, np.ndarray):
            # Make a copy to avoid mutating original
            np_img = image.copy()
            if np_img.ndim == 2:
                # Grayscale to RGB
                np_img = cv2.cvtColor(np_img, cv2.COLOR_GRAY2RGB)
            elif np_img.ndim == 3:
                if np_img.shape[2] == 4:
                    # RGBA to RGB over white canvas
                    alpha = np_img[:, :, 3] / 255.0
                    rgb = np_img[:, :, :3]
                    white_bg = np.ones_like(rgb, dtype=np.uint8) * 255
                    np_img = (rgb * alpha[:, :, None] + white_bg * (1.0 - alpha[:, :, None])).astype(np.uint8)
                elif np_img.shape[2] == 1:
                    np_img = cv2.cvtColor(np_img, cv2.COLOR_GRAY2RGB)
        else:
            raise ValueError(f"Unsupported image type: {type(image)}. Expected PIL.Image or np.ndarray.")

        if np_img.size == 0 or np_img.shape[0] < 16 or np_img.shape[1] < 16:
            raise ValueError("Input image is invalid or has dimensions smaller than 16x16 pixels.")

        return np_img

    def letterbox_resize(
        self,
        image_rgb: np.ndarray,
        target_w: int,
        target_h: int,
        pad_color: int = 255,
    ) -> Tuple[np.ndarray, Tuple[int, int, int, int]]:
        """Resize image preserving aspect ratio with letterbox padding.

        Returns:
            (padded_image, (pad_top, pad_bottom, pad_left, pad_right))
        """
        h, w = image_rgb.shape[:2]
        scale = min(target_w / w, target_h / h)
        new_w = max(1, int(round(w * scale)))
        new_h = max(1, int(round(h * scale)))

        # High-quality interpolation
        interp = cv2.INTER_AREA if scale < 1.0 else cv2.INTER_LANCZOS4
        resized = cv2.resize(image_rgb, (new_w, new_h), interpolation=interp)

        # Pad to target dimensions
        pad_top = (target_h - new_h) // 2
        pad_bottom = target_h - new_h - pad_top
        pad_left = (target_w - new_w) // 2
        pad_right = target_w - new_w - pad_left

        if resized.ndim == 3:
            padded = cv2.copyMakeBorder(
                resized,
                pad_top,
                pad_bottom,
                pad_left,
                pad_right,
                cv2.BORDER_CONSTANT,
                value=[pad_color, pad_color, pad_color],
            )
        else:
            padded = cv2.copyMakeBorder(
                resized,
                pad_top,
                pad_bottom,
                pad_left,
                pad_right,
                cv2.BORDER_CONSTANT,
                value=pad_color,
            )

        return padded, (pad_top, pad_bottom, pad_left, pad_right)

    @abstractmethod
    def process(
        self,
        image: Union[np.ndarray, Image.Image],
        target_width: int = 512,
        target_height: int = 512,
    ) -> Tuple[Image.Image, ConditioningMetadata]:
        """Generate ControlNet conditioning PIL Image and metadata."""
        pass
