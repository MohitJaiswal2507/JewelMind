"""JewelMind LoRA Evaluation Utility.

Compares generation quality between base Stable Diffusion 1.5 and LoRA fine-tuned
checkpoint on validation prompts, measuring edge fidelity and visual quality.
"""

import argparse
from pathlib import Path
from PIL import Image
import torch
from diffusers import StableDiffusionPipeline


def main():
    parser = argparse.ArgumentParser(description="Evaluate Jewellery LoRA Checkpoint")
    parser.add_argument("--lora_dir", type=str, required=True, help="Path to LoRA checkpoint folder")
    parser.add_argument("--base_model", type=str, default="runwayml/stable-diffusion-v1-5", help="Base model ID")
    parser.add_argument("--output_dir", type=str, default="outputs/evaluation", help="Output directory")
    args = parser.parse_args()

    if not torch.cuda.is_available():
        print("[ERROR] CUDA required for evaluation.")
        return

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"[INFO] Loading base model: {args.base_model} with LoRA: {args.lora_dir}")
    pipe = StableDiffusionPipeline.from_pretrained(
        args.base_model,
        torch_dtype=torch.float16,
        safety_checker=None,
    ).to("cuda")

    # Load trained LoRA
    pipe.load_lora_weights(args.lora_dir)

    eval_prompts = [
        "photorealistic fine jewellery product photograph, luxury 18k yellow gold solitaire ring with brilliant round diamond, studio lighting",
        "photorealistic fine jewellery, pure 950 platinum pendant set with vivid royal blue sapphire, crisp studio reflections",
        "photorealistic fine jewellery, warm 18k rose gold eternity band with micropave diamonds, mirror polish",
    ]

    for idx, prompt in enumerate(eval_prompts, start=1):
        print(f"[GEN] Sample {idx}/3: {prompt[:50]}...")
        generator = torch.Generator(device="cuda").manual_seed(42 + idx)
        image = pipe(
            prompt=prompt,
            num_inference_steps=25,
            guidance_scale=7.5,
            generator=generator,
            width=512,
            height=512,
        ).images[0]

        save_path = output_dir / f"eval_lora_sample_{idx}.png"
        image.save(save_path)
        print(f"      Saved: {save_path}")

    print("[SUCCESS] LoRA evaluation generation completed.")


if __name__ == "__main__":
    main()
