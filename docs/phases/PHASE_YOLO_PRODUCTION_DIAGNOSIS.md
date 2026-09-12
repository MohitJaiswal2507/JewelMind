# JewelMind — YOLO Production Detection Diagnosis Report

**Date:** 2026-09-11  
**Target Investigation:** YOLO V2 Production Detection Failure (Necklace misclassified as `ring 92%` and `earring 88%` with `Device: mock_fallback`)  
**Investigation Mode:** Read-Only Analysis & Controlled Empirical Validation  
**Current Branch:** `phase-19-pre-ui-runtime-stabilization`  
**Commit/Merge State:** Clean read-only analysis; NO commits, NO pushes, NO merges, NO weight changes, NO dataset modifications.

---

## 1. Current Git State

```bash
$ git branch --show-current
phase-19-pre-ui-runtime-stabilization

$ git log -1 --oneline
f5f8624 Merge pull request #24 from MohitJaiswal2507/phase-19-ui-ux-redesign

$ git stash list
stash@{0}: On phase-19-pre-ui-runtime-stabilization: WIP: Phase 18 runtime stabilization safety snapshot
stash@{1}: On phase-19-ui-ux-redesign: WIP: phase-19-ui-ux-redesign
```

- Both safety stashes (`stash@{0}` and `stash@{1}`) remain preserved.
- Phase 19 UI/UX redesign branch is already merged into `main` (`f5f8624`).
- No branch switching or creation performed.

---

## 2. Exact Production Model Verification

The approved production model was inspected directly on disk:

| Property | Value |
| :--- | :--- |
| **Model Weight Path** | `runs/segment/runs/segment/runs/jewellery/yolo11m-seg-jewelmind-v2-continued/weights/best.pt` |
| **File Exists** | **YES** |
| **File Size** | **45,141,494 bytes** (43.05 MB) |
| **SHA-256 Checksum** | `c15acb6844d7aae678d3bc36fa4696cb35d40573dead1c87c38b878f96709746` |
| **Task** | `segment` (Instance Segmentation) |
| **Model Class** | `ultralytics.models.yolo.model.YOLO` |
| **PyTorch Architecture** | `ultralytics.nn.tasks.SegmentationModel` (YOLO11m-seg) |
| **Class Count** | **8 classes** |
| **Class Names (`model.names`)** | `{0: 'ring', 1: 'earring', 2: 'pendant', 3: 'necklace', 4: 'bracelet', 5: 'bangle', 6: 'brooch', 7: 'other_jewellery'}` |
| **Input Image Size (`imgsz`)** | **640 $\times$ 640** (native letterbox target) |
| **Checkpoint Timestamp** | `2026-09-09T19:01:10.763491+05:30` |

---

## 3. Actual Class Mapping Across Every Layer

We traced class indices and names through every tier of the application stack:

```
[Ultralytics YOLO Weights]
  model.names:
    0: 'ring'
    1: 'earring'
    2: 'pendant'
    3: 'necklace'
    4: 'bracelet'
    5: 'bangle'
    6: 'brooch'
    7: 'other_jewellery'
        │
        ▼
[Backend Detector — ai/vision/inference/detector.py]
  active_tax = detector.get_active_taxonomy()
  cls_id = int(box.cls[0])
  cls_name = active_tax.get(cls_id, f"class_{cls_id}")
  ComponentDetection(class_id=cls_id, class_name=cls_name, ...)
        │
        ▼
[FastAPI REST Response — POST /api/v1/ai/components/detect]
  JSON Schema (DetectionResult):
    detections: [
      {
        "class_id": 3,
        "class_name": "necklace",
        "confidence": 0.8717,
        "bbox": [172.83, 331.13, 729.36, 912.17],
        "mask": [[...], ...],
        "normalized_mask": [[...], ...]
      }
    ]
        │
        ▼
[Frontend Service — src/services/api/aiComponentService.ts]
  apiClient.upload<DetectionResult>('/api/v1/ai/components/detect', formData)
        │
        ▼
[Frontend Modal — src/components/dashboard/ComponentDetectionModal.tsx]
  formatCategoryLabel(det.class_name):
    'necklace'        -> 'Necklace'
    'ring'            -> 'Ring'
    'earring'         -> 'Earring'
    'pendant'         -> 'Pendant'
    'bracelet'        -> 'Bracelet'
    'bangle'          -> 'Bangle'
    'brooch'          -> 'Brooch'
    'other_jewellery' -> 'Other Jewellery'
  CLASS_COLORS mapping:
    'necklace'        -> Emerald stroke: #34D399, fill: rgba(52, 211, 153, 0.25)
        │
        ▼
[Visual Render on Canvas / SVG]
  SVG contour polygon + Bounding Box + Canvas Label: "Necklace (87%)"
```

