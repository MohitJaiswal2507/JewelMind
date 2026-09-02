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

ControlType = Literal["lineart", "canny"]


class RenderingConfig(BaseModel):
    """Configuration settings for Stable Diffusion + ControlNet rendering pipeline."""

    # Model identifiers
    base_model_id: str = Field(
        default=os.getenv("JEWELMIND_DIFFUSION_MODEL", "runwayml/stable-diffusion-v1-5"),
        description="HuggingFace model ID or local path for base SD pipeline",
    )
    lineart_controlnet_id: str = Field(
        default=os.getenv("JEWELMIND_CONTROLNET_LINEART", "lllyasviel/control_v11p_sd15_lineart"),
        description="HuggingFace model ID or local path for LineArt ControlNet",
    )
    canny_controlnet_id: str = Field(
        default=os.getenv("JEWELMIND_CONTROLNET_CANNY", "lllyasviel/control_v11p_sd15_canny"),
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
    default_control_strength: float = Field(default=0.8, ge=0.0, le=1.0)
    default_control_type: ControlType = Field(default="lineart")

    # Memory optimization parameters
    use_fp16: bool = Field(default=True, description="Enables float16 inference")
    enable_attention_slicing: bool = Field(default=True, description="Reduces peak VRAM during attention")
    enable_vae_slicing: bool = Field(default=True, description="Reduces peak VRAM during latent decoding")
    enable_vae_tiling: bool = Field(default=False, description="Tiled VAE decoding if extra memory headroom needed")
    device: str = Field(default="cuda", description="Device name (cuda or cpu)")


# Global default configuration instance
rendering_config = RenderingConfig()
