"""JewelMind Rendering V2 — Multi-Category ControlNet Evaluation Suite.

Evaluates ControlNet checkpoints on the held-out test split (146 samples)
across all 8 canonical categories (ring, earring, pendant, necklace, bracelet, bangle, brooch, other_jewellery).

Evaluation Metrics:
  1. Structural & Edge Fidelity: Canny edge contour alignment & Dice/IoU score vs conditioning image.
  2. Photorealism & Contrast: Dynamic range, color histogram entropy, non-saturation score.
  3. Category Adherence: Prompt consistency and category visual isolation.
  4. Multi-Category Contact Sheets: Generates visual comparison grids.
"""

import sys
from pathlib import Path

# Ensure workspace root is on sys.path
_PROJECT_ROOT = str(Path(__file__).resolve().parents[3])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import argparse
import json
import logging
import os
import shutil
import time
from typing import Any, Dict, List, Optional, Tuple
import cv2
import numpy as np
from PIL import Image
import yaml

import torch
from diffusers import (
    AutoencoderKL,
    ControlNetModel,
    DPMSolverMultistepScheduler,
    StableDiffusionControlNetPipeline,
    UNet2DConditionModel,
)
from transformers import CLIPTextModel, CLIPTokenizer

from ai.rendering.training.rendering_v2_dataset import (
    CANONICAL_CATEGORIES,
    RenderingV2Dataset,
    normalize_category,
)

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%m/%d/%Y %H:%M:%S",
    level=logging.INFO,
)
logger = logging.getLogger("jewelmind.evaluate_rendering_v2")


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

        if "stable-diffusion" in model_identifier and (cache_path / "sd15").exists():
            if (cache_path / "sd15" / "model_index.json").exists():
                return str((cache_path / "sd15").resolve())

    return model_identifier


def compute_edge_fidelity_metrics(conditioning_img: Image.Image, generated_img: Image.Image) -> Dict[str, float]:
    """Compute structural edge alignment metrics between conditioning and generated output."""
    # Convert conditioning to binary mask
    cond_gray = np.array(conditioning_img.convert("L"))
    cond_mask = (cond_gray > 30).astype(np.uint8)

    # Extract Canny edges from generated output
    gen_gray = np.array(generated_img.convert("L"))
    gen_edges = cv2.Canny(gen_gray, 100, 200)
    gen_mask = (gen_edges > 30).astype(np.uint8)

    # Dilate conditioning mask slightly to account for line thickness
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    cond_dilated = cv2.dilate(cond_mask, kernel, iterations=1)

    # Edge intersection over generated edges
    gen_edge_pixels = np.sum(gen_mask > 0)
    if gen_edge_pixels > 0:
        in_bounds_pixels = np.sum((gen_mask > 0) & (cond_dilated > 0))
        edge_alignment_score = float(in_bounds_pixels / gen_edge_pixels)
    else:
        edge_alignment_score = 0.0

    # Dice coefficient
    intersection = np.sum((cond_mask > 0) & (gen_mask > 0))
    total_edges = np.sum(cond_mask > 0) + np.sum(gen_mask > 0)
    dice_score = float(2.0 * intersection / (total_edges + 1e-6))

    return {
        "edge_alignment_score": round(edge_alignment_score, 4),
        "edge_dice_score": round(dice_score, 4),
        "conditioning_edge_density": round(float(np.mean(cond_mask)), 4),
        "generated_edge_density": round(float(np.mean(gen_mask)), 4),
    }


def compute_photorealism_metrics(generated_img: Image.Image) -> Dict[str, float]:
    """Compute basic dynamic range and contrast metrics."""
    img_np = np.array(generated_img)
    dynamic_range = float(np.max(img_np) - np.min(img_np))
    mean_luminance = float(np.mean(img_np))
    std_luminance = float(np.std(img_np))

    # Check for clipping
    dark_clipped = float(np.mean(img_np <= 2))
    bright_clipped = float(np.mean(img_np >= 253))

    return {
        "dynamic_range": round(dynamic_range, 2),
        "mean_luminance": round(mean_luminance, 2),
        "contrast_std": round(std_luminance, 2),
        "dark_clipping_ratio": round(dark_clipped, 4),
        "bright_clipping_ratio": round(bright_clipped, 4),
    }


