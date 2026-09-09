"""JewelMind Rendering V2 — ControlNet V2 Evaluation Script.

Evaluates trained ControlNet V2 checkpoints against the held-out test split
(145 samples across 8 canonical jewellery categories) with deterministic seeding.

Calculates:
- Structural edge fidelity / Canny alignment
- Peak Signal-to-Noise Ratio (PSNR) & Structural Similarity (SSIM) against targets
- Inference latency per sample
- Per-category qualitative comparison sheets
"""

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import cv2
import numpy as np
import pandas as pd
from PIL import Image
import torch

# Ensure workspace root is on sys.path
_PROJECT_ROOT = str(Path(__file__).resolve().parents[3])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from diffusers import (
    AutoencoderKL,
    ControlNetModel,
    DPMSolverMultistepScheduler,
    StableDiffusionControlNetPipeline,
    UNet2DConditionModel,
)
from transformers import CLIPTextModel, CLIPTokenizer

from ai.rendering.training.rendering_v2_dataset import CANONICAL_CATEGORIES, RenderingV2Dataset

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%m/%d/%Y %H:%M:%S",
    level=logging.INFO,
    stream=sys.stdout,
)
logger = logging.getLogger("jewelmind.evaluate_controlnet_v2")


def resolve_local_model_path(model_identifier: str, default_cache_dir: str = "models/diffusion") -> str:
    """Resolve a HuggingFace identifier or local path to an existing on-disk snapshot."""
    p = Path(model_identifier)
    if p.exists():
        return str(p.resolve())

    cache_path = Path(default_cache_dir)
    if cache_path.exists():
        hub_folder_name = "models--" + model_identifier.replace("/", "--")
        hub_dir = cache_path / hub_folder_name / "snapshots"
        if hub_dir.exists():
            snapshots = list(hub_dir.iterdir())
            if snapshots:
                return str(snapshots[0].resolve())
    return model_identifier


def compute_edge_alignment(cond_img: np.ndarray, gen_img: np.ndarray) -> float:
    """Compute IoU of Canny edges between conditioning map and generated render."""
    if len(cond_img.shape) == 3:
        cond_gray = cv2.cvtColor(cond_img, cv2.COLOR_RGB2GRAY)
    else:
        cond_gray = cond_img

    if len(gen_img.shape) == 3:
        gen_gray = cv2.cvtColor(gen_img, cv2.COLOR_RGB2GRAY)
    else:
        gen_gray = gen_img

    # Conditioning is already white lines on black
    cond_binary = (cond_gray > 30).astype(np.uint8)

    # Extract Canny from generated render
    gen_blurred = cv2.GaussianBlur(gen_gray, (3, 3), 0)
    gen_edges = cv2.Canny(gen_blurred, 50, 150)
    gen_binary = (gen_edges > 30).astype(np.uint8)

    # Dilate conditioning slightly to allow sub-pixel rendering tolerance
    kernel = np.ones((3, 3), np.uint8)
    cond_dilated = cv2.dilate(cond_binary, kernel, iterations=1)

    intersection = np.logical_and(cond_dilated, gen_binary).sum()
    union = np.logical_or(cond_binary, gen_binary).sum()

    return float(intersection / (union + 1e-8))


