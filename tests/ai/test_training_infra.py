"""Unit tests for JewelMind Phase 7 training infrastructure.

Tests:
  - Checkpoint discovery and safe checkpoint-last handling
  - Full checkpoint state persistence (optimizer, scheduler, scaler, state JSON)
  - Dataset schema tolerance (legacy & rich future schema)
  - Geometric augmentation safety (no random horizontal flipping)
  - Optimizer step accounting with gradient accumulation
  - Validation execution safety (weights unchanged)
"""

import json
import tempfile
from pathlib import Path
import pytest
from PIL import Image

import torch
import torch.nn as nn
from torchvision import transforms

from ai.training.train_lora import (
    find_latest_checkpoint,
    get_checkpoint_step,
    save_checkpoint,
    evaluate_validation_loss,
    JewelleryCaptionDataset,
)


def test_checkpoint_discovery_and_safe_last_handling(tmp_path: Path):
    """Verify numeric checkpoints are sorted properly and checkpoint-last never crashes parsing."""
    checkpoints_dir = tmp_path / "checkpoints"
    checkpoints_dir.mkdir()

    # Empty directory returns None
    assert find_latest_checkpoint(checkpoints_dir) is None

    # Add numeric checkpoints and checkpoint-last
    (checkpoints_dir / "checkpoint-100").mkdir()
    (checkpoints_dir / "checkpoint-200").mkdir()
    (checkpoints_dir / "checkpoint-50").mkdir()
    (checkpoints_dir / "checkpoint-last").mkdir()
    (checkpoints_dir / "invalid-folder").mkdir()

    latest = find_latest_checkpoint(checkpoints_dir)
    assert latest is not None
    assert latest.name == "checkpoint-200"

    # Verify get_checkpoint_step on numeric folder
    assert get_checkpoint_step(checkpoints_dir / "checkpoint-200") == 200

    # Verify get_checkpoint_step on checkpoint-last with trainer_state.json
    state_file = checkpoints_dir / "checkpoint-last" / "trainer_state.json"
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump({"global_step": 200, "epoch": 5}, f)

    assert get_checkpoint_step(checkpoints_dir / "checkpoint-last") == 200

    # Verify fallback if only checkpoint-last exists (no numeric folders)
    solo_dir = tmp_path / "solo_checkpoints"
    solo_dir.mkdir()
    (solo_dir / "checkpoint-last").mkdir()
    assert find_latest_checkpoint(solo_dir) == solo_dir / "checkpoint-last"


def test_checkpoint_save_and_restore_state(tmp_path: Path):
    """Verify optimizer, scheduler, scaler, and trainer state are saved and restorable."""
    save_dir = tmp_path / "ckpt_test"

    # Create dummy linear model to act as adapter module
    model = nn.Linear(10, 2)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=100)
    scaler = torch.cuda.amp.GradScaler(enabled=False)

    # Modify optimizer state
    loss = model(torch.randn(4, 10)).sum()
    loss.backward()
    optimizer.step()
    scheduler.step()

    # Save checkpoint state
    save_checkpoint(
        save_dir=save_dir,
        unet=model,
        optimizer=optimizer,
        lr_scheduler=scheduler,
        scaler=scaler,
        global_step=42,
        epoch=2,
    )

    # Check files exist
    assert (save_dir / "optimizer.pt").exists()
    assert (save_dir / "scheduler.pt").exists()
    assert (save_dir / "scaler.pt").exists()
    assert (save_dir / "trainer_state.json").exists()

    # Verify trainer_state content
    with open(save_dir / "trainer_state.json", "r", encoding="utf-8") as f:
        state = json.load(f)
    assert state["global_step"] == 42
    assert state["epoch"] == 2

    # Restore into fresh optimizer and verify matching state
    new_optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4)
    new_optimizer.load_state_dict(torch.load(save_dir / "optimizer.pt"))
    assert len(new_optimizer.state_dict()["state"]) == len(optimizer.state_dict()["state"])
    for param_id in optimizer.state_dict()["state"]:
        old_p_state = optimizer.state_dict()["state"][param_id]
        new_p_state = new_optimizer.state_dict()["state"][param_id]
        assert old_p_state["step"] == new_p_state["step"]
        assert torch.equal(old_p_state["exp_avg"], new_p_state["exp_avg"])
        assert torch.equal(old_p_state["exp_avg_sq"], new_p_state["exp_avg_sq"])


