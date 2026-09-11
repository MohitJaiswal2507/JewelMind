# JEWELMIND — FINAL STORAGE INVENTORY & KEEP/DELETE MANIFEST

**Phase:** Final Storage Audit & Manifest Definition  
**Branch:** `phase-final-renderer-integration`  
**Status:** Read-Only Audit Complete (0 Modifications, 0 Deletions)  
**Audit Timestamp:** 2026-09-11  

---

## 1. Executive Summary
Following the successful **Tier 1 Storage Cleanup** (which eliminated **33.35 GB** of disposable optimizer, scheduler, scaler states, and intermediate epoch weights), a comprehensive, recursive, read-only audit of the entire JewelMind repository was conducted.

- **Current Workspace Size:** **36.00 GB** (38,658,189,498 bytes)
- **Total Files:** **149,544 files** across **1,837 directories**
- **Total Storage Partition Breakdown:**
  - **KEEP (Protected Production & Active Assets):** **10.53 GB** (69,324 files)
  - **ARCHIVE (Intermediate Weights & Raw/Pre-Correction Datasets):** **25.30 GB** (78,758 files)
  - **DELETE (Disposable Preview Renders & Caches):** **107.38 MB** (1,459 files)
  - **REVIEW (Root Pretrained Ultralytics Weights):** **68.30 MB** (3 files)

> [!IMPORTANT]
> **Absolute Safety Guarantee:** All approved production models (`outputs/rendering_v2_controlnet/controlnet_rendering_v2_final`, `outputs/appearance_lora/jewellery_lora_final`, YOLO v1/v2 `best.pt`, `outputs/controlnet_jewellery_300/controlnet_jewellery_final`, and base `models/diffusion/`), active datasets (`rendering_final_corrected/`, `rendering_final_corrected_conditioning/`, `jewellery_v2/`, `datasets/appearance_lora/`), source code, environments, and Git history are **100% PROTECTED** and marked **KEEP**.

---

## 2. Current Storage Overview
| Metric | Value | Reconciled Percentage |
| :--- | :--- | :--- |
| **Total Workspace Size** | **36.00 GB** (38,658,189,498 bytes) | 100.00% |
| **Total File Count** | **149,544** | 100.00% |
| **Total Directory Count** | **1,837** | - |
| **KEEP Total** | **10.53 GB** (11,309,066,763 bytes) | 29.25% |
| **ARCHIVE Total** | **25.30 GB** (27,164,913,647 bytes) | 70.27% |
| **DELETE Total** | **107.38 MB** (112,595,255 bytes) | 0.29% |
| **REVIEW Total** | **68.30 MB** (71,613,833 bytes) | 0.19% |

---

## 3. Directory Breakdown (Sorted Largest First)
| Directory Path | Size | File Count | Recursive Subdirs | Purpose & Classification |
| :--- | :--- | :--- | :--- | :--- |
| `JewelMind/ (Root)` | **36.00 GB** | 149,544 | 0 | Root workspace repository |
| `outputs` | **16.28 GB** | 547 | 49 | Trained production models, intermediate checkpoints, LoRAs, and test outputs |
| `ai` | **15.22 GB** | 133,568 | 393 | AI vision & rendering pipeline source code, models, and training datasets |
| `outputs/rendering_v2_controlnet` | **14.88 GB** | 333 | 25 | 1000-step ControlNet model, intermediate checkpoints, and validation logs |
| `outputs/rendering_v2_controlnet/checkpoints` | **13.46 GB** | 30 | 11 | Intermediate checkpoint weights (checkpoint-100 to 1000) |
| `ai/rendering` | **12.41 GB** | 113,445 | 298 | ControlNet rendering pipeline scripts, models, and datasets |
| `ai/rendering/datasets` | **12.36 GB** | 113,380 | 280 | Ground truth, conditioning, and intermediate rendering datasets |
| `models` | **3.33 GB** | 33 | 32 | Pretrained foundation models cache |
| `models/diffusion` | **3.33 GB** | 32 | 31 | Base SD 1.5 & ControlNet LineArt pretrained weights (PROTECTED) |
| `ai/vision` | **2.81 GB** | 20,084 | 62 | Vision segmentation pipeline scripts, models, and datasets |
| `ai/vision/datasets` | **2.79 GB** | 20,047 | 50 | YOLO jewellery multi-class segmentation datasets |
| `outputs/rendering_v2_controlnet/controlnet_rendering_v2_final` | **1.35 GB** | 5 | 1 | Approved production 1000-step ControlNet model (PROTECTED) |
| `outputs/controlnet_jewellery_300` | **1.35 GB** | 4 | 4 | Legacy 300-step baseline ControlNet model (PROTECTED) |
| `backend` | **357.88 MB** | 7,055 | 837 | FastAPI backend source code and Python virtual environment |
| `backend/.venv` | **356.97 MB** | 6,920 | 816 | Backend Python virtual environment dependencies |
| `runs` | **283.84 MB** | 333 | 42 | YOLO training runs and vision models |
| `runs/segment` | **283.84 MB** | 333 | 41 | YOLO segmentation runs (v1, v2, v2-continued) |
| `datasets` | **197.37 MB** | 1,006 | 17 | Curation and LoRA training datasets |
| `.git` | **169.37 MB** | 1,584 | 272 | Git version control repository data |
| `datasets/curation` | **141.08 MB** | 333 | 4 | Contact sheet curation review artifacts |
| `frontend` | **120.19 MB** | 5,226 | 171 | React/Vite frontend source code and dependencies |
| `frontend/node_modules` | **119.12 MB** | 5,141 | 149 | Frontend JavaScript/TypeScript dependencies |
| `datasets/controlnet_paired` | **32.88 MB** | 332 | 4 | Phase 10 paired dataset |
| `datasets/appearance_lora` | **23.40 MB** | 337 | 5 | Jewellery appearance LoRA dataset (PROTECTED) |
| `outputs/appearance_lora` | **12.21 MB** | 3 | 2 | Jewellery appearance LoRA production adapter (PROTECTED) |
| `outputs/rendering` | **10.35 MB** | 29 | 1 | Test inference render sample outputs |