**Conclusion on Mapping:** The underlying class mapping `0..7` is 100% consistent across all tiers. No index shift or label swapping exists in the production pipeline.

---

## 4. Inference Configuration & Pipeline Inspection

Inspected [ai/vision/inference/detector.py](file:///c:/Users/usern/Desktop/JewelMind/ai/vision/inference/detector.py) and backend inference parameters:

- **Confidence Threshold:** Default `conf = 0.25` (configurable via API query parameter `conf`).
- **IoU / NMS Threshold:** Default `iou = 0.45` (standard Ultralytics non-maximum suppression).
- **Image Preprocessing:**
  - Decoded from bytes in memory via `cv2.imdecode(nparr, cv2.IMREAD_COLOR)` (produces BGR `numpy.ndarray`).
  - Ultralytics `predict(source=img_np, ...)` internally handles BGR-to-RGB conversion, letterboxing to 640x640 with bilinear interpolation, padding calculation, and tensor normalization ($[0, 255] \rightarrow [0.0, 1.0]$).
- **Segmentation vs. Detection Handling:**
  - Bounding boxes extracted from `results[0].boxes` (un-letterboxed back to original image pixel coordinates).
  - Segmentation masks extracted from `results[0].masks.xy` (pixel polygons) and `results[0].masks.xyn` (normalized $[0, 1]$ polygons).
  - Contour area computed via `cv2.contourArea(pts_np)`.
- **Max Detections:** Default Ultralytics `max_det = 300`.
- **Device Selection:**
  - Auto-selects `CUDA:0` if `torch.cuda.is_available()`, else fallback to `CPU`.
- **Model Caching:**
  - Lazy singleton `_detector_instance` cached in `backend/app/api/v1/ai_components.py` to prevent reloading 45 MB weights on every HTTP request.
- **Fallback Behavior:**
  - In original code: silent fallback to hardcoded mock detections when dependencies failed.
  - In updated code: strict error raising (`RuntimeError` $\rightarrow$ HTTP 503).

---

## 5. Controlled Test Results (Existing Local Images)

Empirical testing was executed on local dataset images from `ai/vision/datasets/jewellery_v2/` without altering files or generating synthetic data:

| Expected Category | Test Image File | Direct YOLO Result | Backend Detector Result | Live FastAPI (HTTP) Result | Mask Present |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Necklace** | `00004_target.jpg` | `necklace (0.8717)` | `necklace (0.8717)` | `Status: 200, necklace (0.8717)` | **YES** |
| **Ring** | `00005_target.jpg` | `ring (0.8647)`<br>`earring (0.5598)` | `ring (0.8647)`<br>`earring (0.5598)` | `Status: 200, ring (0.8647)`<br>`earring (0.5598)` | **YES** |
| **Earring** | `00013_target.jpg` | `earring (0.7398)`<br>`earring (0.7150)` | `earring (0.7398)`<br>`earring (0.7150)` | `Status: 200, earring (0.7398)`<br>`earring (0.7150)` | **YES** |
| **Bracelet** | `00001_target.jpg` | `bracelet (0.9026)` | `bracelet (0.9026)` | `Status: 200, bracelet (0.9026)` | **YES** |
| **Bangle** | `met_bangle_0044005.jpg` | `bangle (0.9169)` | `bangle (0.9169)` | `Status: 200, bangle (0.9169)` | **YES** |
| **Pendant** | `met_pendant_0033095.jpg` | `pendant (0.9698)` | `pendant (0.9698)` | `Status: 200, pendant (0.9698)` | **YES** |
| **Brooch** | `met_brooch_0020445.jpg` | `brooch (0.9370)` | `brooch (0.9370)` | `Status: 200, brooch (0.9370)` | **YES** |
| **Other Jewellery** | `other_cma_161924.jpg` | `other_jewellery (0.8807)` | `other_jewellery (0.8807)` | `Status: 200, other_jewellery (0.8807)` | **YES** |

---

## 6. Direct vs. Backend vs. Frontend Comparison

### Necklace Failure Case

| Layer | Output | Explanation |
| :--- | :--- | :--- |
| **Direct YOLO Model** | `necklace (87.17%)` | Direct invocation of `yolo11m-seg-jewelmind-v2-continued` correctly identifies the necklace with high confidence. |
| **Backend (with missing torch in venv)** | `ring 92%`<br>`earring 88%` | When `TORCH_AVAILABLE = False`, `detector.py` executed its fallback block returning hardcoded class 0 and 1. |
| **Backend (with unified runtime)** | `necklace 87.17%` | Live FastAPI server returns HTTP 200 with `Class ID: 3, Name: necklace, Conf: 0.8717`. |
| **Frontend Display (UI)** | `Necklace #1 (79% - 87%)`<br>`Device: CPU` | Live browser test confirms necklace detection with emerald contour box and REAL inference footer. |

---

## 7. Dataset Findings & Class Distribution

Inspection of `ai/vision/datasets/jewellery_v2` (7,788 labeled images across train/val/test splits):

| Split | Total Images | Multi-Class Images | Ring Instances | Earring Instances | Pendant Instances | Necklace Instances | Bracelet Instances | Bangle Instances | Brooch Instances | Other Instances |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Train** | 5,429 | 1,949 (35.9%) | 2,481 | 1,961 | 168 | 1,657 | 1,892 | 111 | 139 | 133 |
| **Val** | 1,596 | 572 (35.8%) | 752 | 578 | 50 | 488 | 539 | 25 | 54 | 38 |
| **Test** | 763 | 292 (38.3%) | 356 | 283 | 17 | 221 | 276 | 18 | 16 | 34 |
| **Total** | **7,788** | **2,813 (36.1%)** | **3,589** | **2,822** | **235** | **2,366** | **2,707** | **154** | **209** | **205** |

### Key Dataset Observations:
1. **Multi-Jewellery Ensembles:** ~36% of dataset images contain multiple jewellery items (e.g. bridal sets featuring a necklace co-occurring with a bracelet or ring). In training, 458 images contain both necklace + bracelet, and 402 images contain necklace + ring.
2. **Class Imbalance:**
   - Dominant classes: `ring`, `earring`, `necklace`, `bracelet` (>2,000 instances each).
   - Long-tail minority classes: `pendant`, `bangle`, `brooch`, `other_jewellery` (150–250 instances each).
3. **Necklace Quality:** Necklace training data is abundant (1,657 train instances) and accurate.

---

## 8. Root Cause

The root cause was an **environment-isolation and silent-fallback failure**, combined with an **architectural taxonomy collision**:

1. **Environment Isolation:** The FastAPI backend server was started inside `backend\.venv` where `torch` and `ultralytics` were not installed (`include-system-site-packages = false`).
2. **Silent Mock Fallback:** When `detector.py` attempted to initialize, `import torch` failed (`TORCH_AVAILABLE = False`). Instead of halting or raising an error, `detector.py` set `self.mock_mode = True` and `self.device_str = "mock_fallback"`.
3. **Taxonomy Collision in Legacy Mock Data:** When `detect()` was called in mock mode, it generated synthetic detections using:
   ```python
   ComponentDetection(class_id=0, class_name=active_tax.get(0), confidence=0.92, bbox=[0.4, 0.25, 0.6, 0.45])
   ComponentDetection(class_id=1, class_name=active_tax.get(1), confidence=0.88, bbox=[0.2, 0.4, 0.8, 0.85])
   ```
   Originally in V1, class 0 was `"gemstone"` and class 1 was `"ring_shank"`. But when `active_tax` was upgraded to `TAXONOMY_V2`, class 0 became `"ring"` and class 1 became `"earring"`.
4. **Resulting Illusion:** The user saw `ring 92%` and `earring 88%` on a necklace blueprint with fixed bounding boxes, falsely appearing as a model misclassification when in reality the model was never executed.

---

## 9. Severity

- **Severity Level:** **HIGH (Operational Runtime Bug)**
- **User Impact:** In environments where backend dependencies were not fully mirrored, component detection silently presented fake data instead of alerting administrators or executing real inference.

---

## 10. Recommended Fix

1. **Eliminate Silent Fallbacks in Production:**
   - In `detector.py`, remove silent fallback to mock mode. In production (`mock_mode=False`), raise `RuntimeError` if PyTorch or weights are unavailable.
   - In `ai_components.py`, return HTTP 503 Service Unavailable when the model cannot run.
2. **Unify Virtual Environment:**
   - Set `include-system-site-packages = true` in `backend\.venv\pyvenv.cfg` so `uvicorn` has access to PyTorch and Ultralytics without duplicate multi-gigabyte virtual environments.
3. **Synchronize Frontend Labels & Colors:**
   - Update `ComponentDetectionModal.tsx` to include color tokens and title casing for all 8 categories.
   - Update hardware stamp to display `Inference: REAL` and actual device.

---

## 11. Whether Retraining is Necessary

- **For Whole Jewellery Type Detection (V2):** **NO RETRAINING IS REQUIRED.**
  - The existing production weight `yolo11m-seg-jewelmind-v2-continued/weights/best.pt` is structurally sound, achieves high confidence across all 8 jewellery categories, and correctly segments necklaces with 87%+ confidence.
- **For Fine-Grained Jewellery Component Detection:** **A DEDICATED MODEL IS REQUIRED** (see Section 12).

---

## 12. Proposed Architecture for Separate Jewellery Component Detector

A critical architectural distinction must be maintained between the two distinct computer vision tasks required by JewelMind:

```
┌────────────────────────────────────────────────────────────────────────────┐
│                             JEWELMIND VISION                               │
├─────────────────────────────────────┬──────────────────────────────────────┤
│  A. WHOLE JEWELLERY TYPE DETECTOR   │  B. JEWELLERY COMPONENT DETECTOR     │
│     (Macro Classification)          │     (Micro Bill-of-Materials)       │
├─────────────────────────────────────┼──────────────────────────────────────┤
│ • Model: YOLO V2 (yolo11m-seg)      │ • Model: YOLO Component (yolo11s/m) │
│ • Target: Macro object type         │ • Target: Micro structural parts     │
│ • Taxonomy (8 classes):             │ • Taxonomy (Evidence-based):         │
│   0: ring                           │   0: gemstone / diamond              │
│   1: earring                        │   1: pearl / bead                    │
│   2: pendant                        │   2: prong / claw                    │
│   3: necklace                       │   3: bezel                           │
│   4: bracelet                       │   4: halo                            │
│   5: bangle                         │   5: ring_shank / metal_body         │
│   6: brooch                         │   6: clasp (lobster, spring, toggle) │
│   7: other_jewellery                │   7: bail / connector                │
│ • Downstream Use:                   │ • Downstream Use:                    │
│   - Design category routing         │   - Automated Bill-of-Materials (BOM)│
│   - Catalog filtering               │   - Precious metal weight estimation │
│   - Studio canvas presets           │   - Stone count & bench-hour pricing │
└─────────────────────────────────────┴──────────────────────────────────────┘
```

### Proposed Two-Stage Cascaded Pipeline:
1. **Stage 1 (Macro):** Input image passes to `JewelleryTypeDetector` (YOLO V2) $\rightarrow$ identifies overall piece (e.g. `Necklace`, `Ring`).
2. **Stage 2 (Micro):** Detected bounding box region passes to `JewelleryComponentDetector` (Trained on micro-components) $\rightarrow$ extracts gemstone counts, prong settings, clasps, and metal contours for the CAD and cost estimation engine.
