# JewelMind YOLO11 Jewellery Component Detection Architecture

This document specifies the technical architecture, component taxonomy, instance segmentation pipeline, and downstream AI integration for JewelMind Phase 6.

---

## 1. Physical Motivation & Business Context

In jewellery manufacturing, converting a 2D sketch or CAD blueprint into an accurate bill of materials (BOM), cost estimate, and casting schedule requires identifying individual constituent components. 

Standard bounding box detection provides only rectangular extents, which fail for curved ring bands, concentric stone bezels, and diagonal claws. **Instance segmentation with YOLO11** produces pixel-accurate polygon contours ($[[x_1, y_1], [x_2, y_2], \dots]$), enabling:
1. **Geometric Measurement:** Contour perimeter and enclosed pixel area map directly to physical stone carat sizes and metal volume.
2. **Feature Extraction for Costing:** Component counts (e.g. number of prongs, stone count) feed directly into Phase 9 XGBoost cost/wastage estimation.
3. **Generative Conditioning:** Segmented component masks act as spatial layout conditioning for Phase 7 ControlNet diffusion.

---

## 2. Evidence-Based Component Taxonomy

JewelMind formalizes a 7-class micro-component taxonomy based on physical jewellery bench manufacturing:

```text
                                  ┌───────────────┐
                                  │  0: gemstone  │
                                  └───────┬───────┘
                                          │ sits in
                ┌─────────────────────────┼─────────────────────────┐
                │                         │                         │
                ▼                         ▼                         ▼
         ┌──────────────┐          ┌──────────────┐          ┌──────────────┐
         │   3: prong   │          │   4: bezel   │          │  5: setting  │
         │ (stone claw) │          │(stone border)│          │(basket/mount)│
         └──────┬───────┘          └──────┬───────┘          └──────┬───────┘
                │                         │                         │
                └─────────────────────────┼─────────────────────────┘
                                          │ mounts to
                                          ▼
                                   ┌──────────────┐
                                   │ 2: ring_head │
                                   └──────┬───────┘
                                          │ transitions via
                                          ▼
                                   ┌──────────────┐
                                   │ 6: shoulder  │
                                   └──────┬───────┘
                                          │ integrates with
                                          ▼
                                  ┌────────────────┐
                                  │  1: ring_shank │
                                  │ (circular band)│
                                  └────────────────┘
```

---

## 3. Candidate Benchmark on NVIDIA RTX 4060

Controlled benchmarking on the local NVIDIA RTX 4060 Laptop GPU (8GB VRAM) yielded empirical performance data:

| Metric | YOLO11s-seg (Small) | YOLO11m-seg (Medium) | Operational Trade-Off |
| :--- | :--- | :--- | :--- |
| **Parameters** | 10.07 Million | 22.34 Million | $2.2\times$ model capacity in YOLO11m |
| **Peak VRAM** | 1,447.7 MiB (1.41 GiB) | 2,690.4 MiB (2.63 GiB) | Both easily fit inside 8GB VRAM with $>5\text{ GB}$ headroom |
| **Inference Latency** | **10.62 ms** | 18.51 ms | YOLO11s is $1.7\times$ faster for real-time canvas feedback |
| **Training Speed** | 21.8 s / epoch | 15.7 s / epoch | Fast convergence with mixed-precision AMP |
| **Recommended Use** | Interactive Studio Canvas | Batch CAD Blueprint Extraction | Complementary dual-checkpoint strategy |

---

## 4. Inference Contract & Stable Schema

The inference pipeline standardizes outputs into the Pydantic `DetectionResult` contract:

```json
{
  "model_version": "yolo11s-seg-jewelmind-v1",
  "image_size": [640, 640],
  "inference_time_ms": 11.4,
  "device_used": "cuda:0",
  "total_detections": 2,
  "detections": [
    {
      "class_id": 0,
      "class_name": "gemstone",
      "confidence": 0.942,
      "bbox": [250.5, 140.0, 390.2, 280.4],
      "mask": [[250.5, 210.2], [320.0, 140.0], [390.2, 210.2], [320.0, 280.4]],
      "normalized_mask": [[0.391, 0.328], [0.500, 0.218], [0.609, 0.328], [0.500, 0.438]],
      "area": 14200.5
    }
  ]
}
```

---

## 5. Downstream AI Service Boundary

Training workflows remain decoupled from the FastAPI application server. The service interface is exposed via:
- **CLI Utility:** `ai/vision/inference/predict_components.py`
- **Python Module:** `from ai.vision.inference.detector import JewelleryComponentDetector`
- **Authenticated API:** `POST /api/v1/ai/components/detect`

```text
Jewellery Blueprint Sketch
           │
           ▼
JewelleryComponentDetector (YOLO11-seg)
           │
           ├──► Polygon Masks ──► Phase 7: ControlNet Diffusion Rendering
           │
           └──► Structured Counts & Areas ──► Phase 9: XGBoost Cost & Wastage Estimator
                                                       │
                                                       ▼
                                            Phase 11: Production Scheduling (OR-Tools)
```
