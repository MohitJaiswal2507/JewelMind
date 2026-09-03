"""Tests for Structural Conditioning Preprocessing Pipeline."""

from pathlib import Path
import numpy as np
from PIL import Image
import pytest
import torch

from ai.rendering.preprocessing.structural import StructuralConditioningProcessor
from ai.rendering.preprocessing import get_conditioning_processor


@pytest.fixture
def dummy_jewellery_image() -> Image.Image:
    """Creates a synthetic jewellery-like test image with solid shape, facets, and dark background."""
    img_np = np.zeros((400, 600, 3), dtype=np.uint8)
    # Background: dark studio tone
    img_np[:] = [30, 30, 35]
    # Draw ring shank (ellipse)
    import cv2
    cv2.ellipse(img_np, (300, 250), (120, 90), 0, 0, 360, (212, 175, 55), 18)
    # Draw ring head / diamond (polygon)
    pts = np.array([[300, 120], [330, 160], [300, 200], [270, 160]], dtype=np.int32)
    cv2.fillPoly(img_np, [pts], (240, 240, 255))
    cv2.polylines(img_np, [pts], True, (255, 255, 255), 2)
    return Image.fromarray(img_np)


def test_structural_processor_output_dimensions_and_aspect_ratio(dummy_jewellery_image: Image.Image):
    """Verifies that processor outputs exact target dimensions and preserves aspect ratio via letterboxing."""
    processor = StructuralConditioningProcessor(
        target_width=512,
        target_height=512,
        use_neural_lineart=False,  # Test algorithmic path for fast deterministic CPU unit test
    )

    out_pil, meta = processor.process(dummy_jewellery_image)

    assert out_pil.size == (512, 512)
    assert meta.processed_size == [512, 512]
    assert meta.original_size == [600, 400]
    assert meta.control_type == "lineart"
    assert len(meta.padding) == 4
    # Padding top/bottom should be non-zero for 600x400 -> 512x512
    pad_top, pad_bottom, pad_left, pad_right = meta.padding
    assert pad_top > 0 or pad_left > 0


def test_structural_processor_deterministic_output(dummy_jewellery_image: Image.Image):
    """Verifies that processing the same image twice produces bit-exact identical output."""
    processor = StructuralConditioningProcessor(target_width=512, target_height=512, use_neural_lineart=False)

    out1, meta1 = processor.process(dummy_jewellery_image)
    out2, meta2 = processor.process(dummy_jewellery_image)

    np1 = np.array(out1)
    np2 = np.array(out2)

    assert np.array_equal(np1, np2)
    assert meta1.edge_density == meta2.edge_density


def test_structural_processor_invalid_image_handling():
    """Verifies graceful exception handling for invalid/tiny images."""
    processor = StructuralConditioningProcessor(target_width=512, target_height=512, use_neural_lineart=False)

    tiny_img = np.zeros((8, 8, 3), dtype=np.uint8)
    with pytest.raises(ValueError, match="smaller than 16x16"):
        processor.process(tiny_img)


def test_factory_registration():
    """Verifies that get_conditioning_processor resolves 'structural' properly."""
    proc = get_conditioning_processor("structural", target_width=512, target_height=512)
    assert isinstance(proc, StructuralConditioningProcessor)


def test_empty_canvas_edge_density():
    """Verifies handling of completely blank/solid image."""
    blank = Image.new("RGB", (200, 200), (0, 0, 0))
    processor = StructuralConditioningProcessor(target_width=512, target_height=512, use_neural_lineart=False)
    out_pil, meta = processor.process(blank)

    assert out_pil.size == (512, 512)
    assert meta.edge_density == 0.0


@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA required for neural LineartDetector verification")
def test_neural_lineart_on_eval_image():
    """Verifies neural LineartDetector execution on actual candidate image if CUDA and dataset available."""
    cand_path = Path("datasets/appearance_lora/images/CAND_001.jpg")
    if not cand_path.exists():
        pytest.skip("CAND_001.jpg not present.")

    processor = StructuralConditioningProcessor(target_width=512, target_height=512, device="cuda", use_neural_lineart=True)
    img = Image.open(cand_path)
    out_pil, meta = processor.process(img)

    assert out_pil.size == (512, 512)
    assert meta.edge_density > 0.01
    assert meta.control_type == "lineart"
