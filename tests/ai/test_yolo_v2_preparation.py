"""Unit Tests for Multi-Jewellery YOLO V2 Dataset Architecture & Configuration."""

from pathlib import Path
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
from ai.vision.training.scripts.audit_dataset import audit_dataset


def test_v1_baseline_taxonomy_preserved():
    """Verify that V1 ring micro-component taxonomy is intact and unmodified."""
    assert len(TAXONOMY_V1) == 7
    assert TAXONOMY_V1[0] == "gemstone"
    assert TAXONOMY_V1[1] == "ring_shank"
    assert TAXONOMY_V1[2] == "ring_head"
    assert TAXONOMY_V1[3] == "prong"
    assert TAXONOMY_V1[4] == "bezel"
    assert TAXONOMY_V1[5] == "setting"
    assert TAXONOMY_V1[6] == "shoulder"
    assert TAXONOMY == TAXONOMY_V1


def test_v2_multi_jewellery_taxonomy_structure():
    """Verify that V2 taxonomy contains all 22 required multi-category component classes."""
    assert len(TAXONOMY_V2) == 22
    # Preserved ring classes
    for i in range(7):
        assert TAXONOMY_V2[i] == TAXONOMY_V1[i]

    # Category extensions
    expected_classes = [
        "earring_body",
        "earring_hook",
        "earring_post",
        "necklace_chain",
        "necklace_pendant",
        "necklace_clasp",
        "pendant_body",
        "pendant_bail",
        "bracelet_band",
        "bracelet_clasp",
        "bracelet_link",
        "bangle_body",
        "brooch_body",
        "brooch_pin",
        "other_jewellery",
    ]
    for cls_name in expected_classes:
        assert cls_name in TAXONOMY_V2.values()


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
    assert len(names) == len(TAXONOMY_V2)
    for cid, cname in TAXONOMY_V2.items():
        assert names[cid] == cname


def test_v2_dataset_directories_exist():
    """Verify that all V2 train/val/test directories are created."""
    base = Path("ai/vision/datasets/jewellery_v2")
    assert base.exists()
    assert (base / "README.md").exists()
    for split in ["train", "val", "test"]:
        assert (base / split / "images").exists()
        assert (base / split / "labels").exists()


def test_validate_dataset_on_v2_config():
    """Verify validate_dataset runs successfully on jewellery_v2.yaml without errors."""
    report = validate_dataset("ai/vision/training/configs/jewellery_v2.yaml")
    assert report["status"] == "PASS"
    assert len(report["errors"]) == 0


def test_audit_dataset_on_v2_config():
    """Verify audit_dataset runs and produces valid metadata."""
    audit = audit_dataset("ai/vision/training/configs/jewellery_v2.yaml")
    assert audit["num_classes"] == 22
    assert "gemstone" in audit["classes"].values()
    assert "necklace_chain" in audit["classes"].values()
    assert len(audit["errors"]) == 0


def test_detector_mock_inference_and_schema():
    """Verify detector mock mode produces schema-compliant DetectionResult."""
    detector = JewelleryComponentDetector(mock_mode=True)
    import numpy as np

    dummy_img = np.zeros((200, 200, 3), dtype=np.uint8)
    result = detector.detect(dummy_img)

    assert isinstance(result, DetectionResult)
    assert result.total_detections == 2
    assert len(result.detections) == 2
    for det in result.detections:
        assert isinstance(det, ComponentDetection)
        assert det.confidence > 0.0
        assert len(det.bbox) == 4
