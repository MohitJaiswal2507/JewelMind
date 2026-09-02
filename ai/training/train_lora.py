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
import shutil
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import yaml
from PIL import Image

import torch
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from tqdm.auto import tqdm

from diffusers import AutoencoderKL, DDPMScheduler, UNet2DConditionModel
from diffusers.optimization import get_scheduler
try:
    from peft import LoraConfig, get_peft_model
except ImportError:
    LoraConfig = None
    get_peft_model = None
from transformers import CLIPTextModel, CLIPTokenizer

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%m/%d/%Y %H:%M:%S",
    level=logging.INFO,
)
logger = logging.getLogger("jewelmind.train_lora")


class JewelleryCaptionDataset(Dataset):
    """Dataset reading jewellery photos and metadata from directory with metadata.jsonl.
    
    Supports both legacy and rich metadata schemas:
      - file_name / target_image / image
      - text / caption / prompt
      - category, metal, gemstone, source
    """

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
                line_str = line.strip()
                if line_str:
                    try:
                        self.entries.append(json.loads(line_str))
                    except json.JSONDecodeError:
                        continue

        # Deterministic normalization: NO RandomHorizontalFlip to preserve jewellery geometry
        self.transforms = transforms.Compose([
            transforms.Resize((size, size), interpolation=transforms.InterpolationMode.BILINEAR),
            transforms.ToTensor(),
            transforms.Normalize([0.5], [0.5]),
        ])

    def __len__(self):
        return len(self.entries)

    def __getitem__(self, idx):
        entry = self.entries[idx]

        # Resolve image filename across supported schema variations
        img_rel_path = (
            entry.get("file_name")
            or entry.get("target_image")
            or entry.get("image")
        )
        if not img_rel_path:
            raise KeyError(f"Entry {idx} in {self.data_dir} missing image filename key ('file_name', 'target_image', or 'image').")

        img_path = self.data_dir / img_rel_path
        image = Image.open(img_path).convert("RGB")
        pixel_values = self.transforms(image)

        # Resolve prompt text across supported schema variations
        caption_text = (
            entry.get("text")
            or entry.get("caption")
            or entry.get("prompt")
            or ""
        )

        inputs = self.tokenizer(
            caption_text,
            padding="max_length",
            truncation=True,
            max_length=self.tokenizer.model_max_length,
            return_tensors="pt",
        )

        sample = {
            "pixel_values": pixel_values,
            "input_ids": inputs.input_ids.squeeze(0),
        }

        # Preserve optional semantic attributes if present in dataset
        for attr in ("category", "metal", "gemstone", "source"):
            if attr in entry:
                sample[attr] = entry[attr]

        return sample


def find_latest_checkpoint(checkpoint_dir: Path) -> Optional[Path]:
    """Find the most recent numeric checkpoint step directory or checkpoint-last for resumable training.
    
    Safe against non-numeric folder names like checkpoint-last.
    """
    if not checkpoint_dir.exists():
        return None

    numeric_checkpoints: List[Tuple[int, Path]] = []
    for d in checkpoint_dir.iterdir():
        if d.is_dir() and d.name.startswith("checkpoint-"):
            step_part = d.name.replace("checkpoint-", "")
            if step_part.isdigit():
                numeric_checkpoints.append((int(step_part), d))

    if numeric_checkpoints:
        numeric_checkpoints.sort(key=lambda x: x[0])
        return numeric_checkpoints[-1][1]

    # Fallback to checkpoint-last if present
    last_dir = checkpoint_dir / "checkpoint-last"
    if last_dir.exists() and last_dir.is_dir():
        return last_dir

    return None


def get_checkpoint_step(checkpoint_path: Path) -> int:
    """Extract global optimizer step safely from trainer_state.json or numeric folder name."""
    state_file = checkpoint_path / "trainer_state.json"
    if state_file.exists():
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                state = json.load(f)
                return int(state.get("global_step", 0))
        except Exception as err:
            logger.warning("Failed to read trainer_state.json from %s: %s", checkpoint_path, err)

    name = checkpoint_path.name
    if name.startswith("checkpoint-"):
        part = name.replace("checkpoint-", "")
        if part.isdigit():
            return int(part)
    return 0


