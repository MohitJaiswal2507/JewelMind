import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Union

# Ensure JewelMind workspace root is on sys.path
_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import cv2
import numpy as np

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    torch = None
    TORCH_AVAILABLE = False

from ai.vision.inference.schemas import ComponentDetection, DetectionResult

# V1 Protected Baseline Taxonomy (7 Ring Micro-Components)
TAXONOMY_V1: Dict[int, str] = {
    0: "gemstone",
    1: "ring_shank",
    2: "ring_head",
    3: "prong",
    4: "bezel",
    5: "setting",
    6: "shoulder",
}

# V2 Multi-Jewellery Taxonomy (22 Components across 8 Categories)
TAXONOMY_V2: Dict[int, str] = {
    # Universal
    0: "gemstone",
    # Ring
    1: "ring_shank",
    2: "ring_head",
    3: "prong",
    4: "bezel",
    5: "setting",
    6: "shoulder",
    # Earring
    7: "earring_body",
    8: "earring_hook",
    9: "earring_post",
    # Necklace
    10: "necklace_chain",
    11: "necklace_pendant",
    12: "necklace_clasp",
    # Pendant
    13: "pendant_body",
    14: "pendant_bail",
    # Bracelet
    15: "bracelet_band",
    16: "bracelet_clasp",
    17: "bracelet_link",
    # Bangle
    18: "bangle_body",
    # Brooch
    19: "brooch_body",
    20: "brooch_pin",
    # Fallback / General
    21: "other_jewellery",
}

# Default backwards-compatible alias
TAXONOMY = TAXONOMY_V1

# Distinct visualization colors for V1 & V2
CLASS_COLORS_V1: Dict[int, tuple] = {
    0: (255, 200, 0),     # gemstone: bright cyan/gold
    1: (0, 140, 255),     # ring_shank: deep orange
    2: (0, 220, 220),     # ring_head: yellow
    3: (255, 0, 255),     # prong: magenta
    4: (0, 220, 0),       # bezel: green
    5: (180, 0, 180),     # setting: purple
    6: (255, 120, 120),   # shoulder: light blue
}

CLASS_COLORS_V2: Dict[int, tuple] = {
    **CLASS_COLORS_V1,
    7: (255, 100, 100),   # earring_body
    8: (255, 150, 50),    # earring_hook
    9: (200, 180, 50),    # earring_post
    10: (50, 200, 100),   # necklace_chain
    11: (50, 220, 220),   # necklace_pendant
    12: (50, 150, 255),   # necklace_clasp
    13: (120, 100, 255),  # pendant_body
    14: (180, 80, 255),   # pendant_bail
    15: (220, 50, 200),   # bracelet_band
    16: (255, 50, 120),   # bracelet_clasp
    17: (200, 100, 150),  # bracelet_link
    18: (150, 200, 80),   # bangle_body
    19: (80, 180, 200),   # brooch_body
    20: (120, 120, 180),  # brooch_pin
    21: (180, 180, 180),  # other_jewellery
}

CLASS_COLORS = CLASS_COLORS_V1


