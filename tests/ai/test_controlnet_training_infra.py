"""Automated Tests for ControlNet Training Infrastructure, Parameter Audit, and Checkpointing."""

import json
from pathlib import Path
import pytest
import torch
import torch.nn as nn
import torch.nn.functional as F
import yaml

from ai.training.train_controlnet import (
    audit_trainable_parameters,
    find_latest_checkpoint,
    get_checkpoint_step,
    get_gpu_memory_report,
    save_checkpoint,
    set_seed,
)


class DummyModule(nn.Module):
    """Simple linear module for testing trainable parameter auditing and forward/backward flows."""

    def __init__(self, in_features: int = 16, out_features: int = 16):
        super().__init__()
        self.fc = nn.Linear(in_features, out_features)

    def forward(self, x):
        return self.fc(x)

    def save_pretrained(self, save_dir: str):
        Path(save_dir).mkdir(parents=True, exist_ok=True)
        torch.save(self.state_dict(), Path(save_dir) / "diffusion_pytorch_model.bin")


def test_controlnet_configuration_file():
    """Verify that configs/controlnet_jewellery.yaml exists and contains all required 8GB VRAM settings."""
    config_path = Path("configs/controlnet_jewellery.yaml")
    assert config_path.exists(), "configs/controlnet_jewellery.yaml not found"

    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    # Base model
    assert cfg["model"]["pretrained_model_name_or_path"] == "runwayml/stable-diffusion-v1-5"
    assert cfg["model"]["conditioning_channels"] == 3

    # Dataset
    assert cfg["dataset"]["train_data_dir"] == "datasets/controlnet_paired"
    assert cfg["dataset"]["resolution"] == 512
    assert cfg["dataset"]["keep_aspect_ratio"] is True
    assert cfg["dataset"]["random_flip"] is False

    # Training for 8GB VRAM
    assert cfg["training"]["train_batch_size"] == 1
    assert cfg["training"]["gradient_accumulation_steps"] == 4
    assert cfg["training"]["gradient_checkpointing"] is True
    assert cfg["training"]["mixed_precision"] == "fp16"
    assert cfg["training"]["learning_rate"] == 1.0e-5
    assert cfg["training"]["seed"] == 42


def test_trainable_parameter_audit_success():
    """Verify audit_trainable_parameters succeeds when only ControlNet is trainable."""
    controlnet = DummyModule()
    unet = DummyModule()
    vae = DummyModule()
    text_encoder = DummyModule()

    # Freeze base components
    unet.requires_grad_(False)
    vae.requires_grad_(False)
    text_encoder.requires_grad_(False)
    # ControlNet is trainable
    controlnet.requires_grad_(True)

    audit = audit_trainable_parameters(controlnet, unet, vae, text_encoder)

    assert audit["ControlNet"]["trainable"] > 0
    assert audit["Base UNet"]["trainable"] == 0
    assert audit["VAE"]["trainable"] == 0
    assert audit["Text Encoder"]["trainable"] == 0


def test_trainable_parameter_audit_catches_unet_leakage():
    """Verify audit_trainable_parameters raises RuntimeError if UNet is accidentally trainable."""
    controlnet = DummyModule()
    unet = DummyModule()
    vae = DummyModule()
    text_encoder = DummyModule()

    controlnet.requires_grad_(True)
    unet.requires_grad_(True)  # Accidental leak
    vae.requires_grad_(False)
    text_encoder.requires_grad_(False)

    with pytest.raises(RuntimeError, match="Base UNet is accidentally trainable"):
        audit_trainable_parameters(controlnet, unet, vae, text_encoder)


def test_trainable_parameter_audit_catches_frozen_controlnet():
    """Verify audit_trainable_parameters raises RuntimeError if ControlNet is accidentally frozen."""
    controlnet = DummyModule()
    unet = DummyModule()
    vae = DummyModule()
    text_encoder = DummyModule()

    controlnet.requires_grad_(False)  # Frozen incorrectly
    unet.requires_grad_(False)
    vae.requires_grad_(False)
    text_encoder.requires_grad_(False)

    with pytest.raises(RuntimeError, match="ControlNet has 0 trainable parameters"):
        audit_trainable_parameters(controlnet, unet, vae, text_encoder)