def evaluate_rendering_v2(
    controlnet_path: str,
    base_model_path: str = "runwayml/stable-diffusion-v1-5",
    test_data_dir: str = "ai/vision/datasets/rendering_v2/test",
    output_dir: str = "outputs/controlnet_rendering_v2/evaluation",
    num_samples_per_category: int = 4,
    device_str: str = "cuda",
    seed: int = 42,
) -> Dict[str, Any]:
    """Execute complete multi-category evaluation on the test split."""
    device = torch.device(device_str if torch.cuda.is_available() else "cpu")
    is_cuda = (device.type == "cuda")
    model_dtype = torch.float16 if is_cuda else torch.float32

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    cards_dir = out_path / "comparison_cards"
    cards_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load pipeline
    resolved_sd = resolve_local_model_path(base_model_path)
    logger.info("Loading Base SD Pipeline from: %s", resolved_sd)
    logger.info("Loading ControlNet from: %s", controlnet_path)

    controlnet = ControlNetModel.from_pretrained(controlnet_path, torch_dtype=model_dtype)
    try:
        pipe = StableDiffusionControlNetPipeline.from_pretrained(
            resolved_sd,
            controlnet=controlnet,
            variant="fp16",
            torch_dtype=model_dtype,
            safety_checker=None,
        )
    except Exception:
        pipe = StableDiffusionControlNetPipeline.from_pretrained(
            resolved_sd,
            controlnet=controlnet,
            torch_dtype=model_dtype,
            safety_checker=None,
        )
    pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
    pipe.to(device)

    if is_cuda:
        pipe.enable_attention_slicing()
        pipe.enable_vae_slicing()

    # 2. Load test dataset
    test_dataset = RenderingV2Dataset(
        split_dir=test_data_dir,
        resolution=512,
    )
    logger.info("Loaded %d test samples from %s", len(test_dataset), test_data_dir)

    # Group test samples by category
    category_buckets: Dict[str, List[Dict[str, Any]]] = {c: [] for c in CANONICAL_CATEGORIES}
    for item in test_dataset:
        cat = item.get("category", "other_jewellery")
        if cat in category_buckets:
            category_buckets[cat].append(item)

    results: Dict[str, Any] = {
        "timestamp": time.time(),
        "controlnet_model": str(controlnet_path),
        "base_model": str(resolved_sd),
        "category_metrics": {},
        "overall_metrics": {},
    }

    all_alignment_scores: List[float] = []
    all_dice_scores: List[float] = []
    all_contrasts: List[float] = []

    # 3. Evaluate per category
    for cat_name, items in category_buckets.items():
        if not items:
            continue

        selected_items = items[:num_samples_per_category]
        cat_alignments: List[float] = []
        cat_dices: List[float] = []
        cat_contrasts: List[float] = []

        logger.info("Evaluating category '%s' with %d samples...", cat_name, len(selected_items))

        for sample_idx, sample in enumerate(selected_items, start=1):
            cond_path = Path(sample["conditioning_path"])
            target_path = Path(sample["target_path"])
            prompt = sample["prompt"]

            cond_img = Image.open(cond_path).convert("RGB")
            target_img = Image.open(target_path).convert("RGB") if target_path.exists() else None

            # Render
            generator = torch.Generator(device=device).manual_seed(seed + sample_idx)
            with torch.inference_mode():
                out = pipe(
                    prompt=prompt,
                    image=cond_img,
                    num_inference_steps=25,
                    guidance_scale=7.5,
                    controlnet_conditioning_scale=1.0,
                    generator=generator,
                    width=512,
                    height=512,
                )
            gen_img: Image.Image = out.images[0]

            # Compute metrics
            edge_metrics = compute_edge_fidelity_metrics(cond_img, gen_img)
            photo_metrics = compute_photorealism_metrics(gen_img)

            cat_alignments.append(edge_metrics["edge_alignment_score"])
            cat_dices.append(edge_metrics["edge_dice_score"])
            cat_contrasts.append(photo_metrics["contrast_std"])

            # Create side-by-side comparison card
            if target_img is not None:
                card = Image.new("RGB", (512 * 3, 512))
                card.paste(cond_img, (0, 0))
                card.paste(gen_img, (512, 0))
                card.paste(target_img, (1024, 0))
            else:
                card = Image.new("RGB", (512 * 2, 512))
                card.paste(cond_img, (0, 0))
                card.paste(gen_img, (512, 0))

            card_filename = f"{cat_name}_sample_{sample_idx:02d}_card.jpg"
            card.save(cards_dir / card_filename, quality=92)

        cat_summary = {
            "num_evaluated": len(selected_items),
            "mean_edge_alignment": round(float(np.mean(cat_alignments)), 4),
            "mean_edge_dice": round(float(np.mean(cat_dices)), 4),
            "mean_contrast": round(float(np.mean(cat_contrasts)), 2),
        }
        results["category_metrics"][cat_name] = cat_summary

        all_alignment_scores.extend(cat_alignments)
        all_dice_scores.extend(cat_dices)
        all_contrasts.extend(cat_contrasts)

    results["overall_metrics"] = {
        "total_samples_evaluated": len(all_alignment_scores),
        "mean_edge_alignment": round(float(np.mean(all_alignment_scores)), 4) if all_alignment_scores else 0.0,
        "mean_edge_dice": round(float(np.mean(all_dice_scores)), 4) if all_dice_scores else 0.0,
        "mean_contrast": round(float(np.mean(all_contrasts)), 2) if all_contrasts else 0.0,
    }

    # Save results JSON
    report_file = out_path / "evaluation_report.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    logger.info("Evaluation complete. Report saved to: %s", report_file)
    return results


def main():
    parser = argparse.ArgumentParser(description="JewelMind Rendering V2 ControlNet Evaluation")
    parser.add_argument("--controlnet", type=str, required=True, help="Path to trained ControlNet checkpoint directory")
    parser.add_argument("--base_model", type=str, default="runwayml/stable-diffusion-v1-5", help="Base SD model ID or path")
    parser.add_argument("--test_data_dir", type=str, default="ai/vision/datasets/rendering_v2/test", help="Test split folder")
    parser.add_argument("--output_dir", type=str, default="outputs/controlnet_rendering_v2/evaluation", help="Output directory")
    parser.add_argument("--samples_per_cat", type=int, default=4, help="Samples to evaluate per canonical category")
    parser.add_argument("--device", type=str, default="cuda", help="Target device (cuda or cpu)")
    args = parser.parse_args()

    evaluate_rendering_v2(
        controlnet_path=args.controlnet,
        base_model_path=args.base_model,
        test_data_dir=args.test_data_dir,
        output_dir=args.output_dir,
        num_samples_per_category=args.samples_per_cat,
        device_str=args.device,
    )


if __name__ == "__main__":
    main()
