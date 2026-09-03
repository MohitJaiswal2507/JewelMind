"""JewelMind Phase 10 — Post-Training Visual Evaluation Script.

Compares Baseline Pretrained ControlNet vs 100-Step Fine-Tuned Jewellery ControlNet
under identical deterministic inference conditions across diverse jewellery categories.
"""

import argparse
import gc
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np
from PIL import Image, ImageDraw, ImageFont

import torch
from diffusers import (
    ControlNetModel,
    StableDiffusionControlNetPipeline,
    UniPCMultistepScheduler,
)

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def create_comparison_panel(
    conditioning_img: Image.Image,
    baseline_img: Image.Image,
    trained_img: Image.Image,
    target_img: Optional[Image.Image],
    sample_id: str,
    category: str,
    prompt: str,
) -> Image.Image:
    """Create a 4-panel side-by-side comparison image."""
    w, h = 512, 512
    c_img = conditioning_img.resize((w, h), Image.Resampling.BILINEAR)
    b_img = baseline_img.resize((w, h), Image.Resampling.BILINEAR)
    t_img = trained_img.resize((w, h), Image.Resampling.BILINEAR)
    if target_img is not None:
        ref_img = target_img.resize((w, h), Image.Resampling.BILINEAR)
    else:
        ref_img = Image.new("RGB", (w, h), (240, 240, 240))

    header_h = 60
    label_h = 40
    panel_w = w * 4
    panel_h = h + header_h + label_h

    canvas = Image.new("RGB", (panel_w, panel_h), (250, 250, 250))
    draw = ImageDraw.Draw(canvas)

    # Header title
    title = f"Sample: {sample_id} | Category: {category.upper()}"
    draw.text((20, 15), title, fill=(20, 20, 20))
    short_prompt = (prompt[:140] + "...") if len(prompt) > 140 else prompt
    draw.text((20, 35), f"Prompt: {short_prompt}", fill=(90, 90, 90))

    # Panel Labels
    labels = [
        "(1) Conditioning LineArt",
        "(2) Baseline ControlNet (Pretrained)",
        "(3) 100-Step Trained ControlNet",
        "(4) Ground-Truth Reference Photo",
    ]

    images = [c_img, b_img, t_img, ref_img]

    for i, (label, img) in enumerate(zip(labels, images)):
        x_offset = i * w
        y_img = header_h
        y_lbl = header_h + h + 10

        canvas.paste(img, (x_offset, y_img))
        draw.text((x_offset + 15, y_lbl), label, fill=(30, 30, 30))
        # Draw vertical separator line
        if i > 0:
            draw.line([(x_offset, header_h), (x_offset, panel_h)], fill=(200, 200, 200), width=2)

    return canvas