def test_checkpoint_save_and_recovery(tmp_path):
    """Verify that save_checkpoint persists all necessary states for seamless resumption."""
    save_dir = tmp_path / "checkpoint-100"
    controlnet = DummyModule(16, 16)
    optimizer = torch.optim.AdamW(controlnet.parameters(), lr=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=100)
    scaler = torch.amp.GradScaler("cpu", enabled=False)

    save_checkpoint(
        save_dir=save_dir,
        controlnet=controlnet,
        optimizer=optimizer,
        lr_scheduler=scheduler,
        scaler=scaler,
        global_step=100,
        epoch=3,
        loss=0.045,
        val_loss=0.048,
        config={"test": True},
    )

    assert save_dir.exists()
    assert (save_dir / "optimizer.pt").exists()
    assert (save_dir / "scheduler.pt").exists()
    assert (save_dir / "scaler.pt").exists()
    assert (save_dir / "trainer_state.json").exists()

    state = json.loads((save_dir / "trainer_state.json").read_text())
    assert state["global_step"] == 100
    assert state["epoch"] == 3
    assert state["loss"] == 0.045

    assert get_checkpoint_step(save_dir) == 100
    assert find_latest_checkpoint(tmp_path) == save_dir


def test_single_step_forward_backward_cpu_simulation():
    """Verify forward pass, loss calculation, backward pass, and optimizer update on CPU."""
    set_seed(42)
    model = DummyModule(16, 16)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)
    scaler = torch.amp.GradScaler("cpu", enabled=False)

    x = torch.randn(2, 16)
    target = torch.randn(2, 16)

    # Initial weights copy
    initial_weight = model.fc.weight.clone()

    optimizer.zero_grad()
    pred = model(x)
    loss = F.mse_loss(pred, target)
    loss.backward()

    # Check gradients exist
    assert model.fc.weight.grad is not None
    assert torch.norm(model.fc.weight.grad) > 0.0

    optimizer.step()

    # Verify weights changed
    assert not torch.equal(initial_weight, model.fc.weight)


def test_gpu_memory_report_structure():
    """Verify GPU memory report returns expected schema distinguishing physical, allocated, and reserved memory."""
    report = get_gpu_memory_report()
    assert "cuda_available" in report
    assert "device_name" in report
    assert "physical_total_mb" in report
    assert "current_allocated_mb" in report
    assert "current_reserved_mb" in report
    assert "peak_allocated_mb" in report
    assert "peak_reserved_mb" in report
    # Backwards compatibility keys
    assert "vram_total_mb" in report
    assert "vram_allocated_mb" in report
    assert "vram_reserved_mb" in report
    assert "vram_peak_mb" in report


def test_controlnet_300_step_configuration():
    """Verify configs/controlnet_jewellery_300.yaml configuration parameters."""
    config_path = Path("configs/controlnet_jewellery_300.yaml")
    assert config_path.exists(), "configs/controlnet_jewellery_300.yaml not found"

    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    assert cfg["training"]["max_train_steps"] == 300
    assert cfg["training"]["checkpointing_steps"] == 100
    assert cfg["training"]["validation_steps"] == 100
    assert cfg["training"]["learning_rate"] == 1.0e-5
    assert cfg["training"]["resume_from_checkpoint"] == "outputs/controlnet_jewellery/checkpoints/checkpoint-100"
    assert cfg["output"]["output_dir"] == "outputs/controlnet_jewellery_300"
    assert cfg["training"]["train_batch_size"] == 1
    assert cfg["training"]["gradient_accumulation_steps"] == 4
    assert cfg["training"]["gradient_checkpointing"] is True
    assert cfg["training"]["mixed_precision"] == "fp16"


def test_resume_checkpoint_step_continuation(tmp_path):
    """Verify that resuming from checkpoint-100 correctly continues global_step accounting and saves step 200/300 in a new output directory."""
    # 1. Create simulated checkpoint-100
    ck_100_dir = tmp_path / "checkpoint-100"
    ck_100_dir.mkdir(parents=True, exist_ok=True)
    state = {"global_step": 100, "epoch": 3, "loss": 0.0099}
    (ck_100_dir / "trainer_state.json").write_text(json.dumps(state))

    assert get_checkpoint_step(ck_100_dir) == 100

    # 2. Simulate next training run saving checkpoint-200 and checkpoint-300 in separate 300 directory
    out_300_dir = tmp_path / "controlnet_jewellery_300" / "checkpoints"
    ck_200_dir = out_300_dir / "checkpoint-200"
    ck_300_dir = out_300_dir / "checkpoint-300"

    dummy_model = DummyModule()
    opt = torch.optim.AdamW(dummy_model.parameters(), lr=1e-5)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=300)
    scaler = torch.amp.GradScaler("cpu", enabled=False)

    save_checkpoint(ck_200_dir, dummy_model, opt, sched, scaler, global_step=200, epoch=5, loss=0.0075)
    save_checkpoint(ck_300_dir, dummy_model, opt, sched, scaler, global_step=300, epoch=8, loss=0.0055)

    assert get_checkpoint_step(ck_200_dir) == 200
    assert get_checkpoint_step(ck_300_dir) == 300
    assert find_latest_checkpoint(out_300_dir) == ck_300_dir

    # 3. Verify original checkpoint-100 is completely untouched
    assert get_checkpoint_step(ck_100_dir) == 100
    state_orig = json.loads((ck_100_dir / "trainer_state.json").read_text())
    assert state_orig["global_step"] == 100