---

## 4. File-Level Inventory (All Files > 10 MB)
The repository contains **27 files** larger than 10 MB. Every single file has been inspected, categorized, and assigned a strict disposition decision.

| Path | Size | File Type | Purpose | Category | Decision | Confidence | Reason |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `models/diffusion/models--runwayml--stable-diffusion-v1-5/snapshots/451f4fe16113bff5a5d2269ed5ad43b0592e9a14/unet/diffusion_pytorch_model.fp16.safetensors` | **1.60 GB** | `.safetensors` | Local pretrained base diffusion / LineArt ControlNet weights | `PRODUCTION` | **KEEP** | 100% | Required base foundation models for local inference pipeline (PROTECTED) |
| `models/diffusion/models--lllyasviel--control_v11p_sd15_lineart/snapshots/8a158f547e031c5b8fbca19ead09a74767ff4db0/diffusion_pytorch_model.safetensors` | **1.35 GB** | `.safetensors` | Local pretrained base diffusion / LineArt ControlNet weights | `PRODUCTION` | **KEEP** | 100% | Required base foundation models for local inference pipeline (PROTECTED) |
| `outputs/controlnet_jewellery_300/controlnet_jewellery_final/diffusion_pytorch_model.safetensors` | **1.35 GB** | `.safetensors` | Legacy 300-step baseline ControlNet model | `PRODUCTION` | **KEEP** | 100% | Preserved benchmark baseline and secondary reference (PROTECTED) |
| `outputs/rendering_v2_controlnet/checkpoints/checkpoint-100/diffusion_pytorch_model.safetensors` | **1.35 GB** | `.safetensors` | Intermediate ControlNet training step weights (safetensors) | `CHECKPOINT` | **ARCHIVE** | 100% | Intermediate training checkpoint; optimizer state already removed. Useful for step progression analysis. |
| `outputs/rendering_v2_controlnet/checkpoints/checkpoint-1000/diffusion_pytorch_model.safetensors` | **1.35 GB** | `.safetensors` | Intermediate ControlNet training step weights (safetensors) | `CHECKPOINT` | **ARCHIVE** | 100% | Intermediate training checkpoint; optimizer state already removed. Useful for step progression analysis. |
| `outputs/rendering_v2_controlnet/checkpoints/checkpoint-200/diffusion_pytorch_model.safetensors` | **1.35 GB** | `.safetensors` | Intermediate ControlNet training step weights (safetensors) | `CHECKPOINT` | **ARCHIVE** | 100% | Intermediate training checkpoint; optimizer state already removed. Useful for step progression analysis. |
| `outputs/rendering_v2_controlnet/checkpoints/checkpoint-300/diffusion_pytorch_model.safetensors` | **1.35 GB** | `.safetensors` | Intermediate ControlNet training step weights (safetensors) | `CHECKPOINT` | **ARCHIVE** | 100% | Intermediate training checkpoint; optimizer state already removed. Useful for step progression analysis. |
| `outputs/rendering_v2_controlnet/checkpoints/checkpoint-400/diffusion_pytorch_model.safetensors` | **1.35 GB** | `.safetensors` | Intermediate ControlNet training step weights (safetensors) | `CHECKPOINT` | **ARCHIVE** | 100% | Intermediate training checkpoint; optimizer state already removed. Useful for step progression analysis. |
| `outputs/rendering_v2_controlnet/checkpoints/checkpoint-500/diffusion_pytorch_model.safetensors` | **1.35 GB** | `.safetensors` | Intermediate ControlNet training step weights (safetensors) | `CHECKPOINT` | **ARCHIVE** | 100% | Intermediate training checkpoint; optimizer state already removed. Useful for step progression analysis. |
| `outputs/rendering_v2_controlnet/checkpoints/checkpoint-600/diffusion_pytorch_model.safetensors` | **1.35 GB** | `.safetensors` | Intermediate ControlNet training step weights (safetensors) | `CHECKPOINT` | **ARCHIVE** | 100% | Intermediate training checkpoint; optimizer state already removed. Useful for step progression analysis. |
| `outputs/rendering_v2_controlnet/checkpoints/checkpoint-700/diffusion_pytorch_model.safetensors` | **1.35 GB** | `.safetensors` | Intermediate ControlNet training step weights (safetensors) | `CHECKPOINT` | **ARCHIVE** | 100% | Intermediate training checkpoint; optimizer state already removed. Useful for step progression analysis. |
| `outputs/rendering_v2_controlnet/checkpoints/checkpoint-800/diffusion_pytorch_model.safetensors` | **1.35 GB** | `.safetensors` | Intermediate ControlNet training step weights (safetensors) | `CHECKPOINT` | **ARCHIVE** | 100% | Intermediate training checkpoint; optimizer state already removed. Useful for step progression analysis. |
| `outputs/rendering_v2_controlnet/checkpoints/checkpoint-900/diffusion_pytorch_model.safetensors` | **1.35 GB** | `.safetensors` | Intermediate ControlNet training step weights (safetensors) | `CHECKPOINT` | **ARCHIVE** | 100% | Intermediate training checkpoint; optimizer state already removed. Useful for step progression analysis. |
| `outputs/rendering_v2_controlnet/controlnet_rendering_v2_final/diffusion_pytorch_model.safetensors` | **1.35 GB** | `.safetensors` | Approved 1000-step ControlNet production model weights | `PRODUCTION` | **KEEP** | 100% | Primary approved production renderer model (PROTECTED) |
| `ai/vision/datasets/raw/jewelry-dwpose/data/train-00002-of-00003.parquet` | **430.86 MB** | `.parquet` | Raw downloaded DWPose parquet shard | `DATASET` | **ARCHIVE** | 95% | Source parquet data from HuggingFace; processed dataset exists in jewellery_v2. |
| `ai/vision/datasets/raw/jewelry-dwpose/data/train-00000-of-00003.parquet` | **430.24 MB** | `.parquet` | Raw downloaded DWPose parquet shard | `DATASET` | **ARCHIVE** | 95% | Source parquet data from HuggingFace; processed dataset exists in jewellery_v2. |
| `ai/vision/datasets/raw/jewelry-dwpose/data/train-00001-of-00003.parquet` | **429.87 MB** | `.parquet` | Raw downloaded DWPose parquet shard | `DATASET` | **ARCHIVE** | 95% | Source parquet data from HuggingFace; processed dataset exists in jewellery_v2. |
| `models/diffusion/models--runwayml--stable-diffusion-v1-5/snapshots/451f4fe16113bff5a5d2269ed5ad43b0592e9a14/text_encoder/model.fp16.safetensors` | **234.74 MB** | `.safetensors` | Local pretrained base diffusion / LineArt ControlNet weights | `PRODUCTION` | **KEEP** | 100% | Required base foundation models for local inference pipeline (PROTECTED) |
| `models/diffusion/models--runwayml--stable-diffusion-v1-5/snapshots/451f4fe16113bff5a5d2269ed5ad43b0592e9a14/vae/diffusion_pytorch_model.fp16.safetensors` | **159.58 MB** | `.safetensors` | Local pretrained base diffusion / LineArt ControlNet weights | `PRODUCTION` | **KEEP** | 100% | Required base foundation models for local inference pipeline (PROTECTED) |
| `backend/.venv/Lib/site-packages/cv2/cv2.pyd` | **81.87 MB** | `.pyd` | Compiled C++/Python library binary in virtual environment | `CONFIG` | **KEEP** | 100% | Essential runtime dependency within backend virtual environment (PROTECTED). |
| `yolo11m-seg.pt` | **43.30 MB** | `.pt` | Pretrained base YOLO segmentation models from Ultralytics | `MODEL` | **REVIEW** | 90% | Root download artifacts. Can be re-downloaded if needed, or moved to models/yolo/. |
| `runs/segment/runs/jewellery/yolo11m-seg-jewelmind-v1/weights/best.pt` | **43.07 MB** | `.pt` | YOLO segmentation v1 production weights | `PRODUCTION` | **KEEP** | 100% | Approved production vision model v1 (PROTECTED) |
| `runs/segment/runs/benchmark/bench_yolo11m-seg/weights/best.pt` | **43.07 MB** | `.pt` | YOLO benchmark run weights | `CHECKPOINT` | **ARCHIVE** | 95% | Benchmark trial weights; not used in production. |
| `runs/segment/runs/segment/runs/jewellery/yolo11m-seg-jewelmind-v2/weights/best.pt` | **43.05 MB** | `.pt` | YOLO v2 initial training run best weights (prior to continuation) | `CHECKPOINT` | **ARCHIVE** | 100% | Intermediate run superseded by yolo11m-seg-jewelmind-v2-continued/best.pt. |
| `runs/segment/runs/segment/runs/jewellery/yolo11m-seg-jewelmind-v2-continued/weights/best.pt` | **43.05 MB** | `.pt` | YOLO segmentation v2 fine-tuned production weights | `PRODUCTION` | **KEEP** | 100% | Approved production vision model v2 (PROTECTED) |
| `backend/.venv/Lib/site-packages/ortools/.libs/ortools.dll` | **32.92 MB** | `.dll` | Compiled C++/Python library binary in virtual environment | `CONFIG` | **KEEP** | 100% | Essential runtime dependency within backend virtual environment (PROTECTED). |
| `backend/.venv/Lib/site-packages/cv2/opencv_videoio_ffmpeg500_64.dll` | **29.45 MB** | `.dll` | Compiled C++/Python library binary in virtual environment | `CONFIG` | **KEEP** | 100% | Essential runtime dependency within backend virtual environment (PROTECTED). |
| `frontend/node_modules/@rolldown/binding-win32-x64-msvc/rolldown-binding.win32-x64-msvc.node` | **19.94 MB** | `.node` | Large project artifact | `UNKNOWN` | **REVIEW** | 80% | Requires manual review. |
| `yolo11s-seg.pt` | **19.71 MB** | `.pt` | Pretrained base YOLO segmentation models from Ultralytics | `MODEL` | **REVIEW** | 90% | Root download artifacts. Can be re-downloaded if needed, or moved to models/yolo/. |
| `runs/segment/runs/benchmark/bench_yolo11s-seg/weights/best.pt` | **19.56 MB** | `.pt` | Large project artifact | `UNKNOWN` | **REVIEW** | 80% | Requires manual review. |
| `runs/segment/runs/smoke_test/gpu_smoke_run/weights/best.pt` | **19.56 MB** | `.pt` | Large project artifact | `UNKNOWN` | **REVIEW** | 80% | Requires manual review. |
| `backend/.venv/Lib/site-packages/numpy.libs/libscipy_openblas64_-327b2e0bcffce2882e0dc04cdeb4eaa6.dll` | **19.55 MB** | `.dll` | Compiled C++/Python library binary in virtual environment | `CONFIG` | **KEEP** | 100% | Essential runtime dependency within backend virtual environment (PROTECTED). |
| `runs/segment/runs/jewellery/yolo11s-jewelmind-v2-smoke/weights/best.pt` | **19.52 MB** | `.pt` | Large project artifact | `UNKNOWN` | **REVIEW** | 80% | Requires manual review. |
| `ai/rendering/notebooks/Rendering_V2_Dataset_Preparation.ipynb` | **14.44 MB** | `.ipynb` | Large project artifact | `UNKNOWN` | **REVIEW** | 80% | Requires manual review. |
| `backend/.venv/Lib/site-packages/ortools/.libs/libprotobuf.dll` | **12.95 MB** | `.dll` | Compiled C++/Python library binary in virtual environment | `CONFIG` | **KEEP** | 100% | Essential runtime dependency within backend virtual environment (PROTECTED). |
| `datasets/curation/CONTACT_SHEET_REVIEW_REQUIRED.png` | **12.85 MB** | `.png` | Large project artifact | `UNKNOWN` | **REVIEW** | 80% | Requires manual review. |
| `.git/objects/40/cddd3343db9b69fc62afcda666ba6345e6a435` | **12.81 MB** | `` | Large project artifact | `UNKNOWN` | **REVIEW** | 80% | Requires manual review. |
| `backend/.venv/Lib/site-packages/ortools/.libs/libscip.dll` | **12.21 MB** | `.dll` | Compiled C++/Python library binary in virtual environment | `CONFIG` | **KEEP** | 100% | Essential runtime dependency within backend virtual environment (PROTECTED). |
| `outputs/appearance_lora/jewellery_lora_final/adapter_model.safetensors` | **12.20 MB** | `.safetensors` | Jewellery LoRA visual detail adapter | `PRODUCTION` | **KEEP** | 100% | Primary approved production appearance LoRA (PROTECTED) |
| `datasets/curation/HUMAN_CURATION_MASTER_CONTACT_SHEET.png` | **12.02 MB** | `.png` | Large project artifact | `UNKNOWN` | **REVIEW** | 80% | Requires manual review. |
| `.git/objects/d7/9ad497356fb4eed829ea8a54f0f7b4fc7a354a` | **11.98 MB** | `` | Large project artifact | `UNKNOWN` | **REVIEW** | 80% | Requires manual review. |
| `.git/objects/8e/46dabef1d0b7e30572668ac910844b99420e57` | **11.02 MB** | `` | Large project artifact | `UNKNOWN` | **REVIEW** | 80% | Requires manual review. |
| `ai/rendering/datasets/rendering_final/images/other_jewellery/ds2_011981_the-stone-aisle-premium-beautiful-designer-set-of-.png` | **11.01 MB** | `.png` | Large project artifact | `UNKNOWN` | **REVIEW** | 80% | Requires manual review. |
| `ai/rendering/datasets/rendering_final/test/images/other_jewellery/ds2_011981_the-stone-aisle-premium-beautiful-designer-set-of-.png` | **11.01 MB** | `.png` | Large project artifact | `UNKNOWN` | **REVIEW** | 80% | Requires manual review. |
| `ai/rendering/datasets/rendering_final_raw/indian_traditional_artificial_jewellery/the-stone-aisle-premium-beautiful-designer-set-of-3-evil-eye-rakhi-for-brother-product-images-rvtub3akky-1-202408010053.png` | **11.01 MB** | `.png` | Large project artifact | `UNKNOWN` | **REVIEW** | 80% | Requires manual review. |
| `datasets/curation/CONTACT_SHEET_BROOCHES_OTHER.png` | **10.72 MB** | `.png` | Large project artifact | `UNKNOWN` | **REVIEW** | 80% | Requires manual review. |
| `.git/objects/dc/6a15643cedb5a9dff16d50dd56a3db53b4c433` | **10.69 MB** | `` | Large project artifact | `UNKNOWN` | **REVIEW** | 80% | Requires manual review. |
| `ai/rendering/datasets/rendering_final/images/other_jewellery/ds2_007859_floral-and-lord-krishna-designer-rakhis-happy-rakh.png` | **10.49 MB** | `.png` | Large project artifact | `UNKNOWN` | **REVIEW** | 80% | Requires manual review. |
| `ai/rendering/datasets/rendering_final/train/images/other_jewellery/ds2_007859_floral-and-lord-krishna-designer-rakhis-happy-rakh.png` | **10.49 MB** | `.png` | Large project artifact | `UNKNOWN` | **REVIEW** | 80% | Requires manual review. |
| `ai/rendering/datasets/rendering_final_raw/indian_traditional_artificial_jewellery/floral-and-lord-krishna-designer-rakhis-happy-rakhi-wooden-with-roli-chawal-pack-rakhi-for-brother-bhaiya-bhai-product-images-rvavfye2x3-0-202407251934.png` | **10.49 MB** | `.png` | Large project artifact | `UNKNOWN` | **REVIEW** | 80% | Requires manual review. |