class JewelleryComponentDetector:
    """Inference engine for jewellery component detection and instance segmentation."""

    def __init__(
        self,
        model_path: Optional[str] = None,
        device: Optional[Union[int, str]] = None,
        mock_mode: bool = False,
    ):
        self.mock_mode = mock_mode
        self.model_version = "yolo11m-seg-jewelmind-v1"
        self.model = None

        if self.mock_mode:
            self.device_str = "mock"
            return

        if not TORCH_AVAILABLE:
            self.mock_mode = True
            self.device_str = "mock_fallback"
            return

        # Device selection
        if device is None:
            if torch.cuda.is_available():
                self.device_str = "cuda:0"
            else:
                self.device_str = "cpu"
        else:
            self.device_str = f"cuda:{device}" if isinstance(device, int) else str(device)

        # Environment-driven model preference (v1 or v2)
        model_pref = os.getenv("JEWELRY_VISION_MODEL", "v1").strip().lower()

        # Locate model weights
        candidate_paths = []
        if model_path:
            candidate_paths.append(model_path)

        if model_pref == "v2":
            candidate_paths.extend([
                "runs/segment/runs/jewellery/yolo11m-seg-jewelmind-v2/weights/best.pt",
                "runs/jewellery/yolo11m-seg-jewelmind-v2/weights/best.pt",
                "runs/jewellery/yolo11s-seg-jewelmind-v2/weights/best.pt",
            ])

        # Protected baseline V1 candidates
        candidate_paths.extend([
            "runs/segment/runs/jewellery/yolo11m-seg-jewelmind-v1/weights/best.pt",
            "runs/jewellery/yolo11m-seg-jewelmind-v1/weights/best.pt",
            "runs/jewellery/yolo11s-seg-jewelmind-v1/weights/best.pt",
            "runs/smoke_test/gpu_smoke_run/weights/best.pt",
            "yolo11m-seg.pt",
            "yolo11s-seg.pt",
        ])

        resolved_path = None
        for p in candidate_paths:
            if p and Path(p).exists():
                resolved_path = str(Path(p).resolve())
                break

        if resolved_path:
            from ultralytics import YOLO
            self.model_path = resolved_path
            p_obj = Path(resolved_path)
            if p_obj.stem in ["best", "last"] and p_obj.parent.name == "weights":
                self.model_version = f"{p_obj.parent.parent.name}:{p_obj.stem}"
            else:
                self.model_version = p_obj.stem
            self.model = YOLO(resolved_path)
        else:
            # Fallback to base pretrained weights
            try:
                from ultralytics import YOLO
                self.model_path = "yolo11s-seg.pt"
                self.model_version = "yolo11s-seg-pretrained"
                self.model = YOLO("yolo11s-seg.pt")
            except Exception:
                self.mock_mode = True
                self.device_str = "mock_fallback"

    def get_active_taxonomy(self) -> Dict[int, str]:
        """Return the active taxonomy mapping based on loaded model classes."""
        if self.model and hasattr(self.model, "names") and self.model.names:
            names = self.model.names
            if len(names) == len(TAXONOMY_V2):
                return TAXONOMY_V2
            elif len(names) == len(TAXONOMY_V1):
                return TAXONOMY_V1
            return {int(k): str(v) for k, v in names.items()}
        return TAXONOMY_V1

    def detect(
        self,
        image: Union[str, Path, np.ndarray],
        conf_threshold: float = 0.25,
        iou_threshold: float = 0.45,
    ) -> DetectionResult:
        """Run component instance segmentation on an input image."""
        start_time = time.perf_counter()

        # Load image if file path
        if isinstance(image, (str, Path)):
            img_path = Path(image)
            if not img_path.exists():
                raise FileNotFoundError(f"Image not found at {img_path}")
            img_np = cv2.imread(str(img_path))
            if img_np is None:
                raise ValueError(f"Could not decode image at {img_path}")
        elif isinstance(image, np.ndarray):
            img_np = image
        else:
            raise TypeError("Expected image to be a filepath (str/Path) or numpy.ndarray")

        h, w = img_np.shape[:2]
        active_tax = self.get_active_taxonomy()

        if self.mock_mode or self.model is None:
            # Deterministic mock detections for testing
            mock_detections = [
                ComponentDetection(
                    class_id=0,
                    class_name=active_tax.get(0, "gemstone"),
                    confidence=0.92,
                    bbox=[w * 0.4, h * 0.25, w * 0.6, h * 0.45],
                    mask=[[w * 0.5, h * 0.25], [w * 0.6, h * 0.35], [w * 0.5, h * 0.45], [w * 0.4, h * 0.35]],
                    normalized_mask=[[0.5, 0.25], [0.6, 0.35], [0.5, 0.45], [0.4, 0.35]],
                    area=float(w * h * 0.04),
                ),
                ComponentDetection(
                    class_id=1,
                    class_name=active_tax.get(1, "ring_shank"),
                    confidence=0.88,
                    bbox=[w * 0.2, h * 0.4, w * 0.8, h * 0.85],
                    mask=[[w * 0.2, h * 0.5], [w * 0.5, h * 0.85], [w * 0.8, h * 0.5], [w * 0.5, h * 0.4]],
                    normalized_mask=[[0.2, 0.5], [0.5, 0.85], [0.8, 0.5], [0.5, 0.4]],
                    area=float(w * h * 0.20),
                ),
            ]
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return DetectionResult(
                model_version=self.model_version,
                image_size=[w, h],
                inference_time_ms=round(elapsed_ms, 2),
                device_used=self.device_str,
                detections=mock_detections,
                total_detections=len(mock_detections),
            )

        # Real inference with Ultralytics
        device_arg = 0 if "cuda" in self.device_str else "cpu"
        results = self.model.predict(
            source=img_np,
            conf=conf_threshold,
            iou=iou_threshold,
            device=device_arg,
            verbose=False,
        )

        detections: List[ComponentDetection] = []
        if results and len(results) > 0:
            result = results[0]
            boxes = result.boxes
            masks = result.masks

            if boxes is not None and len(boxes) > 0:
                for i in range(len(boxes)):
                    box = boxes[i]
                    cls_id = int(box.cls[0])
                    conf = float(box.conf[0])
                    xyxy = box.xyxy[0].tolist()

                    cls_name = active_tax.get(cls_id, f"class_{cls_id}")

                    pixel_polygon = []
                    norm_polygon = []
                    area = 0.0

                    if masks is not None and len(masks.xy) > i:
                        pts = masks.xy[i]
                        if len(pts) > 0:
                            pixel_polygon = pts.tolist()
                            pts_np = np.array(pixel_polygon, dtype=np.float32)
                            area = float(cv2.contourArea(pts_np))

                        if len(masks.xyn) > i:
                            norm_polygon = masks.xyn[i].tolist()

                    detections.append(
                        ComponentDetection(
                            class_id=cls_id,
                            class_name=cls_name,
                            confidence=round(conf, 4),
                            bbox=[round(coord, 2) for coord in xyxy],
                            mask=pixel_polygon,
                            normalized_mask=norm_polygon,
                            area=round(area, 2),
                        )
                    )

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        return DetectionResult(
            model_version=self.model_version,
            image_size=[w, h],
            inference_time_ms=round(elapsed_ms, 2),
            device_used=self.device_str,
            detections=detections,
            total_detections=len(detections),
        )
