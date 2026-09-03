"""Structural Conditioning Processor for paired Sketch/Photo ControlNet datasets.

Combines bilateral surface noise suppression, neural Lineart extraction, and 
contrast normalization to produce clean, high-fidelity structural line maps
from fine jewellery photography.
"""

from pathlib import Path
from typing import Optional, Tuple, Union
import cv2
import numpy as np
from PIL import Image, ImageOps

from ai.rendering.preprocessing.base import ConditioningProcessor
from ai.rendering.schemas import ConditioningMetadata


class StructuralConditioningProcessor(ConditioningProcessor):
    """Generates clean structural lineart conditioning maps for ControlNet LineArt from jewellery photos."""

    def __init__(
        self,
        target_width: int = 512,
        target_height: int = 512,
        device: str = "cuda",
        noise_floor: int = 35,
        bilateral_d: int = 9,
        bilateral_sigma: float = 75.0,
        coarse: bool = False,
        use_neural_lineart: bool = True,
    ):
        super().__init__(target_width=target_width, target_height=target_height)
        self.device = device
        self.noise_floor = noise_floor
        self.bilateral_d = bilateral_d
        self.bilateral_sigma = bilateral_sigma
        self.coarse = coarse
        self.use_neural_lineart = use_neural_lineart
        self._detector = None

    def _get_detector(self):
        """Lazy-load LineartDetector on configured device."""
        if self._detector is None and self.use_neural_lineart:
            try:
                from controlnet_aux import LineartDetector
                import torch

                dev = self.device
                if dev.startswith("cuda") and not torch.cuda.is_available():
                    dev = "cpu"

                self._detector = LineartDetector.from_pretrained("lllyasviel/Annotators").to(dev)
            except Exception as e:
                print(f"[WARN] Could not initialize LineartDetector ({e}). Falling back to algorithmic lineart.")
                self.use_neural_lineart = False
        return self._detector

    def process(
        self,
        image: Union[np.ndarray, Image.Image],
        target_width: Optional[int] = None,
        target_height: Optional[int] = None,
    ) -> Tuple[Image.Image, ConditioningMetadata]:
        """Process input image into clean structural conditioning lineart."""
        tw = target_width or self.target_width
        th = target_height or self.target_height

        orig_np = self.normalize_input(image)
        orig_h, orig_w = orig_np.shape[:2]

        # Step 1: Letterbox resize preserving aspect ratio with black border
        resized, padding = self.letterbox_resize(
            orig_np, target_w=tw, target_h=th, pad_color=0
        )

        # Step 2: Bilateral filtering to smooth specular noise/micro-textures
        bilat = cv2.bilateralFilter(
            resized,
            d=self.bilateral_d,
            sigmaColor=self.bilateral_sigma,
            sigmaSpace=self.bilateral_sigma,
        )

        # Step 3: Extract lineart
        detector = self._get_detector()
        if self.use_neural_lineart and detector is not None:
            pil_bilat = Image.fromarray(bilat)
            raw_lineart_pil = detector(
                pil_bilat,
                coarse=self.coarse,
                detect_resolution=max(tw, th),
                image_resolution=max(tw, th),
            )
            lineart_np = np.array(raw_lineart_pil)
            if lineart_np.ndim == 3:
                lineart_gray = cv2.cvtColor(lineart_np, cv2.COLOR_RGB2GRAY)
            else:
                lineart_gray = lineart_np
        else:
            # Algorithmic fallback: adaptive Canny + inverted gradient
            gray = cv2.cvtColor(bilat, cv2.COLOR_RGB2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            canny = cv2.Canny(blurred, 80, 180)
            lineart_gray = canny

        # Step 4: Suppress low-intensity noise floor (reflections, smudges)
        cleaned = lineart_gray.copy()
        cleaned[cleaned < self.noise_floor] = 0

        # Step 5: Normalize contrast
        positive_pixels = cleaned[cleaned > 0]
        if len(positive_pixels) > 0:
            p2, p98 = np.percentile(positive_pixels, (2, 98))
            if p98 > p2:
                enhanced = np.clip((cleaned.astype(float) - p2) * (255.0 / (p98 - p2)), 0, 255).astype(np.uint8)
            else:
                enhanced = cleaned
        else:
            enhanced = cleaned

        # Step 6: Edge density metric
        active_pixels = int(np.count_nonzero(enhanced > 30))
        total_pixels = enhanced.size
        density = round(active_pixels / total_pixels, 4) if total_pixels > 0 else 0.0

        # Convert to 3-channel RGB PIL Image
        rgb_lineart = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2RGB)
        pil_result = Image.fromarray(rgb_lineart)

        metadata = ConditioningMetadata(
            original_size=[orig_w, orig_h],
            processed_size=[tw, th],
            control_type="lineart",
            padding=list(padding),
            edge_density=density,
        )

        return pil_result, metadata
