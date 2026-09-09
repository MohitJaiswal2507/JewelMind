"""JewelMind Rendering — V1 Production Baseline vs V2 Candidate Comparison Script.

Runs side-by-side comparative inference under identical experimental controls:
- Identical LineArt Conditioning Map
- Identical Text Prompt
- Identical Random Seed
- Identical Denoising Steps (25 steps, DPM-Solver++)
- Identical CFG Guidance (7.5) & Control Scale (1.0)
- Identical 512x512 Resolution

Generates a structured side-by-side visual contact sheet:
[ Conditioning LineArt | V1 Production Render | V2 Candidate Render | Ground Truth Target ]
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
from PIL import Image, ImageDraw, ImageFont
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
)

from ai.rendering.training.rendering_v2_dataset import CANONICAL_CATEGORIES, RenderingV2Dataset

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%m/%d/%Y %H:%M:%S",
    level=logging.INFO,
    stream=sys.stdout,
)
logger = logging.getLogger("jewelmind.compare_v1_v2")


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


def create_comparison_row(
    cond_img: Image.Image,
    v1_img: Image.Image,
    v2_img: Image.Image,
    target_img: Optional[Image.Image],
    label_text: str,
) -> Image.Image:
    """Combine 4 images side-by-side with titles."""
    w, h = 512, 512
    header_h = 40
    panels = [
        ("LineArt Conditioning", cond_img.resize((w, h))),
        ("V1 Baseline (300-Step)", v1_img.resize((w, h))),
        ("V2 Candidate (Rendering V2)", v2_img.resize((w, h))),
    ]
    if target_img is not None:
        panels.append(("Ground Truth Target", target_img.resize((w, h))))

    total_w = w * len(panels)
    total_h = h + header_h + 30
    canvas = Image.new("RGB", (total_w, total_h), (20, 24, 30))
    draw = ImageDraw.Draw(canvas)

    for i, (title, img) in enumerate(panels):
        x_offset = i * w
        # Draw header banner
        draw.rectangle([x_offset + 2, 2, x_offset + w - 2, header_h - 2], fill=(35, 40, 50))
        draw.text((x_offset + 10, 10), title, fill=(240, 240, 240))
        # Paste image
        canvas.paste(img, (x_offset, header_h))

    # Draw bottom label
    draw.rectangle([0, total_h - 30, total_w, total_h], fill=(15, 18, 22))
    draw.text((15, total_h - 22), label_text, fill=(200, 220, 255))

    return canvas


def main():
    parser = argparse.ArgumentParser(description="JewelMind ControlNet V1 vs V2 Side-by-Side Benchmark")
    parser.add_argument(
        "--v1_controlnet_path",
        type=str,
        default="outputs/controlnet_jewellery_300/controlnet_jewellery_final",
        help="Path to production V1 ControlNet checkpoint",
    )
    parser.add_argument(
        "--v2_controlnet_path",
        type=str,
        default="outputs/rendering_v2_controlnet/checkpoints/checkpoint-300",
        help="Path to trained V2 ControlNet checkpoint",
    )
    parser.add_argument(
        "--sd_model_id",
        type=str,
        default="runwayml/stable-diffusion-v1-5",
        help="Base SD 1.5 path or identifier",
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
        default="outputs/rendering_v2_controlnet/v1_vs_v2_comparison",
        help="Output folder for comparison sheets",
    )
    parser.add_argument("--num_inference_steps", type=int, default=25, help="Denoising steps")
    parser.add_argument("--guidance_scale", type=float, default=7.5, help="CFG scale")
    parser.add_argument("--seed", type=int, default=42, help="Deterministic random seed")
    parser.add_argument("--samples_per_category", type=int, default=2, help="Number of benchmark samples per category")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    model_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

    logger.info("Initializing V1 vs V2 Comparison on device: %s", device)

    # Check paths
    v1_path = Path(args.v1_controlnet_path)
    v2_path = Path(args.v2_controlnet_path)

    if not v1_path.exists():
        logger.error("V1 ControlNet path missing: %s", v1_path)
        sys.exit(1)
    if not v2_path.exists():
        logger.error("V2 ControlNet path missing: %s", v2_path)
        logger.info("Please train the V2 model first before running comparative benchmarking.")
        sys.exit(1)

    sd_resolved = resolve_local_model_path(args.sd_model_id)

    # Load V1 Pipeline
    logger.info("Loading V1 ControlNet Pipeline from: %s", v1_path)
    v1_ctrl = ControlNetModel.from_pretrained(str(v1_path), torch_dtype=model_dtype).to(device)
    try:
        pipe_v1 = StableDiffusionControlNetPipeline.from_pretrained(
            sd_resolved,
            controlnet=v1_ctrl,
            torch_dtype=model_dtype,
            variant="fp16",
            safety_checker=None,
        ).to(device)
    except Exception:
        pipe_v1 = StableDiffusionControlNetPipeline.from_pretrained(
            sd_resolved,
            controlnet=v1_ctrl,
            torch_dtype=model_dtype,
            safety_checker=None,
        ).to(device)
    pipe_v1.scheduler = DPMSolverMultistepScheduler.from_config(pipe_v1.scheduler.config)

    # Load Test Dataset
    dataset = RenderingV2Dataset(split_dir=args.test_data_dir, resolution=512)

    # Group test samples by category
    samples_by_cat: Dict[str, List[Dict[str, Any]]] = {c: [] for c in CANONICAL_CATEGORIES}
    for idx in range(len(dataset)):
        s = dataset[idx]
        cat = s.get("category", "other_jewellery")
        if cat in samples_by_cat and len(samples_by_cat[cat]) < args.samples_per_category:
            samples_by_cat[cat].append((idx, s))

    # Run V1 Generations
    logger.info("Generating V1 baseline renders...")
    v1_results: Dict[int, Image.Image] = {}
    for cat, items in samples_by_cat.items():
        for idx, s in items:
            cond_np = (s["conditioning_pixel_values"].permute(1, 2, 0).cpu().numpy() * 255.0).astype(np.uint8)
            cond_pil = Image.fromarray(cond_np)
            prompt = s.get("prompt", f"a luxury {cat}, fine jewellery, studio product photography")
            gen = torch.Generator(device=device).manual_seed(args.seed + idx)
            with torch.no_grad():
                img_v1 = pipe_v1(
                    prompt=prompt,
                    image=cond_pil,
                    num_inference_steps=args.num_inference_steps,
                    guidance_scale=args.guidance_scale,
                    generator=gen,
                ).images[0]
            v1_results[idx] = img_v1

    # Unload V1 to save VRAM
    del pipe_v1
    del v1_ctrl
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    # Load V2 Pipeline
    logger.info("Loading V2 ControlNet Pipeline from: %s", v2_path)
    v2_ctrl = ControlNetModel.from_pretrained(str(v2_path), torch_dtype=model_dtype).to(device)
    try:
        pipe_v2 = StableDiffusionControlNetPipeline.from_pretrained(
            sd_resolved,
            controlnet=v2_ctrl,
            torch_dtype=model_dtype,
            variant="fp16",
            safety_checker=None,
        ).to(device)
    except Exception:
        pipe_v2 = StableDiffusionControlNetPipeline.from_pretrained(
            sd_resolved,
            controlnet=v2_ctrl,
            torch_dtype=model_dtype,
            safety_checker=None,
        ).to(device)
    pipe_v2.scheduler = DPMSolverMultistepScheduler.from_config(pipe_v2.scheduler.config)

    # Run V2 Generations & Assemble Comparisons
    logger.info("Generating V2 candidate renders and assembling comparison contact sheets...")
    comparison_rows = []
    for cat, items in samples_by_cat.items():
        for idx, s in items:
            cond_np = (s["conditioning_pixel_values"].permute(1, 2, 0).cpu().numpy() * 255.0).astype(np.uint8)
            cond_pil = Image.fromarray(cond_np)
            prompt = s.get("prompt", f"a luxury {cat}, fine jewellery, studio product photography")
            target_path_str = s.get("target_path", "")
            target_img = Image.open(target_path_str).convert("RGB") if target_path_str and Path(target_path_str).exists() else None

            gen = torch.Generator(device=device).manual_seed(args.seed + idx)
            with torch.no_grad():
                img_v2 = pipe_v2(
                    prompt=prompt,
                    image=cond_pil,
                    num_inference_steps=args.num_inference_steps,
                    guidance_scale=args.guidance_scale,
                    generator=gen,
                ).images[0]

            img_v1 = v1_results[idx]
            label = f"Sample ID: {s.get('sample_id', idx)} | Category: {cat.upper()} | Prompt: {prompt[:60]}... | Seed: {args.seed + idx}"
            row = create_comparison_row(cond_pil, img_v1, img_v2, target_img, label)
            save_path = out_dir / f"compare_{cat}_{s.get('sample_id', idx)}.png"
            row.save(save_path)
            comparison_rows.append(row)
            logger.info("Saved comparison sheet: %s", save_path)

    logger.info("Successfully generated %d side-by-side comparison sheets in %s", len(comparison_rows), out_dir)


if __name__ == "__main__":
    main()