def main():
    parser = argparse.ArgumentParser(description="Evaluate 100-step ControlNet against Pretrained Baseline")
    parser.add_argument("--trained_model", type=str, default="outputs/controlnet_jewellery/controlnet_jewellery_final", help="Path to fine-tuned ControlNet")
    parser.add_argument("--baseline_model", type=str, default="lllyasviel/control_v11p_sd15_lineart", help="Pretrained ControlNet model ID")
    parser.add_argument("--base_diffusion_model", type=str, default="runwayml/stable-diffusion-v1-5", help="Base SD 1.5 model ID")
    parser.add_argument("--output_dir", type=str, default="outputs/controlnet_jewellery/evaluation", help="Evaluation output root")
    parser.add_argument("--val_metadata", type=str, default="datasets/controlnet_paired/metadata/validation.jsonl", help="Validation JSONL")
    parser.add_argument("--steps", type=int, default=20, help="Inference steps")
    parser.add_argument("--guidance_scale", type=float, default=7.5, help="Guidance scale")
    parser.add_argument("--controlnet_scale", type=float, default=1.0, help="ControlNet conditioning scale")
    parser.add_argument("--max_samples", type=int, default=6, help="Number of diverse validation samples to evaluate")
    parser.add_argument("--seed", type=int, default=42, help="Deterministic base seed")
    args = parser.parse_args()

    if not torch.cuda.is_available():
        print("[ERROR] CUDA is required for evaluation on local GPU.")
        sys.exit(1)

    device = torch.device("cuda")
    print("=" * 70)
    print("  JEWELMIND PHASE 10 — POST-TRAINING VISUAL EVALUATION")
    print(f"  Target GPU:        {torch.cuda.get_device_name(0)}")
    print(f"  Base SD Model:     {args.base_diffusion_model}")
    print(f"  Baseline Model:    {args.baseline_model}")
    print(f"  Trained Model:     {args.trained_model}")
    print("=" * 70)

    out_root = Path(args.output_dir)
    baseline_dir = out_root / "baseline"
    trained_dir = out_root / "trained"
    cond_dir = out_root / "conditioning"
    target_dir = out_root / "target"
    comp_dir = out_root / "comparisons"

    for d in [baseline_dir, trained_dir, cond_dir, target_dir, comp_dir]:
        d.mkdir(parents=True, exist_ok=True)

    # 1. Load validation records
    val_meta_path = Path(args.val_metadata)
    if not val_meta_path.exists():
        print(f"[ERROR] Validation metadata not found: {val_meta_path}")
        sys.exit(1)

    with open(val_meta_path, "r", encoding="utf-8") as f:
        val_records = [json.loads(line.strip()) for line in f if line.strip()]

    print(f"[DATASET] Loaded {len(val_records)} validation records.")

    # Select diverse representative samples across different categories
    categories_covered = set()
    selected_samples: List[Dict[str, Any]] = []
    for r in val_records:
        cat = r.get("category", "unknown")
        if cat not in categories_covered or len(selected_samples) < args.max_samples:
            selected_samples.append(r)
            categories_covered.add(cat)
        if len(selected_samples) >= args.max_samples:
            break

    print(f"[SELECTION] Evaluating {len(selected_samples)} samples across categories: {list(categories_covered)}")

    # 2. Initialize Base Pipeline with Pretrained ControlNet
    print("\n[1/2] Generating Baseline Images with Pretrained ControlNet...")
    baseline_controlnet = ControlNetModel.from_pretrained(
        args.baseline_model,
        torch_dtype=torch.float16,
    ).to(device)

    pipe = StableDiffusionControlNetPipeline.from_pretrained(
        args.base_diffusion_model,
        controlnet=baseline_controlnet,
        torch_dtype=torch.float16,
        safety_checker=None,
    ).to(device)
    pipe.scheduler = UniPCMultistepScheduler.from_config(pipe.scheduler.config)

    baseline_images: Dict[str, Image.Image] = {}
    conditioning_images: Dict[str, Image.Image] = {}
    target_images: Dict[str, Optional[Image.Image]] = {}

    for idx, sample in enumerate(selected_samples, start=1):
        stem = Path(sample["target"]).stem
        cond_path = Path("datasets/controlnet_paired") / sample["source"]
        target_path = Path("datasets/controlnet_paired") / sample["target"]
        prompt = sample.get("prompt", "")

        cond_img = Image.open(cond_path).convert("RGB")
        target_img = Image.open(target_path).convert("RGB") if target_path.exists() else None

        conditioning_images[stem] = cond_img
        target_images[stem] = target_img

        # Save conditioning and target reference
        cond_img.save(cond_dir / f"{stem}_conditioning.png")
        if target_img:
            target_img.save(target_dir / f"{stem}_target.jpg")

        generator = torch.Generator(device=device).manual_seed(args.seed + idx)
        with torch.inference_mode():
            out = pipe(
                prompt=prompt,
                image=cond_img,
                num_inference_steps=args.steps,
                guidance_scale=args.guidance_scale,
                controlnet_conditioning_scale=args.controlnet_scale,
                generator=generator,
                width=512,
                height=512,
            )
        b_img = out.images[0]
        b_img.save(baseline_dir / f"{stem}_baseline.png")
        baseline_images[stem] = b_img
        print(f"  [{idx}/{len(selected_samples)}] Baseline generated: {stem} ({sample.get('category')})")

    # Clean VRAM before loading trained model
    del baseline_controlnet
    del pipe
    gc.collect()
    torch.cuda.empty_cache()

    # 3. Initialize Pipeline with Trained ControlNet
    print("\n[2/2] Generating Trained Images with Fine-Tuned ControlNet (100-step)...")
    trained_controlnet = ControlNetModel.from_pretrained(
        args.trained_model,
        torch_dtype=torch.float16,
    ).to(device)

    pipe_trained = StableDiffusionControlNetPipeline.from_pretrained(
        args.base_diffusion_model,
        controlnet=trained_controlnet,
        torch_dtype=torch.float16,
        safety_checker=None,
    ).to(device)
    pipe_trained.scheduler = UniPCMultistepScheduler.from_config(pipe_trained.scheduler.config)

    trained_images: Dict[str, Image.Image] = {}

    for idx, sample in enumerate(selected_samples, start=1):
        stem = Path(sample["target"]).stem
        cond_img = conditioning_images[stem]
        prompt = sample.get("prompt", "")

        generator = torch.Generator(device=device).manual_seed(args.seed + idx)
        with torch.inference_mode():
            out = pipe_trained(
                prompt=prompt,
                image=cond_img,
                num_inference_steps=args.steps,
                guidance_scale=args.guidance_scale,
                controlnet_conditioning_scale=args.controlnet_scale,
                generator=generator,
                width=512,
                height=512,
            )
        t_img = out.images[0]
        t_img.save(trained_dir / f"{stem}_trained_100step.png")
        trained_images[stem] = t_img
        print(f"  [{idx}/{len(selected_samples)}] Trained generated:  {stem} ({sample.get('category')})")

    # Clean VRAM
    del trained_controlnet
    del pipe_trained
    gc.collect()
    torch.cuda.empty_cache()

    # 4. Create Side-by-Side Comparison Panels
    print("\n[3/3] Creating 4-Panel Comparison Sheets...")
    for idx, sample in enumerate(selected_samples, start=1):
        stem = Path(sample["target"]).stem
        comp_panel = create_comparison_panel(
            conditioning_img=conditioning_images[stem],
            baseline_img=baseline_images[stem],
            trained_img=trained_images[stem],
            target_img=target_images[stem],
            sample_id=stem,
            category=sample.get("category", "jewellery"),
            prompt=sample.get("prompt", ""),
        )
        comp_path = comp_dir / f"comparison_{stem}.png"
        comp_panel.save(comp_path)
        print(f"  Saved comparison panel: {comp_path}")

    print("\n" + "=" * 70)
    print("  VISUAL EVALUATION COMPLETE")
    print(f"  Outputs saved to: {out_root}")
    print("=" * 70)


if __name__ == "__main__":
    main()
