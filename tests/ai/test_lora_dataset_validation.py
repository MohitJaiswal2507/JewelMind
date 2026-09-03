"""Unit tests for JewelMind LoRA Dataset Integrity Validator.

Validates:
- Correct shared-images layout (<data_dir>/splits/*.jsonl + <data_dir>/images/*)
- Missing image detection
- Empty caption detection
- Invalid JSON line handling
- Corrupted image detection
- Cross-split duplicate leakage detection (Train <-> Validation)
"""

import json
from pathlib import Path
import pytest
from PIL import Image

from ai.training.validate_dataset import (
    calculate_image_hash,
    resolve_image_path,
    validate_split,
    validate_dataset,
)


@pytest.fixture
def mock_lora_dataset(tmp_path: Path):
    """Create a temporary mock LoRA dataset adhering to Phase 8 layout."""
    data_dir = tmp_path / "mock_dataset"
    images_dir = data_dir / "images"
    splits_dir = data_dir / "splits"
    images_dir.mkdir(parents=True)
    splits_dir.mkdir(parents=True)

    # Create 3 valid mock images
    for i in range(1, 4):
        img = Image.new("RGB", (512, 512), color=(i * 40, i * 40, i * 40))
        img.save(images_dir / f"CAND_{i:03d}.jpg")

    # Write train split (CAND_001, CAND_002)
    train_entries = [
        {"file_name": "images/CAND_001.jpg", "text": "gold diamond ring", "category": "ring"},
        {"file_name": "images/CAND_002.jpg", "text": "platinum sapphire necklace", "category": "necklace"},
    ]
    with open(splits_dir / "train_metadata.jsonl", "w", encoding="utf-8") as f:
        for entry in train_entries:
            f.write(json.dumps(entry) + "\n")

    # Write val split (CAND_003)
    val_entries = [
        {"file_name": "images/CAND_003.jpg", "text": "emerald drop earrings", "category": "earrings"},
    ]
    with open(splits_dir / "val_metadata.jsonl", "w", encoding="utf-8") as f:
        for entry in val_entries:
            f.write(json.dumps(entry) + "\n")

    return data_dir


def test_correct_shared_images_layout(mock_lora_dataset: Path):
    """Verify that a properly structured Phase 8 dataset passes validation."""
    passed = validate_dataset(str(mock_lora_dataset))
    assert passed is True


def test_missing_image_detected(mock_lora_dataset: Path):
    """Verify missing referenced image triggers validation failure."""
    # Delete CAND_001.jpg
    (mock_lora_dataset / "images" / "CAND_001.jpg").unlink()
    passed = validate_dataset(str(mock_lora_dataset))
    assert passed is False


def test_empty_caption_detected(mock_lora_dataset: Path):
    """Verify empty text caption triggers validation failure."""
    train_meta = mock_lora_dataset / "splits" / "train_metadata.jsonl"
    with open(train_meta, "w", encoding="utf-8") as f:
        f.write(json.dumps({"file_name": "images/CAND_001.jpg", "text": "  "}) + "\n")

    passed = validate_dataset(str(mock_lora_dataset))
    assert passed is False


def test_invalid_json_detected(mock_lora_dataset: Path):
    """Verify malformed JSON line triggers validation failure."""
    train_meta = mock_lora_dataset / "splits" / "train_metadata.jsonl"
    with open(train_meta, "w", encoding="utf-8") as f:
        f.write("INVALID_NOT_JSON\n")

    passed = validate_dataset(str(mock_lora_dataset))
    assert passed is False


def test_corrupt_image_detected(mock_lora_dataset: Path):
    """Verify corrupt/unreadable image triggers validation failure."""
    corrupt_file = mock_lora_dataset / "images" / "CAND_001.jpg"
    with open(corrupt_file, "wb") as f:
        f.write(b"NOT_A_VALID_JPEG_BYTE_STREAM")

    passed = validate_dataset(str(mock_lora_dataset))
    assert passed is False


def test_train_val_duplicate_leakage_detected(mock_lora_dataset: Path):
    """Verify identical image present in both train and val splits fails validation."""
    # Add CAND_001.jpg (same hash as train sample 1) to validation manifest
    val_meta = mock_lora_dataset / "splits" / "val_metadata.jsonl"
    with open(val_meta, "a", encoding="utf-8") as f:
        f.write(json.dumps({"file_name": "images/CAND_001.jpg", "text": "leaked sample"}) + "\n")

    passed = validate_dataset(str(mock_lora_dataset))
    assert passed is False
