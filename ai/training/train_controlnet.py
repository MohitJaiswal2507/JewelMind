"""JewelMind Jewellery ControlNet Training Infrastructure.

IMPORTANT: Antigravity MUST NEVER run long-running training loops automatically.
This script is executed manually by the developer on the local RTX 4060 GPU:
    python scripts/train_controlnet.py --config configs/controlnet_jewellery.yaml --smoke_test
"""

import argparse
import gc
import json
import logging
import math
import os
import random
import shutil
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import yaml
from PIL import Image

import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader
from tqdm.auto import tqdm

from diffusers import (
    AutoencoderKL,
    ControlNetModel,
    DDPMScheduler,
    UNet2DConditionModel,
)
from diffusers.optimization import get_scheduler
from transformers import CLIPTextModel, CLIPTokenizer

from ai.training.dataset_controlnet import ControlNetJewelleryDataset

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%m/%d/%Y %H:%M:%S",
    level=logging.INFO,
)
logger = logging.getLogger("jewelmind.train_controlnet")


def set_seed(seed: int = 42) -> None:
    """Set random seeds for reproducibility across Python, NumPy, and PyTorch."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def get_gpu_memory_report() -> Dict[str, Any]:
    """Retrieve detailed GPU memory metrics distinguishing physical, allocated, and reserved memory."""
    if not torch.cuda.is_available():
        return {
            "cuda_available": False,
            "device_name": "CPU",
            "physical_total_mb": 0.0,
            "current_allocated_mb": 0.0,
            "current_reserved_mb": 0.0,
            "peak_allocated_mb": 0.0,
            "peak_reserved_mb": 0.0,
            # Backward-compatibility keys
            "vram_total_mb": 0.0,
            "vram_allocated_mb": 0.0,
            "vram_reserved_mb": 0.0,
            "vram_peak_mb": 0.0,
        }

    props = torch.cuda.get_device_properties(0)
    total_mb = props.total_memory / (1024 * 1024)
    allocated_mb = torch.cuda.memory_allocated(0) / (1024 * 1024)
    reserved_mb = torch.cuda.memory_reserved(0) / (1024 * 1024)
    peak_allocated_mb = torch.cuda.max_memory_allocated(0) / (1024 * 1024)
    peak_reserved_mb = torch.cuda.max_memory_reserved(0) / (1024 * 1024)

    return {
        "cuda_available": True,
        "device_name": torch.cuda.get_device_name(0),
        "physical_total_mb": round(total_mb, 2),
        "current_allocated_mb": round(allocated_mb, 2),
        "current_reserved_mb": round(reserved_mb, 2),
        "peak_allocated_mb": round(peak_allocated_mb, 2),
        "peak_reserved_mb": round(peak_reserved_mb, 2),
        # Backward-compatibility keys
        "vram_total_mb": round(total_mb, 2),
        "vram_allocated_mb": round(allocated_mb, 2),
        "vram_reserved_mb": round(reserved_mb, 2),
        "vram_peak_mb": round(peak_allocated_mb, 2),
    }


def audit_trainable_parameters(
    controlnet: torch.nn.Module,
    unet: torch.nn.Module,
    vae: torch.nn.Module,
    text_encoder: torch.nn.Module,
) -> Dict[str, Dict[str, int]]:
    """Audit and verify parameter trainability across all architecture components.

    Mandatory check:
      - ControlNet: TRAINABLE
      - Base UNet:  FROZEN (0 trainable parameters)
      - VAE:        FROZEN (0 trainable parameters)
      - Text Encoder: FROZEN (0 trainable parameters)
    """
    components = {
        "ControlNet": controlnet,
        "Base UNet": unet,
        "VAE": vae,
        "Text Encoder": text_encoder,
    }

    audit_results: Dict[str, Dict[str, int]] = {}
    total_trainable = 0
    total_frozen = 0

    print("\n" + "=" * 65)
    print("  MANDATORY TRAINABLE PARAMETER AUDIT")
    print("=" * 65)

    for name, module in components.items():
        if module is None:
            continue
        params_total = sum(p.numel() for p in module.parameters())
        params_trainable = sum(p.numel() for p in module.parameters() if p.requires_grad)
        params_frozen = params_total - params_trainable

        audit_results[name] = {
            "total": params_total,
            "trainable": params_trainable,
            "frozen": params_frozen,
        }
        total_trainable += params_trainable
        total_frozen += params_frozen

        status = "TRAINABLE" if params_trainable > 0 else "FROZEN"
        print(f"  - {name:<14}: {status:<9} | Trainable: {params_trainable:>12,d} | Frozen: {params_frozen:>12,d} | Total: {params_total:>12,d}")

    print("-" * 65)
    print(f"  TOTAL PARAMETERS:     {total_trainable + total_frozen:>12,d}")
    print(f"  TRAINABLE PARAMETERS: {total_trainable:>12,d} ({total_trainable / max(1, total_trainable + total_frozen) * 100:.2f}%)")
    print(f"  FROZEN PARAMETERS:    {total_frozen:>12,d}")
    print("=" * 65)

    # Verification assertions
    if audit_results["ControlNet"]["trainable"] == 0:
        raise RuntimeError("Parameter Audit Failed: ControlNet has 0 trainable parameters!")

    if audit_results["Base UNet"]["trainable"] > 0:
        raise RuntimeError(f"Parameter Audit Failed: Base UNet is accidentally trainable ({audit_results['Base UNet']['trainable']} parameters)!")

    if audit_results["VAE"]["trainable"] > 0:
        raise RuntimeError(f"Parameter Audit Failed: VAE is accidentally trainable ({audit_results['VAE']['trainable']} parameters)!")

    if audit_results["Text Encoder"]["trainable"] > 0:
        raise RuntimeError(f"Parameter Audit Failed: Text Encoder is accidentally trainable ({audit_results['Text Encoder']['trainable']} parameters)!")

    logger.info("Parameter audit passed successfully: Only ControlNet is trainable.")
    return audit_results


def find_latest_checkpoint(checkpoint_dir: Path) -> Optional[Path]:
    """Locate the most recent checkpoint folder safely."""
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

    last_dir = checkpoint_dir / "checkpoint-last"
    if last_dir.exists() and last_dir.is_dir():
        return last_dir

    return None


def get_checkpoint_step(checkpoint_path: Path) -> int:
    """Extract global step from trainer_state.json or directory name."""
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
    controlnet: ControlNetModel,
    optimizer: torch.optim.Optimizer,
    lr_scheduler: Any,
    scaler: torch.amp.GradScaler,
    global_step: int,
    epoch: int,
    loss: Optional[float] = None,
    val_loss: Optional[float] = None,
    config: Optional[Dict[str, Any]] = None,
) -> None:
    """Persist ControlNet weights, optimizer, scheduler, scaler, and training state."""
    save_dir.mkdir(parents=True, exist_ok=True)

    # Save ControlNet model weights via Diffusers
    controlnet.save_pretrained(str(save_dir))

    # Save optimization states for resume support
    torch.save(optimizer.state_dict(), save_dir / "optimizer.pt")
    torch.save(lr_scheduler.state_dict(), save_dir / "scheduler.pt")
    torch.save(scaler.state_dict(), save_dir / "scaler.pt")

    state = {
        "global_step": global_step,
        "epoch": epoch,
        "loss": loss,
        "val_loss": val_loss,
        "timestamp": time.time(),
        "gpu_memory": get_gpu_memory_report(),
        "config": config,
    }
    with open(save_dir / "trainer_state.json", "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def evaluate_validation_loss(
    controlnet: ControlNetModel,
    unet: UNet2DConditionModel,
    vae: AutoencoderKL,
    text_encoder: CLIPTextModel,
    noise_scheduler: DDPMScheduler,
    val_dataloader: DataLoader,
    device: torch.device,
    max_val_batches: int = 15,
) -> Optional[float]:
    """Compute validation MSE loss across validation pairs without updating weights."""
    if val_dataloader is None or len(val_dataloader) == 0:
        return None

    controlnet.eval()
    val_losses = []
    is_cuda = (device.type == "cuda")
    model_dtype = torch.float16 if is_cuda else torch.float32

    with torch.no_grad():
        for b_idx, batch in enumerate(val_dataloader):
            if b_idx >= max_val_batches:
                break

            target_pixel_values = batch["pixel_values"].to(device, dtype=model_dtype)
            conditioning_pixel_values = batch["conditioning_pixel_values"].to(device, dtype=model_dtype)
            input_ids = batch["input_ids"].to(device)

            latents = vae.encode(target_pixel_values).latent_dist.sample() * 0.18215
            noise = torch.randn_like(latents)
            timesteps = torch.randint(
                0, noise_scheduler.config.num_train_timesteps, (latents.shape[0],), device=device
            ).long()
            noisy_latents = noise_scheduler.add_noise(latents, noise, timesteps)

            encoder_hidden_states = text_encoder(input_ids)[0]

            with torch.amp.autocast(device_type=device.type, dtype=model_dtype, enabled=is_cuda):
                down_block_res_samples, mid_block_res_sample = controlnet(
                    noisy_latents,
                    timesteps,
                    encoder_hidden_states=encoder_hidden_states,
                    controlnet_cond=conditioning_pixel_values,
                    return_dict=False,
                )
                model_pred = unet(
                    noisy_latents,
                    timesteps,
                    encoder_hidden_states=encoder_hidden_states,
                    down_block_additional_residuals=down_block_res_samples,
                    mid_block_additional_residual=mid_block_res_sample,
                ).sample
                v_loss = F.mse_loss(model_pred.float(), noise.float(), reduction="mean")
                val_losses.append(v_loss.item())

    controlnet.train()
    if not val_losses:
        return None
    return sum(val_losses) / len(val_losses)


def generate_validation_samples(
    controlnet: ControlNetModel,
    unet: UNet2DConditionModel,
    vae: AutoencoderKL,
    text_encoder: CLIPTextModel,
    tokenizer: CLIPTokenizer,
    noise_scheduler: DDPMScheduler,
    val_dataset: ControlNetJewelleryDataset,
    output_dir: Path,
    step: int,
    device: torch.device,
    num_samples: int = 2,
    num_inference_steps: int = 20,
    seed: int = 42,
) -> None:
    """Generate deterministic validation images comparing conditioning, target, and output."""
    if len(val_dataset) == 0:
        return

    val_step_dir = output_dir / "validation" / f"step-{step:04d}"
    val_step_dir.mkdir(parents=True, exist_ok=True)
    is_cuda = (device.type == "cuda")
    model_dtype = torch.float16 if is_cuda else torch.float32

    controlnet.eval()
    logger.info("Generating %d validation image comparisons at step %d -> %s", num_samples, step, val_step_dir)

    with torch.no_grad():
        for i in range(min(num_samples, len(val_dataset))):
            sample = val_dataset[i]
            cond_tensor = sample["conditioning_pixel_values"].unsqueeze(0).to(device, dtype=model_dtype)
            prompt_text = sample.get("prompt", "")
            target_path_str = sample.get("target_path", "")

            # Save conditioning map image
            cond_np = (sample["conditioning_pixel_values"].permute(1, 2, 0).cpu().numpy() * 255.0).astype(np.uint8)
            Image.fromarray(cond_np).save(val_step_dir / f"sample_{i+1:02d}_conditioning.png")

            # Save target original if available
            if target_path_str and Path(target_path_str).exists():
                shutil.copy2(target_path_str, val_step_dir / f"sample_{i+1:02d}_target.png")

            # Deterministic inference using standard scheduler
            gen = torch.Generator(device=device).manual_seed(seed + i)
            latents = torch.randn(
                (1, 4, sample["pixel_values"].shape[1] // 8, sample["pixel_values"].shape[2] // 8),
                generator=gen,
                device=device,
                dtype=model_dtype,
            )

            # Tokenize prompt
            tokens = tokenizer(
                prompt_text,
                padding="max_length",
                max_length=tokenizer.model_max_length,
                truncation=True,
                return_tensors="pt",
            ).input_ids.to(device)
            encoder_hidden_states = text_encoder(tokens)[0]

            # Set inference timesteps
            noise_scheduler.set_timesteps(num_inference_steps, device=device)
            latents = latents * noise_scheduler.init_noise_sigma

            for t in noise_scheduler.timesteps:
                latent_model_input = noise_scheduler.scale_model_input(latents, t)
                with torch.amp.autocast(device_type=device.type, dtype=model_dtype, enabled=is_cuda):
                    down_block_res_samples, mid_block_res_sample = controlnet(
                        latent_model_input,
                        t,
                        encoder_hidden_states=encoder_hidden_states,
                        controlnet_cond=cond_tensor,
                        return_dict=False,
                    )
                    noise_pred = unet(
                        latent_model_input,
                        t,
                        encoder_hidden_states=encoder_hidden_states,
                        down_block_additional_residuals=down_block_res_samples,
                        mid_block_additional_residual=mid_block_res_sample,
                    ).sample

                latents = noise_scheduler.step(noise_pred, t, latents).prev_sample

            # Decode latents
            latents = 1.0 / 0.18215 * latents
            image = vae.decode(latents.to(vae.dtype)).sample
            image = (image / 2 + 0.5).clamp(0, 1)
            image = image.cpu().permute(0, 2, 3, 1).float().numpy()
            image = (image[0] * 255).round().astype(np.uint8)
            Image.fromarray(image).save(val_step_dir / f"sample_{i+1:02d}_generated.png")

    controlnet.train()


def main():
    parser = argparse.ArgumentParser(description="JewelMind ControlNet Trainer (Manual GPU Execution)")
    parser.add_argument("--config", type=str, default="configs/controlnet_jewellery.yaml", help="Path to YAML training configuration")
    parser.add_argument("--smoke_test", action="store_true", help="Perform a 1-step GPU smoke test and exit")
    parser.add_argument("--resume", type=str, default=None, help="Path to checkpoint folder or 'latest' to resume")
    parser.add_argument("--max_train_steps", type=int, default=None, help="Override maximum optimizer training steps")
    parser.add_argument("--learning_rate", type=float, default=None, help="Override learning rate")
    parser.add_argument("--train_batch_size", type=int, default=None, help="Override train batch size per device")
    parser.add_argument("--gradient_accumulation_steps", type=int, default=None, help="Override gradient accumulation steps")
    parser.add_argument("--seed", type=int, default=None, help="Override random seed")
    parser.add_argument("--output_dir", type=str, default=None, help="Override output directory")
    parser.add_argument("--train_data_dir", type=str, default=None, help="Override training dataset root")
    parser.add_argument("--val_data_dir", type=str, default=None, help="Override validation dataset root")
    parser.add_argument("--allow_cpu", action="store_true", help="Allow running on CPU (for unit tests / mock execution)")
    args = parser.parse_args()

    # Load configuration
    config_path = Path(args.config)
    if not config_path.exists():
        logger.error("Configuration file not found: %s", config_path)
        sys.exit(1)

    with open(config_path, "r", encoding="utf-8") as f:
        cfg: Dict[str, Any] = yaml.safe_load(f)

    # Apply overrides
    if args.max_train_steps is not None:
        cfg["training"]["max_train_steps"] = args.max_train_steps
    if args.learning_rate is not None:
        cfg["training"]["learning_rate"] = args.learning_rate
    if args.train_batch_size is not None:
        cfg["training"]["train_batch_size"] = args.train_batch_size
    if args.gradient_accumulation_steps is not None:
        cfg["training"]["gradient_accumulation_steps"] = args.gradient_accumulation_steps
    if args.seed is not None:
        cfg["training"]["seed"] = args.seed
    if args.output_dir is not None:
        cfg["output"]["output_dir"] = args.output_dir
    if args.train_data_dir is not None:
        cfg["dataset"]["train_data_dir"] = args.train_data_dir
    if args.val_data_dir is not None:
        cfg["dataset"]["val_data_dir"] = args.val_data_dir

    if args.smoke_test:
        cfg["training"]["max_train_steps"] = 1
        cfg["training"]["checkpointing_steps"] = 1
        cfg["training"]["validation_steps"] = 1
        logger.info("[SMOKE TEST MODE ACTIVE] Running exactly 1 step verification.")

    # Check CUDA
    is_cuda = torch.cuda.is_available()
    if not is_cuda and not args.allow_cpu:
        logger.error("CUDA is not available! ControlNet training requires an NVIDIA GPU (RTX 4060). Pass --allow_cpu only for testing.")
        sys.exit(1)

    device = torch.device("cuda" if is_cuda else "cpu")
    mem_report = get_gpu_memory_report()
    if is_cuda:
        logger.info("Target GPU: %s (Total VRAM: %.0f MiB)", mem_report["device_name"], mem_report["vram_total_mb"])
    else:
        logger.warning("Running on CPU device (Testing Mode).")

    # Set seed
    seed = cfg["training"].get("seed", 42)
    set_seed(seed)

    # Configure TF32
    if is_cuda and cfg.get("memory", {}).get("allow_tf32", True):
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True
        logger.info("Enabled TF32 precision on Ampere/Ada GPU.")

    # Prepare output directories
    output_dir = Path(cfg["output"]["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    checkpoints_dir = output_dir / "checkpoints"
    checkpoints_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load Tokenizer & Scheduler
    model_id = cfg["model"]["pretrained_model_name_or_path"]
    logger.info("Loading base diffusion components from: %s", model_id)

    tokenizer = CLIPTokenizer.from_pretrained(model_id, subfolder="tokenizer")
    noise_scheduler = DDPMScheduler.from_pretrained(model_id, subfolder="scheduler")

    # 2. Checkpoint Resume Resolution & Model Loading
    starting_step = 0
    starting_epoch = 0
    resume_target = args.resume or cfg["training"].get("resume_from_checkpoint")
    if resume_target == "latest":
        resume_checkpoint = find_latest_checkpoint(checkpoints_dir)
    elif resume_target:
        resume_checkpoint = Path(resume_target)
    else:
        resume_checkpoint = None

    text_encoder = CLIPTextModel.from_pretrained(model_id, subfolder="text_encoder")
    vae = AutoencoderKL.from_pretrained(model_id, subfolder="vae")
    unet = UNet2DConditionModel.from_pretrained(model_id, subfolder="unet")

    if resume_checkpoint and resume_checkpoint.exists():
        logger.info("Resuming ControlNet architecture and weights from checkpoint: %s", resume_checkpoint)
        controlnet = ControlNetModel.from_pretrained(str(resume_checkpoint))
        starting_step = get_checkpoint_step(resume_checkpoint)

        state_file = resume_checkpoint / "trainer_state.json"
        if state_file.exists():
            try:
                with open(state_file, "r", encoding="utf-8") as f:
                    state_data = json.load(f)
                    starting_epoch = state_data.get("epoch", 0)
            except Exception:
                pass
    else:
        controlnet_id = cfg["model"].get("pretrained_controlnet_name_or_path")
        if controlnet_id:
            logger.info("Loading pretrained ControlNet adapter from: %s", controlnet_id)
            controlnet = ControlNetModel.from_pretrained(controlnet_id)
        else:
            logger.info("Initializing ControlNet from UNet architecture.")
            controlnet = ControlNetModel.from_unet(unet)

    # 3. Parameter Freezing & Auditing
    vae.requires_grad_(False)
    text_encoder.requires_grad_(False)
    unet.requires_grad_(False)
    controlnet.requires_grad_(True)

    model_dtype = torch.float16 if is_cuda else torch.float32
    vae.to(device, dtype=model_dtype)
    text_encoder.to(device, dtype=model_dtype)
    unet.to(device, dtype=model_dtype)
    controlnet.to(device)

    # Enable Gradient Checkpointing
    if cfg["training"].get("gradient_checkpointing", True):
        if hasattr(controlnet, "enable_gradient_checkpointing"):
            controlnet.enable_gradient_checkpointing()
            logger.info("Enabled ControlNet gradient checkpointing.")
        if hasattr(unet, "enable_gradient_checkpointing"):
            unet.enable_gradient_checkpointing()
            logger.info("Enabled UNet gradient checkpointing.")

    # Enable Memory-Efficient Attention / SDPA
    if cfg.get("memory", {}).get("enable_sdpa", True) and hasattr(F, "scaled_dot_product_attention"):
        logger.info("Using native PyTorch Scaled Dot-Product Attention (SDPA) for memory efficiency.")

    # Perform mandatory parameter audit
    audit_trainable_parameters(controlnet, unet, vae, text_encoder)

    # 4. Dataloaders
    train_dir = cfg["dataset"]["train_data_dir"]
    train_meta = cfg["dataset"].get("train_metadata_file")
    resolution = cfg["dataset"].get("resolution", 512)
    keep_ar = cfg["dataset"].get("keep_aspect_ratio", True)

    train_dataset = ControlNetJewelleryDataset(
        data_dir=train_dir,
        metadata_file=train_meta,
        tokenizer=tokenizer,
        size=resolution,
        keep_aspect_ratio=keep_ar,
    )
    train_batch_size = cfg["training"].get("train_batch_size", 1)
    train_dataloader = DataLoader(
        train_dataset,
        batch_size=train_batch_size,
        shuffle=True,
        num_workers=0,
    )
    logger.info("Training dataset loaded: %d paired samples from %s", len(train_dataset), train_dir)

    val_dir = cfg["dataset"].get("val_data_dir")
    val_meta = cfg["dataset"].get("val_metadata_file")
    val_dataset = None
    val_dataloader = None
    if val_dir and Path(val_dir).exists():
        try:
            val_dataset = ControlNetJewelleryDataset(
                data_dir=val_dir,
                metadata_file=val_meta,
                tokenizer=tokenizer,
                size=resolution,
                keep_aspect_ratio=keep_ar,
            )
            val_dataloader = DataLoader(val_dataset, batch_size=1, shuffle=False, num_workers=0)
            logger.info("Validation dataset loaded: %d paired samples from %s", len(val_dataset), val_dir)
        except Exception as err:
            logger.warning("Validation dataloader disabled: %s", err)

    # 5. Optimizer, LR Scheduler & GradScaler
    max_train_steps = cfg["training"].get("max_train_steps", 1000)
    lr = float(cfg["training"].get("learning_rate", 1.0e-5))
    opt_cfg = cfg.get("optimizer", {})
    optimizer = torch.optim.AdamW(
        controlnet.parameters(),
        lr=lr,
        betas=(opt_cfg.get("beta1", 0.9), opt_cfg.get("beta2", 0.999)),
        weight_decay=float(opt_cfg.get("weight_decay", 1.0e-2)),
        eps=float(opt_cfg.get("epsilon", 1.0e-8)),
    )

    lr_scheduler = get_scheduler(
        cfg["training"].get("lr_scheduler", "cosine"),
        optimizer=optimizer,
        num_warmup_steps=cfg["training"].get("lr_warmup_steps", 50),
        num_training_steps=max_train_steps,
    )
    scaler = torch.amp.GradScaler("cuda", enabled=is_cuda)

    # 6. Restore Optimization & Scaler States if Resuming
    if resume_checkpoint and resume_checkpoint.exists():
        opt_path = resume_checkpoint / "optimizer.pt"
        if opt_path.exists():
            try:
                optimizer.load_state_dict(torch.load(opt_path, map_location=device))
                logger.info("Restored optimizer momentum and state.")
            except Exception as e:
                logger.warning("Could not restore optimizer state: %s", e)

        sched_path = resume_checkpoint / "scheduler.pt"
        if sched_path.exists():
            try:
                lr_scheduler.load_state_dict(torch.load(sched_path))
                logger.info("Restored learning rate scheduler state.")
            except Exception as e:
                logger.warning("Could not restore scheduler state: %s", e)

        scaler_path = resume_checkpoint / "scaler.pt"
        if scaler_path.exists() and is_cuda:
            try:
                scaler.load_state_dict(torch.load(scaler_path))
                logger.info("Restored GradScaler state.")
            except Exception as e:
                logger.warning("Could not restore scaler state: %s", e)

        logger.info("Successfully resumed at global optimizer step %d / %d (epoch %d)", starting_step, max_train_steps, starting_epoch)
    else:
        logger.info("Starting fresh ControlNet training from step 0.")

    # 7. Training Loop Execution
    grad_accum_steps = cfg["training"].get("gradient_accumulation_steps", 4)
    checkpoint_interval = cfg["training"].get("checkpointing_steps", 200)
    validation_interval = cfg["training"].get("validation_steps", 200)
    max_grad_norm = float(cfg["training"].get("max_grad_norm", 1.0))

    global_step = starting_step
    epoch = starting_epoch
    accumulated_loss = 0.0
    val_loss_val = None

    progress_bar = tqdm(
        total=max_train_steps,
        initial=starting_step,
        desc="ControlNet Steps",
        dynamic_ncols=True,
    )

    optimizer.zero_grad()
    controlnet.train()

    logger.info("Training initialized. Total training steps: %d | Batch size: %d | Accumulation: %d", max_train_steps, train_batch_size, grad_accum_steps)

    # If resuming from existing checkpoint, evaluate and record baseline validation loss at starting step
    if starting_step > 0 and val_dataloader is not None:
        logger.info("Evaluating baseline validation loss at resume step %d...", starting_step)
        val_loss_val = evaluate_validation_loss(
            controlnet, unet, vae, text_encoder, noise_scheduler, val_dataloader, device
        )
        if val_loss_val is not None:
            logger.info("Resume Step %d | Initial Validation Loss: %.4f", starting_step, val_loss_val)

    start_time = time.time()

    while global_step < max_train_steps:
        epoch += 1
        for batch_idx, batch in enumerate(train_dataloader):
            # Encode target image to latents with frozen VAE
            with torch.no_grad():
                target_pixel_values = batch["pixel_values"].to(device, dtype=model_dtype)
                latents = vae.encode(target_pixel_values).latent_dist.sample() * 0.18215

            # Sample random noise & timesteps
            noise = torch.randn_like(latents)
            timesteps = torch.randint(
                0, noise_scheduler.config.num_train_timesteps, (latents.shape[0],), device=device
            ).long()
            noisy_latents = noise_scheduler.add_noise(latents, noise, timesteps)

            # Encode text prompt with frozen text encoder
            with torch.no_grad():
                input_ids = batch["input_ids"].to(device)
                encoder_hidden_states = text_encoder(input_ids)[0]

            conditioning_pixel_values = batch["conditioning_pixel_values"].to(device, dtype=model_dtype)

            # Forward pass through ControlNet + UNet under autocast
            with torch.amp.autocast(device_type=device.type, dtype=model_dtype, enabled=is_cuda):
                down_block_res_samples, mid_block_res_sample = controlnet(
                    noisy_latents,
                    timesteps,
                    encoder_hidden_states=encoder_hidden_states,
                    controlnet_cond=conditioning_pixel_values,
                    return_dict=False,
                )

                model_pred = unet(
                    noisy_latents,
                    timesteps,
                    encoder_hidden_states=encoder_hidden_states,
                    down_block_additional_residuals=down_block_res_samples,
                    mid_block_additional_residual=mid_block_res_sample,
                ).sample

                raw_loss = F.mse_loss(model_pred.float(), noise.float(), reduction="mean")
                loss = raw_loss / grad_accum_steps

            # Backward pass with GradScaler
            scaler.scale(loss).backward()
            accumulated_loss += raw_loss.item()

            # Optimizer update on accumulation window
            if (batch_idx + 1) % grad_accum_steps == 0 or (batch_idx + 1) == len(train_dataloader) or args.smoke_test:
                scaler.unscale_(optimizer)
                torch.nn.utils.clip_grad_norm_(controlnet.parameters(), max_grad_norm)
                scaler.step(optimizer)
                scaler.update()
                optimizer.zero_grad()
                lr_scheduler.step()

                global_step += 1
                progress_bar.update(1)

                avg_step_loss = accumulated_loss / min(grad_accum_steps, (batch_idx % grad_accum_steps) + 1)
                accumulated_loss = 0.0

                current_lr = lr_scheduler.get_last_lr()[0]
                postfix_data = {"loss": f"{avg_step_loss:.4f}", "lr": f"{current_lr:.2e}", "epoch": epoch}
                if is_cuda:
                    postfix_data["vram"] = f"{torch.cuda.memory_allocated(0)/(1024*1024):.0f}MB"
                progress_bar.set_postfix(postfix_data)

                # Validation & Checkpointing
                if global_step % validation_interval == 0 or global_step == max_train_steps or args.smoke_test:
                    if val_dataloader is not None:
                        val_loss_val = evaluate_validation_loss(
                            controlnet, unet, vae, text_encoder, noise_scheduler, val_dataloader, device
                        )
                        if val_loss_val is not None:
                            logger.info("Step %d | Validation Loss: %.4f", global_step, val_loss_val)

                if global_step % checkpoint_interval == 0 or global_step == max_train_steps or args.smoke_test:
                    save_name = f"smoke_test_checkpoint" if args.smoke_test else f"checkpoint-{global_step}"
                    save_dir = checkpoints_dir / save_name
                    logger.info("Saving checkpoint at optimizer step %d -> %s", global_step, save_dir)
                    save_checkpoint(
                        save_dir=save_dir,
                        controlnet=controlnet,
                        optimizer=optimizer,
                        lr_scheduler=lr_scheduler,
                        scaler=scaler,
                        global_step=global_step,
                        epoch=epoch,
                        loss=avg_step_loss,
                        val_loss=val_loss_val,
                        config=cfg,
                    )

                # In smoke-test mode: break immediately after 1 step
                if args.smoke_test or global_step >= max_train_steps:
                    break

    progress_bar.close()
    elapsed_time = time.time() - start_time

    # Final Summary & Diagnostics
    final_mem = get_gpu_memory_report()
    print("\n" + "=" * 65)
    if args.smoke_test:
        print("  CONTROLNET 1-STEP GPU SMOKE TEST COMPLETED SUCCESSFULLY!")
    else:
        print("  CONTROLNET TRAINING RUN FINISHED!")
    print("=" * 65)
    print(f"  - Completed Global Steps: {global_step}")
    print(f"  - Elapsed Time:           {elapsed_time:.2f}s")
    print(f"  - Target Device:          {final_mem['device_name']}")
    if is_cuda:
        print(f"  - Physical VRAM Total:    {final_mem['physical_total_mb']:.1f} MiB")
        print(f"  - Current Allocated VRAM: {final_mem['current_allocated_mb']:.1f} MiB (active live tensors)")
        print(f"  - Current Reserved VRAM:  {final_mem['current_reserved_mb']:.1f} MiB (caching allocator pool)")
        print(f"  - Peak Allocated VRAM:    {final_mem['peak_allocated_mb']:.1f} MiB (max tensor memory requested)")
        print(f"  - Peak Reserved VRAM:     {final_mem['peak_reserved_mb']:.1f} MiB (max allocator cache reserved)")
    print("=" * 65)

    if not args.smoke_test:
        final_dir = output_dir / "controlnet_jewellery_final"
        logger.info("Saving final ControlNet weights to: %s", final_dir)
        controlnet.save_pretrained(str(final_dir))
        logger.info("SUCCESS: Fine-tuned ControlNet ready for jewellery rendering.")


if __name__ == "__main__":
    main()
