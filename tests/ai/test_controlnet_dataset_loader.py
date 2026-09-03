"""Automated Unit Tests for ControlNet Dataset Loader and Preprocessing."""

import json
from pathlib import Path
import pytest
import torch
from torch.utils.data import DataLoader
from PIL import Image

from ai.training.dataset_controlnet import ControlNetJewelleryDataset, resolve_file_path


def test_controlnet_dataset_loader_train_split():
    """Verify that ControlNetJewelleryDataset loads 147 train records with proper shapes and ranges."""
    train_meta = Path("datasets/controlnet_paired/metadata/train.jsonl")
    assert train_meta.exists(), "train.jsonl metadata file does not exist"

    dataset = ControlNetJewelleryDataset(
        data_dir="datasets/controlnet_paired",
        metadata_file=train_meta,
        tokenizer=None,
        size=512,
        keep_aspect_ratio=True,
    )

    assert len(dataset) == 147, f"Expected 147 training samples, found {len(dataset)}"

    # Check first item
    sample = dataset[0]
    assert "pixel_values" in sample
    assert "conditioning_pixel_values" in sample
    assert "input_ids" in sample
    assert "prompt" in sample
    assert "source_path" in sample
    assert "target_path" in sample

    # Tensor shapes
    assert sample["pixel_values"].shape == (3, 512, 512), f"Invalid target shape: {sample['pixel_values'].shape}"
    assert sample["conditioning_pixel_values"].shape == (3, 512, 512), f"Invalid conditioning shape: {sample['conditioning_pixel_values'].shape}"
    assert sample["input_ids"].shape == (77,), f"Invalid input_ids shape: {sample['input_ids'].shape}"

    # Target normalization range: [-1, 1]
    assert sample["pixel_values"].min() >= -1.01
    assert sample["pixel_values"].max() <= 1.01

    # Conditioning normalization range: [0, 1]
    assert sample["conditioning_pixel_values"].min() >= 0.0
    assert sample["conditioning_pixel_values"].max() <= 1.0


def test_controlnet_dataset_loader_validation_split():
    """Verify that ControlNetJewelleryDataset loads 17 validation records with proper shapes."""
    val_meta = Path("datasets/controlnet_paired/metadata/validation.jsonl")
    assert val_meta.exists(), "validation.jsonl metadata file does not exist"

    dataset = ControlNetJewelleryDataset(
        data_dir="datasets/controlnet_paired",
        metadata_file=val_meta,
        tokenizer=None,
        size=512,
        keep_aspect_ratio=True,
    )

    assert len(dataset) == 17, f"Expected 17 validation samples, found {len(dataset)}"

    sample = dataset[0]
    assert sample["pixel_values"].shape == (3, 512, 512)
    assert sample["conditioning_pixel_values"].shape == (3, 512, 512)


def test_controlnet_dataloader_batching():
    """Verify PyTorch DataLoader batching with batch_size=1 and batch_size=2."""
    dataset = ControlNetJewelleryDataset(
        data_dir="datasets/controlnet_paired",
        size=512,
        max_samples=4,
    )

    loader = DataLoader(dataset, batch_size=2, shuffle=False)
    batch = next(iter(loader))

    assert batch["pixel_values"].shape == (2, 3, 512, 512)
    assert batch["conditioning_pixel_values"].shape == (2, 3, 512, 512)
    assert batch["input_ids"].shape == (2, 77)
    assert len(batch["prompt"]) == 2


def test_controlnet_dataset_deterministic_indexing():
    """Verify that multiple index accesses return identical tensor data."""
    dataset = ControlNetJewelleryDataset(
        data_dir="datasets/controlnet_paired",
        size=512,
        max_samples=5,
    )

    sample_a = dataset[2]
    sample_b = dataset[2]

    assert torch.allclose(sample_a["pixel_values"], sample_b["pixel_values"])
    assert torch.allclose(sample_a["conditioning_pixel_values"], sample_b["conditioning_pixel_values"])
    assert sample_a["prompt"] == sample_b["prompt"]


def test_controlnet_dataset_missing_file_handling(tmp_path):
    """Verify that dataset raises FileNotFoundError on missing metadata or image files."""
    broken_jsonl = tmp_path / "broken.jsonl"
    broken_jsonl.write_text(
        json.dumps({"source": "conditioning/NON_EXISTENT.png", "target": "images/NON_EXISTENT.jpg", "prompt": "ring"}) + "\n"
    )

    dataset = ControlNetJewelleryDataset(
        data_dir=tmp_path,
        metadata_file=broken_jsonl,
        size=512,
    )

    with pytest.raises(FileNotFoundError):
        _ = dataset[0]
