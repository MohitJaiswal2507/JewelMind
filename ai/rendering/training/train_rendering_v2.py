"""JewelMind Rendering V2 — Multi-Category ControlNet Training Script.

Trains a unified, category-aware ControlNet on the 8-category JewelMind Rendering V2 dataset
(1,429 pairs across ring, earring, pendant, necklace, bracelet, bangle, brooch, other_jewellery).

Constraints:
  - Supports 8GB VRAM (NVIDIA RTX 4060 Laptop GPU) via fp16, gradient checkpointing,
    gradient accumulation (eff_batch=4), SDPA attention, and memory clearing.
  - Zero modification to Rendering V1 baseline models or checkpoints.
  - Offline-first: uses local pretrained snapshots in models/diffusion/ or standard cache.
"""

import sys
from pathlib import Path

# Force immediate log flushing
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(line_buffering=True)

# Ensure workspace root is on sys.path
_PROJECT_ROOT = str(Path(__file__).resolve().parents[3])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import argparse
import gc
import json
import logging
import math
import os
import random
import shutil
import time
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
from PIL import Image
import yaml

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

from ai.rendering.training.rendering_v2_dataset import (
    CANONICAL_CATEGORIES,
    RenderingV2Dataset,
    normalize_category,
)

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%m/%d/%Y %H:%M:%S",
    level=logging.INFO,
    stream=sys.stdout,
)
logger = logging.getLogger("jewelmind.train_rendering_v2")