def test_resume_amp_gradscaler_optimization_flow(tmp_path):
    """Verify that resuming from checkpoint correctly binds optimizer to the resumed model instance and passes scaler.unscale_ & scaler.step without inf check assertion errors."""
    save_dir = tmp_path / "checkpoint-100"
    model_orig = DummyModule(16, 16)
    opt_orig = torch.optim.AdamW(model_orig.parameters(), lr=1e-4)
    sched_orig = torch.optim.lr_scheduler.CosineAnnealingLR(opt_orig, T_max=100)
    scaler_orig = torch.amp.GradScaler("cpu", enabled=False)

    save_checkpoint(save_dir, model_orig, opt_orig, sched_orig, scaler_orig, global_step=100, epoch=3)

    # 1. Simulate Resumed Model Loading
    model_resumed = DummyModule(16, 16)
    model_resumed.load_state_dict(torch.load(save_dir / "diffusion_pytorch_model.bin"))

    # 2. Initialize Optimizer on Resumed Model parameters
    opt_resumed = torch.optim.AdamW(model_resumed.parameters(), lr=1e-4)
    opt_resumed.load_state_dict(torch.load(save_dir / "optimizer.pt"))

    sched_resumed = torch.optim.lr_scheduler.CosineAnnealingLR(opt_resumed, T_max=300)
    sched_resumed.load_state_dict(torch.load(save_dir / "scheduler.pt"))

    scaler_resumed = torch.amp.GradScaler("cpu", enabled=False)
    scaler_resumed.load_state_dict(torch.load(save_dir / "scaler.pt"))

    # 3. Forward & Backward on Resumed Model
    x = torch.randn(2, 16)
    target = torch.randn(2, 16)

    opt_resumed.zero_grad()
    pred = model_resumed(x)
    loss = F.mse_loss(pred, target)

    scaler_resumed.scale(loss).backward()

    # 4. Verify Gradients Exist on the Resumed Model Parameters
    assert model_resumed.fc.weight.grad is not None
    assert torch.norm(model_resumed.fc.weight.grad) > 0.0

    # 5. Verify unscale_ and step succeed without "No inf checks were recorded" error
    scaler_resumed.unscale_(opt_resumed)
    torch.nn.utils.clip_grad_norm_(model_resumed.parameters(), 1.0)
    scaler_resumed.step(opt_resumed)
    scaler_resumed.update()
    opt_resumed.zero_grad()
    sched_resumed.step()

    assert model_resumed.fc.weight.grad is None  # Zeroed after step


def test_100_vs_300_evaluation_artifacts_and_paths():
    """Verify that both final 1000-step and 300-step trained model weights exist and evaluation artifacts are present."""
    model_final_dir = Path("outputs/rendering_v2_controlnet/controlnet_rendering_v2_final")
    model_300_dir = Path("outputs/controlnet_jewellery_300/controlnet_jewellery_final")
    report_file = Path("docs/phases/PHASE_10_100_VS_300_EVALUATION_REPORT.md")
    eval_output_dir = Path("outputs/controlnet_evaluation_100_vs_300/comparisons")

    assert model_final_dir.exists(), "Final 1000-step model directory does not exist"
    assert model_300_dir.exists(), "300-step model directory does not exist"
    assert report_file.exists(), "100 vs 300 evaluation report does not exist"
    assert eval_output_dir.exists(), "100 vs 300 comparisons directory does not exist"

    # Verify all 6 comparison panels were generated
    panels = list(eval_output_dir.glob("comparison_100_vs_300_*.png"))
    assert len(panels) >= 6, f"Expected at least 6 comparison panels, found {len(panels)}"



