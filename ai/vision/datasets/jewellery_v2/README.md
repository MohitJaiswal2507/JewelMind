# JewelMind Multi-Jewellery V2 Dataset Architecture

This directory is designated for the **JewelMind Multi-Jewellery YOLO V2 Instance Segmentation Dataset**.

---

## 📁 Directory Structure

```text
jewellery_v2/
├── train/
│   ├── images/      # Training JPEG/PNG jewellery images
│   └── labels/      # YOLO segmentation polygon labels (.txt)
├── val/
│   ├── images/      # Validation JPEG/PNG images
│   └── labels/      # Validation polygon labels (.txt)
├── test/
│   ├── images/      # Independent test evaluation images
│   └── labels/      # Test polygon labels (.txt)
└── README.md        # Dataset specifications & provenance documentation
```

---

## 🏷️ Label Format (YOLO Instance Segmentation)

Each label file (`<image_name>.txt`) contains one line per annotated instance:
```text
<class_id> <x1> <y1> <x2> <y2> <x3> <y3> ... <xn> <yn>
```
- `<class_id>`: Integer between `0` and `21` matching `jewellery_v2.yaml`.
- Coordinates `(x, y)`: Normalized polygon vertices in range `[0.0, 1.0]`. Minimum 3 points (6 floats).

---

## 🔒 Baseline Protection Notice
The V1 sample dataset located at `ai/vision/datasets/sample/` and the trained V1 weights at `runs/segment/runs/jewellery/yolo11m-seg-jewelmind-v1/weights/best.pt` are **protected production baselines** and must never be overwritten.
