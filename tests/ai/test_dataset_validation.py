"""Unit Tests for Dataset Validation Logic (YOLO Instance Segmentation)."""

import tempfile
from pathlib import Path
import pytest
import yaml

from ai.vision.training.scripts.validate_dataset import compute_file_hash, validate_dataset


@pytest.fixture
def temp_dataset_dir():
    """Create a temporary mock YOLO segmentation dataset."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_p = Path(tmpdir)
        train_img = tmp_p / "train" / "images"
        train_lbl = tmp_p / "train" / "labels"
        train_img.mkdir(parents=True)
        train_lbl.mkdir(parents=True)

        # Create 1 dummy image file
        import cv2
        import numpy as np
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        img_file = train_img / "ring_001.jpg"
        cv2.imwrite(str(img_file), img)

        # Create valid segmentation label: class 0 with 4 polygon points
        lbl_file = train_lbl / "ring_001.txt"
        lbl_file.write_text("0 0.1 0.1 0.5 0.1 0.5 0.5 0.1 0.5\n", encoding="utf-8")

        # Create dataset YAML
        yaml_path = tmp_p / "data.yaml"
        yaml_content = {
            "path": str(tmp_p),
            "train": "train/images",
            "val": "train/images",
            "test": "train/images",
            "names": {0: "gemstone", 1: "ring_shank"},
        }
        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(yaml_content, f)

        yield yaml_path, tmp_p


def test_valid_dataset_passes(temp_dataset_dir):
    yaml_path, _ = temp_dataset_dir
    report = validate_dataset(str(yaml_path))
    assert report["status"] == "PASS"
    assert report["total_images"] > 0
    assert len(report["errors"]) == 0


def test_missing_label_caught(temp_dataset_dir):
    yaml_path, tmp_p = temp_dataset_dir
    # Remove label file
    lbl_file = tmp_p / "train" / "labels" / "ring_001.txt"
    lbl_file.unlink()

    report = validate_dataset(str(yaml_path))
    assert report["status"] == "FAIL"
    assert any("Missing label file" in e for e in report["errors"])


def test_degenerate_polygon_caught(temp_dataset_dir):
    yaml_path, tmp_p = temp_dataset_dir
    # Write only 2 points (4 coordinates) which cannot form a polygon
    lbl_file = tmp_p / "train" / "labels" / "ring_001.txt"
    lbl_file.write_text("0 0.1 0.1 0.5 0.5\n", encoding="utf-8")

    report = validate_dataset(str(yaml_path))
    assert report["status"] == "FAIL"
    assert any("Degenerate polygon" in e for e in report["errors"])


def test_out_of_bounds_coordinate_caught(temp_dataset_dir):
    yaml_path, tmp_p = temp_dataset_dir
    # Write coordinate > 1.0
    lbl_file = tmp_p / "train" / "labels" / "ring_001.txt"
    lbl_file.write_text("0 0.1 0.1 1.5 0.1 0.5 0.5 0.1 0.5\n", encoding="utf-8")

    report = validate_dataset(str(yaml_path))
    assert report["status"] == "FAIL"
    assert any("Coordinate out of range" in e for e in report["errors"])


def test_invalid_class_id_caught(temp_dataset_dir):
    yaml_path, tmp_p = temp_dataset_dir
    # Class ID 99 exceeds registered classes (0, 1)
    lbl_file = tmp_p / "train" / "labels" / "ring_001.txt"
    lbl_file.write_text("99 0.1 0.1 0.5 0.1 0.5 0.5 0.1 0.5\n", encoding="utf-8")

    report = validate_dataset(str(yaml_path))
    assert report["status"] == "FAIL"
    assert any("Invalid class ID" in e for e in report["errors"])