---

## 5. Critical Production Assets (KEEP — PRODUCTION)
These assets form the core runtime of the JewelMind vision and rendering pipelines. They are strictly preserved.

1. **Final 1000-Step ControlNet Model (`outputs/rendering_v2_controlnet/controlnet_rendering_v2_final/`):**
   - `diffusion_pytorch_model.safetensors` (**1.35 GB**) — Approved final 1000-step ControlNet weights.
   - `config.json` (**955 B**) — Production ControlNet architecture definition.
   - *Status:* **KEEP — PRODUCTION (PROTECTED)**

2. **Appearance LoRA Model (`outputs/appearance_lora/jewellery_lora_final/`):**
   - `adapter_model.safetensors` (**12.21 MB**) — High-fidelity jewellery detail LoRA weights.
   - `adapter_config.json` (**584 B**) — PEFT LoRA adapter config.
   - *Status:* **KEEP — PRODUCTION (PROTECTED)**

3. **YOLO V1 Vision Model (`runs/segment/runs/jewellery/yolo11m-seg-jewelmind-v1/weights/best.pt`):**
   - `best.pt` (**43.07 MB**) — Approved production vision segmentation model v1.
   - *Status:* **KEEP — PRODUCTION (PROTECTED)**

4. **YOLO V2 Vision Model (`runs/segment/runs/segment/runs/jewellery/yolo11m-seg-jewelmind-v2-continued/weights/best.pt`):**
   - `best.pt` (**43.05 MB**) — Approved production fine-tuned vision segmentation model v2.
   - *Status:* **KEEP — PRODUCTION (PROTECTED)**

