"""Unit tests for AI Generative Rendering Module: preprocessing, schemas, and pipeline."""

import numpy as np
import pytest
from PIL import Image

from ai.rendering.config import RenderingConfig
from ai.rendering.preprocessing import get_conditioning_processor
from ai.rendering.preprocessing.base import ConditioningProcessor
from ai.rendering.preprocessing.canny import CannyProcessor
from ai.rendering.preprocessing.lineart import LineArtProcessor
from ai.rendering.prompts import build_jewellery_prompt, build_negative_prompt
from ai.rendering.schemas import ConditioningMetadata, RenderRequest, RenderResult


def test_rendering_config_defaults():
    """Verify default rendering configuration parameters."""
    cfg = RenderingConfig()
    assert cfg.default_width == 512
    assert cfg.default_height == 512
    assert cfg.batch_size == 1
    assert cfg.use_fp16 is True
    assert cfg.enable_attention_slicing is True
    assert cfg.default_control_strength == 1.0
    assert "stable-diffusion" in cfg.base_model_id
    assert "rendering_v2_controlnet" in cfg.lineart_controlnet_id.lower() or "controlnet" in cfg.lineart_controlnet_id.lower()


def test_controlnet_model_resolution_env_override(monkeypatch):
    """Verify that JEWELMIND_RENDERING_CONTROLNET_PATH and legacy env vars override default resolution."""
    monkeypatch.setenv("JEWELMIND_RENDERING_CONTROLNET_PATH", "custom/jewellery/rendering_v2_final")
    cfg = RenderingConfig()
    assert cfg.lineart_controlnet_id == "custom/jewellery/rendering_v2_final"

    monkeypatch.delenv("JEWELMIND_RENDERING_CONTROLNET_PATH", raising=False)
    monkeypatch.setenv("JEWELMIND_CONTROLNET_MODEL_PATH", "custom/jewellery/controlnet")
    cfg2 = RenderingConfig()
    assert cfg2.lineart_controlnet_id == "custom/jewellery/controlnet"


def test_production_model_resolution_success(monkeypatch):
    """Verify production resolution resolves directly to approved 1000-step final model."""
    monkeypatch.delenv("JEWELMIND_RENDERING_CONTROLNET_PATH", raising=False)
    monkeypatch.delenv("JEWELMIND_CONTROLNET_MODEL_PATH", raising=False)
    monkeypatch.delenv("JEWELMIND_CONTROLNET_LINEART", raising=False)
    from ai.rendering.config import get_default_lineart_controlnet
    res = get_default_lineart_controlnet()
    assert "rendering_v2_controlnet" in res.lower() or "controlnet" in res.lower()


def test_production_model_strict_resolution_no_silent_fallback(monkeypatch, tmp_path):
    """Verify that if the final model is missing, production inference fails loudly without silent fallback."""
    monkeypatch.delenv("JEWELMIND_RENDERING_CONTROLNET_PATH", raising=False)
    monkeypatch.delenv("JEWELMIND_CONTROLNET_MODEL_PATH", raising=False)
    monkeypatch.delenv("JEWELMIND_CONTROLNET_LINEART", raising=False)
    monkeypatch.delenv("JEWELMIND_ALLOW_MODEL_FALLBACK", raising=False)

    import ai.rendering.config as cfg_module
    # Point final model path to a non-existent path
    monkeypatch.setattr(cfg_module, "DEFAULT_PRODUCTION_FINAL_CONTROLNET", str(tmp_path / "non_existent_final"))

    # Must raise FileNotFoundError with actionable message, NOT silently return 300-step or pretrained baseline
    with pytest.raises(FileNotFoundError, match="Silent fallback to obsolete 300-step model.*is strictly disabled"):
        cfg_module.get_default_lineart_controlnet()


