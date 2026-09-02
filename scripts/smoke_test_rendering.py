"""JewelMind Phase 7 — Real GPU Smoke Test.

Verifies CUDA availability, loads Stable Diffusion 1.5 + ControlNet on RTX 4060 8GB,
renders a single test jewellery sketch, and logs VRAM telemetry and latency.
"""

import os
import sys
import time
from pathlib import Path
from PIL import Image
import torch

# Ensure workspace root is in sys.path
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from ai.rendering.config import rendering_config
from ai.rendering.pipeline import JewelleryRenderingPipeline
from ai.rendering.schemas import RenderRequest


def run_smoke_test():
    print("=" * 65)
    print("  JEWELMIND PHASE 7 — REAL GPU SMOKE TEST")
    print("=" * 65)

    # 1. Verify CUDA
    if not torch.cuda.is_available():
        print("[FAIL] CUDA is not available. Smoke test requires local NVIDIA GPU.")
        sys.exit(1)

    device_name = torch.cuda.get_device_name(0)
    total_vram_mb = torch.cuda.get_device_properties(0).total_memory / (1024 * 1024)
    print(f"[CUDA] Device: {device_name}")
    print(f"[CUDA] Total VRAM: {total_vram_mb:.1f} MiB")

    # 2. Select jewellery sketch
    sample_sketch_path = WORKSPACE_ROOT / "ai" / "vision" / "datasets" / "sample" / "train" / "images" / "ring_train_000.jpg"
    if not sample_sketch_path.exists():
        # Fallback to test image
        fallback_candidates = list((WORKSPACE_ROOT / "ai" / "vision" / "datasets").rglob("*.jpg"))
        if not fallback_candidates:
            print("[FAIL] No sample jewellery sketch found in ai/vision/datasets.")
            sys.exit(1)
        sample_sketch_path = fallback_candidates[0]

    print(f"[INPUT] Using jewellery sketch: {sample_sketch_path.name}")
    sketch_img = Image.open(sample_sketch_path)

    # 3. Initialize Pipeline
    print(f"[MODEL] Initializing JewelleryRenderingPipeline...")
    print(f"        Base Model: {rendering_config.base_model_id}")
    print(f"        ControlNet: {rendering_config.lineart_controlnet_id}")
    print(f"        Precision: fp16 (target: RTX 4060 8GB)")

    torch.cuda.reset_peak_memory_stats()
    vram_before_mb = torch.cuda.memory_allocated() / (1024 * 1024)
    print(f"[VRAM] Memory allocated before load: {vram_before_mb:.1f} MiB")

    pipeline = JewelleryRenderingPipeline()

    # 4. Prepare Render Request (512x512, batch 1, 20 steps, seed 42)
    request = RenderRequest(
        material="18k yellow gold",
        gemstone="round brilliant diamond",
        control_type="lineart",
        control_strength=0.8,
        steps=20,
        guidance_scale=7.5,
        seed=42,
        width=512,
        height=512,
    )

    # 5. Execute Rendering
    print("\n[INFERENCE] Starting generative render (batch 1, 512x512, 20 steps)...")
    start_time = time.perf_counter()
    rendered_img, result = pipeline.render(sketch_img, request=request)
    total_elapsed = time.perf_counter() - start_time

    # 6. Record Telemetry
    vram_after_mb = torch.cuda.memory_allocated() / (1024 * 1024)
    peak_vram_mb = torch.cuda.max_memory_allocated() / (1024 * 1024)

    output_disk_path = Path(rendering_config.output_dir) / Path(result.output_url).name

    print("\n" + "=" * 65)
    print("  SMOKE TEST RESULTS")
    print("=" * 65)
    print(f"  Status:             SUCCESS")
    print(f"  Model:              {result.model_version}")
    print(f"  ControlNet:         {result.controlnet_version}")
    print(f"  Device:             {result.device_used}")
    print(f"  Resolution:         {result.image_width}x{result.image_height}")
    print(f"  Seed:               {result.seed}")
    print(f"  Steps:              {result.steps}")
    print(f"  Inference Latency:  {result.inference_time_ms:.1f} ms ({result.inference_time_ms/1000:.2f} s)")
    print(f"  Total Run Time:     {total_elapsed:.2f} s (including I/O and preprocessing)")
    print(f"  VRAM Before:        {vram_before_mb:.1f} MiB")
    print(f"  Peak VRAM (Active): {peak_vram_mb:.1f} MiB ({peak_vram_mb/1024:.2f} GiB)")
    print(f"  VRAM Headroom:      {(total_vram_mb - peak_vram_mb):.1f} MiB free out of {total_vram_mb:.1f} MiB")
    print(f"  Output URL:         {result.output_url}")
    print(f"  Output Exists:      {output_disk_path.exists()} ({output_disk_path})")
    print("=" * 65)

    if not output_disk_path.exists():
        print("[FAIL] Rendered image was not saved to disk.")
        sys.exit(1)

    print("\n[SMOKE TEST PASS] Model loaded and generated photorealistic render successfully on local GPU.")


if __name__ == "__main__":
    run_smoke_test()
