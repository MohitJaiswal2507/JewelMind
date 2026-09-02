"""Unit Tests for Component Inference Pipeline and Output Schemas."""

import numpy as np
import pytest

from ai.vision.inference.detector import JewelleryComponentDetector
from ai.vision.inference.schemas import ComponentDetection, DetectionResult


def test_component_detection_schema_validation():
    """Ensure ComponentDetection model validates correct polygon coordinates."""
    det = ComponentDetection(
        class_id=0,
        class_name="gemstone",
        confidence=0.95,
        bbox=[100.0, 150.0, 200.0, 250.0],
        mask=[[100.0, 150.0], [200.0, 150.0], [200.0, 250.0], [100.0, 250.0]],
        normalized_mask=[[0.1, 0.15], [0.2, 0.15], [0.2, 0.25], [0.1, 0.25]],
        area=10000.0,
    )
    assert det.class_id == 0
    assert det.class_name == "gemstone"
    assert len(det.mask) == 4
    assert len(det.bbox) == 4


def test_detection_result_serialization():
    """Ensure DetectionResult serializes cleanly to JSON dictionary."""
    result = DetectionResult(
        model_version="yolo11s-seg-test",
        image_size=[640, 640],
        inference_time_ms=14.5,
        device_used="cuda:0",
        detections=[],
        total_detections=0,
    )
    d = result.model_dump()
    assert d["model_version"] == "yolo11s-seg-test"
    assert d["total_detections"] == 0
    assert d["inference_time_ms"] == 14.5


def test_mock_detector_mode():
    """Ensure detector in mock mode returns stable deterministic detections."""
    detector = JewelleryComponentDetector(mock_mode=True)
    dummy_img = np.zeros((400, 400, 3), dtype=np.uint8)

    result = detector.detect(dummy_img)
    assert isinstance(result, DetectionResult)
    assert result.total_detections >= 2
    assert result.device_used == "mock"
    assert any(d.class_name == "gemstone" for d in result.detections)
    assert any(d.class_name == "ring_shank" for d in result.detections)