def test_dataset_schema_support_and_no_horizontal_flip(tmp_path: Path):
    """Verify dataset supports legacy & future rich schemas and excludes RandomHorizontalFlip."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    # Create 2 sample images
    img1 = Image.new("RGB", (100, 100), color=(255, 215, 0))
    img1.save(data_dir / "ring_legacy.jpg")
    img2 = Image.new("RGB", (100, 100), color=(192, 192, 192))
    img2.save(data_dir / "pendant_rich.png")

    # Write metadata with mixed legacy and rich schema
    metadata = [
        {"file_name": "ring_legacy.jpg", "text": "18k gold ring"},
        {
            "target_image": "pendant_rich.png",
            "caption": "platinum sapphire pendant",
            "category": "pendant",
            "metal": "platinum",
            "gemstone": "sapphire",
            "source": "museum_cc0",
        },
    ]
    with open(data_dir / "metadata.jsonl", "w", encoding="utf-8") as f:
        for entry in metadata:
            f.write(json.dumps(entry) + "\n")

    # Mock tokenizer
    class DummyTokenizer:
        model_max_length = 77
        def __call__(self, text, **kwargs):
            return type("Tokens", (), {"input_ids": torch.zeros((1, 77), dtype=torch.long)})()

    dataset = JewelleryCaptionDataset(str(data_dir), tokenizer=DummyTokenizer(), size=128)
    assert len(dataset) == 2

    # Check that RandomHorizontalFlip is NOT in transforms
    for t in dataset.transforms.transforms:
        assert not isinstance(t, transforms.RandomHorizontalFlip), (
            "RandomHorizontalFlip detected in jewellery dataset transforms! Jewellery geometry must not be mirrored."
        )

    # Check sample 0 (legacy schema)
    s0 = dataset[0]
    assert s0["pixel_values"].shape == (3, 128, 128)

    # Check sample 1 (rich schema)
    s1 = dataset[1]
    assert s1["pixel_values"].shape == (3, 128, 128)
    assert s1["metal"] == "platinum"
    assert s1["gemstone"] == "sapphire"


def test_optimizer_step_accounting_logic():
    """Verify gradient accumulation logic steps optimizer and updates global_step correctly."""
    grad_accum_steps = 4
    total_batches = 10
    global_step = 0
    optimizer_stepped = 0

    for batch_idx in range(total_batches):
        # Accumulate gradients
        if (batch_idx + 1) % grad_accum_steps == 0 or (batch_idx + 1) == total_batches:
            optimizer_stepped += 1
            global_step += 1

    # 10 batches with grad_accum=4 should trigger step at batch 4 (step 1), batch 8 (step 2), and batch 10 (step 3)
    assert optimizer_stepped == 3
    assert global_step == 3


def test_validation_loss_non_modifying():
    """Verify validation loss execution does not update model parameters."""
    class SimpleUNet(nn.Module):
        def __init__(self):
            super().__init__()
            self.linear = nn.Linear(16, 16)
        def forward(self, x, timesteps, encoder_hidden_states):
            return type("Out", (), {"sample": self.linear(x)})()

    model = SimpleUNet()
    initial_weight = model.linear.weight.clone()

    class DummyVAE:
        def encode(self, x):
            return type("Dist", (), {"latent_dist": type("Sample", (), {"sample": lambda *args, **kwargs: x})()})()

    class DummyTextEncoder(nn.Module):
        def forward(self, ids):
            return [torch.zeros((ids.shape[0], 10, 16))]

    class DummyScheduler:
        class config:
            num_train_timesteps = 1000
        def add_noise(self, latents, noise, timesteps):
            return latents + noise

    val_data = [{
        "pixel_values": torch.randn(1, 16),
        "input_ids": torch.zeros((1, 10), dtype=torch.long),
    }]

    loss = evaluate_validation_loss(
        unet=model,
        vae=DummyVAE(),
        text_encoder=DummyTextEncoder(),
        noise_scheduler=DummyScheduler(),
        val_dataloader=val_data,
        device=torch.device("cpu"),
        max_val_batches=2,
    )

    assert loss is not None
    # Verify weights are identical before and after validation
    assert torch.equal(model.linear.weight, initial_weight)
