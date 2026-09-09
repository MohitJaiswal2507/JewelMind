# JewelMind YOLO V2 Notebook & Model Analysis Report
**Academic & Technical Documentation for YOLO11m-seg Jewellery Segmentation**

---

## 1. Executive Summary

This report documents the creation and end-to-end execution of the academic Jupyter Notebook presentation for the completed **JewelMind YOLO V2 Multi-Jewellery Instance Segmentation Model**. The notebook is specifically structured to provide a comprehensive, publication-grade experimental analysis suitable for presentation to academic advisors, course faculty, and technical evaluators.

**Strict Data Integrity & Verification Standard:**
- **Zero Retraining or Weight Modification:** The trained checkpoint was evaluated in strict inference mode.
- **Zero Synthetic Metrics:** All quantitative metrics, loss curves, confusion matrices, and distribution statistics are derived directly from physical dataset labels (`ai/vision/datasets/jewellery_v2`), training log artifacts (`results.csv`), and held-out test evaluations on 763 unseen images.

---

## 2. Notebook Deliverables & Key File Paths

| Item | Path / Location |
| :--- | :--- |
| **Jupyter Notebook (Pre-Rendered & Executed)** | [`ai/vision/notebooks/YOLO_V2_Training_Analysis.ipynb`](file:///c:/Users/usern/Desktop/JewelMind/ai/vision/notebooks/YOLO_V2_Training_Analysis.ipynb) |
| **Output Figures & Visualizations** | [`ai/vision/notebooks/outputs/yolo_v2/`](file:///c:/Users/usern/Desktop/JewelMind/ai/vision/notebooks/outputs/yolo_v2) |
| **Final Trained Model Checkpoint** | [`runs/segment/runs/segment/runs/jewellery/yolo11m-seg-jewelmind-v2-continued/weights/best.pt`](file:///c:/Users/usern/Desktop/JewelMind/runs/segment/runs/segment/runs/jewellery/yolo11m-seg-jewelmind-v2-continued/weights/best.pt) |
| **Dataset Configuration** | [`ai/vision/training/configs/jewellery_v2.yaml`](file:///c:/Users/usern/Desktop/JewelMind/ai/vision/training/configs/jewellery_v2.yaml) |
| **Dataset Directory** | [`ai/vision/datasets/jewellery_v2`](file:///c:/Users/usern/Desktop/JewelMind/ai/vision/datasets/jewellery_v2) |
| **Initial Training Run (Stage 1)** | `runs/segment/runs/segment/runs/jewellery/yolo11m-seg-jewelmind-v2/` |
| **Continuation Training Run (Stage 2)** | `runs/segment/runs/segment/runs/jewellery/yolo11m-seg-jewelmind-v2-continued/` |

---

## 3. Dataset Audit & Class Distribution

The dataset was parsed programmatically from the YOLO polygon label files across all splits.

### Split Overview
* **Train Split:** 5,429 images | 8,542 instances (1.57 instances/image)
* **Validation Split:** 1,596 images | 2,524 instances (1.58 instances/image)
* **Held-Out Test Split:** 763 images | 1,221 labeled instances in files (1.60 instances/image)
* **Total Dataset Volume:** **7,788 images | 12,287 labeled instances**

### Verified Per-Class Breakdown (8 Categories)
1. **Ring:** 3,589 instances (29.21%)
2. **Earring:** 2,822 instances (22.97%)
3. **Bracelet:** 2,707 instances (22.03%)
4. **Necklace:** 2,366 instances (19.26%)
5. **Pendant:** 235 instances (1.91%)
6. **Brooch:** 209 instances (1.70%)
7. **Other Jewellery:** 205 instances (1.67%)
8. **Bangle:** 154 instances (1.25%)

---

## 4. Model Architecture & Actual Training Configuration

* **Model Architecture:** Ultralytics YOLO11m-seg (Medium Instance Segmentation)
* **Parameter Count:** 22,365,384 parameters (~22.37 Million)
* **Hardware:** NVIDIA GeForce RTX 4060 Laptop GPU (8GB VRAM), PyTorch CUDA acceleration

### Documented Two-Stage Training Protocol:
- **Stage 1 (Initial Domain Training — 50 Epochs):**
  - Model: `YOLO11m-seg` initialized from `yolo11m-seg.pt` (COCO Pretrained)
  - Epochs: `50`
  - Batch size: `4`
  - Image resolution: `640x640`
  - Initial learning rate (`lr0`): `0.001`
  - Hardware / Acceleration: `NVIDIA RTX 4060 Laptop GPU (CUDA)`
  - Automatic Mixed Precision (`amp`): `True`

- **Stage 2 (Sequential Fine-Tuning — 50 Epochs):**
  - Checkpoint: Initialized from Stage 1 `best.pt`
  - Epochs: `50`
  - Batch size: `4`
  - Image resolution: `640x640`
  - Initial learning rate (`lr0`): `0.0005`
  - Hardware / Acceleration: `NVIDIA RTX 4060 Laptop GPU (CUDA)`
  - Automatic Mixed Precision (`amp`): `True`
  - **Academic Precision Note:** This stage was sequential fine-tuning initialized from the Stage 1 best checkpoint, **NOT** an uninterrupted optimizer-state resume.

---

## 5. Verified Held-Out Test Set Evaluation

The evaluation was executed on the **763 held-out test images** (with **1,220 evaluated instances** as reported by the actual Ultralytics test evaluation, completely unseen during training):

### Overall Test Metrics
| Metric | Box Detection | Mask Segmentation (Headline) |
| :--- | :---: | :---: |
| **Precision** | **77.0%** | **78.1%** |
| **Recall** | **70.9%** | **64.9%** |
| **mAP@50** | **70.3%** | **66.1%** |
| **mAP@50-95** | **60.4%** | **48.7%** |

### Per-Class Test Performance (Mask Segmentation)
| Category | Test Images | Evaluated Instances | Mask Precision | Mask Recall | Mask mAP@50 | Mask mAP@50-95 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **bangle** | 18 | 18 | 77.1% | 74.9% | **84.2%** | **74.2%** |
| **brooch** | 16 | 16 | 70.3% | 81.2% | **83.6%** | **79.1%** |
| **earring** | 238 | 283 | **93.8%** | 70.0% | **72.2%** | 49.2% |
| **pendant** | 16 | 17 | 61.0% | 76.5% | **67.9%** | 53.5% |
| **ring** | 316 | 355 | **93.9%** | 63.9% | **65.6%** | 44.4% |
| **necklace** | 214 | 221 | **93.1%** | 64.7% | **64.9%** | 36.6% |
| **bracelet** | 219 | 276 | 83.4% | 52.5% | **53.3%** | 34.4% |
| **other_jewellery** | 18 | 34 | 52.0% | 35.3% | **37.3%** | 18.4% |

---

## 6. Generated Visualization Artifacts

All charts were programmatically rendered with Matplotlib and saved to `ai/vision/notebooks/outputs/yolo_v2/`:

1. `dataset_class_distribution.png`: Bar chart of dataset instance counts across 8 classes.
2. `training_loss_curves.png`: 4-panel progression of Box Loss, Seg Loss, Cls Loss, and DFL Loss across Stages 1 & 2.
3. `training_map_curves.png`: 4-panel convergence of Precision, Recall, Box mAP, and Mask mAP.
4. `test_metrics_summary.png`: Comparative bar chart of Box vs Mask metrics on the held-out test split.
5. `test_per_class_map50.png`: Horizontal ranking of Mask mAP@50 by jewellery category.
6. `prediction_grid.png`: 3x3 visual prediction grid on held-out test images with instance masks.
7. `category_examples.png`: 8-panel gallery showcasing representative predictions across all 8 classes.
8. `challenging_examples.png`: Multi-panel failure analysis highlighting difficult cases (thin chains, low contrast, overlapping pieces).

---

## 7. Notebook Execution & Verification Status

- **Execution Environment:** Python 3.10 / `conda:tgpu` (PyTorch 2.6.0+cu124, Ultralytics 8.3.81, CUDA enabled)
- **Cell Verification:**
  - Total Cells: 42 (25 Markdown, 17 Code)
  - Code Cells with Rendered Outputs: 17 / 17 (100%)
  - Execution Errors: 0
- **Path Portability:** Employs dynamic root detection (`find_project_root()`), ensuring seamless execution whether launched from repository root or `ai/vision/notebooks/`.

---

## 8. Confirmations & Academic Integrity Statement

1. **No Training Was Performed:** Model weights were solely loaded from the pre-existing `best.pt` file.
2. **Real Artifact Sourcing:** All metrics, loss values, confusion matrices, and precision-recall curves originate directly from physical training runs and dataset annotations.
3. **No Synthetic / Fabricated Data:** Metric tables, split counts, and test results represent true ground-truth and inference outputs.
4. **Git State:** No git commits or pushes were made.
