"""JewelMind Jewellery LoRA Fine-Tuning Script.

IMPORTANT: Antigravity MUST NEVER run this script automatically.
This script is manually invoked by the human operator on the local RTX 4060 GPU:
    python ai/training/train_lora.py --config configs/jewellery_lora.yaml
"""

import argparse
import json
import logging
import math
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any
import yaml
from PIL import Image

import torch
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from tqdm.auto import tqdm

from diffusers import AutoencoderKL, DDPMScheduler, UNet2DConditionModel
from diffusers.optimization import get_scheduler
from peft import LoraConfig, get_peft_model
from transformers import CLIPTextModel, CLIPTokenizer

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%m/%d/%Y %H:%M:%S",
    level=logging.INFO,
)
logger = logging.getLogger("jewelmind.train_lora")


class JewelleryCaptionDataset(Dataset):
    """Dataset reading images and text captions from directory with metadata.jsonl."""

    def __init__(self, data_dir: str, tokenizer: CLIPTokenizer, size: int = 512):
        self.data_dir = Path(data_dir)
        self.tokenizer = tokenizer
        self.size = size
        self.entries = []

        meta_file = self.data_dir / "metadata.jsonl"
        if not meta_file.exists():
            raise FileNotFoundError(f"metadata.jsonl not found in {data_dir}")

        with open(meta_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    self.entries.append(json.loads(line.strip()))

        self.transforms = transforms.Compose([
            transforms.Resize((size, size), interpolation=transforms.InterpolationMode.BILINEAR),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.ToTensor(),
            transforms.Normalize([0.5], [0.5]),
        ])

    def __len__(self):
        return len(self.entries)

    def __getitem__(self, idx):
        entry = self.entries[idx]
        img_path = self.data_dir / entry["file_name"]
        image = Image.open(img_path).convert("RGB")
        pixel_values = self.transforms(image)

        # Tokenize prompt text
        inputs = self.tokenizer(
            entry["text"],
            padding="max_length",
            truncation=True,
            max_length=self.tokenizer.model_max_length,
            return_tensors="pt",
        )

        return {
            "pixel_values": pixel_values,
            "input_ids": inputs.input_ids.squeeze(0),
        }


def find_latest_checkpoint(checkpoint_dir: Path):
    """Find the most recent checkpoint step directory for resumable training."""
    if not checkpoint_dir.exists():
        return None
    checkpoints = [
        d for d in checkpoint_dir.iterdir()
        if d.is_dir() and d.name.startswith("checkpoint-")
    ]
    if not checkpoints:
        return None
    # Sort by step number
    checkpoints.sort(key=lambda x: int(x.name.split("-")[1]))
    return checkpoints[-1]


def main():
    parser = argparse.ArgumentParser(description="JewelMind Manual Jewellery LoRA Trainer")
    parser.add_argument("--config", type=str, default="configs/jewellery_lora.yaml", help="Path to training config YAML")
    parser.add_argument("--resume", type=str, default=None, help="Explicit checkpoint folder to resume from")
    args = parser.parse_args()

    # Load configuration
    config_path = Path(args.config)
    if not config_path.exists():
        logger.error("Configuration file not found: %s", config_path)
        sys.exit(1)

    with open(config_path, "r", encoding="utf-8") as f:
        cfg: Dict[str, Any] = yaml.safe_load(f)

    # Verify CUDA
    if not torch.cuda.is_available():
        logger.error("CUDA is not available! Training requires local NVIDIA GPU (RTX 4060).")
        sys.exit(1)

    device = torch.device("cuda")
    vram_mb = torch.cuda.get_device_properties(0).total_memory / (1024 * 1024)
    logger.info("Starting training on: %s (%.0f MiB VRAM)", torch.cuda.get_device_name(0), vram_mb)

    # Set seed
    seed = cfg["training"].get("seed", 42)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)

    # Output setup
    output_dir = Path(cfg["output"]["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    checkpoints_dir = output_dir / "checkpoints"
    checkpoints_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load Tokenizer and Models
    model_id = cfg["model"]["pretrained_model_name_or_path"]
    logger.info("Loading base diffusion components from: %s", model_id)

    tokenizer = CLIPTokenizer.from_pretrained(model_id, subfolder="tokenizer")
    text_encoder = CLIPTextModel.from_pretrained(model_id, subfolder="text_encoder")
    vae = AutoencoderKL.from_pretrained(model_id, subfolder="vae")
    unet = UNet2DConditionModel.from_pretrained(model_id, subfolder="unet")
    noise_scheduler = DDPMScheduler.from_pretrained(model_id, subfolder="scheduler")

    # Freeze VAE and Text Encoder to save VRAM
    vae.requires_grad_(False)
    text_encoder.requires_grad_(False)
    vae.to(device, dtype=torch.float16)
    text_encoder.to(device, dtype=torch.float16)

    # Enable Gradient Checkpointing on UNet to fit 8GB VRAM
    if cfg["training"].get("gradient_checkpointing", True):
        unet.enable_gradient_checkpointing()
        logger.info("Enabled UNet gradient checkpointing for 8GB VRAM optimization.")

    # 2. Configure LoRA via PEFT
    lora_rank = cfg["model"].get("lora_rank", 16)
    lora_alpha = cfg["model"].get("lora_alpha", 32)
    lora_dropout = cfg["model"].get("lora_dropout", 0.05)
    target_modules = cfg["model"].get("target_modules", ["to_k", "to_q", "to_v", "to_out.0"])

    lora_config = LoraConfig(
        r=lora_rank,
        lora_alpha=lora_alpha,
        target_modules=target_modules,
        lora_dropout=lora_dropout,
        bias="none",
    )
    unet = get_peft_model(unet, lora_config)
    unet.to(device)
    unet.print_trainable_parameters()

    # 3. Dataset & Dataloader
    train_dir = cfg["dataset"]["train_data_dir"]
    dataset = JewelleryCaptionDataset(data_dir=train_dir, tokenizer=tokenizer, size=cfg["dataset"].get("resolution", 512))
    train_dataloader = DataLoader(
        dataset,
        batch_size=cfg["training"].get("train_batch_size", 1),
        shuffle=True,
        num_workers=0,
    )

    # 4. Optimizer & Scheduler
    lr = float(cfg["training"].get("learning_rate", 1e-4))
    optimizer = torch.optim.AdamW(
        unet.parameters(),
        lr=lr,
        betas=(cfg["optimizer"].get("beta1", 0.9), cfg["optimizer"].get("beta2", 0.999)),
        weight_decay=float(cfg["optimizer"].get("weight_decay", 1e-2)),
    )

    max_train_steps = cfg["training"].get("max_train_steps", 1000)
    lr_scheduler = get_scheduler(
        cfg["training"].get("lr_scheduler", "cosine"),
        optimizer=optimizer,
        num_warmup_steps=cfg["training"].get("lr_warmup_steps", 50),
        num_training_steps=max_train_steps,
    )

    # 5. Checkpoint Resume Logic
    starting_step = 0
    resume_target = args.resume or cfg["training"].get("resume_from_checkpoint")
    if resume_target == "latest":
        resume_checkpoint = find_latest_checkpoint(checkpoints_dir)
    elif resume_target:
        resume_checkpoint = Path(resume_target)
    else:
        resume_checkpoint = None

    if resume_checkpoint and resume_checkpoint.exists():
        logger.info("Resuming training from checkpoint: %s", resume_checkpoint)
        adapter_weights = resume_checkpoint / "adapter_model.bin"
        if not adapter_weights.exists():
            adapter_weights = resume_checkpoint / "adapter_model.safetensors"
        unet.load_adapter(str(resume_checkpoint), adapter_name="default")
        starting_step = int(resume_checkpoint.name.split("-")[1])
        logger.info("Successfully resumed at step: %d (skipping steps 0 to %d)", starting_step, starting_step)
    else:
        logger.info("Starting fresh training run from step 0.")

    # 6. Training Loop
    grad_accum_steps = cfg["training"].get("gradient_accumulation_steps", 4)
    checkpoint_interval = cfg["training"].get("checkpointing_steps", 200)
    scaler = torch.cuda.amp.GradScaler(enabled=True)

    progress_bar = tqdm(range(starting_step, max_train_steps), desc="Training Steps", initial=starting_step, total=max_train_steps)
    global_step = starting_step

    logger.info("Training started. Monitor GPU VRAM with: nvidia-smi -l 2")

    for step in progress_bar:
        for batch in train_dataloader:
            if global_step >= max_train_steps:
                break

            unet.train()
            # Encode images to latents with frozen VAE
            with torch.no_grad():
                pixel_values = batch["pixel_values"].to(device, dtype=torch.float16)
                latents = vae.encode(pixel_values).latent_dist.sample() * 0.18215

            # Sample Gaussian noise
            noise = torch.randn_like(latents)
            timesteps = torch.randint(0, noise_scheduler.config.num_train_timesteps, (latents.shape[0],), device=device).long()
            noisy_latents = noise_scheduler.add_noise(latents, noise, timesteps)

            # Get text conditioning embedding
            with torch.no_grad():
                encoder_hidden_states = text_encoder(batch["input_ids"].to(device))[0]

            # Forward pass with mixed precision
            with torch.cuda.amp.autocast(dtype=torch.float16):
                model_pred = unet(noisy_latents, timesteps, encoder_hidden_states).sample
                loss = F.mse_loss(model_pred.float(), noise.float(), reduction="mean")
                loss = loss / grad_accum_steps

            scaler.scale(loss).backward()

            if (global_step + 1) % grad_accum_steps == 0:
                scaler.step(optimizer)
                scaler.update()
                optimizer.zero_grad()
                lr_scheduler.step()

            global_step += 1
            progress_bar.set_postfix({"loss": f"{loss.item() * grad_accum_steps:.4f}", "lr": f"{lr_scheduler.get_last_lr()[0]:.2e}"})

            # Checkpoint saving
            if global_step % checkpoint_interval == 0 or global_step == max_train_steps:
                save_dir = checkpoints_dir / f"checkpoint-{global_step}"
                logger.info("Saving checkpoint at step %d -> %s", global_step, save_dir)
                unet.save_pretrained(str(save_dir))
                # Also save a symlink or folder 'checkpoint-last' for seamless resume
                last_dir = checkpoints_dir / "checkpoint-last"
                unet.save_pretrained(str(last_dir))

    # Save final model
    final_dir = output_dir / "jewellery_lora_final"
    logger.info("Training complete! Saving final LoRA weights to: %s", final_dir)
    unet.save_pretrained(str(final_dir))
    logger.info("SUCCESS: LoRA weights ready for inference.")


if __name__ == "__main__":
    main()
