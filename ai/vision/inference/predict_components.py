import argparse
import json
import sys
from pathlib import Path

# Ensure workspace root is in sys.path
_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import cv2
import numpy as np

from ai.vision.inference.detector import CLASS_COLORS, TAXONOMY, JewelleryComponentDetector



def draw_detection_overlay(img: np.ndarray, detections: list) -> np.ndarray:
    """Draw translucent segmentation masks, contours, bounding boxes, and labels."""
    overlay = img.copy()
    canvas = img.copy()

    for det in detections:
        color = (0, 200, 255)  # Default gold
        cid = det.class_id
        if cid == 0:
            color = (255, 200, 0)   # gemstone (cyan)
        elif cid == 1:
            color = (0, 140, 255)   # shank (orange)
        elif cid == 2:
            color = (0, 220, 220)   # head (yellow)
        elif cid == 3:
            color = (255, 0, 255)   # prong (magenta)
        elif cid == 4:
            color = (0, 220, 0)     # bezel (green)
        elif cid == 6:
            color = (255, 120, 120) # shoulder (light blue)

        # Draw polygon mask if available
        if det.mask and len(det.mask) >= 3:
            pts_arr = np.array(det.mask, dtype=np.int32)
            cv2.fillPoly(overlay, [pts_arr], color)
            cv2.polylines(canvas, [pts_arr], True, color, 2, cv2.LINE_AA)

        # Draw bounding box
        x1, y1, x2, y2 = [int(v) for v in det.bbox]
        cv2.rectangle(canvas, (x1, y1), (x2, y2), color, 1, cv2.LINE_AA)

        # Draw text badge
        badge_text = f"{det.class_name} {det.confidence:.2f}"
        (tw, th), _ = cv2.getTextSize(badge_text, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
        cv2.rectangle(canvas, (x1, max(0, y1 - th - 6)), (x1 + tw + 4, max(th + 6, y1)), (30, 30, 30), -1)
        cv2.putText(
            canvas,
            badge_text,
            (x1 + 2, max(th, y1 - 3)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )

    # Blend alpha
    alpha = 0.35
    blended = cv2.addWeighted(overlay, alpha, canvas, 1 - alpha, 0)
    return blended


def main():
    parser = argparse.ArgumentParser(description="Predict jewellery components on a sketch image.")
    parser.add_argument("--model", default=None, help="Path to trained YOLO model weights (.pt)")
    parser.add_argument("--source", required=True, help="Path to input jewellery sketch image")
    parser.add_argument("--conf", type=float, default=0.25, help="Confidence threshold (0.0 to 1.0)")
    parser.add_argument("--output", default=None, help="Path to save annotated output image")
    parser.add_argument("--device", default=None, help="CUDA device index (0) or 'cpu'")
    parser.add_argument("--json_output", default=None, help="Path to save JSON detections output")
    args = parser.parse_args()

    source_path = Path(args.source)
    if not source_path.exists():
        print(f"[ERROR] Source image not found: {source_path}")
        sys.exit(1)

    detector = JewelleryComponentDetector(model_path=args.model, device=args.device)
    result = detector.detect(source_path, conf_threshold=args.conf)

    # Output formatted JSON
    result_dict = result.model_dump()
    print("\n" + "=" * 60)
    print(f"JEWELMIND COMPONENT DETECTION: {source_path.name}")
    print("=" * 60)
    print(f"Model:          {result.model_version}")
    print(f"Inference Time: {result.inference_time_ms:.2f} ms")
    print(f"Hardware:       {result.device_used}")
    print(f"Total Detected: {result.total_detections} components")
    print("-" * 60)
    for idx, det in enumerate(result.detections):
        print(f"[{idx+1}] {det.class_name:<12} (Conf: {det.confidence:.2%}) BBox: {det.bbox} Area: {det.area or 0:.1f}px")

    if args.json_output:
        json_path = Path(args.json_output)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result_dict, f, indent=2)
        print(f"[*] JSON detections saved to: {json_path}")

    # Render visualization overlay if output specified
    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        orig_img = cv2.imread(str(source_path))
        annotated_img = draw_detection_overlay(orig_img, result.detections)
        cv2.imwrite(str(out_path), annotated_img)
        print(f"[*] Visualized prediction saved to: {out_path}")

    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