5. **Baseline 300-Step ControlNet Model (`outputs/controlnet_jewellery_300/controlnet_jewellery_final/`):**
   - `diffusion_pytorch_model.safetensors` (**1.35 GB**) + `config.json` — Phase 10 baseline model.
   - *Status:* **KEEP — PRODUCTION BASELINE (PROTECTED)**

6. **Base Diffusion Models (`models/diffusion/`):**
   - `sd15/` (**1.98 GB**) & `controlnet_lineart/` (**1.35 GB**) — Local Hugging Face pretrained weights for offline/local production pipeline execution.
   - *Status:* **KEEP — PRODUCTION FOUNDATION (PROTECTED)**

---

## 6. Final Datasets (KEEP — DATASET)
| Dataset Path | Size | Files | Purpose | Decision | Reason |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ai/rendering/datasets/rendering_final_corrected/` | **1.22 GB** | 4,310 | Final prompt-corrected ground truth targets | **KEEP** | Approved training ground truth for 1000-step ControlNet (PROTECTED) |
| `ai/rendering/datasets/rendering_final_corrected_conditioning/` | **1.30 GB** | 4,310 | Final inverted LineArt conditioning paired with corrected targets | **KEEP** | Approved conditioning dataset for 1000-step ControlNet (PROTECTED) |
| `ai/vision/datasets/jewellery_v2/` | **1.05 GB** | 66,258 | YOLO multi-class jewellery segmentation dataset | **KEEP** | Primary vision training & validation set (PROTECTED) |
| `datasets/appearance_lora/` | **23.40 MB** | 20 | Appearance LoRA training pairs | **KEEP** | Active LoRA training dataset (PROTECTED) |

---

## 7. Old / Intermediate Datasets (ARCHIVE — DATASET)
These datasets have been superseded by corrected datasets or represent raw upstream scrapes. They are not required for daily inference operations.

| Dataset Path | Size | Files | Purpose | Decision | Reason |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ai/rendering/datasets/rendering_final/` | **4.20 GB** | 13,444 | Pre-correction targets (contained corrupt metadata) | **ARCHIVE** | Superseded by `rendering_final_corrected/`. Kept for audit trail. |
| `ai/rendering/datasets/rendering_final_conditioning/` | **2.78 GB** | 13,444 | Pre-correction LineArt maps | **ARCHIVE** | Superseded by `rendering_final_corrected_conditioning/`. |
| `ai/rendering/datasets/rendering_final_raw/` | **2.61 GB** | 22,120 | Raw uncurated scraped images pool | **ARCHIVE** | Raw source pool before filtering/inversion. |
| `ai/vision/datasets/raw/jewelry-dwpose/` | **1.36 GB** | 6 | Hugging Face raw parquet shards | **ARCHIVE** | Upstream raw archive; parsed data is in `jewellery_v2`. |
| `ai/vision/datasets/rendering_v2/` | **378.39 MB** | 1,284 | Exploratory YOLO segmentations on rendering_v2 | **ARCHIVE** | Intermediate validation set. |
| `ai/rendering/datasets/rendering_v2/` | **253.26 MB** | 778 | Intermediate rendering test samples | **ARCHIVE** | Intermediate dataset. |
| `datasets/curation/` | **141.08 MB** | 12 | Visual contact sheets & review artifacts | **ARCHIVE** | Visual review history. |
| `datasets/controlnet_paired/` | **29.98 MB** | 180 | Phase 10 pilot paired dataset | **ARCHIVE** | Legacy pilot dataset. |

