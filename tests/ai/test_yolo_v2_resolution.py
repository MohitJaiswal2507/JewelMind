"""Unit tests verifying production YOLO V2 multi-jewellery model path resolution."""

import os
from pathlib import Path
import pytest

from ai.vision.inference.detector import JewelleryComponentDetector, TAXONOMY_V2


def test_yolo_v2_production_model_resolution():
    """Verify that JewelleryComponentDetector resolves strictly to the production YOLO V2 continued model."""
    detector = JewelleryComponentDetector()

    assert detector.model is not None, "YOLO detector model should load successfully"
    assert detector.model_path is not None, "Model path should be resolved"

    resolved_path = Path(detector.model_path)
    assert resolved_path.name == "best.pt", f"Expected filename 'best.pt', got '{resolved_path.name}'"
    assert "yolo11m-seg-jewelmind-v2-continued" in str(resolved_path), (
        f"Path must point to 'yolo11m-seg-jewelmind-v2-continued', got '{resolved_path}'"
    )
    assert "yolo11m-seg-jewelmind-v1" not in str(resolved_path), "Should not resolve to V1 baseline"
    assert "checkpoint" not in str(resolved_path), "Should not resolve to an intermediate checkpoint"


def test_yolo_v2_active_taxonomy():
    """Verify that the loaded YOLO V2 model active taxonomy matches the 8 multi-jewellery classes."""
    detector = JewelleryComponentDetector()
    taxonomy = detector.get_active_taxonomy()

    assert len(taxonomy) == 8, f"Expected 8 classes in active taxonomy, got {len(taxonomy)}"
    assert taxonomy[0] == "ring"
    assert taxonomy[1] == "earring"
    assert taxonomy[2] == "pendant"
    assert taxonomy[3] == "necklace"
    assert taxonomy[4] == "bracelet"
    assert taxonomy[5] == "bangle"
    assert taxonomy[6] == "brooch"
    assert taxonomy[7] == "other_jewellery"
