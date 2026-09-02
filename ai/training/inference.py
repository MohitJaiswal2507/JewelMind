"""JewelMind LoRA + ControlNet Inference Utility.

Combines base Stable Diffusion 1.5, trained jewellery LoRA weights, and ControlNet LineArt
to render an input sketch with enhanced fine jewellery domain specificity.
"""

import argparse
from pathlib import Path
from PIL import Image
import torch
from diffusers import ControlNetModel, StableDiffusionControlNetPipeline

from ai.rendering.preprocessing.lineart import LineArtProcessor


def main():
    parser = argparse.ArgumentParser(description="Inference with Base Model + ControlNet + LoRA")
    parser.add_argument("--sketch", type=str, required=True, help="Input sketch path")
    parser.add_argument("--lora_dir", type=str, default=None, help="Optional path to LoRA checkpoint folder")
    parser.add_argument("--prompt", type=str, default="photorealistic fine jewellery ring, 18k yellow gold with diamond, studio lighting", help="Prompt text")
    parser.add_argument("--output", type=str, default="outputs/lora_render.png", help="Output image path")
    parser.add_argument("--seed", type=int, default=42, help="Seed for generation")
    args = parser.parse_args()

    if not torch.cuda.is_available():
        print("[ERROR] CUDA required for rendering.")
        return

    # Preprocess sketch
    processor = LineArtProcessor(target_width=512, target_height=512)
    sketch_img = Image.open(args.sketch)
    cond_img, _ = processor.process(sketch_img, target_width=512, target_height=512)

    # Load ControlNet & Pipeline
    print("[INFO] Loading ControlNet LineArt...")
    controlnet = ControlNetModel.from_pretrained(
        "lllyasviel/control_v11p_sd15_lineart",
        torch_dtype=torch.float16,
    ).to("cuda")

    pipe = StableDiffusionControlNetPipeline.from_pretrained(
        "runwayml/stable-diffusion-v1-5",
        controlnet=controlnet,
        torch_dtype=torch.float16,
        safety_checker=None,
    ).to("cuda")

    if args.lora_dir and Path(args.lora_dir).exists():
        print(f"[INFO] Applying jewellery LoRA adapter from: {args.lora_dir}")
        pipe.load_lora_weights(args.lora_dir)

    generator = torch.Generator(device="cuda").manual_seed(args.seed)
    print(f"[INFO] Rendering: '{args.prompt}'")
    rendered = pipe(
        prompt=args.prompt,
        image=cond_img,
        num_inference_steps=20,
        guidance_scale=7.5,
        controlnet_conditioning_scale=0.8,
        generator=generator,
        width=512,
        height=512,
    ).images[0]

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    rendered.save(out_path)
    print(f"[SUCCESS] Saved rendered output to: {out_path}")


if __name__ == "__main__":
    main()
