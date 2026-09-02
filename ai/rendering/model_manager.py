"""Model Manager for Diffusion + ControlNet lifecycle and VRAM safety on RTX 4060 8GB."""

import gc
import logging
import threading
from typing import Dict, Optional
import torch

from ai.rendering.config import RenderingConfig, rendering_config

logger = logging.getLogger("jewelmind.ai.rendering")


class DiffusionModelManager:
    """Manages lazy-loading, ControlNet swapping, serialization locks, and VRAM cleanup."""

    _instance: Optional["DiffusionModelManager"] = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(DiffusionModelManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, config: Optional[RenderingConfig] = None):
        if getattr(self, "_initialized", False):
            return

        self.config = config or rendering_config
        self.device = self._resolve_device()
        self.torch_dtype = torch.float16 if (self.config.use_fp16 and self.device == "cuda") else torch.float32

        # In-memory pipeline and controlnet cache
        self.pipeline = None
        self.loaded_control_type: Optional[str] = None
        self._controlnet_models: Dict[str, torch.nn.Module] = {}

        # Concurrency lock enforcing 1 render job at a time on GPU
        self.execution_lock = threading.Lock()
        self._initialized = True
        logger.info("Initialized DiffusionModelManager targeting device: %s", self.device)

    def _resolve_device(self) -> str:
        """Determine device targeting local CUDA GPU."""
        if torch.cuda.is_available() and self.config.device == "cuda":
            return "cuda"
        return "cpu"

    def get_vram_info(self) -> Dict[str, float]:
        """Return allocated and reserved VRAM in Megabytes."""
        if self.device == "cuda" and torch.cuda.is_available():
            allocated = torch.cuda.memory_allocated() / (1024 * 1024)
            reserved = torch.cuda.memory_reserved() / (1024 * 1024)
            max_allocated = torch.cuda.max_memory_allocated() / (1024 * 1024)
            return {
                "allocated_mb": round(allocated, 2),
                "reserved_mb": round(reserved, 2),
                "max_allocated_mb": round(max_allocated, 2),
            }
        return {"allocated_mb": 0.0, "reserved_mb": 0.0, "max_allocated_mb": 0.0}

    def clear_vram(self) -> None:
        """Purge cached PyTorch memory to avoid fragmentation."""
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()

    def _get_controlnet(self, control_type: str):
        """Lazy load and cache ControlNet adapter."""
        from diffusers import ControlNetModel

        normalized = control_type.strip().lower()
        if normalized in self._controlnet_models:
            return self._controlnet_models[normalized]

        if normalized == "lineart":
            model_id = self.config.lineart_controlnet_id
        elif normalized == "canny":
            model_id = self.config.canny_controlnet_id
        else:
            raise ValueError(f"Unknown control type: '{control_type}'")

        logger.info("Loading ControlNet [%s] from: %s", normalized, model_id)
        controlnet = ControlNetModel.from_pretrained(
            model_id,
            torch_dtype=self.torch_dtype,
            cache_dir=self.config.model_cache_dir,
            use_safetensors=True,
        )
        if self.device == "cuda":
            controlnet = controlnet.to(self.device)

        self._controlnet_models[normalized] = controlnet
        return controlnet

    def get_pipeline(self, control_type: str = "lineart"):
        """Lazy load or swap ControlNet adapter in StableDiffusionControlNetPipeline."""
        from diffusers import StableDiffusionControlNetPipeline, UniPCMultistepScheduler

        normalized = control_type.strip().lower()

        # If pipeline is already loaded and using this controlnet, return it
        if self.pipeline is not None and self.loaded_control_type == normalized:
            return self.pipeline

        target_controlnet = self._get_controlnet(normalized)

        if self.pipeline is None:
            logger.info("Initializing StableDiffusionControlNetPipeline with model: %s", self.config.base_model_id)
            self.clear_vram()

            variant = "fp16" if self.torch_dtype == torch.float16 else None
            pipe = StableDiffusionControlNetPipeline.from_pretrained(
                self.config.base_model_id,
                controlnet=target_controlnet,
                torch_dtype=self.torch_dtype,
                cache_dir=self.config.model_cache_dir,
                safety_checker=None,  # Not needed for jewellery CAD blueprint renderings
                use_safetensors=True,
                variant=variant,
            )

            # UniPC / Euler a provides fast, stable sampling with ControlNet
            pipe.scheduler = UniPCMultistepScheduler.from_config(pipe.scheduler.config)

            if self.device == "cuda":
                pipe = pipe.to(self.device)

            # Apply memory optimizations for 8GB RTX 4060
            if self.config.enable_attention_slicing:
                pipe.enable_attention_slicing("auto")
                logger.info("Enabled attention slicing for 8GB VRAM optimization.")

            if self.config.enable_vae_slicing:
                pipe.enable_vae_slicing()
                logger.info("Enabled VAE slicing.")

            if self.config.enable_vae_tiling:
                pipe.enable_vae_tiling()

            self.pipeline = pipe
            self.loaded_control_type = normalized
        else:
            # Hot-swap ControlNet without re-instantiating UNet / VAE
            logger.info("Hot-swapping ControlNet adapter to [%s]", normalized)
            self.pipeline.controlnet = target_controlnet
            self.loaded_control_type = normalized

        return self.pipeline

    def unload_models(self) -> None:
        """Release all models from GPU VRAM."""
        with self.execution_lock:
            self.pipeline = None
            self.loaded_control_type = None
            self._controlnet_models.clear()
            self.clear_vram()
            logger.info("Unloaded diffusion pipeline and ControlNet adapters from memory.")


# Singleton helper
def get_model_manager(config: Optional[RenderingConfig] = None) -> DiffusionModelManager:
    return DiffusionModelManager(config=config)
