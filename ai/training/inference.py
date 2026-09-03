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


def load_peft_lora_to_unet(unet, lora_dir: str, adapter_name: str = "default") -> None:
    """Loads a PEFT-trained LoRA adapter into a UNet2DConditionModel preserving exact saved hyperparameters."""
    lora_path = Path(lora_dir)
    if not lora_path.exists():
        raise FileNotFoundError(f"LoRA path does not exist: {lora_dir}")

    if lora_path.is_file():
        model_dir = lora_path.parent
        weights_file = lora_path
    else:
        model_dir = lora_path
        if (lora_path / "adapter_model.safetensors").exists():
            weights_file = lora_path / "adapter_model.safetensors"
        elif (lora_path / "pytorch_lora_weights.safetensors").exists():
            weights_file = lora_path / "pytorch_lora_weights.safetensors"
        elif (lora_path / "adapter_model.bin").exists():
            weights_file = lora_path / "adapter_model.bin"
        else:
            weights_file = None

    adapter_config_file = model_dir / "adapter_config.json"

    if adapter_config_file.exists() and weights_file is not None:
        print(f"[INFO] Loading PEFT LoRA adapter with saved config from: {model_dir}")
        from peft import LoraConfig, inject_adapter_in_model, set_peft_model_state_dict
        from safetensors.torch import load_file

        peft_config = LoraConfig.from_pretrained(str(model_dir))
        if weights_file.suffix == ".safetensors":
            state_dict = load_file(str(weights_file))
        else:
            state_dict = torch.load(str(weights_file), map_location="cpu")

        inject_adapter_in_model(peft_config, unet, adapter_name=adapter_name)
        set_peft_model_state_dict(unet, state_dict, adapter_name=adapter_name)
        unet._hf_peft_config_loaded = True
    else:
        weight_name = weights_file.name if weights_file else None
        print(f"[INFO] Loading PEFT LoRA adapter into UNet from: {lora_dir} (weight_name={weight_name})")
        unet.load_lora_adapter(
            str(model_dir),
            weight_name=weight_name,
            prefix="base_model.model",
            adapter_name=adapter_name,
        )

    # Diagnostic verification
    peft_configs = getattr(unet, "peft_config", {})
    active_adapters = unet.active_adapters() if callable(getattr(unet, "active_adapters", None)) else getattr(unet, "active_adapters", None)

    lora_modules = [name for name, mod in unet.named_modules() if hasattr(mod, "lora_A")]
    total_lora_params = sum(
        p.numel() for mod in unet.modules() if hasattr(mod, "lora_A")
        for p in list(mod.lora_A.parameters()) + list(mod.lora_B.parameters())
    )

    if len(lora_modules) == 0:
        raise RuntimeError(f"LoRA adapter injection failed: 0 LoRA modules found in UNet after loading {lora_dir}")

    print("[DIAGNOSTIC] PEFT LoRA Adapter Successfully Injected into UNet:")
    print(f"  - Adapter Name: {adapter_name}")
    print(f"  - Active Adapters: {active_adapters}")
    print(f"  - Injected LoRA Modules: {len(lora_modules)}")
    print(f"  - Total Injected LoRA Parameters: {total_lora_params:,}")
    if adapter_name in peft_configs:
        cfg = peft_configs[adapter_name]
        targets = sorted(list(cfg.target_modules)) if isinstance(cfg.target_modules, (set, list)) else cfg.target_modules
        print(f"  - PEFT Config [{adapter_name}]: rank={cfg.r}, alpha={cfg.lora_alpha}, dropout={cfg.lora_dropout}, target_modules={targets}")
    print(f"  - Sample Injected Modules: {lora_modules[:4]}")


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
        load_peft_lora_to_unet(pipe.unet, args.lora_dir)

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
