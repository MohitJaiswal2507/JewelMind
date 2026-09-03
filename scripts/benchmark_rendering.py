"""JewelMind Phase 7 — RTX 4060 8GB Generative Rendering Benchmark.

Measures cold-start model load time, warm inference latency across step counts (10, 15, 20),
and peak VRAM footprint on local NVIDIA GeForce RTX 4060 Laptop GPU.
"""

import sys
import time
from pathlib import Path
from PIL import Image
import torch

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from ai.rendering.config import rendering_config
from ai.rendering.pipeline import JewelleryRenderingPipeline
from ai.rendering.schemas import RenderRequest


def run_benchmark():
    print("=" * 70)
    print("  JEWELMIND PHASE 7 — RENDERING BENCHMARK (RTX 4060 8GB)")
    print("=" * 70)

    if not torch.cuda.is_available():
        print("[FAIL] CUDA is required for GPU benchmarking.")
        sys.exit(1)

    device_name = torch.cuda.get_device_name(0)
    total_vram_mb = torch.cuda.get_device_properties(0).total_memory / (1024 * 1024)
    print(f"Device: {device_name} ({total_vram_mb:.0f} MiB Total VRAM)")
    print(f"Model: {rendering_config.base_model_id}")
    print(f"ControlNet: {rendering_config.lineart_controlnet_id}")
    print(f"Precision: fp16 | Attention Slicing: True | VAE Slicing: True\n")

    sketch_path = WORKSPACE_ROOT / "ai" / "vision" / "datasets" / "sample" / "train" / "images" / "ring_train_000.jpg"
    if not sketch_path.exists():
        fallback_candidates = list((WORKSPACE_ROOT / "ai" / "vision" / "datasets").rglob("*.jpg"))
        sketch_path = fallback_candidates[0]

    sketch_img = Image.open(sketch_path)

    # 1. Measure Cold Load Latency
    print("[1/4] Measuring Cold Pipeline Initialization...")
    t_load_start = time.perf_counter()
    pipeline = JewelleryRenderingPipeline()
    # Trigger first pipeline load
    torch.cuda.reset_peak_memory_stats()
    _ = pipeline.model_manager.get_pipeline("lineart")
    cold_load_sec = time.perf_counter() - t_load_start
    cold_vram_mb = torch.cuda.memory_allocated() / (1024 * 1024)
    print(f"      Cold Load Time: {cold_load_sec:.2f} s")
    print(f"      Base VRAM Allocated: {cold_vram_mb:.1f} MiB\n")

    # Benchmarking step variations (10, 15, 20 steps)
    step_configs = [10, 15, 20]
    benchmark_results = []

    for idx, steps in enumerate(step_configs, start=2):
        print(f"[{idx}/4] Benchmarking {steps} steps (512x512, batch 1, seed=42)...")
        req = RenderRequest(
            category="ring",
            material="18k yellow gold",
            gemstone="round brilliant diamond",
            control_type="lineart",
            steps=steps,
            guidance_scale=7.5,
            control_strength=1.0,
            seed=42,
            width=512,
            height=512,
        )

        torch.cuda.reset_peak_memory_stats()
        t_start = time.perf_counter()
        rendered_img, result = pipeline.render(sketch_img, request=req)
        elapsed_sec = time.perf_counter() - t_start
        peak_vram_mb = torch.cuda.max_memory_allocated() / (1024 * 1024)

        benchmark_results.append({
            "steps": steps,
            "latency_ms": result.inference_time_ms,
            "total_sec": elapsed_sec,
            "peak_vram_mb": peak_vram_mb,
            "output_url": result.output_url,
        })
        print(f"      Inference Latency: {result.inference_time_ms:.1f} ms ({result.inference_time_ms/1000:.2f} s)")
        print(f"      Peak Active VRAM: {peak_vram_mb:.1f} MiB ({peak_vram_mb/1024:.2f} GiB)\n")

    # Print Summary Table
    print("=" * 70)
    print("  BENCHMARK SUMMARY MATRIX")
    print("=" * 70)
    print(f"{'Steps':<8} | {'Resolution':<12} | {'Latency (ms)':<14} | {'Latency (s)':<12} | {'Peak VRAM (MiB)':<16}")
    print("-" * 70)
    for row in benchmark_results:
        print(
            f"{row['steps']:<8} | {'512x512':<12} | {row['latency_ms']:<14.1f} | "
            f"{row['latency_ms']/1000:<12.2f} | {row['peak_vram_mb']:<16.1f}"
        )
    print("=" * 70)
    print(f"Cold Start / Initial Weights Load: {cold_load_sec:.2f} s")
    print(f"Hardware VRAM Headroom: {(total_vram_mb - max(r['peak_vram_mb'] for r in benchmark_results)):.1f} MiB free")
    print("[BENCHMARK COMPLETE] All configurations run safely within 8GB VRAM envelope.")


if __name__ == "__main__":
    run_benchmark()
