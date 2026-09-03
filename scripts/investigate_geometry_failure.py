"""JewelMind Phase 10 — Geometry Failure Investigation Script.

Investigates ring_train_000.jpg preprocessing, conditioning map, prompt semantics,
and comparative inference across Pretrained Baseline, 100-Step, and 300-Step models.
"""

import argparse
import gc
import json
import os
import sys
import time
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

import torch
from diffusers import (
    ControlNetModel,
    StableDiffusionControlNetPipeline,
    UniPCMultistepScheduler,
)

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from ai.rendering.preprocessing.lineart import LineArtProcessor
from ai.rendering.prompts import build_jewellery_prompt, build_negative_prompt


def main():
    if not torch.cuda.is_available():
        print("[ERROR] CUDA is required for investigation.")
        sys.exit(1)

    device = torch.device("cuda")
    out_dir = Path("outputs/investigation")
    out_dir.mkdir(parents=True, exist_ok=True)

    input_path = WORKSPACE_ROOT / "ai" / "vision" / "datasets" / "sample" / "train" / "images" / "ring_train_000.jpg"
    print("=" * 75)
    print("  PHASE 10 — GEOMETRY FAILURE INVESTIGATION")
    print(f"  Target File: {input_path}")
    print("=" * 75)

    if not input_path.exists():
        print(f"[ERROR] Input path does not exist: {input_path}")
        sys.exit(1)

    src_img = Image.open(input_path).convert("RGB")
    src_w, src_h = src_img.size
    print(f"[1. INPUT] Dimensions: {src_w}x{src_h} | Mode: {src_img.mode}")

    # Step 2: Preprocess conditioning map
    processor = LineArtProcessor(target_width=512, target_height=512)
    cond_img, meta = processor.process(src_img, target_width=512, target_height=512)
    cond_path = out_dir / "conditioning_ring_train_000.png"
    cond_img.save(cond_path)
    print(f"[2. CONDITIONING] Saved to: {cond_path}")
    print(f"    Edge density: {meta.edge_density}")
    print(f"    Processed size: {meta.processed_size}")
    print(f"    Padding applied: {meta.padding}")

    # Step 3: Check Prompts
    smoke_prompt = build_jewellery_prompt(material="18k yellow gold", gemstone="round brilliant diamond", user_prompt=None)
    category_prompt = build_jewellery_prompt(material="18k yellow gold", gemstone="round brilliant diamond", user_prompt="solitaire fine jewellery finger ring")
    neg_prompt = build_negative_prompt()

    print("\n[3. PROMPT TRACE]")
    print(f"  Production Smoke Prompt: '{smoke_prompt}'")
    print(f"  Contains 'ring'? {'ring' in smoke_prompt.lower()}")
    print(f"  Contains 'pendant'? {'pendant' in smoke_prompt.lower()}")
    print(f"  Negative Prompt: '{neg_prompt[:120]}...'")

    # Step 4: Run Comparative Inference (Smoke Prompt vs Category-Aware Prompt)
    models = {
        "Pretrained Baseline": "lllyasviel/control_v11p_sd15_lineart",
        "100-Step Model": "outputs/controlnet_jewellery/controlnet_jewellery_final",
        "300-Step Model": "outputs/controlnet_jewellery_300/controlnet_jewellery_final",
    }

    results_smoke = {}
    results_cat = {}

    for model_name, model_path in models.items():
        print(f"\n[INFERENCE] Testing Model: {model_name} ({model_path})...")
        cnet = ControlNetModel.from_pretrained(model_path, torch_dtype=torch.float16).to(device)
        pipe = StableDiffusionControlNetPipeline.from_pretrained(
            "runwayml/stable-diffusion-v1-5",
            controlnet=cnet,
            torch_dtype=torch.float16,
            safety_checker=None,
        ).to(device)
        pipe.scheduler = UniPCMultistepScheduler.from_config(pipe.scheduler.config)

        # 1. Run with smoke test prompt (generic)
        gen = torch.Generator(device=device).manual_seed(42)
        with torch.inference_mode():
            out1 = pipe(
                prompt=smoke_prompt,
                negative_prompt=neg_prompt,
                image=cond_img,
                num_inference_steps=20,
                guidance_scale=7.5,
                controlnet_conditioning_scale=0.8,
                generator=gen,
                width=512,
                height=512,
            )
        img1 = out1.images[0]
        img1.save(out_dir / f"{model_name.lower().replace(' ', '_')}_smoke_prompt.png")
        results_smoke[model_name] = img1

        # 2. Run with category-explicit prompt ("solitaire fine jewellery finger ring")
        gen2 = torch.Generator(device=device).manual_seed(42)
        with torch.inference_mode():
            out2 = pipe(
                prompt=category_prompt,
                negative_prompt=neg_prompt,
                image=cond_img,
                num_inference_steps=20,
                guidance_scale=7.5,
                controlnet_conditioning_scale=0.8,
                generator=gen2,
                width=512,
                height=512,
            )
        img2 = out2.images[0]
        img2.save(out_dir / f"{model_name.lower().replace(' ', '_')}_with_ring_prompt.png")
        results_cat[model_name] = img2

        del cnet
        del pipe
        gc.collect()
        torch.cuda.empty_cache()

    # Step 5: Build Multi-Panel Contact Sheet
    w, h = 512, 512
    canvas = Image.new("RGB", (w * 4, h * 2 + 100), (250, 250, 250))
    draw = ImageDraw.Draw(canvas)

    draw.text((20, 15), "INVESTIGATION: ring_train_000.jpg Geometry Analysis", fill=(20, 20, 20))
    draw.text((20, 35), f"Row 1: Production Generic Prompt | Row 2: Category-Explicit Prompt ('ring')", fill=(80, 80, 80))

    # Row 1: Generic Prompt
    canvas.paste(cond_img.resize((w, h)), (0, 60))
    draw.text((15, 60 + h + 5), "LineArt Conditioning Map", fill=(30, 30, 30))

    for idx, (m_name, img) in enumerate(results_smoke.items(), start=1):
        canvas.paste(img.resize((w, h)), (idx * w, 60))
        draw.text((idx * w + 15, 60 + h + 5), f"{m_name} (Generic Prompt)", fill=(30, 30, 30))

    # Row 2: Category-Explicit Prompt
    canvas.paste(src_img.resize((w, h)), (0, 60 + h + 30))
    draw.text((15, 60 + 2 * h + 35), "Source Input Blueprint", fill=(30, 30, 30))

    for idx, (m_name, img) in enumerate(results_cat.items(), start=1):
        canvas.paste(img.resize((w, h)), (idx * w, 60 + h + 30))
        draw.text((idx * w + 15, 60 + 2 * h + 35), f"{m_name} (Prompt: 'ring')", fill=(30, 30, 30))

    comp_path = out_dir / "investigation_comparison_matrix.png"
    canvas.save(comp_path)
    print(f"\n[COMPLETE] Matrix saved to: {comp_path}")


if __name__ == "__main__":
    main()