def set_seed(seed: int = 42) -> None:
    """Set random seeds for reproducibility across Python, NumPy, and PyTorch."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def resolve_local_model_path(model_identifier: str, default_cache_dir: str = "models/diffusion") -> str:
    """Resolve a HuggingFace identifier or local path to an existing on-disk snapshot."""
    p = Path(model_identifier)
    if p.exists():
        return str(p.resolve())

    # Check in models/diffusion snapshots
    cache_path = Path(default_cache_dir)
    if cache_path.exists():
        # Clean folder name like models--runwayml--stable-diffusion-v1-5
        hub_folder_name = "models--" + model_identifier.replace("/", "--")
        hub_dir = cache_path / hub_folder_name / "snapshots"
        if hub_dir.exists():
            snapshots = list(hub_dir.iterdir())
            if snapshots:
                return str(snapshots[0].resolve())

        # Check direct subfolder (e.g. models/diffusion/sd15)
        if "stable-diffusion" in model_identifier and (cache_path / "sd15").exists():
            if (cache_path / "sd15" / "model_index.json").exists():
                return str((cache_path / "sd15").resolve())

    return model_identifier


def get_gpu_memory_report() -> Dict[str, Any]:
    """Retrieve detailed GPU memory metrics."""
    if not torch.cuda.is_available():
        return {
            "cuda_available": False,
            "device_name": "CPU",
            "physical_total_mb": 0.0,
            "allocated_mb": 0.0,
            "reserved_mb": 0.0,
            "peak_allocated_mb": 0.0,
        }

    props = torch.cuda.get_device_properties(0)
    total_mb = props.total_memory / (1024 * 1024)
    allocated_mb = torch.cuda.memory_allocated(0) / (1024 * 1024)
    reserved_mb = torch.cuda.memory_reserved(0) / (1024 * 1024)
    peak_allocated_mb = torch.cuda.max_memory_allocated(0) / (1024 * 1024)

    return {
        "cuda_available": True,
        "device_name": torch.cuda.get_device_name(0),
        "physical_total_mb": round(total_mb, 2),
        "allocated_mb": round(allocated_mb, 2),
        "reserved_mb": round(reserved_mb, 2),
        "peak_allocated_mb": round(peak_allocated_mb, 2),
    }


def audit_trainable_parameters(
    controlnet: torch.nn.Module,
    unet: torch.nn.Module,
    vae: torch.nn.Module,
    text_encoder: torch.nn.Module,
) -> Dict[str, Dict[str, int]]:
    """Assert parameter freezing: only ControlNet should have trainable parameters."""
    modules = {
        "ControlNet": controlnet,
        "Base UNet": unet,
        "VAE": vae,
        "Text Encoder": text_encoder,
    }
    audit: Dict[str, Dict[str, int]] = {}

    for name, mod in modules.items():
        trainable = sum(p.numel() for p in mod.parameters() if p.requires_grad)
        frozen = sum(p.numel() for p in mod.parameters() if not p.requires_grad)
        audit[name] = {"trainable": trainable, "frozen": frozen, "total": trainable + frozen}

    logger.info("================ PARAMETER AUDIT ================")
    for name, counts in audit.items():
        logger.info(
            "%-15s: Trainable=%12s | Frozen=%12s | Total=%12s",
            name,
            f"{counts['trainable']:,}",
            f"{counts['frozen']:,}",
            f"{counts['total']:,}",
        )
    logger.info("==================================================")

    if audit["ControlNet"]["trainable"] == 0:
        raise RuntimeError("Parameter Audit Failed: ControlNet has 0 trainable parameters!")
    if audit["Base UNet"]["trainable"] > 0:
        raise RuntimeError("Parameter Audit Failed: Base UNet is not frozen!")
    if audit["VAE"]["trainable"] > 0:
        raise RuntimeError("Parameter Audit Failed: VAE is not frozen!")
    if audit["Text Encoder"]["trainable"] > 0:
        raise RuntimeError("Parameter Audit Failed: Text Encoder is not frozen!")

    return audit


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
    controlnet.save_pretrained(str(save_dir))

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

    logger.info("Successfully saved checkpoint at step %d -> %s", global_step, save_dir)


def find_latest_checkpoint(checkpoint_dir: Path) -> Optional[Path]:
    """Find the most recent checkpoint folder in checkpoint_dir."""
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

    return None


def run_multi_category_validation(
    controlnet: ControlNetModel,
    unet: UNet2DConditionModel,
    vae: AutoencoderKL,
    text_encoder: CLIPTextModel,
    tokenizer: CLIPTokenizer,
    val_dataset: RenderingV2Dataset,
    output_dir: Path,
    step: int,
    device: torch.device,
    scheduler_config: Optional[Any] = None,
    max_samples: int = 8,
    num_inference_steps: int = 15,
    seed: int = 42,
) -> None:
    """Generate deterministic validation images across canonical categories."""
    if len(val_dataset) == 0 or max_samples <= 0:
        return

    from diffusers import DPMSolverMultistepScheduler

    val_step_dir = output_dir / "validation" / f"step-{step:04d}"
    val_step_dir.mkdir(parents=True, exist_ok=True)
    is_cuda = (device.type == "cuda")
    model_dtype = torch.float16 if is_cuda else torch.float32

    controlnet.eval()
    if is_cuda:
        controlnet.to(dtype=model_dtype)

    logger.info("Generating multi-category validation comparisons at step %d -> %s", step, val_step_dir)

    # Pick 1 sample per category from validation set
    category_samples: Dict[str, Dict[str, Any]] = {}
    for i in range(len(val_dataset)):
        sample = val_dataset[i]
        cat = sample.get("category", "other_jewellery")
        if cat not in category_samples:
            category_samples[cat] = sample
        if len(category_samples) >= min(len(CANONICAL_CATEGORIES), max_samples):
            break

    # Use a dedicated validation scheduler so we do not mutate training state
    if scheduler_config is not None:
        eval_scheduler = DPMSolverMultistepScheduler.from_config(scheduler_config)
    else:
        eval_scheduler = DPMSolverMultistepScheduler(
            num_train_timesteps=1000,
            beta_start=0.00085,
            beta_end=0.012,
            beta_schedule="scaled_linear",
        )

    with torch.no_grad():
        for cat_idx, (cat_name, sample) in enumerate(category_samples.items(), start=1):
            # Reset scheduler state and timesteps cleanly for each validation sample
            eval_scheduler.set_timesteps(num_inference_steps, device=device)

            cond_tensor = sample["conditioning_pixel_values"].unsqueeze(0).to(device, dtype=model_dtype)
            prompt_text = sample.get("prompt", "")
            target_path_str = sample.get("target_path", "")

            # Save conditioning map image
            cond_np = (sample["conditioning_pixel_values"].permute(1, 2, 0).cpu().numpy() * 255.0).astype(np.uint8)
            Image.fromarray(cond_np).save(val_step_dir / f"{cat_idx:02d}_{cat_name}_conditioning.png")

            # Save original target if available
            if target_path_str and Path(target_path_str).exists():
                shutil.copy2(target_path_str, val_step_dir / f"{cat_idx:02d}_{cat_name}_target.png")

            # Deterministic noise generator
            gen = torch.Generator(device=device).manual_seed(seed + cat_idx)
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

            latents = latents * eval_scheduler.init_noise_sigma

            for t in eval_scheduler.timesteps:
                latent_model_input = eval_scheduler.scale_model_input(latents, t)
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

                latents = eval_scheduler.step(noise_pred, t, latents).prev_sample

            # Decode latents
            latents = 1.0 / 0.18215 * latents
            image = vae.decode(latents.to(vae.dtype)).sample
            image = (image / 2 + 0.5).clamp(0, 1)
            image = image.cpu().permute(0, 2, 3, 1).float().numpy()
            image_np = (image[0] * 255).round().astype(np.uint8)
            Image.fromarray(image_np).save(val_step_dir / f"{cat_idx:02d}_{cat_name}_generated.png")
            logger.info("  Generated validation preview [%d/%d]: %s", cat_idx, len(category_samples), cat_name)

            if is_cuda:
                torch.cuda.empty_cache()

    if is_cuda:
        controlnet.to(dtype=torch.float32)
    controlnet.train()


def main():
    parser = argparse.ArgumentParser(description="JewelMind Rendering V2 ControlNet Training Pipeline")
    parser.add_argument("--config", type=str, default="ai/rendering/training/config_rendering_v2.yaml", help="Path to YAML training config")
    parser.add_argument("--smoke_test", action="store_true", help="Perform a 1-step verification and exit")
    parser.add_argument("--pilot", action="store_true", help="Perform a 5-step pilot test and exit")
    parser.add_argument("--resume", type=str, default=None, help="Checkpoint path or 'latest'")
    parser.add_argument("--max_train_steps", type=int, default=None, help="Override maximum training steps")
    parser.add_argument("--learning_rate", type=float, default=None, help="Override learning rate")
    parser.add_argument("--train_batch_size", type=int, default=None, help="Override batch size")
    parser.add_argument("--gradient_accumulation_steps", type=int, default=None, help="Override grad accum steps")
    parser.add_argument("--output_dir", type=str, default=None, help="Override output directory")
    parser.add_argument("--allow_cpu", action="store_true", help="Permit running on CPU for testing")
    args = parser.parse_args()

    # Load configuration
    config_path = Path(args.config)
    if not config_path.exists():
        # Check fallback
        fallback_cfg = Path("configs/controlnet_rendering_v2.yaml")
        if fallback_cfg.exists():
            config_path = fallback_cfg
        else:
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
    if args.output_dir is not None:
        cfg["output"]["output_dir"] = args.output_dir

    if args.smoke_test:
        cfg["training"]["max_train_steps"] = 1
        cfg["training"]["gradient_accumulation_steps"] = 1
        cfg["training"]["checkpointing_steps"] = 1
        cfg["training"]["validation_steps"] = 1
        logger.info("[SMOKE TEST ACTIVE] Running fast 1-step verification.")
    elif args.pilot:
        cfg["training"]["max_train_steps"] = 5
        cfg["training"]["checkpointing_steps"] = 5
        cfg["training"]["validation_steps"] = 5
        logger.info("[PILOT MODE ACTIVE] Running 5-step pilot verification.")

    set_seed(cfg["training"].get("seed", 42))

    # Hardware detection
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    is_cuda = (device.type == "cuda")
    model_dtype = torch.float16 if is_cuda else torch.float32

    if not is_cuda and not args.allow_cpu:
        logger.error("No CUDA GPU detected. RTX 4060 GPU required. Use --allow_cpu for CPU verification.")
        sys.exit(1)

    logger.info("Initializing on device: %s (%s)", device, torch.cuda.get_device_name(0) if is_cuda else "CPU")
    if is_cuda:
        logger.info("Initial GPU VRAM: %s", get_gpu_memory_report())
        if cfg.get("memory", {}).get("allow_tf32", True):
            torch.backends.cuda.matmul.allow_tf32 = True
            torch.backends.cudnn.allow_tf32 = True
            logger.info("Enabled TF32 precision on Ada Lovelace architecture.")

    # Output paths
    output_dir = Path(cfg["output"]["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    checkpoints_dir = output_dir / "checkpoints"
    checkpoints_dir.mkdir(parents=True, exist_ok=True)

    # 1. Resolve & Load Models
    raw_sd_id = cfg["model"]["pretrained_model_name_or_path"]
    sd_model_id = resolve_local_model_path(raw_sd_id)
    raw_controlnet_id = cfg["model"]["pretrained_controlnet_name_or_path"]
    controlnet_model_id = resolve_local_model_path(raw_controlnet_id)

    logger.info("Resolved Base SD Path: %s", sd_model_id)
    logger.info("Resolved ControlNet Path: %s", controlnet_model_id)

    tokenizer = CLIPTokenizer.from_pretrained(sd_model_id, subfolder="tokenizer")
    noise_scheduler = DDPMScheduler.from_pretrained(sd_model_id, subfolder="scheduler")

    # Load SD 1.5 components (try fp16 variant first, fallback to standard)
    try:
        text_encoder = CLIPTextModel.from_pretrained(sd_model_id, subfolder="text_encoder", variant="fp16", torch_dtype=model_dtype)
        vae = AutoencoderKL.from_pretrained(sd_model_id, subfolder="vae", variant="fp16", torch_dtype=model_dtype)
        unet = UNet2DConditionModel.from_pretrained(sd_model_id, subfolder="unet", variant="fp16", torch_dtype=model_dtype)
    except Exception:
        text_encoder = CLIPTextModel.from_pretrained(sd_model_id, subfolder="text_encoder", torch_dtype=model_dtype)
        vae = AutoencoderKL.from_pretrained(sd_model_id, subfolder="vae", torch_dtype=model_dtype)
        unet = UNet2DConditionModel.from_pretrained(sd_model_id, subfolder="unet", torch_dtype=model_dtype)

    # Resume or load fresh ControlNet
    resume_target = args.resume or cfg["training"].get("resume_from_checkpoint")
    if resume_target == "latest":
        resume_checkpoint = find_latest_checkpoint(checkpoints_dir)
    elif resume_target:
        resume_checkpoint = Path(resume_target)
    else:
        resume_checkpoint = None

    starting_step = 0
    starting_epoch = 0

    if resume_checkpoint and resume_checkpoint.exists():
        logger.info("Resuming ControlNet from checkpoint: %s", resume_checkpoint)
        controlnet = ControlNetModel.from_pretrained(str(resume_checkpoint))
        state_file = resume_checkpoint / "trainer_state.json"
        if state_file.exists():
            try:
                with open(state_file, "r", encoding="utf-8") as f:
                    state_data = json.load(f)
                    starting_step = state_data.get("global_step", 0)
                    starting_epoch = state_data.get("epoch", 0)
            except Exception as err:
                logger.warning("Failed to parse trainer_state.json: %s", err)
    else:
        logger.info("Loading pretrained ControlNet initialization: %s", controlnet_model_id)
        try:
            controlnet = ControlNetModel.from_pretrained(controlnet_model_id)
        except Exception:
            logger.warning("Falling back to UNet-derived ControlNet initialization.")
            controlnet = ControlNetModel.from_unet(unet)

    # 2. Freeze parameters & set dtypes
    vae.requires_grad_(False)
    text_encoder.requires_grad_(False)
    unet.requires_grad_(False)
    controlnet.requires_grad_(True)

    # Frozen components in fp16 to save memory; trainable ControlNet in fp32 for GradScaler
    vae.to(device, dtype=model_dtype)
    text_encoder.to(device, dtype=model_dtype)
    unet.to(device, dtype=model_dtype)
    controlnet.to(device)

    if cfg["training"].get("gradient_checkpointing", False):
        if hasattr(controlnet, "enable_gradient_checkpointing"):
            controlnet.enable_gradient_checkpointing()
            logger.info("Enabled ControlNet gradient checkpointing.")

    # 3. Mandatory Parameter Audit
    audit_trainable_parameters(controlnet, unet, vae, text_encoder)

    # 4. Create Datasets & DataLoaders
    train_dir = cfg["dataset"]["train_data_dir"]
    train_metadata_file = cfg["dataset"].get("train_metadata_file")
    val_dir = cfg["dataset"]["val_data_dir"]
    val_metadata_file = cfg["dataset"].get("val_metadata_file")
    max_train_samples = cfg["dataset"].get("max_train_samples")
    if args.smoke_test:
        max_train_samples = 1
    elif args.pilot:
        max_train_samples = 16

    train_dataset = RenderingV2Dataset(
        split_dir=train_dir,
        metadata_file=train_metadata_file,
        tokenizer=tokenizer,
        resolution=cfg["dataset"].get("resolution", 512),
        max_samples=max_train_samples,
    )
    val_dataset = RenderingV2Dataset(
        split_dir=val_dir,
        metadata_file=val_metadata_file,
        tokenizer=tokenizer,
        resolution=cfg["dataset"].get("resolution", 512),
        max_samples=16 if (args.smoke_test or args.pilot) else None,
    )

    batch_size = cfg["training"].get("train_batch_size", 1)
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=cfg["training"].get("num_workers", 0),
        pin_memory=is_cuda,
    )

    # 5. Optimizer & Scheduler
    lr = float(cfg["training"].get("learning_rate", 1e-5))
    opt_cfg = cfg.get("optimizer", {})
    optimizer = torch.optim.AdamW(
        controlnet.parameters(),
        lr=lr,
        betas=(opt_cfg.get("beta1", 0.9), opt_cfg.get("beta2", 0.999)),
        weight_decay=opt_cfg.get("weight_decay", 1e-2),
        eps=opt_cfg.get("epsilon", 1e-8),
    )

    max_train_steps = cfg["training"].get("max_train_steps", 1000)
    lr_scheduler = get_scheduler(
        cfg["training"].get("lr_scheduler", "cosine"),
        optimizer=optimizer,
        num_warmup_steps=cfg["training"].get("lr_warmup_steps", 50),
        num_training_steps=max_train_steps,
    )

    scaler = torch.amp.GradScaler(device=device.type, enabled=(is_cuda and cfg["training"].get("mixed_precision") == "fp16"))

    # Restore optimizer/scheduler state if resuming
    if resume_checkpoint and resume_checkpoint.exists():
        opt_path = resume_checkpoint / "optimizer.pt"
        sched_path = resume_checkpoint / "scheduler.pt"
        scaler_path = resume_checkpoint / "scaler.pt"
        if opt_path.exists():
            optimizer.load_state_dict(torch.load(opt_path, map_location=device))
        if sched_path.exists():
            lr_scheduler.load_state_dict(torch.load(sched_path))
        if scaler_path.exists() and is_cuda:
            scaler.load_state_dict(torch.load(scaler_path))

    # 6. Training Loop
    grad_accum_steps = cfg["training"].get("gradient_accumulation_steps", 4)
    checkpointing_steps = cfg["training"].get("checkpointing_steps", 100)
    validation_steps = cfg["training"].get("validation_steps", 100)
    max_grad_norm = cfg["training"].get("max_grad_norm", 1.0)

    logger.info("================ STARTING TRAINING ================")
    logger.info("Total Training Samples: %d", len(train_dataset))
    logger.info("Max Train Steps: %d (Starting Step: %d)", max_train_steps, starting_step)
    logger.info("Batch Size: %d | Grad Accum: %d (Effective Batch: %d)", batch_size, grad_accum_steps, batch_size * grad_accum_steps)
    logger.info("Mixed Precision: %s", cfg["training"].get("mixed_precision", "fp16"))
    logger.info("===================================================")

    global_step = starting_step
    epoch = starting_epoch
    progress_bar = tqdm(total=max_train_steps, initial=global_step, desc="Rendering V2 Steps")

    controlnet.train()
    optimizer.zero_grad(set_to_none=True)

    while global_step < max_train_steps:
        epoch += 1
        for step, batch in enumerate(train_loader):
            # Move inputs to device
            pixel_values = batch["pixel_values"].to(device, dtype=model_dtype)
            cond_pixel_values = batch["conditioning_pixel_values"].to(device, dtype=model_dtype)
            input_ids = batch["input_ids"].to(device)

            # Encode target images into latents via frozen VAE
            with torch.no_grad():
                latents = vae.encode(pixel_values).latent_dist.sample()
                latents = latents * 0.18215

            # Sample noise and timesteps
            noise = torch.randn_like(latents)
            bsz = latents.shape[0]
            timesteps = torch.randint(0, noise_scheduler.config.num_train_timesteps, (bsz,), device=latents.device).long()
            noisy_latents = noise_scheduler.add_noise(latents, noise, timesteps)

            # Text embeddings
            with torch.no_grad():
                encoder_hidden_states = text_encoder(input_ids)[0]

            # Forward pass with mixed precision
            with torch.amp.autocast(device_type=device.type, dtype=model_dtype, enabled=is_cuda):
                down_block_res_samples, mid_block_res_sample = controlnet(
                    noisy_latents,
                    timesteps,
                    encoder_hidden_states=encoder_hidden_states,
                    controlnet_cond=cond_pixel_values,
                    return_dict=False,
                )

                # UNet prediction (frozen UNet taking ControlNet residuals)
                model_pred = unet(
                    noisy_latents,
                    timesteps,
                    encoder_hidden_states=encoder_hidden_states,
                    down_block_additional_residuals=down_block_res_samples,
                    mid_block_additional_residual=mid_block_res_sample,
                ).sample

                # Compute MSE loss vs true noise
                if noise_scheduler.config.prediction_type == "epsilon":
                    target = noise
                elif noise_scheduler.config.prediction_type == "v_prediction":
                    target = noise_scheduler.get_velocity(latents, noise, timesteps)
                else:
                    target = noise

                loss = F.mse_loss(model_pred.float(), target.float(), reduction="mean")
                loss = loss / grad_accum_steps

            # Backward pass with gradient scaling
            scaler.scale(loss).backward()
            logger.info("  [Accumulation Pass %d/%d] micro_loss=%.4f", (step % grad_accum_steps) + 1, grad_accum_steps, loss.item() * grad_accum_steps)

            # Gradient step at accumulation boundary
            if (step + 1) % grad_accum_steps == 0 or (step + 1) == len(train_loader):
                if max_grad_norm > 0:
                    scaler.unscale_(optimizer)
                    torch.nn.utils.clip_grad_norm_(controlnet.parameters(), max_grad_norm)

                scaler.step(optimizer)
                scaler.update()
                lr_scheduler.step()
                optimizer.zero_grad(set_to_none=True)

                global_step += 1
                progress_bar.update(1)
                current_loss = loss.item() * grad_accum_steps
                progress_bar.set_postfix({"loss": f"{current_loss:.4f}", "lr": f"{lr_scheduler.get_last_lr()[0]:.2e}"})

                if cfg.get("memory", {}).get("empty_cache_at_step", True) and is_cuda:
                    torch.cuda.empty_cache()

                # Save periodic checkpoint
                if global_step % checkpointing_steps == 0 or global_step >= max_train_steps:
                    ckpt_dir = checkpoints_dir / f"checkpoint-{global_step}"
                    save_checkpoint(
                        save_dir=ckpt_dir,
                        controlnet=controlnet,
                        optimizer=optimizer,
                        lr_scheduler=lr_scheduler,
                        scaler=scaler,
                        global_step=global_step,
                        epoch=epoch,
                        loss=current_loss,
                        config=cfg,
                    )

                # Periodic multi-category validation
                if global_step % validation_steps == 0 or global_step >= max_train_steps:
                    val_samples_count = 1 if args.smoke_test else cfg["training"].get("validation_samples", 8)
                    run_multi_category_validation(
                        controlnet=controlnet,
                        unet=unet,
                        vae=vae,
                        text_encoder=text_encoder,
                        tokenizer=tokenizer,
                        val_dataset=val_dataset,
                        output_dir=output_dir,
                        step=global_step,
                        device=device,
                        scheduler_config=noise_scheduler.config,
                        max_samples=val_samples_count,
                        seed=cfg["training"].get("seed", 42),
                    )

                if global_step >= max_train_steps:
                    break

    progress_bar.close()

    # Save final model
    final_dir = output_dir / "controlnet_rendering_v2_final"
    save_checkpoint(
        save_dir=final_dir,
        controlnet=controlnet,
        optimizer=optimizer,
        lr_scheduler=lr_scheduler,
        scaler=scaler,
        global_step=global_step,
        epoch=epoch,
        loss=current_loss if 'current_loss' in locals() else 0.0,
        config=cfg,
    )
    logger.info("Training concluded. Final model saved to: %s", final_dir)


if __name__ == "__main__":
    main()