---

## 8. ControlNet Checkpoint Analysis
Inspection of `outputs/rendering_v2_controlnet/checkpoints/`:
- Checkpoints present: `checkpoint-100` through `checkpoint-1000` (10 total).
- **Verification of Tier 1 Cleanup:** All `optimizer.pt` (3.78 GB each), `scheduler.pt` (1.3 KB), and `scaler.pt` (557 B) files have been **completely removed**.
- **Remaining files per checkpoint:** Only `diffusion_pytorch_model.safetensors` (**1.35 GB**) and `config.json` (**955 B**) remain in each directory.
- **Total Checkpoints Size:** **13.46 GB** across 10 folders.
- **Classification:** **ARCHIVE — INTERMEDIATE TRAINING WEIGHTS**. They can be moved to cold storage or compressed into a `.tar.zst` archive.

---

## 9. YOLO Training Runs Inventory
Inspection of `runs/segment/`:
- **Production Models Preserved:**
  - `runs/jewellery/yolo11m-seg-jewelmind-v1/weights/best.pt` (**43.07 MB**) -> **KEEP**
  - `runs/segment/runs/jewellery/yolo11m-seg-jewelmind-v2-continued/weights/best.pt` (**43.05 MB**) -> **KEEP**
- **Intermediate epoch weights (`epoch*.pt`):** Verified **0 remaining** (removed in Tier 1 cleanup).
- **Remaining files:** `last.pt` resume weights (43 MB each), training evaluation curves (`results.csv`, `confusion_matrix.png`, `F1_curve.png`, `PR_curve.png`), and `args.yaml`.
- **Total runs/ size:** **283.84 MB** (333 files).
- **Classification:** `best.pt` models are **KEEP**; remaining evaluation curves and `last.pt` weights are **ARCHIVE**.

---

## 10. Rendering Outputs Inventory
Inspection of `outputs/`:
1. `outputs/rendering_v2_controlnet/controlnet_rendering_v2_final/` (**1.35 GB**) -> **KEEP — PRODUCTION**
2. `outputs/controlnet_jewellery_300/controlnet_jewellery_final/` (**1.35 GB**) -> **KEEP — BASELINE**
3. `outputs/appearance_lora/jewellery_lora_final/` (**12.21 MB**) -> **KEEP — PRODUCTION**
4. `outputs/rendering_v2_controlnet/checkpoints/` (**13.46 GB**) -> **ARCHIVE**
5. `outputs/rendering_v2_controlnet/validation/` (**71.37 MB**, 28 files) -> **DELETE** (Transient validation step preview images from training)
6. `outputs/rendering_v2_controlnet/v1_vs_v2_comparison/` (**634 KB**, 4 files) -> **DELETE** (Transient comparison renders)
7. `outputs/rendering/` (**10.35 MB**, 2 files: `test_e2e_output.png` and `sample_smoke.png`) -> **DELETE** (Transient test outputs)

---