def save_checkpoint(
    save_dir: Path,
    unet: torch.nn.Module,
    optimizer: torch.optim.Optimizer,
    lr_scheduler: Any,
    scaler: torch.cuda.amp.GradScaler,
    global_step: int,
    epoch: int,
) -> None:
    """Persist LoRA adapter weights, optimizer, scheduler, scaler, and trainer state."""
    save_dir.mkdir(parents=True, exist_ok=True)
    
    # Save PEFT adapter weights (or raw state dict if raw torch module)
    if hasattr(unet, "save_pretrained"):
        unet.save_pretrained(str(save_dir))
    else:
        torch.save(unet.state_dict(), save_dir / "adapter_model.pt")
    
    # Save optimization and scheduler states for genuine resumability
    torch.save(optimizer.state_dict(), save_dir / "optimizer.pt")
    torch.save(lr_scheduler.state_dict(), save_dir / "scheduler.pt")
    torch.save(scaler.state_dict(), save_dir / "scaler.pt")

    state = {
        "global_step": global_step,
        "epoch": epoch,
        "timestamp": time.time(),
    }
    with open(save_dir / "trainer_state.json", "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def evaluate_validation_loss(
    unet: torch.nn.Module,
    vae: AutoencoderKL,
    text_encoder: CLIPTextModel,
    noise_scheduler: DDPMScheduler,
    val_dataloader: DataLoader,
    device: torch.device,
    max_val_batches: int = 15,
) -> Optional[float]:
    """Compute validation loss on validation split without modifying model weights."""
    if val_dataloader is None or len(val_dataloader) == 0:
        return None

    unet.eval()
    val_losses = []
    model_dtype = torch.float16 if device.type == "cuda" else torch.float32

    with torch.no_grad():
        for b_idx, batch in enumerate(val_dataloader):
            if b_idx >= max_val_batches:
                break

            pixel_values = batch["pixel_values"].to(device, dtype=model_dtype)
            latents = vae.encode(pixel_values).latent_dist.sample() * 0.18215

            noise = torch.randn_like(latents)
            timesteps = torch.randint(
                0, noise_scheduler.config.num_train_timesteps, (latents.shape[0],), device=device
            ).long()
            noisy_latents = noise_scheduler.add_noise(latents, noise, timesteps)

            encoder_hidden_states = text_encoder(batch["input_ids"].to(device))[0]

            with torch.autocast(device_type=device.type, dtype=model_dtype, enabled=(device.type == "cuda")):
                model_pred = unet(noisy_latents, timesteps, encoder_hidden_states).sample
                val_loss = F.mse_loss(model_pred.float(), noise.float(), reduction="mean")
                val_losses.append(val_loss.item())

    unet.train()
    if not val_losses:
        return None
    return sum(val_losses) / len(val_losses)


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
    logger.info("Target GPU: %s (%.0f MiB VRAM)", torch.cuda.get_device_name(0), vram_mb)

    # Set seed
    seed = cfg["training"].get("seed", 42)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)

    # Output directories
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

    # Freeze VAE and Text Encoder to save VRAM on 8GB GPU
    vae.requires_grad_(False)
    text_encoder.requires_grad_(False)
    vae.to(device, dtype=torch.float16)
    text_encoder.to(device, dtype=torch.float16)

    # Enable Gradient Checkpointing on UNet to fit 8GB VRAM
    if cfg["training"].get("gradient_checkpointing", True):
        unet.enable_gradient_checkpointing()
        logger.info("Enabled UNet gradient checkpointing.")

    # 2. Configure LoRA via PEFT
    if LoraConfig is None or get_peft_model is None:
        logger.error("The 'peft' library is required for training. Please run: pip install peft")
        sys.exit(1)

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

    # 3. Dataloaders (Train & Validation)
    train_dir = cfg["dataset"]["train_data_dir"]
    resolution = cfg["dataset"].get("resolution", 512)
    train_dataset = JewelleryCaptionDataset(data_dir=train_dir, tokenizer=tokenizer, size=resolution)
    train_batch_size = cfg["training"].get("train_batch_size", 1)
    train_dataloader = DataLoader(
        train_dataset,
        batch_size=train_batch_size,
        shuffle=True,
        num_workers=0,
    )

    val_dir = cfg["dataset"].get("val_data_dir")
    val_dataloader = None
    if val_dir and Path(val_dir).exists() and (Path(val_dir) / "metadata.jsonl").exists():
        val_dataset = JewelleryCaptionDataset(data_dir=val_dir, tokenizer=tokenizer, size=resolution)
        val_dataloader = DataLoader(val_dataset, batch_size=1, shuffle=False, num_workers=0)
        logger.info("Validation dataset active: %d samples in %s", len(val_dataset), val_dir)

    # 4. Optimizer & LR Scheduler
    # global_step strictly represents OPTIMIZER updates
    max_train_steps = cfg["training"].get("max_train_steps", 1000)
    lr = float(cfg["training"].get("learning_rate", 1e-4))
    optimizer = torch.optim.AdamW(
        unet.parameters(),
        lr=lr,
        betas=(cfg["optimizer"].get("beta1", 0.9), cfg["optimizer"].get("beta2", 0.999)),
        weight_decay=float(cfg["optimizer"].get("weight_decay", 1e-2)),
    )

    lr_scheduler = get_scheduler(
        cfg["training"].get("lr_scheduler", "cosine"),
        optimizer=optimizer,
        num_warmup_steps=cfg["training"].get("lr_warmup_steps", 50),
        num_training_steps=max_train_steps,
    )
    scaler = torch.cuda.amp.GradScaler(enabled=True)

    # 5. Checkpoint Resume Logic
    starting_step = 0
    starting_epoch = 0
    resume_target = args.resume or cfg["training"].get("resume_from_checkpoint")
    if resume_target == "latest":
        resume_checkpoint = find_latest_checkpoint(checkpoints_dir)
    elif resume_target:
        resume_checkpoint = Path(resume_target)
    else:
        resume_checkpoint = None

    if resume_checkpoint and resume_checkpoint.exists():
        logger.info("Resuming training from checkpoint: %s", resume_checkpoint)
        
        # Load adapter weights
        unet.load_adapter(str(resume_checkpoint), adapter_name="default")
        starting_step = get_checkpoint_step(resume_checkpoint)

        # Restore optimizer state if saved
        opt_path = resume_checkpoint / "optimizer.pt"
        if opt_path.exists():
            try:
                optimizer.load_state_dict(torch.load(opt_path, map_location=device))
                logger.info("Restored optimizer momentum and state.")
            except Exception as e:
                logger.warning("Could not restore optimizer state: %s", e)

        # Restore scheduler state if saved
        sched_path = resume_checkpoint / "scheduler.pt"
        if sched_path.exists():
            try:
                lr_scheduler.load_state_dict(torch.load(sched_path))
                logger.info("Restored learning rate scheduler state.")
            except Exception as e:
                logger.warning("Could not restore scheduler state: %s", e)

        # Restore scaler state if saved
        scaler_path = resume_checkpoint / "scaler.pt"
        if scaler_path.exists():
            try:
                scaler.load_state_dict(torch.load(scaler_path))
                logger.info("Restored GradScaler state.")
            except Exception as e:
                logger.warning("Could not restore scaler state: %s", e)

        state_file = resume_checkpoint / "trainer_state.json"
        if state_file.exists():
            try:
                with open(state_file, "r", encoding="utf-8") as f:
                    state_data = json.load(f)
                    starting_epoch = state_data.get("epoch", 0)
            except Exception:
                pass

        logger.info("Successfully resumed at optimizer step %d / %d (epoch %d)", starting_step, max_train_steps, starting_epoch)
    else:
        logger.info("Starting fresh training run from step 0.")

    # 6. Training Loop
    grad_accum_steps = cfg["training"].get("gradient_accumulation_steps", 4)
    checkpoint_interval = cfg["training"].get("checkpointing_steps", 200)

    global_step = starting_step
    epoch = starting_epoch

    # Progress bar strictly tracks global optimizer steps
    progress_bar = tqdm(
        total=max_train_steps,
        initial=starting_step,
        desc="Optimizer Steps",
        dynamic_ncols=True,
    )

    accumulated_loss = 0.0
    optimizer.zero_grad()
    unet.train()

    logger.info("Manual training active. Monitor VRAM via: nvidia-smi -l 2")

    while global_step < max_train_steps:
        epoch += 1
        for batch_idx, batch in enumerate(train_dataloader):
            # Encode target images to latents
            with torch.no_grad():
                pixel_values = batch["pixel_values"].to(device, dtype=torch.float16)
                latents = vae.encode(pixel_values).latent_dist.sample() * 0.18215

            noise = torch.randn_like(latents)
            timesteps = torch.randint(
                0, noise_scheduler.config.num_train_timesteps, (latents.shape[0],), device=device
            ).long()
            noisy_latents = noise_scheduler.add_noise(latents, noise, timesteps)

            with torch.no_grad():
                encoder_hidden_states = text_encoder(batch["input_ids"].to(device))[0]

            with torch.cuda.amp.autocast(dtype=torch.float16):
                model_pred = unet(noisy_latents, timesteps, encoder_hidden_states).sample
                raw_loss = F.mse_loss(model_pred.float(), noise.float(), reduction="mean")
                loss = raw_loss / grad_accum_steps

            scaler.scale(loss).backward()
            accumulated_loss += raw_loss.item()

            # Perform optimizer step upon completing accumulation window
            if (batch_idx + 1) % grad_accum_steps == 0 or (batch_idx + 1) == len(train_dataloader):
                scaler.step(optimizer)
                scaler.update()
                optimizer.zero_grad()
                lr_scheduler.step()

                global_step += 1
                progress_bar.update(1)

                avg_step_loss = accumulated_loss / grad_accum_steps
                accumulated_loss = 0.0

                current_lr = lr_scheduler.get_last_lr()[0]
                progress_bar.set_postfix({"loss": f"{avg_step_loss:.4f}", "lr": f"{current_lr:.2e}", "epoch": epoch})

                # Checkpoint saving & Validation loss tracking
                if global_step % checkpoint_interval == 0 or global_step == max_train_steps:
                    val_loss_val = None
                    if val_dataloader is not None:
                        val_loss_val = evaluate_validation_loss(
                            unet, vae, text_encoder, noise_scheduler, val_dataloader, device
                        )
                        if val_loss_val is not None:
                            logger.info("Step %d | Validation Loss: %.4f", global_step, val_loss_val)

                    save_dir = checkpoints_dir / f"checkpoint-{global_step}"
                    logger.info("Saving checkpoint at optimizer step %d -> %s", global_step, save_dir)
                    save_checkpoint(
                        save_dir=save_dir,
                        unet=unet,
                        optimizer=optimizer,
                        lr_scheduler=lr_scheduler,
                        scaler=scaler,
                        global_step=global_step,
                        epoch=epoch,
                    )

                    # Update checkpoint-last cleanly
                    last_dir = checkpoints_dir / "checkpoint-last"
                    save_checkpoint(
                        save_dir=last_dir,
                        unet=unet,
                        optimizer=optimizer,
                        lr_scheduler=lr_scheduler,
                        scaler=scaler,
                        global_step=global_step,
                        epoch=epoch,
                    )

                if global_step >= max_train_steps:
                    break

    progress_bar.close()

    # Save final model
    final_dir = output_dir / "jewellery_lora_final"
    logger.info("Training complete! Saving final LoRA weights to: %s", final_dir)
    unet.save_pretrained(str(final_dir))
    logger.info("SUCCESS: LoRA weights ready for inference.")


if __name__ == "__main__":
    main()