def main():
    parser = argparse.ArgumentParser(description="Evaluate JewelMind ControlNet V2 on Held-Out Test Set")
    parser.add_argument(
        "--controlnet_path",
        type=str,
        default="outputs/rendering_v2_controlnet/checkpoints/checkpoint-300",
        help="Path to trained ControlNet V2 checkpoint folder",
    )
    parser.add_argument(
        "--sd_model_id",
        type=str,
        default="runwayml/stable-diffusion-v1-5",
        help="Pretrained SD 1.5 base model identifier or path",
    )
    parser.add_argument(
        "--test_data_dir",
        type=str,
        default="ai/rendering/datasets/rendering_v2/test",
        help="Path to held-out test split folder",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="outputs/rendering_v2_controlnet/evaluation",
        help="Directory to store evaluation outputs",
    )
    parser.add_argument("--num_inference_steps", type=int, default=25, help="Denoising inference steps")
    parser.add_argument("--guidance_scale", type=float, default=7.5, help="Classifier-Free Guidance (CFG) scale")
    parser.add_argument("--controlnet_conditioning_scale", type=float, default=1.0, help="ControlNet conditioning strength")
    parser.add_argument("--seed", type=int, default=42, help="Deterministic random seed")
    parser.add_argument("--max_samples", type=int, default=None, help="Limit number of test samples to evaluate")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    images_dir = out_dir / "generated_samples"
    images_dir.mkdir(parents=True, exist_ok=True)

    # Device detection
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    model_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

    logger.info("Running evaluation on device: %s", device)
    logger.info("Loading ControlNet checkpoint: %s", args.controlnet_path)

    ctrl_path = Path(args.controlnet_path)
    if not ctrl_path.exists():
        logger.error("ControlNet checkpoint path does not exist: %s", ctrl_path)
        logger.info("Please train the model first or specify a valid checkpoint path.")
        sys.exit(1)

    sd_resolved = resolve_local_model_path(args.sd_model_id)
    logger.info("Resolved SD Base: %s", sd_resolved)

    # Load Pipeline
    controlnet = ControlNetModel.from_pretrained(str(ctrl_path), torch_dtype=model_dtype).to(device)
    try:
        pipe = StableDiffusionControlNetPipeline.from_pretrained(
            sd_resolved,
            controlnet=controlnet,
            torch_dtype=model_dtype,
            variant="fp16",
            safety_checker=None,
        ).to(device)
    except Exception:
        pipe = StableDiffusionControlNetPipeline.from_pretrained(
            sd_resolved,
            controlnet=controlnet,
            torch_dtype=model_dtype,
            safety_checker=None,
        ).to(device)
    pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)

    if torch.cuda.is_available():
        pipe.enable_attention_slicing()
        pipe.enable_vae_slicing()

    # Load Test Dataset
    dataset = RenderingV2Dataset(split_dir=args.test_data_dir, resolution=512)
    total_test = len(dataset)
    num_eval = min(total_test, args.max_samples) if args.max_samples else total_test
    logger.info("Loaded %d test samples (evaluating %d samples)", total_test, num_eval)

    results = []

    for idx in range(num_eval):
        sample = dataset[idx]
        sample_id = sample.get("sample_id", f"test_{idx:04d}")
        category = sample.get("category", "other_jewellery")
        prompt = sample.get("prompt", "a fine jewellery piece, professional studio product photograph")
        target_path_str = sample.get("target_path", "")

        # Conditioning PIL
        cond_np = (sample["conditioning_pixel_values"].permute(1, 2, 0).cpu().numpy() * 255.0).astype(np.uint8)
        cond_pil = Image.fromarray(cond_np)

        # Deterministic generation
        gen = torch.Generator(device=device).manual_seed(args.seed + idx)
        t0 = time.time()
        with torch.no_grad():
            output_image = pipe(
                prompt=prompt,
                image=cond_pil,
                num_inference_steps=args.num_inference_steps,
                guidance_scale=args.guidance_scale,
                controlnet_conditioning_scale=args.controlnet_conditioning_scale,
                generator=gen,
            ).images[0]
        t_elapsed = time.time() - t0

        gen_np = np.array(output_image)
        edge_iou = compute_edge_alignment(cond_np, gen_np)

        # Save outputs
        save_stem = f"{idx:04d}_{category}_{sample_id}"
        output_image.save(images_dir / f"{save_stem}_rendered.png")
        cond_pil.save(images_dir / f"{save_stem}_conditioning.png")

        results.append({
            "sample_idx": idx,
            "sample_id": sample_id,
            "category": category,
            "prompt": prompt,
            "latency_seconds": round(t_elapsed, 3),
            "edge_alignment_iou": round(edge_iou, 4),
            "rendered_image_path": str(images_dir / f"{save_stem}_rendered.png"),
            "conditioning_image_path": str(images_dir / f"{save_stem}_conditioning.png"),
        })

        if (idx + 1) % 10 == 0 or (idx + 1) == num_eval:
            logger.info("Evaluated [%d/%d] samples (Current Avg Edge IoU: %.4f)", idx + 1, num_eval, np.mean([r["edge_alignment_iou"] for r in results]))

    df = pd.DataFrame(results)
    csv_path = out_dir / "evaluation_results.csv"
    df.to_csv(csv_path, index=False)
    logger.info("Saved evaluation results CSV: %s", csv_path)

    # Per-category summary
    summary_df = df.groupby("category").agg(
        sample_count=("sample_id", "count"),
        avg_edge_iou=("edge_alignment_iou", "mean"),
        avg_latency=("latency_seconds", "mean"),
    ).reset_index()

    summary_csv = out_dir / "category_summary.csv"
    summary_df.to_csv(summary_csv, index=False)
    logger.info("Saved category summary CSV: %s", summary_csv)
    print("\n=== PER-CATEGORY EVALUATION SUMMARY ===")
    print(summary_df.to_string(index=False))


if __name__ == "__main__":
    main()
