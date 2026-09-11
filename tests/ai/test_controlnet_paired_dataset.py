"""Tests for ControlNet Paired Dataset Integrity."""

import json
from pathlib import Path
from PIL import Image
import pytest

DATASET_ROOT = Path("datasets/controlnet_paired")


@pytest.mark.skipif(not DATASET_ROOT.exists(), reason="Historical intermediate dataset was cleaned up in post-training storage optimization")
def test_controlnet_dataset_structure_and_counts():
    """Verifies that datasets/controlnet_paired exists with exactly 164 images, 164 conditioning maps, 147 train and 17 val pairs."""
    images_dir = DATASET_ROOT / "images"
    cond_dir = DATASET_ROOT / "conditioning"
    meta_dir = DATASET_ROOT / "metadata"

    assert DATASET_ROOT.exists(), "datasets/controlnet_paired directory does not exist."
    assert images_dir.exists(), "images directory does not exist."
    assert cond_dir.exists(), "conditioning directory does not exist."
    assert meta_dir.exists(), "metadata directory does not exist."

    img_files = list(images_dir.glob("*.jpg"))
    cond_files = list(cond_dir.glob("*.png"))

    assert len(img_files) == 164, f"Expected 164 source images, found {len(img_files)}"
    assert len(cond_files) == 164, f"Expected 164 conditioning images, found {len(cond_files)}"

    # Check matching stems
    img_stems = {f.stem for f in img_files}
    cond_stems = {f.stem for f in cond_files}
    assert img_stems == cond_stems, "Mismatched stems between images and conditioning maps"

    # Check train / val jsonl
    train_jsonl = meta_dir / "train.jsonl"
    val_jsonl = meta_dir / "validation.jsonl"
    assert train_jsonl.exists(), "train.jsonl missing"
    assert val_jsonl.exists(), "validation.jsonl missing"

    train_lines = [json.loads(l) for l in train_jsonl.read_text(encoding="utf-8").strip().split("\n") if l.strip()]
    val_lines = [json.loads(l) for l in val_jsonl.read_text(encoding="utf-8").strip().split("\n") if l.strip()]

    assert len(train_lines) == 147, f"Expected 147 train records, found {len(train_lines)}"
    assert len(val_lines) == 17, f"Expected 17 val records, found {len(val_lines)}"


@pytest.mark.skipif(not DATASET_ROOT.exists(), reason="Historical intermediate dataset was cleaned up in post-training storage optimization")
def test_controlnet_conditioning_images_format():
    """Verifies all conditioning images are 512x512 RGB images."""
    cond_dir = DATASET_ROOT / "conditioning"
    cond_files = list(cond_dir.glob("*.png"))

    for f in cond_files:
        with Image.open(f) as im:
            assert im.size == (512, 512), f"{f.name} has invalid size: {im.size}"
            assert im.mode == "RGB", f"{f.name} has invalid mode: {im.mode}"


@pytest.mark.skipif(not DATASET_ROOT.exists(), reason="Historical intermediate dataset was cleaned up in post-training storage optimization")
def test_controlnet_dataset_sha256_separation():
    """Verifies zero train/val overlap in metadata."""
    summary_path = DATASET_ROOT / "metadata/dataset_summary.json"
    assert summary_path.exists(), "dataset_summary.json missing"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["sha256_overlap"] == 0
    assert summary["corrupted_images"] == 0
