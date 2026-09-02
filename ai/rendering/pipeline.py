"""Jewellery Generative Rendering Pipeline using Stable Diffusion + ControlNet."""

import os
import random
import time
import uuid
from pathlib import Path
from typing import Optional, Tuple, Union
import numpy as np
from PIL import Image
import torch

from ai.rendering.config import RenderingConfig, rendering_config
from ai.rendering.model_manager import DiffusionModelManager, get_model_manager
from ai.rendering.preprocessing import get_conditioning_processor
from ai.rendering.prompts import build_jewellery_prompt, build_negative_prompt
from ai.rendering.schemas import ConditioningMetadata, RenderRequest, RenderResult


class RenderingOutOfMemoryError(RuntimeError):
    """Raised when GPU VRAM is exceeded during diffusion execution."""
    pass


class JewelleryRenderingPipeline:
    """End-to-end rendering pipeline: sketch -> preprocessing -> ControlNet -> Diffusion -> Photorealistic Image."""

    def __init__(
        self,
        config: Optional[RenderingConfig] = None,
        model_manager: Optional[DiffusionModelManager] = None,
    ):
        self.config = config or rendering_config
        self.model_manager = model_manager or get_model_manager(self.config)

        # Ensure output directory exists
        Path(self.config.output_dir).mkdir(parents=True, exist_ok=True)

    def render(
        self,
        sketch_image: Union[np.ndarray, Image.Image],
        request: Optional[RenderRequest] = None,
    ) -> Tuple[Image.Image, RenderResult]:
        """Execute conditioned generative rendering on input sketch."""
        req = request or RenderRequest()

        # Step 1: Preprocess sketch to ControlNet conditioning image
        processor = get_conditioning_processor(
            control_type=req.control_type,
            target_width=req.width,
            target_height=req.height,
        )
        conditioning_image, cond_meta = processor.process(
            sketch_image,
            target_width=req.width,
            target_height=req.height,
        )

        # Step 2: Build tailored prompts
        positive_prompt = build_jewellery_prompt(
            material=req.material,
            gemstone=req.gemstone,
            user_prompt=req.prompt,
        )
        negative_prompt = build_negative_prompt(
            user_negative_prompt=req.negative_prompt,
        )

        # Step 3: Determine seed
        actual_seed = req.seed if req.seed is not None else random.randint(0, 2147483647)
        generator = torch.Generator(device=self.model_manager.device).manual_seed(actual_seed)

        # Step 4: Acquire serialization lock (strictly 1 rendering job on GPU at a time)
        acquired = self.model_manager.execution_lock.acquire(timeout=60.0)
        if not acquired:
            raise RuntimeError("GPU rendering service is currently busy. Please try again shortly.")

        start_time = time.perf_counter()
        try:
            # Memory housekeeping before denoising
            self.model_manager.clear_vram()

            # Lazy load or hot-swap pipeline
            pipeline = self.model_manager.get_pipeline(control_type=req.control_type)

            with torch.inference_mode():
                output = pipeline(
                    prompt=positive_prompt,
                    negative_prompt=negative_prompt,
                    image=conditioning_image,
                    num_inference_steps=req.steps,
                    guidance_scale=req.guidance_scale,
                    controlnet_conditioning_scale=req.control_strength,
                    generator=generator,
                    width=req.width,
                    height=req.height,
                )

            rendered_image: Image.Image = output.images[0]

        except torch.cuda.OutOfMemoryError as oom_err:
            self.model_manager.clear_vram()
            raise RenderingOutOfMemoryError(
                f"GPU VRAM limit exceeded during rendering. Target resolution: {req.width}x{req.height}, steps: {req.steps}. "
                "Try 512x512 with fewer steps or ensure no other GPU tasks are active."
            ) from oom_err
        finally:
            self.model_manager.clear_vram()
            self.model_manager.execution_lock.release()

        inference_time_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

        # Step 5: Save output image to Git-ignored directory
        image_id = f"render_{uuid.uuid4().hex[:12]}_{actual_seed}.png"
        output_file_path = Path(self.config.output_dir) / image_id
        rendered_image.save(output_file_path, format="PNG")

        # Public output URL for backend retrieval without exposing filesystem paths
        output_url = f"/api/v1/ai/render/outputs/{image_id}"

        controlnet_version = (
            self.config.lineart_controlnet_id if req.control_type == "lineart" else self.config.canny_controlnet_id
        )

        result = RenderResult(
            model_version=self.config.base_model_id,
            controlnet_version=controlnet_version,
            image_width=req.width,
            image_height=req.height,
            seed=actual_seed,
            control_type=req.control_type,
            control_strength=req.control_strength,
            steps=req.steps,
            guidance_scale=req.guidance_scale,
            inference_time_ms=inference_time_ms,
            device_used=f"{self.model_manager.device}:0" if self.model_manager.device == "cuda" else "cpu",
            output_url=output_url,
            conditioning_metadata=cond_meta,
        )

        return rendered_image, result
