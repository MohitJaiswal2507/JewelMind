"""Unit Tests for Multi-Jewellery YOLO V2 Dataset Engineering & Conversion Pipeline."""

import tempfile
from pathlib import Path
import cv2
import numpy as np
import pytest
import yaml

from ai.vision.inference.detector import (
    TAXONOMY,
    TAXONOMY_V1,
    TAXONOMY_V2,
    CLASS_COLORS_V1,
    CLASS_COLORS_V2,
    JewelleryComponentDetector,
)
from ai.vision.inference.schemas import ComponentDetection, DetectionResult
from ai.vision.training.scripts.validate_dataset import validate_dataset
from scripts.convert_dwpose_to_yolo import (
    JEWELMIND_CATEGORIES,
    normalize_prompt,
    mask_to_yolo_polygons,
    get_deterministic_split,
)


def test_v1_baseline_taxonomy_preserved():
    """Verify that V1 ring micro-component taxonomy is intact and unmodified."""
    assert len(TAXONOMY_V1) == 7
    assert TAXONOMY_V1[0] == "gemstone"
    assert TAXONOMY_V1[1] == "ring_shank"
    assert TAXONOMY == TAXONOMY_V1


def test_v2_jewelmind_category_taxonomy():
    """Verify that V2 taxonomy contains all 8 required JewelMind categories."""
    assert len(TAXONOMY_V2) == 8
    expected = ["ring", "earring", "pendant", "necklace", "bracelet", "bangle", "brooch", "other_jewellery"]
    for idx, name in enumerate(expected):
        assert TAXONOMY_V2[idx] == name
        assert JEWELMIND_CATEGORIES[name] == idx


def test_v2_yaml_configuration_validity():
    """Verify jewellery_v2.yaml loads cleanly and matches TAXONOMY_V2."""
    yaml_path = Path("ai/vision/training/configs/jewellery_v2.yaml")
    assert yaml_path.exists(), "jewellery_v2.yaml must exist"

    with open(yaml_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    assert config["path"] == "ai/vision/datasets/jewellery_v2"
    assert config["train"] == "train/images"
    assert config["val"] == "val/images"
    assert config["test"] == "test/images"

    names = config["names"]
    assert len(names) == 8
    for cid, cname in TAXONOMY_V2.items():
        assert names[cid] == cname


def test_prompt_normalization_rules():
    """Verify prompt normalization handles gender removal, plurals, and watches."""
    assert normalize_prompt("female, earring") == "earring"
    assert normalize_prompt("female, earrings") == "earring"
    assert normalize_prompt("female,earring") == "earring"
    assert normalize_prompt("male, bracelet") == "bracelet"
    assert normalize_prompt("female, ring") == "ring"
    assert normalize_prompt("female, necklace") == "necklace"
    assert normalize_prompt("female, watch") is None  # Excluded
    assert normalize_prompt("female, oops") is None    # Ambiguous


def test_mask_to_yolo_polygons_conversion():
    """Verify polygon conversion from binary mask produces valid YOLO format coordinates."""
    # Create 100x100 mask with 20x20 square in center
    mask = np.zeros((100, 100), dtype=np.uint8)
    mask[40:60, 40:60] = 255

    polygons = mask_to_yolo_polygons(mask, class_id=0, min_area_px=10)
    assert len(polygons) == 1

    tokens = polygons[0].split()
    assert tokens[0] == "0"
    coords = [float(x) for x in tokens[1:]]
    assert len(coords) >= 6  # Minimum 3 points (6 floats)
    assert all(0.0 <= c <= 1.0 for c in coords)


def test_deterministic_split_zero_leakage():
    """Verify deterministic split ensures same target path always gets identical split."""
    test_targets = ["01067_target.jpg", "04262_target.jpg", "00576_target.jpg"]
    for t in test_targets:
        split1 = get_deterministic_split(t)
        split2 = get_deterministic_split(t)
        assert split1 == split2
        assert split1 in ["train", "val", "test"]


def test_validate_dataset_on_v2_generated_data():
    """Verify validate_dataset passes cleanly on converted dataset."""
    report = validate_dataset("ai/vision/training/configs/jewellery_v2.yaml")
    assert report["status"] == "PASS"
    assert report["total_images"] > 5000
    assert report["total_instances"] > 10000
    assert len(report["errors"]) == 0


def test_detector_mock_inference():
    """Verify detector mock mode produces schema-compliant DetectionResult."""
    detector = JewelleryComponentDetector(mock_mode=True)
    dummy_img = np.zeros((200, 200, 3), dtype=np.uint8)
    result = detector.detect(dummy_img)

    assert isinstance(result, DetectionResult)
    assert result.total_detections == 2
    assert len(result.detections) == 2
    for det in result.detections:
        assert isinstance(det, ComponentDetection)
        assert det.confidence > 0.0
        assert len(det.bbox) == 4
