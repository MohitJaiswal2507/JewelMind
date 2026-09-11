"""Automated Unit Tests for ControlNet Dataset Loader and Preprocessing."""

import json
from pathlib import Path
import pytest
import torch
from torch.utils.data import DataLoader
from PIL import Image

from ai.training.dataset_controlnet import ControlNetJewelleryDataset, resolve_file_path


@pytest.fixture
def mock_paired_dataset(tmp_path):
    """Fixture creating a synthetic 4-sample paired dataset for testing loader logic."""
    data_dir = tmp_path / "controlnet_paired"
    img_dir = data_dir / "images"
    cond_dir = data_dir / "conditioning"
    meta_dir = data_dir / "metadata"
    img_dir.mkdir(parents=True, exist_ok=True)
    cond_dir.mkdir(parents=True, exist_ok=True)
    meta_dir.mkdir(parents=True, exist_ok=True)

    records = []
    for i in range(4):
        # Create dummy image and conditioning
        im = Image.new("RGB", (512, 512), color=(i * 50, i * 50, i * 50))
        cond = Image.new("RGB", (512, 512), color=(255, 255, 255))
        im_name = f"sample_{i:03d}.jpg"
        cond_name = f"sample_{i:03d}.png"
        im.save(img_dir / im_name)
        cond.save(cond_dir / cond_name)

        records.append({
            "source": f"conditioning/{cond_name}",
            "target": f"images/{im_name}",
            "prompt": f"luxury gold ring style {i}",
        })

    train_meta = meta_dir / "train.jsonl"
    val_meta = meta_dir / "validation.jsonl"
    with open(train_meta, "w", encoding="utf-8") as f:
        for r in records[:3]:
            f.write(json.dumps(r) + "\n")
    with open(val_meta, "w", encoding="utf-8") as f:
        for r in records[3:]:
            f.write(json.dumps(r) + "\n")

    return {
        "data_dir": data_dir,
        "train_meta": train_meta,
        "val_meta": val_meta,
    }


def test_controlnet_dataset_loader_train_split(mock_paired_dataset):
    """Verify that ControlNetJewelleryDataset loads records with proper tensor shapes and ranges."""
    train_meta = Path("datasets/controlnet_paired/metadata/train.jsonl")
    if train_meta.exists():
        dataset = ControlNetJewelleryDataset(
            data_dir="datasets/controlnet_paired",
            metadata_file=train_meta,
            tokenizer=None,
            size=512,
            keep_aspect_ratio=True,
        )
        assert len(dataset) == 147, f"Expected 147 training samples, found {len(dataset)}"
    else:
        dataset = ControlNetJewelleryDataset(
            data_dir=mock_paired_dataset["data_dir"],
            metadata_file=mock_paired_dataset["train_meta"],
            tokenizer=None,
            size=512,
            keep_aspect_ratio=True,
        )
        assert len(dataset) == 3

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


def test_controlnet_dataset_loader_validation_split(mock_paired_dataset):
    """Verify that ControlNetJewelleryDataset loads validation records with proper shapes."""
    val_meta = Path("datasets/controlnet_paired/metadata/validation.jsonl")
    if val_meta.exists():
        dataset = ControlNetJewelleryDataset(
            data_dir="datasets/controlnet_paired",
            metadata_file=val_meta,
            tokenizer=None,
            size=512,
            keep_aspect_ratio=True,
        )
        assert len(dataset) == 17
    else:
        dataset = ControlNetJewelleryDataset(
            data_dir=mock_paired_dataset["data_dir"],
            metadata_file=mock_paired_dataset["val_meta"],
            tokenizer=None,
            size=512,
            keep_aspect_ratio=True,
        )
        assert len(dataset) == 1

    sample = dataset[0]
    assert sample["pixel_values"].shape == (3, 512, 512)
    assert sample["conditioning_pixel_values"].shape == (3, 512, 512)


def test_controlnet_dataloader_batching(mock_paired_dataset):
    """Verify PyTorch DataLoader batching with batch_size=1 and batch_size=2."""
    train_meta = Path("datasets/controlnet_paired/metadata/train.jsonl")
    data_dir = "datasets/controlnet_paired" if train_meta.exists() else mock_paired_dataset["data_dir"]
    meta_file = train_meta if train_meta.exists() else mock_paired_dataset["train_meta"]

    dataset = ControlNetJewelleryDataset(
        data_dir=data_dir,
        metadata_file=meta_file,
        size=512,
    )

    loader = DataLoader(dataset, batch_size=2, shuffle=False)
    batch = next(iter(loader))

    assert batch["pixel_values"].shape == (2, 3, 512, 512)
    assert batch["conditioning_pixel_values"].shape == (2, 3, 512, 512)
    assert batch["input_ids"].shape == (2, 77)
    assert len(batch["prompt"]) == 2


def test_controlnet_dataset_deterministic_indexing(mock_paired_dataset):
    """Verify that multiple index accesses return identical tensor data."""
    train_meta = Path("datasets/controlnet_paired/metadata/train.jsonl")
    data_dir = "datasets/controlnet_paired" if train_meta.exists() else mock_paired_dataset["data_dir"]
    meta_file = train_meta if train_meta.exists() else mock_paired_dataset["train_meta"]

    dataset = ControlNetJewelleryDataset(
        data_dir=data_dir,
        metadata_file=meta_file,
        size=512,
    )

    sample_a = dataset[0]
    sample_b = dataset[0]

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