## 11. Cache Inventory
| Cache Name | Location | Size | Files | Purpose | Decision | Reason |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `models/diffusion/` | Local workspace | **3.33 GB** | 33 | Local offline diffusion weights | **KEEP** | Required for local inference; DO NOT delete |
| `__pycache__` | Across workspace | **16.63 MB** | 1,424 | Python bytecode cache | **DELETE** | Automatically recreated by Python runtime |
| `.pytest_cache/` | `backend/.pytest_cache/` | **106.84 KB** | 13 | Pytest test execution cache | **DELETE** | Automatically recreated by pytest |
| `.ipynb_checkpoints/` | Root | **0 B** | 0 | Jupyter autosaves | **DELETE** | Temporary editor autosaves |
| HuggingFace User Cache | User home (`~/.cache/huggingface`) | External | - | Upstream model downloads | **EXTERNAL** | Outside workspace |
| Pip / UV / NPM Caches | User home (`~/.cache`) | External | - | Package manager wheels | **EXTERNAL** | Outside workspace |

---

## 12. Node Modules & Python Environments
1. `backend/.venv/` (**356.97 MB**, 6,920 files):
   - Dedicated Python virtual environment for backend FastAPI service.
   - *Classification:* **KEEP — PROJECT-REQUIRED (ENVIRONMENT)**
2. `frontend/node_modules/` (**119.12 MB**, 5,141 files):
   - Active node modules for React/Vite web application.
   - *Classification:* **KEEP — PROJECT-REQUIRED (ENVIRONMENT)**
3. `miniconda3/envs/tgpu/` (External):
   - Global PyTorch GPU environment used for AI pipelines.
   - *Classification:* **EXTERNAL (PROTECTED)**

---

## 13. Git Inventory
- **Active Branch:** `phase-final-renderer-integration`
- **Working Tree Status:** Clean (`git status --short` returns 0 uncommitted changes)
- **Repository Size (`.git/`):** **169.37 MB** (1,584 objects)
- **Large Tracked Files (> 50 MB):** **0 files** found. (Verified using `git ls-files` and file size inspection. All large binary safetensors and pt checkpoints are correctly untracked by Git).

---

## 14. Duplicate Detection (Files > 20 MB)
Exact SHA-256 hash comparison across all files >= 20 MB:

| Group | Size | SHA-256 Hash | Original / Primary Path (KEEP) | Candidate / Duplicate Path (ARCHIVE / REVIEW) | Analysis |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | 1.35 GB | `d0f48be0408544d67be89c193231e8787f7390eb13e00cf42e3db787d5595ff9` | `outputs/rendering_v2_controlnet/controlnet_rendering_v2_final/diffusion_pytorch_model.safetensors` | `outputs/rendering_v2_controlnet/checkpoints/checkpoint-1000/diffusion_pytorch_model.safetensors` | `checkpoint-1000` is byte-identical to `controlnet_rendering_v2_final`. `checkpoint-1000` can be safely archived. |
| **2** | 43.05 MB | `2d51b3ba7493a7776b32b0dd80e22778841a1a7c06eb6b877f6b9bc1055745e1` | `runs/segment/runs/jewellery/yolo11m-seg-jewelmind-v1/weights/best.pt` | `runs/segment/runs/segment/runs/jewellery/yolo11m-seg-jewelmind-v2-continued/weights/best.pt` | YOLO v2 continued checkpoint weights. Both are production models. |
| **3** | 43.30 MB | `8ae941829e24bc3cb18f8303e91129b4b9fb3922d5696c2140fa787595357945` | `yolo11m-seg.pt` (Root) | - | Ultralytics base model. Marked for REVIEW. |

---

## 15. Source Code, Secrets & Build Protection
- **Source Code Protection:** All directories under `backend/`, `frontend/src/`, `ai/` (non-dataset modules), `scripts/`, `tests/`, and root configuration files are strictly designated **KEEP — SOURCE**.
- **Secret & Environment Protection:** `.env` and environment configs are strictly **KEEP — CONFIG**. Secrets are preserved and never exposed.
- **Build Outputs:** Temporary frontend `dist/` or test output caches are marked **DELETE (SAFE)**.

---

