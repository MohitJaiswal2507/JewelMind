"""JewelMind Rendering Final Conditioning Processing Module.

Provides deterministic image preprocessing for ControlNet Target Photos,
LineArt conditioning, and Canny edge maps across the 8 canonical jewellery categories.
"""

import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import cv2
import numpy as np
from PIL import Image, ImageOps


# Default Conditioning Hyperparameters
DEFAULT_TARGET_SIZE = (512, 512)
DEFAULT_CANNY_LOW = 80
DEFAULT_CANNY_HIGH = 180
DEFAULT_CANNY_GAUSSIAN = (5, 5)

DEFAULT_BILATERAL_D = 7
DEFAULT_BILATERAL_SIGMA_COLOR = 50.0
DEFAULT_BILATERAL_SIGMA_SPACE = 50.0
DEFAULT_LINEART_NOISE_FLOOR = 25
DEFAULT_LINEART_CANNY_WEIGHT = 0.5
DEFAULT_LINEART_GRADIENT_WEIGHT = 0.5

MIN_EDGE_DENSITY = 0.002
MAX_EDGE_DENSITY = 0.400


def compute_file_sha256(filepath: Union[str, Path]) -> str:
    """Compute SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def letterbox_target_image(
    img_bgr: np.ndarray,
    target_w: int = 512,
    target_h: int = 512,
    pad_color: int = 255,
) -> Tuple[np.ndarray, Tuple[int, int, int, int]]:
    """Resize and letterbox target image preserving aspect ratio with high-quality interpolation.

    Returns:
        target_padded_rgb: np.ndarray of shape (target_h, target_w, 3) in RGB format.
        padding: Tuple (pad_top, pad_bottom, pad_left, pad_right)
    """
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    h, w = img_rgb.shape[:2]
    scale = min(target_w / w, target_h / h)
    nw = max(1, int(round(w * scale)))
    nh = max(1, int(round(h * scale)))

    interp = cv2.INTER_AREA if scale < 1.0 else cv2.INTER_LANCZOS4
    resized = cv2.resize(img_rgb, (nw, nh), interpolation=interp)

    pad_top = (target_h - nh) // 2
    pad_bottom = target_h - nh - pad_top
    pad_left = (target_w - nw) // 2
    pad_right = target_w - nw - pad_left

    target_padded = cv2.copyMakeBorder(
        resized,
        pad_top,
        pad_bottom,
        pad_left,
        pad_right,
        cv2.BORDER_CONSTANT,
        value=[pad_color, pad_color, pad_color],
    )
    return target_padded, (pad_top, pad_bottom, pad_left, pad_right)


def extract_lineart_map(
    target_rgb: np.ndarray,
    bilateral_d: int = DEFAULT_BILATERAL_D,
    bilateral_sigma: float = DEFAULT_BILATERAL_SIGMA_COLOR,
    noise_floor: int = DEFAULT_LINEART_NOISE_FLOOR,
    canny_weight: float = DEFAULT_LINEART_CANNY_WEIGHT,
    gradient_weight: float = DEFAULT_LINEART_GRADIENT_WEIGHT,
    canny_low: int = DEFAULT_CANNY_LOW,
    canny_high: int = DEFAULT_CANNY_HIGH,
) -> Tuple[np.ndarray, float]:
    """Derive clean structural LineArt conditioning map (white lines on black canvas).

    Returns:
        lineart_rgb: np.ndarray of shape (H, W, 3) in RGB.
        edge_density: float in [0.0, 1.0] representing active edge fraction.
    """
    gray = cv2.cvtColor(target_rgb, cv2.COLOR_RGB2GRAY)

    # 1. Bilateral smoothing suppresses paper grain/specular micro-noise while retaining sharp contours
    bilat = cv2.bilateralFilter(
        gray,
        d=bilateral_d,
        sigmaColor=bilateral_sigma,
        sigmaSpace=bilateral_sigma,
    )

    # 2. Morphological gradient for jewellery silhouette & metal boundaries
    grad = cv2.morphologyEx(bilat, cv2.MORPH_GRADIENT, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
    grad_cleaned = np.where(grad > 20, grad, 0)

    # 3. Dynamic contrast enhancement on active contours
    pos = grad_cleaned[grad_cleaned > 0]
    if len(pos) > 0:
        p2, p98 = np.percentile(pos, (2, 98))
        if p98 > p2:
            grad_enh = np.clip((grad_cleaned.astype(float) - p2) * (255.0 / (p98 - p2)), 0, 255).astype(np.uint8)
        else:
            grad_enh = grad_cleaned
    else:
        grad_enh = grad_cleaned

    # 4. Fine setting/gemstone contours via Canny
    blurred = cv2.GaussianBlur(gray, DEFAULT_CANNY_GAUSSIAN, 0)
    canny = cv2.Canny(blurred, canny_low, canny_high)

    # 5. Composite LineArt
    lineart = cv2.addWeighted(canny, canny_weight, grad_enh, gradient_weight, 0)
    lineart[lineart < noise_floor] = 0

    lineart_rgb = cv2.cvtColor(lineart, cv2.COLOR_GRAY2RGB)
    active_pixels = int(np.count_nonzero(lineart > noise_floor))
    density = round(active_pixels / lineart.size, 4)

    return lineart_rgb, density


def extract_canny_map(
    target_rgb: np.ndarray,
    canny_low: int = DEFAULT_CANNY_LOW,
    canny_high: int = DEFAULT_CANNY_HIGH,
    gaussian_kernel: Tuple[int, int] = DEFAULT_CANNY_GAUSSIAN,
) -> Tuple[np.ndarray, float]:
    """Derive standard Canny edge conditioning map (white edges on black canvas).

    Returns:
        canny_rgb: np.ndarray of shape (H, W, 3) in RGB.
        edge_density: float in [0.0, 1.0] representing active edge fraction.
    """
    gray = cv2.cvtColor(target_rgb, cv2.COLOR_RGB2GRAY)
    blurred = cv2.GaussianBlur(gray, gaussian_kernel, 0)
    canny = cv2.Canny(blurred, canny_low, canny_high)

    canny_rgb = cv2.cvtColor(canny, cv2.COLOR_GRAY2RGB)
    active_pixels = int(np.count_nonzero(canny))
    density = round(active_pixels / canny.size, 4)

    return canny_rgb, density


def process_image_to_conditioning_trio(
    source_img_path: Path,
    out_target_path: Path,
    out_lineart_path: Path,
    out_canny_path: Path,
    target_size: Tuple[int, int] = DEFAULT_TARGET_SIZE,
    canny_low: int = DEFAULT_CANNY_LOW,
    canny_high: int = DEFAULT_CANNY_HIGH,
    bilateral_d: int = DEFAULT_BILATERAL_D,
    bilateral_sigma: float = DEFAULT_BILATERAL_SIGMA_COLOR,
    noise_floor: int = DEFAULT_LINEART_NOISE_FLOOR,
) -> Tuple[float, float, str, str]:
    """Process a single image and save Target, LineArt, and Canny files.

    Returns:
        (lineart_density, canny_density, source_sha256, target_sha256)
    """
    img_bgr = cv2.imread(str(source_img_path))
    if img_bgr is None:
        raise IOError(f"Could not read source image at {source_img_path}")

    target_rgb, _ = letterbox_target_image(img_bgr, target_size[0], target_size[1])
    lineart_rgb, l_dens = extract_lineart_map(
        target_rgb,
        bilateral_d=bilateral_d,
        bilateral_sigma=bilateral_sigma,
        noise_floor=noise_floor,
        canny_low=canny_low,
        canny_high=canny_high,
    )
    canny_rgb, c_dens = extract_canny_map(
        target_rgb,
        canny_low=canny_low,
        canny_high=canny_high,
    )

    out_target_path.parent.mkdir(parents=True, exist_ok=True)
    out_lineart_path.parent.mkdir(parents=True, exist_ok=True)
    out_canny_path.parent.mkdir(parents=True, exist_ok=True)

    cv2.imwrite(str(out_target_path), cv2.cvtColor(target_rgb, cv2.COLOR_RGB2BGR))
    cv2.imwrite(str(out_lineart_path), cv2.cvtColor(lineart_rgb, cv2.COLOR_RGB2BGR))
    cv2.imwrite(str(out_canny_path), cv2.cvtColor(canny_rgb, cv2.COLOR_RGB2BGR))

    src_sha = compute_file_sha256(source_img_path)
    tgt_sha = compute_file_sha256(out_target_path)

    return l_dens, c_dens, src_sha, tgt_sha
