"""JewelMind Phase 10 — ControlNet Conditioning Strength A/B Test (0.8 vs 1.0).

Compares ControlNet guidance scales on ring_train_000.jpg using the fine-tuned 300-step checkpoint
to determine optimal geometry preservation and structure stability.
"""

import gc
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


def run_ab_test():
    if not torch.cuda.is_available():
        print("[ERROR] CUDA GPU is required for ControlNet A/B test.")
        sys.exit(1)

    device = torch.device("cuda")
    out_dir = WORKSPACE_ROOT / "outputs" / "ab_test"
    out_dir.mkdir(parents=True, exist_ok=True)

    input_path = WORKSPACE_ROOT / "ai" / "vision" / "datasets" / "sample" / "train" / "images" / "ring_train_000.jpg"
    if not input_path.exists():
        print(f"[ERROR] Target sketch not found: {input_path}")
        sys.exit(1)

    model_path = WORKSPACE_ROOT / "outputs" / "controlnet_jewellery_300" / "controlnet_jewellery_final"
    if not model_path.exists():
        # Fallback to 100-step or pretrained if 300-step path differs
        fallback_300 = WORKSPACE_ROOT / "outputs" / "controlnet_jewellery" / "controlnet_jewellery_final"
        if fallback_300.exists():
            model_path = fallback_300
        else:
            model_path = Path("lllyasviel/control_v11p_sd15_lineart")

    print("=" * 75)
    print("  PHASE 10 — CONTROLNET STRENGTH A/B TEST (0.8 vs 1.0)")
    print(f"  Sketch:      {input_path.name}")
    print(f"  Model:       {model_path}")
    print(f"  Base Model:  runwayml/stable-diffusion-v1-5")
    print(f"  Category:    ring")
    print(f"  Material:    18k yellow gold | Gemstone: round brilliant diamond")
    print(f"  Seed:        42 | Steps: 20 | CFG: 7.5 | Res: 512x512")
    print("=" * 75)

    # 1. Load and save input
    src_img = Image.open(input_path).convert("RGB")
    src_path = out_dir / "input_sketch.png"
    src_img.save(src_path)
    print(f"[1/4] Input sketch saved to: {src_path}")

    # 2. Preprocess Conditioning Map
    processor = LineArtProcessor(target_width=512, target_height=512)
    cond_img, meta = processor.process(src_img, target_width=512, target_height=512)
    cond_path = out_dir / "conditioning_lineart.png"
    cond_img.save(cond_path)
    print(f"[2/4] Conditioning map saved to: {cond_path}")
    print(f"      Edge density: {meta.edge_density:.4f}")

    # 3. Build Prompts
    positive_prompt = build_jewellery_prompt(
        category="ring",
        material="18k yellow gold",
        gemstone="round brilliant diamond",
    )
    negative_prompt = build_negative_prompt()
    print(f"[PROMPT] Positive: '{positive_prompt}'")
    print(f"[PROMPT] Negative: '{negative_prompt[:80]}...'")

    # 4. Load Pipeline
    print("\n[PIPELINE] Loading ControlNet and SD 1.5 into GPU VRAM (fp16)...")
    cnet = ControlNetModel.from_pretrained(str(model_path), torch_dtype=torch.float16).to(device)
    pipe = StableDiffusionControlNetPipeline.from_pretrained(
        "runwayml/stable-diffusion-v1-5",
        controlnet=cnet,
        torch_dtype=torch.float16,
        safety_checker=None,
    ).to(device)
    pipe.scheduler = UniPCMultistepScheduler.from_config(pipe.scheduler.config)

    # 5. Generate with Strength = 0.8
    print("\n[INFERENCE A] Generating with ControlNet Strength = 0.8 (seed=42, 20 steps)...")
    gen_a = torch.Generator(device=device).manual_seed(42)
    t0 = time.perf_counter()
    with torch.inference_mode():
        out_a = pipe(
            prompt=positive_prompt,
            negative_prompt=negative_prompt,
            image=cond_img,
            num_inference_steps=20,
            guidance_scale=7.5,
            controlnet_conditioning_scale=0.8,
            generator=gen_a,
            width=512,
            height=512,
        )
    lat_a = (time.perf_counter() - t0) * 1000
    img_a = out_a.images[0]
    path_a = out_dir / "render_strength_0_8.png"
    img_a.save(path_a)
    print(f"              Saved to: {path_a} (Latency: {lat_a:.1f} ms)")

    # 6. Generate with Strength = 1.0
    print("\n[INFERENCE B] Generating with ControlNet Strength = 1.0 (seed=42, 20 steps)...")
    gen_b = torch.Generator(device=device).manual_seed(42)
    t1 = time.perf_counter()
    with torch.inference_mode():
        out_b = pipe(
            prompt=positive_prompt,
            negative_prompt=negative_prompt,
            image=cond_img,
            num_inference_steps=20,
            guidance_scale=7.5,
            controlnet_conditioning_scale=1.0,
            generator=gen_b,
            width=512,
            height=512,
        )
    lat_b = (time.perf_counter() - t1) * 1000
    img_b = out_b.images[0]
    path_b = out_dir / "render_strength_1_0.png"
    img_b.save(path_b)
    print(f"              Saved to: {path_b} (Latency: {lat_b:.1f} ms)")

    # Cleanup GPU memory
    del cnet
    del pipe
    gc.collect()
    torch.cuda.empty_cache()

    # 7. Generate 4-Panel Side-by-Side Comparison Matrix
    w, h = 512, 512
    margin_top = 80
    canvas_w = w * 4
    canvas_h = h + margin_top + 40
    canvas = Image.new("RGB", (canvas_w, canvas_h), (245, 245, 248))
    draw = ImageDraw.Draw(canvas)

    # Title header
    draw.text((30, 20), "JEWELMIND PHASE 10 — CONTROLNET CONDITIONING STRENGTH A/B TEST", fill=(20, 20, 30))
    draw.text((30, 45), f"Model: 300-Step Checkpoint | Category: ring | Seed: 42 | Steps: 20 | CFG: 7.5", fill=(90, 90, 100))

    panels = [
        ("1. Input Sketch (Blueprint)", src_img.resize((w, h))),
        ("2. LineArt Conditioning Map", cond_img.resize((w, h))),
        ("3. Render (Strength = 0.8)", img_a.resize((w, h))),
        ("4. Render (Strength = 1.0)", img_b.resize((w, h))),
    ]

    for idx, (label, img) in enumerate(panels):
        x_offset = idx * w
        canvas.paste(img, (x_offset, margin_top))
        draw.text((x_offset + 15, margin_top + h + 10), label, fill=(30, 30, 40))

    matrix_path = out_dir / "ab_comparison_matrix.png"
    canvas.save(matrix_path)
    print("\n" + "=" * 75)
    print(f"[COMPLETE] 4-Panel comparison contact sheet saved to:\n  {matrix_path}")
    print("=" * 75)


if __name__ == "__main__":
    run_ab_test()