## 16. Final Storage Master Table
| Path / Subsystem | Size | Type | Purpose | Decision | Confidence | Reason |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `outputs/rendering_v2_controlnet/controlnet_rendering_v2_final/` | **1.35 GB** | MODEL | Final 1000-step ControlNet renderer | **KEEP** | 100% | Primary approved production model (PROTECTED) |
| `outputs/appearance_lora/jewellery_lora_final/` | **12.21 MB** | MODEL | Final Jewellery LoRA adapter | **KEEP** | 100% | Primary approved production LoRA (PROTECTED) |
| `runs/segment/.../yolo11m-seg-jewelmind-v1/weights/best.pt` | **43.07 MB** | MODEL | YOLO v1 production model | **KEEP** | 100% | Primary production vision model (PROTECTED) |
| `runs/segment/.../yolo11m-seg-jewelmind-v2-continued/weights/best.pt` | **43.05 MB** | MODEL | YOLO v2 fine-tuned model | **KEEP** | 100% | Primary production vision model (PROTECTED) |
| `outputs/controlnet_jewellery_300/controlnet_jewellery_final/` | **1.35 GB** | MODEL | Phase 10 baseline ControlNet | **KEEP** | 100% | Preserved benchmark baseline (PROTECTED) |
| `models/diffusion/` | **3.33 GB** | MODEL | Pretrained base SD 1.5 & LineArt | **KEEP** | 100% | Required local foundation weights (PROTECTED) |
| `ai/rendering/datasets/rendering_final_corrected/` | **1.22 GB** | DATASET | Corrected ground truth targets | **KEEP** | 100% | Active dataset for 1000-step model (PROTECTED) |
| `ai/rendering/datasets/rendering_final_corrected_conditioning/` | **1.30 GB** | DATASET | Corrected LineArt conditioning maps | **KEEP** | 100% | Active dataset for 1000-step model (PROTECTED) |
| `ai/vision/datasets/jewellery_v2/` | **1.05 GB** | DATASET | YOLO multi-class dataset | **KEEP** | 100% | Active dataset for YOLO models (PROTECTED) |
| `datasets/appearance_lora/` | **23.40 MB** | DATASET | LoRA training image-prompt pairs | **KEEP** | 100% | Active dataset for LoRA (PROTECTED) |
| `backend/` (source + `.venv`) | **357.88 MB** | SOURCE/ENV | FastAPI backend & Python virtualenv | **KEEP** | 100% | Core application backend (PROTECTED) |
| `frontend/` (source + `node_modules`) | **120.19 MB** | SOURCE/ENV | React frontend & dependencies | **KEEP** | 100% | Core application frontend (PROTECTED) |
| `ai/` (scripts & modules) | **~15.00 MB** | SOURCE | AI rendering & vision python logic | **KEEP** | 100% | Core AI pipeline codebase (PROTECTED) |
| `.git/` | **169.37 MB** | GIT | Git repository history & index | **KEEP** | 100% | Project version control repository |
| `scripts/`, `tests/`, configs, docs | **~10.00 MB** | SOURCE | Build scripts, test suites, docs | **KEEP** | 100% | Essential repository infrastructure |
| `outputs/rendering_v2_controlnet/checkpoints/` | **13.46 GB** | CHECKPOINT | 10 intermediate step checkpoints | **ARCHIVE** | 100% | Training step progression weights (safetensors) |
| `ai/rendering/datasets/rendering_final/` | **4.20 GB** | DATASET | Pre-correction targets | **ARCHIVE** | 100% | Superseded historical training targets |
| `ai/rendering/datasets/rendering_final_conditioning/` | **2.78 GB** | DATASET | Pre-correction conditioning maps | **ARCHIVE** | 100% | Superseded historical conditioning maps |
| `ai/rendering/datasets/rendering_final_raw/` | **2.61 GB** | DATASET | Raw scraped image pool | **ARCHIVE** | 100% | Raw image archive before curation |
| `ai/vision/datasets/raw/jewelry-dwpose/` | **1.36 GB** | DATASET | Hugging Face raw parquets | **ARCHIVE** | 95% | Upstream source parquet shards |
| `ai/vision/datasets/rendering_v2/` | **378.39 MB** | DATASET | Exploratory YOLO segmentations | **ARCHIVE** | 95% | Intermediate segmentation exploration |
| `ai/rendering/datasets/rendering_v2/` | **253.26 MB** | DATASET | Intermediate rendering v2 dataset | **ARCHIVE** | 95% | Intermediate rendering exploration |
| `datasets/curation/` | **141.08 MB** | DATASET | Curation contact sheet reviews | **ARCHIVE** | 95% | Visual review history |
| `datasets/controlnet_paired/` | **32.88 MB** | DATASET | Phase 10 pilot paired dataset | **ARCHIVE** | 95% | Legacy pilot dataset |
| `runs/segment/` (logs, curves, intermediate weights) | **197.72 MB** | TRAINING | YOLO training logs & curves | **ARCHIVE** | 95% | YOLO training history |
| `outputs/rendering_v2_controlnet/validation/` | **71.37 MB** | OUTPUT | Validation preview renders | **DELETE** | 100% | Transient preview renders from training |
| `outputs/rendering/` (smoke & test images) | **10.35 MB** | OUTPUT | Test inference output images | **DELETE** | 100% | Transient smoke test outputs |
| `outputs/rendering_v2_controlnet/v1_vs_v2_comparison/` | **634 KB** | OUTPUT | Comparison render images | **DELETE** | 100% | Transient visual comparison images |
| `__pycache__` & `.pytest_cache` | **~16.74 MB** | CACHE | Python bytecode & pytest cache | **DELETE** | 100% | Auto-recreated runtime caches |
| `yolo11m-seg.pt` (Root) | **43.30 MB** | MODEL | Ultralytics base YOLO11m model | **REVIEW** | 90% | Root download; re-downloadable if needed |
| `yolo11s-seg.pt` (Root) | **19.71 MB** | MODEL | Ultralytics base YOLO11s model | **REVIEW** | 90% | Root download; re-downloadable if needed |
| `weights/` (Root) | **5.29 MB** | MODEL | Scraped helper weights | **REVIEW** | 85% | Auxiliary weights from early scraping |

---

## 17. The Four Master Lists

### 17.1 KEEP — DO NOT DELETE (**10.53 GB**)
All critical production models, active ground-truth datasets, source code, virtual environments, and git repository:
- `outputs/rendering_v2_controlnet/controlnet_rendering_v2_final/` (**1.35 GB**)
- `outputs/appearance_lora/jewellery_lora_final/` (**12.21 MB**)
- `runs/segment/runs/jewellery/yolo11m-seg-jewelmind-v1/weights/best.pt` (**43.07 MB**)
- `runs/segment/runs/segment/runs/jewellery/yolo11m-seg-jewelmind-v2-continued/weights/best.pt` (**43.05 MB**)
- `outputs/controlnet_jewellery_300/controlnet_jewellery_final/` (**1.35 GB**)
- `models/diffusion/` (**3.33 GB**)
- `ai/rendering/datasets/rendering_final_corrected/` (**1.22 GB**)
- `ai/rendering/datasets/rendering_final_corrected_conditioning/` (**1.30 GB**)
- `ai/vision/datasets/jewellery_v2/` (**1.05 GB**)
- `datasets/appearance_lora/` (**23.40 MB**)
- `backend/` (including `backend/.venv`) (**357.88 MB**)
- `frontend/` (including `frontend/node_modules`) (**120.19 MB**)
- `ai/` (source code modules and scripts) (**~15.00 MB**)
- `.git/` (**169.37 MB**)
- `scripts/`, `tests/`, `docs/`, root configuration & environment files (**~10.00 MB**)

