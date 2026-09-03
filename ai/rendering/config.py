"""Configuration and settings for JewelMind Generative Diffusion & ControlNet Rendering."""

import os
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, Field

# Base workspace path
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent

# Cache and model storage directory (overrideable via JEWELMIND_MODEL_DIR)
DEFAULT_MODEL_CACHE_DIR = os.getenv(
    "JEWELMIND_MODEL_DIR",
    str(WORKSPACE_ROOT / "models" / "diffusion")
)

# Output image directory
DEFAULT_OUTPUT_DIR = os.getenv(
    "JEWELMIND_OUTPUT_DIR",
    str(WORKSPACE_ROOT / "outputs" / "rendering")
)

# Default model identifiers
DEFAULT_PRETRAINED_LINEART_FALLBACK = "lllyasviel/control_v11p_sd15_lineart"
DEFAULT_PRETRAINED_CANNY_FALLBACK = "lllyasviel/control_v11p_sd15_canny"
DEFAULT_PRODUCTION_300_CONTROLNET = str(WORKSPACE_ROOT / "outputs" / "controlnet_jewellery_300" / "controlnet_jewellery_final")

ControlType = Literal["lineart", "canny"]


def get_default_lineart_controlnet() -> str:
    """Resolve production LineArt ControlNet model path or fallback.

    Priority:
    1. Explicit env var JEWELMIND_CONTROLNET_MODEL_PATH
    2. Legacy env var JEWELMIND_CONTROLNET_LINEART
    3. Fine-tuned 300-step model if present on disk
    4. Pretrained HuggingFace lineart ControlNet baseline fallback
    """
    env_path = os.getenv("JEWELMIND_CONTROLNET_MODEL_PATH") or os.getenv("JEWELMIND_CONTROLNET_LINEART")
    if env_path and env_path.strip():
        return env_path.strip()

    prod_path = Path(DEFAULT_PRODUCTION_300_CONTROLNET)
    if prod_path.exists() and (prod_path / "config.json").exists():
        return str(prod_path)

    # Relative path check
    rel_prod_path = Path("outputs/controlnet_jewellery_300/controlnet_jewellery_final")
    if rel_prod_path.exists() and (rel_prod_path / "config.json").exists():
        return str(rel_prod_path)

    return DEFAULT_PRETRAINED_LINEART_FALLBACK


class RenderingConfig(BaseModel):
    """Configuration settings for Stable Diffusion + ControlNet rendering pipeline."""

    # Model identifiers
    base_model_id: str = Field(
        default=os.getenv("JEWELMIND_DIFFUSION_MODEL", "runwayml/stable-diffusion-v1-5"),
        description="HuggingFace model ID or local path for base SD pipeline",
    )
    lineart_controlnet_id: str = Field(
        default_factory=get_default_lineart_controlnet,
        description="Production Jewellery ControlNet model path or HuggingFace ID",
    )
    canny_controlnet_id: str = Field(
        default=os.getenv("JEWELMIND_CONTROLNET_CANNY", DEFAULT_PRETRAINED_CANNY_FALLBACK),
        description="HuggingFace model ID or local path for Canny ControlNet",
    )
    model_cache_dir: str = Field(
        default=DEFAULT_MODEL_CACHE_DIR,
        description="Directory for local model checkpoints and huggingface cache",
    )
    output_dir: str = Field(
        default=DEFAULT_OUTPUT_DIR,
        description="Directory for storing rendered images",
    )

    # Resolution & batch constraints for RTX 4060 8GB
    default_width: int = Field(default=512, ge=256, le=1024)
    default_height: int = Field(default=512, ge=256, le=1024)
    batch_size: int = Field(default=1, description="Strictly 1 on 8GB VRAM")

    # Inference defaults
    default_steps: int = Field(default=20, ge=5, le=50)
    default_guidance_scale: float = Field(default=7.5, ge=1.0, le=20.0)
    default_control_strength: float = Field(default=1.0, ge=0.0, le=1.0)
    default_control_type: ControlType = Field(default="lineart")

    # Memory optimization parameters
    use_fp16: bool = Field(default=True, description="Enables float16 inference")
    enable_attention_slicing: bool = Field(default=True, description="Reduces peak VRAM during attention")
    enable_vae_slicing: bool = Field(default=True, description="Reduces peak VRAM during latent decoding")
    enable_vae_tiling: bool = Field(default=False, description="Tiled VAE decoding if extra memory headroom needed")
    device: str = Field(default="cuda", description="Device name (cuda or cpu)")


# Global default configuration instance
rendering_config = RenderingConfig()
