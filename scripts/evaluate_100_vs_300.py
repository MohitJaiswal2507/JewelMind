"""JewelMind Phase 10 — 100-Step vs 300-Step ControlNet Evaluation Script.

Performs a rigorous, deterministic A/B comparison between:
- 100-Step Checkpoint (outputs/controlnet_jewellery/controlnet_jewellery_final)
- 300-Step Checkpoint (outputs/controlnet_jewellery_300/controlnet_jewellery_final)
- Pretrained Baseline (lllyasviel/control_v11p_sd15_lineart) [Reference]

Across the exact same validation samples under identical inference conditions.
"""

import argparse
import gc
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from PIL import Image, ImageDraw, ImageFont

import torch
from diffusers import (
    ControlNetModel,
    StableDiffusionControlNetPipeline,
    UniPCMultistepScheduler,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def create_5panel_comparison(
    conditioning_img: Image.Image,
    baseline_img: Image.Image,
    step100_img: Image.Image,
    step300_img: Image.Image,
    target_img: Optional[Image.Image],
    sample_id: str,
    category: str,
    prompt: str,
) -> Image.Image:
    """Create a 5-panel side-by-side comparison image."""
    w, h = 512, 512
    c_img = conditioning_img.resize((w, h), Image.Resampling.BILINEAR)
    b_img = baseline_img.resize((w, h), Image.Resampling.BILINEAR)
    s100_img = step100_img.resize((w, h), Image.Resampling.BILINEAR)
    s300_img = step300_img.resize((w, h), Image.Resampling.BILINEAR)
    if target_img is not None:
        ref_img = target_img.resize((w, h), Image.Resampling.BILINEAR)
    else:
        ref_img = Image.new("RGB", (w, h), (240, 240, 240))

    header_h = 60
    label_h = 40
    panel_w = w * 5
    panel_h = h + header_h + label_h

    canvas = Image.new("RGB", (panel_w, panel_h), (250, 250, 250))
    draw = ImageDraw.Draw(canvas)

    # Header title
    title = f"Sample: {sample_id} | Category: {category.upper()}"
    draw.text((20, 15), title, fill=(20, 20, 20))
    short_prompt = (prompt[:180] + "...") if len(prompt) > 180 else prompt
    draw.text((20, 35), f"Prompt: {short_prompt}", fill=(90, 90, 90))

    # Panel Labels
    labels = [
        "(1) Conditioning LineArt",
        "(2) Pretrained Baseline (Ref)",
        "(3) 100-Step Model",
        "(4) 300-Step Model",
        "(5) Ground-Truth Reference",
    ]

    images = [c_img, b_img, s100_img, s300_img, ref_img]

    for i, (label, img) in enumerate(zip(labels, images)):
        x_offset = i * w
        y_img = header_h
        y_lbl = header_h + h + 10

        canvas.paste(img, (x_offset, y_img))
        draw.text((x_offset + 15, y_lbl), label, fill=(30, 30, 30))
        if i > 0:
            draw.line([(x_offset, header_h), (x_offset, panel_h)], fill=(200, 200, 200), width=2)

    return canvas


def main():
    parser = argparse.ArgumentParser(description="Evaluate 100-Step vs 300-Step ControlNet")
    parser.add_argument("--model_100", type=str, default="outputs/controlnet_jewellery/controlnet_jewellery_final", help="Path to 100-step ControlNet")
    parser.add_argument("--model_300", type=str, default="outputs/controlnet_jewellery_300/controlnet_jewellery_final", help="Path to 300-step ControlNet")
    parser.add_argument("--baseline_model", type=str, default="lllyasviel/control_v11p_sd15_lineart", help="Pretrained baseline ID")
    parser.add_argument("--base_diffusion_model", type=str, default="runwayml/stable-diffusion-v1-5", help="Base SD 1.5 ID")
    parser.add_argument("--output_dir", type=str, default="outputs/controlnet_evaluation_100_vs_300", help="Output directory")
    parser.add_argument("--val_metadata", type=str, default="datasets/controlnet_paired/metadata/validation.jsonl", help="Validation JSONL")
    parser.add_argument("--steps", type=int, default=20, help="Inference steps")
    parser.add_argument("--guidance_scale", type=float, default=7.5, help="Guidance scale")
    parser.add_argument("--controlnet_scale", type=float, default=1.0, help="ControlNet scale")
    parser.add_argument("--max_samples", type=int, default=6, help="Samples to evaluate")
    parser.add_argument("--seed", type=int, default=42, help="Deterministic base seed")
    args = parser.parse_args()

    if not torch.cuda.is_available():
        print("[ERROR] CUDA is required for evaluation.")
        sys.exit(1)

    device = torch.device("cuda")
    print("=" * 75)
    print("  JEWELMIND PHASE 10 — 100-STEP VS 300-STEP CONTROLNET EVALUATION")
    print(f"  Target GPU:        {torch.cuda.get_device_name(0)}")
    print(f"  100-Step Model:    {args.model_100}")
    print(f"  300-Step Model:    {args.model_300}")
    print(f"  Baseline Model:    {args.baseline_model}")
    print("=" * 75)

    out_root = Path(args.output_dir)
    dir_100 = out_root / "100step"
    dir_300 = out_root / "300step"
    dir_base = out_root / "baseline"
    dir_comp = out_root / "comparisons"

    for d in [dir_100, dir_300, dir_base, dir_comp]:
        d.mkdir(parents=True, exist_ok=True)

    # 1. Load exact validation records
    val_meta_path = Path(args.val_metadata)
    with open(val_meta_path, "r", encoding="utf-8") as f:
        val_records = [json.loads(line.strip()) for line in f if line.strip()]

    categories_covered = set()
    selected_samples: List[Dict[str, Any]] = []
    for r in val_records:
        cat = r.get("category", "unknown")
        if cat not in categories_covered or len(selected_samples) < args.max_samples:
            selected_samples.append(r)
            categories_covered.add(cat)
        if len(selected_samples) >= args.max_samples:
            break

    print(f"[SELECTION] Evaluating {len(selected_samples)} validation samples across categories: {list(categories_covered)}")

    conditioning_images: Dict[str, Image.Image] = {}
    target_images: Dict[str, Optional[Image.Image]] = {}

    for sample in selected_samples:
        stem = Path(sample["target"]).stem
        cond_path = Path("datasets/controlnet_paired") / sample["source"]
        target_path = Path("datasets/controlnet_paired") / sample["target"]
        conditioning_images[stem] = Image.open(cond_path).convert("RGB")
        target_images[stem] = Image.open(target_path).convert("RGB") if target_path.exists() else None

    # Function to generate batch of samples with a given model
    def run_model_inference(model_path_or_id: str, label: str, save_dir: Path) -> Dict[str, Image.Image]:
        print(f"\n[{label}] Loading ControlNet from: {model_path_or_id}...")
        cnet = ControlNetModel.from_pretrained(model_path_or_id, torch_dtype=torch.float16).to(device)
        pipe = StableDiffusionControlNetPipeline.from_pretrained(
            args.base_diffusion_model,
            controlnet=cnet,
            torch_dtype=torch.float16,
            safety_checker=None,
        ).to(device)
        pipe.scheduler = UniPCMultistepScheduler.from_config(pipe.scheduler.config)

        results = {}
        for idx, sample in enumerate(selected_samples, start=1):
            stem = Path(sample["target"]).stem
            cond_img = conditioning_images[stem]
            prompt = sample.get("prompt", "")

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
            img = out.images[0]
            save_path = save_dir / f"{stem}_{label.lower().replace(' ', '_')}.png"
            img.save(save_path)
            results[stem] = img
            print(f"  [{idx}/{len(selected_samples)}] {label} generated: {stem} ({sample.get('category')})")

        del cnet
        del pipe
        gc.collect()
        torch.cuda.empty_cache()
        return results

    # 1. Baseline
    baseline_images = run_model_inference(args.baseline_model, "Baseline Pretrained", dir_base)

    # 2. 100-step
    step100_images = run_model_inference(args.model_100, "100-Step Model", dir_100)

    # 3. 300-step
    step300_images = run_model_inference(args.model_300, "300-Step Model", dir_300)

    # 4. Create 5-Panel Comparison Sheets
    print("\n[PANELS] Generating 5-Panel Side-by-Side Comparison Sheets...")
    for idx, sample in enumerate(selected_samples, start=1):
        stem = Path(sample["target"]).stem
        comp_panel = create_5panel_comparison(
            conditioning_img=conditioning_images[stem],
            baseline_img=baseline_images[stem],
            step100_img=step100_images[stem],
            step300_img=step300_images[stem],
            target_img=target_images[stem],
            sample_id=stem,
            category=sample.get("category", "jewellery"),
            prompt=sample.get("prompt", ""),
        )
        comp_path = dir_comp / f"comparison_100_vs_300_{stem}.png"
        comp_panel.save(comp_path)
        print(f"  Saved comparison panel: {comp_path}")

    print("\n" + "=" * 75)
    print("  EVALUATION COMPLETE")
    print(f"  All outputs saved in: {out_root}")
    print("=" * 75)


if __name__ == "__main__":
    main()