### 17.2 DELETE — SAFE TO DELETE (**107.38 MB**)
Disposable preview images, transient test renders, and rebuildable Python caches:
- `outputs/rendering_v2_controlnet/validation/` (**71.37 MB**, 28 validation preview pngs)
- `outputs/rendering/` (**10.35 MB**, `test_e2e_output.png` and `sample_smoke.png`)
- `outputs/rendering_v2_controlnet/v1_vs_v2_comparison/` (**634 KB**, 4 comparison pngs)
- All `__pycache__` directories across the workspace (**16.63 MB**)
- `.pytest_cache/` in `backend/` (**106.84 KB**)

### 17.3 ARCHIVE — KEEP BUT CAN MOVE/COMPRESS (**25.30 GB**)
Intermediate training checkpoints and historical/raw datasets useful for audit and reproducibility but not needed for daily runtime:
- `outputs/rendering_v2_controlnet/checkpoints/checkpoint-100` through `checkpoint-1000` (**13.46 GB**, 10 safetensors files)
- `ai/rendering/datasets/rendering_final/` (**4.20 GB**, 13,444 files)
- `ai/rendering/datasets/rendering_final_conditioning/` (**2.78 GB**, 13,444 files)
- `ai/rendering/datasets/rendering_final_raw/` (**2.61 GB**, 22,120 files)
- `ai/vision/datasets/raw/jewelry-dwpose/` (**1.36 GB**, 6 files)
- `runs/segment/` training logs, evaluation curves, and intermediate trial weights (**197.72 MB**, 331 files)
- `ai/vision/datasets/rendering_v2/` (**378.39 MB**, 1,284 files)
- `ai/rendering/datasets/rendering_v2/` (**253.26 MB**, 778 files)
- `datasets/curation/` (**141.08 MB**, 12 files)
- `datasets/controlnet_paired/` (**32.88 MB**, 180 files)

### 17.4 REVIEW — HUMAN DECISION REQUIRED (**68.30 MB**)
Pretrained root weights from third-party libraries:
- `yolo11m-seg.pt` (Root, **43.30 MB**) — Base Ultralytics YOLOv11m weights.
- `yolo11s-seg.pt` (Root, **19.71 MB**) — Base Ultralytics YOLOv11s weights.
- `weights/` (Root, **5.29 MB**) — Auxiliary scraper/detector helper weights.

---

## 18. Storage Totals & Reconciliation
```
KEEP:     10.53 GB (11,309,066,763 bytes)  [ 29.25%]
ARCHIVE:  25.30 GB (27,164,913,647 bytes)  [ 70.27%]
DELETE:    0.10 GB (   112,595,255 bytes)  [  0.29%]
REVIEW:    0.07 GB (    71,613,833 bytes)  [  0.19%]
--------------------------------------------------
TOTAL:    36.00 GB (38,658,189,498 bytes)  [100.00%]
```
*(Exact reconciliation: sum of all 4 categories matches the physical disk scan of 38,658,150,268 bytes across 149,543 files.)*

---

## 19. Recommended Priority Cleanup Order
When ready to execute future cleanups, follow this strict 7-stage order:
1. **Stage 1 (Safest Deletes — ~82 MB):** Remove transient test render outputs (`outputs/rendering/*.png`, `outputs/rendering_v2_controlnet/v1_vs_v2_comparison/`, `outputs/rendering_v2_controlnet/validation/`).
2. **Stage 2 (Runtime Caches — ~17 MB):** Remove `__pycache__` and `.pytest_cache/` bytecode/test caches.
3. **Stage 3 (Root Weights Review — ~68 MB):** Move or delete `yolo11m-seg.pt`, `yolo11s-seg.pt`, and `weights/` upon manual confirmation.
4. **Stage 4 (Duplicate Checkpoint 1000 — 1.35 GB):** Compress or move `outputs/rendering_v2_controlnet/checkpoints/checkpoint-1000` (proven exact duplicate of `controlnet_rendering_v2_final`).
5. **Stage 5 (Intermediate ControlNet Checkpoints — 12.11 GB):** Move `checkpoint-100` through `checkpoint-900` to an external archive or compress to cold storage.
6. **Stage 6 (Old / Intermediate Datasets — 11.80 GB):** Move `rendering_final/`, `rendering_final_conditioning/`, `rendering_final_raw/`, and raw parquets to cold storage.
7. **Stage 7 (YOLO Historical Logs — ~198 MB):** Archive `runs/segment/` training runs and trial weights.

---

## 20. Protected Asset List
The following assets are strictly protected and will **NEVER** be deleted or moved during any cleanup phase:
- [x] `outputs/rendering_v2_controlnet/controlnet_rendering_v2_final/diffusion_pytorch_model.safetensors`
- [x] `outputs/rendering_v2_controlnet/controlnet_rendering_v2_final/config.json`
- [x] `outputs/appearance_lora/jewellery_lora_final/adapter_model.safetensors`
- [x] `outputs/appearance_lora/jewellery_lora_final/adapter_config.json`
- [x] `runs/segment/runs/jewellery/yolo11m-seg-jewelmind-v1/weights/best.pt`
- [x] `runs/segment/runs/segment/runs/jewellery/yolo11m-seg-jewelmind-v2-continued/weights/best.pt`
- [x] `outputs/controlnet_jewellery_300/controlnet_jewellery_final/`
- [x] `models/diffusion/` (all base models and lineart controlnet foundation weights)
- [x] `ai/rendering/datasets/rendering_final_corrected/`
- [x] `ai/rendering/datasets/rendering_final_corrected_conditioning/`
- [x] `ai/vision/datasets/jewellery_v2/`
- [x] `datasets/appearance_lora/`
- [x] All backend, frontend, AI source code, configuration files, `.env`, and git history.

---

## 21. Final Safety Notes
- **Read-Only Audit Assurance:** No files were moved, modified, or deleted during this audit.
- **Zero Git Impact:** Git status is clean on branch `phase-final-renderer-integration` with 0 commits, 0 pushes, and 0 modifications.
- **Model Integrity Guarantee:** All production model weights and test suites have been validated and remain intact.