def test_deliberate_dev_fallback_mechanism(monkeypatch, tmp_path):
    """Verify deliberate, documented development fallback when explicitly requested."""
    monkeypatch.delenv("JEWELMIND_RENDERING_CONTROLNET_PATH", raising=False)
    monkeypatch.delenv("JEWELMIND_CONTROLNET_MODEL_PATH", raising=False)
    monkeypatch.delenv("JEWELMIND_CONTROLNET_LINEART", raising=False)

    import ai.rendering.config as cfg_module
    # Point final model path to a non-existent path
    monkeypatch.setattr(cfg_module, "DEFAULT_PRODUCTION_FINAL_CONTROLNET", str(tmp_path / "non_existent_final"))

    # 1. Fallback via function argument
    res1 = cfg_module.get_default_lineart_controlnet(allow_fallback=True)
    assert "controlnet" in res1.lower() or "lineart" in res1.lower()

    # 2. Fallback via environment variable
    monkeypatch.setenv("JEWELMIND_ALLOW_MODEL_FALLBACK", "1")
    res2 = cfg_module.get_default_lineart_controlnet()
    assert "controlnet" in res2.lower() or "lineart" in res2.lower()


def test_render_request_validation():
    """Verify bounds and validation rules on RenderRequest."""
    req_default = RenderRequest()
    assert req_default.control_strength == 1.0

    req = RenderRequest(
        width=512,
        height=512,
        steps=25,
        control_strength=0.85,
        seed=12345,
    )
    assert req.width == 512
    assert req.steps == 25
    assert req.control_strength == 0.85
    assert req.seed == 12345

    # Invalid width (not multiple of 8)
    with pytest.raises(ValueError, match="multiple of 8"):
        RenderRequest(width=513)

    # Invalid steps (< 10)
    with pytest.raises(ValueError):
        RenderRequest(steps=5)

    # Invalid control strength (> 1.0)
    with pytest.raises(ValueError):
        RenderRequest(control_strength=1.5)


def test_render_result_schema_sanitization():
    """Verify RenderResult structure and path safety."""
    res = RenderResult(
        model_version="sd15",
        controlnet_version="lineart_v11",
        image_width=512,
        image_height=512,
        seed=999,
        control_type="lineart",
        control_strength=0.8,
        steps=20,
        guidance_scale=7.5,
        inference_time_ms=3100.0,
        device_used="cuda:0",
        output_url="/api/v1/ai/render/outputs/render_abc.png",
    )
    serialized = res.model_dump_json()
    assert "C:\\" not in serialized
    assert "/Users/" not in serialized
    assert res.image_width == 512


def test_preprocessing_transparency_handling():
    """Verify RGBA sketch with transparent background composites over pure white."""
    processor = LineArtProcessor(target_width=512, target_height=512)

    # Create RGBA image: black circle on transparent background
    rgba = Image.new("RGBA", (200, 200), (0, 0, 0, 0))
    # Draw dark rectangle in center
    for x in range(80, 120):
        for y in range(80, 120):
            rgba.putpixel((x, y), (20, 20, 20, 255))

    normalized = processor.normalize_input(rgba)
    assert normalized.shape == (200, 200, 3)
    # The transparent corner should now be white (255, 255, 255)
    assert np.all(normalized[10, 10] == [255, 255, 255])
    # The drawn center should be dark
    assert np.all(normalized[100, 100] == [20, 20, 20])


def test_preprocessing_letterbox_aspect_ratio():
    """Verify non-square sketches are letterboxed without distortion."""
    processor = LineArtProcessor(target_width=512, target_height=512)

    # 400 wide x 200 high sketch (aspect ratio 2:1)
    wide_img = np.full((200, 400, 3), 255, dtype=np.uint8)
    # Draw vertical line in center
    wide_img[:, 200] = [0, 0, 0]

    cond_img, meta = processor.process(wide_img, target_width=512, target_height=512)
    assert isinstance(cond_img, Image.Image)
    assert cond_img.size == (512, 512)
    assert meta.original_size == [400, 200]
    assert meta.processed_size == [512, 512]
    # In 2:1 aspect ratio, top and bottom must be padded
    assert meta.padding[0] > 0 or meta.padding[1] > 0


def test_canny_processor_edge_detection():
    """Verify CannyProcessor extracts edges and computes density."""
    canny = CannyProcessor(target_width=512, target_height=512)

    # Draw white square on dark background
    canvas = np.zeros((256, 256, 3), dtype=np.uint8)
    canvas[64:192, 64:192] = 255

    cond_img, meta = canny.process(canvas, target_width=512, target_height=512)
    assert cond_img.size == (512, 512)
    assert meta.control_type == "canny"
    assert meta.edge_density > 0.0


def test_prompt_builder():
    """Verify prompt and negative prompt composition."""
    prompt = build_jewellery_prompt(
        material="18k yellow gold",
        gemstone="round brilliant diamond",
        user_prompt="Victorian filigree solitaire engagement ring",
    )
    assert "Victorian filigree" in prompt
    assert "18k yellow gold" in prompt
    assert "diamond" in prompt
    assert "studio lighting" in prompt

    neg_prompt = build_negative_prompt(user_negative_prompt="low contrast")
    assert "malformed jewellery" in neg_prompt
    assert "deformed ring" in neg_prompt
    assert "low contrast" in neg_prompt


@pytest.mark.parametrize(
    "category",
    ["ring", "earring", "pendant", "necklace", "bracelet", "bangle", "brooch"],
)
def test_prompt_builder_supported_categories(category):
    """Verify each supported controlled category is semantically injected into the prompt."""
    prompt = build_jewellery_prompt(
        material="18k yellow gold",
        gemstone="round brilliant diamond",
        category=category,
    )
    assert f"fine jewellery {category}" in prompt
    assert "polished 18k yellow gold" in prompt
    assert "round brilliant diamond" in prompt
    assert "studio lighting" in prompt


def test_prompt_builder_other_and_default_category():
    """Verify 'other', 'other_jewellery', and None categories generate generic fine jewellery prompts without ring bias."""
    # Category = 'other'
    prompt_other = build_jewellery_prompt(
        material="platinum",
        gemstone="blue sapphire",
        category="other",
    )
    assert "photorealistic fine jewellery product photograph" in prompt_other
    assert "ring" not in prompt_other
    assert "earring" not in prompt_other

    # Category = 'other_jewellery'
    prompt_other_j = build_jewellery_prompt(
        material="platinum",
        gemstone="blue sapphire",
        category="other_jewellery",
    )
    assert "photorealistic fine jewellery product photograph" in prompt_other_j
    assert "ring" not in prompt_other_j
    assert "earring" not in prompt_other_j

    # Category = None (default backwards compatibility)
    prompt_none = build_jewellery_prompt(
        material="platinum",
        gemstone="blue sapphire",
        category=None,
    )
    assert "photorealistic fine jewellery product photograph" in prompt_none
    assert "ring" not in prompt_none


def test_prompt_builder_invalid_category_raises():
    """Verify invalid categories raise ValueError with supported categories listed."""
    with pytest.raises(ValueError, match="Unsupported jewellery category 'tiara'"):
        build_jewellery_prompt(category="tiara")

    with pytest.raises(ValueError, match="Unsupported jewellery category 'automobile'"):
        build_jewellery_prompt(category="automobile")


def test_prompt_builder_case_and_whitespace_normalization():
    """Verify category parameter trims whitespace and handles mixed casing."""
    prompt = build_jewellery_prompt(
        material="18k yellow gold",
        gemstone="diamond",
        category="  RING  ",
    )
    assert "photorealistic fine jewellery ring product photograph" in prompt


def test_render_request_category_validation():
    """Verify category validation and normalization on RenderRequest schema."""
    # Valid explicit category
    req = RenderRequest(category="earring")
    assert req.category == "earring"

    # Uppercase normalization
    req_upper = RenderRequest(category="PENDANT")
    assert req_upper.category == "pendant"

    # Default is None (no universal ring default)
    req_default = RenderRequest()
    assert req_default.category is None

    # Invalid category raises ValidationError
    with pytest.raises(ValueError):
        RenderRequest(category="unsupported_item")
