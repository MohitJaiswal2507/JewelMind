# JewelMind — Storage Size Audit & Capacity Analysis Report

**Date:** September 11, 2026  
**Audit Type:** READ-ONLY Deep Storage Inspection & Capacity Analysis  
**Branch:** `phase-final-renderer-integration`  
**Execution Status:** ✅ **AUDIT COMPLETE — ZERO FILES MODIFIED / DELETED**  

---

## 1. Executive Storage Summary

| Storage Metric | Value | Notes |
| :--- | :--- | :--- |
| **Current Total Size (Exact)** | **69.33 GB** (74,444,281,417 bytes) | Windows reported ~69.3 GB |
| **Current File Count** | **149,643 files** | Verified from disk |
| **Current Directory Count** | **1,842 directories** | Verified from disk |
| **Previous Known Clean Baseline** | **38.70 GB** | Post-Phase 9/10 cleanup baseline |
| **Net Storage Growth** | **+30.63 GB** (+79.1%) | Driven primarily by 1000-step ControlNet checkpoints & datasets |
| **Immediately Safe to Reclaim** | **~33.29 GB** (48.0% of total) | 10 optimizer states + redundant final optimizer + YOLO epoch checkpoints |
| **Archivable to Cold Storage** | **~24.59 GB** (35.5% of total) | Intermediate step weights + pre-correction/raw source datasets |
| **Essential Production Core** | **~11.45 GB** (16.5% of total) | Models, active datasets, source code, node_modules, .venv, git |

---

## 2. Where Did the ~30 GB Increase Come From?

The **+30.63 GB** increase occurred across three major operations executed during recent phases:

### A. 1000-Step ControlNet Training Run (`outputs/rendering_v2_controlnet/`) $\to$ **+44.49 GB**
During the full 1000-step training of the final ControlNet model (`ai/rendering/training/train_rendering_v2.py`), full checkpoints were saved every 100 steps:
- **10 Intermediate Checkpoints (`checkpoint-100` through `checkpoint-1000`):** Each checkpoint saved full model weights (`diffusion_pytorch_model.safetensors`, 1.35 GB) AND full AdamW optimizer state (`optimizer.pt`, 2.69 GB), totaling **4.04 GB per checkpoint** $\times 10 = $ **40.38 GB**.
- **Final Model Export (`controlnet_rendering_v2_final/`):** Contains model weights (1.35 GB) PLUS an unneeded 2.69 GB `optimizer.pt` copy (exact duplicate of `checkpoint-1000/optimizer.pt`), totaling **4.04 GB**.
- **Summary for ControlNet Training:** Optimizer states alone consume **29.59 GB** (11 $\times$ 2.69 GB). Intermediate model weights consume **12.15 GB** (9 $\times$ 1.35 GB).

### B. Full Curation, Quality Correction & Conditioning Datasets (`ai/rendering/datasets/`) $\to$ **+12.36 GB**
As part of creating the corrected training dataset across 5 jewellery categories:
- `rendering_final_raw/`: **2.61 GB** (19,366 raw uncurated source images)
- `rendering_final/`: **4.20 GB** (21,374 pre-correction curated target images)
- `rendering_final_conditioning/`: **2.78 GB** (32,071 pre-correction lineart maps)
- `rendering_final_corrected/`: **1.22 GB** (15,423 final quality-corrected target images — **ACTIVE/PROTECTED**)
- `rendering_final_corrected_conditioning/`: **1.30 GB** (23,126 final lineart conditioning maps — **ACTIVE/PROTECTED**)
- `rendering_v2/`: **253.26 MB** (2,020 sample images)

### C. YOLO V2 Multi-Jewellery Training Runs (`runs/segment/`) $\to$ **+3.99 GB**
YOLO training generated 25 intermediate epoch checkpoint files (`epoch0.pt`, `epoch5.pt`, ..., `epoch45.pt` at 171.37 MB each) across `yolo11m-seg-jewelmind-v2` and `yolo11m-seg-jewelmind-v2-continued`, totaling **~3.5 GB** in intermediate non-best weights.

---

## 3. Top-Level Directory Breakdown

| Directory / Item | Size | File Count | Directory Count | Role / Classification |
| :--- | :--- | :---: | :---: | :--- |
| `outputs/` | **45.90 GB** | 578 | 49 | Training outputs & models (40.4 GB intermediate checkpoints) |
| `ai/` | **15.22 GB** | 133,571 | 395 | AI subsystems & datasets (12.4 GB rendering + 2.8 GB vision) |
| `runs/` | **3.99 GB** | 358 | 42 | YOLO segmentation runs (3.5 GB intermediate epoch weights) |
| `models/` | **3.33 GB** | 33 | 32 | Base SD 1.5 & ControlNet Hugging Face model cache |
| `backend/` | **358.50 MB** | 7,096 | 840 | FastAPI backend & Python `.venv` virtual environment |
| `datasets/` | **197.37 MB** | 1,006 | 17 | Historical datasets & curation contact sheets |
| `.git/` | **169.37 MB** | 1,584 | 272 | Git metadata and commit objects |
| `frontend/` | **120.19 MB** | 5,226 | 171 | React / Vite frontend source & node_modules |
| `yolo11m-seg.pt` | **43.30 MB** | 1 | 0 | Root model weights (YOLO segmentation baselines) |
| `yolo11s-seg.pt` | **19.71 MB** | 1 | 0 | Root model weights (YOLO segmentation baselines) |
| `weights/` | **5.29 MB** | 1 | 1 | Repository root files and configurations |
| `docs/` | **1.32 MB** | 107 | 11 | Phase documentation, UML diagrams, reports |
| `tests/` | **247.02 KB** | 35 | 5 | Repository root files and configurations |
| `scripts/` | **246.22 KB** | 25 | 2 | Repository root files and configurations |
| `.audit_results.json` | **47.56 KB** | 1 | 0 | Repository root files and configurations |
| `PHASE_RENDERING_FINAL_MANUAL_TRAINING_READINESS_REPORT.md` | **15.64 KB** | 1 | 0 | Repository root files and configurations |
| `configs/` | **13.00 KB** | 4 | 1 | Repository root files and configurations |
| `PHASE_FINAL_RENDERER_INTEGRATION_REPORT.md` | **10.48 KB** | 1 | 0 | Repository root files and configurations |
| `.pytest_cache/` | **9.57 KB** | 5 | 3 | Repository root files and configurations |
| `PHASE_RENDERING_FINAL_TRAINING_METADATA_FIX_REPORT.md` | **7.91 KB** | 1 | 0 | Repository root files and configurations |
| `README.md` | **6.38 KB** | 1 | 0 | Repository root files and configurations |
| `.gitignore` | **4.96 KB** | 1 | 0 | Repository root files and configurations |
| `scratch/` | **3.66 KB** | 2 | 1 | Repository root files and configurations |
| `.env` | **1.58 KB** | 1 | 0 | Repository root files and configurations |
| `run_all.bat` | **591.00 B** | 1 | 0 | Repository root files and configurations |
| `run_backend.bat` | **197.00 B** | 1 | 0 | Repository root files and configurations |
| `run_ai.bat` | **150.00 B** | 1 | 0 | Repository root files and configurations |
| `run_frontend.bat` | **102.00 B** | 1 | 0 | Repository root files and configurations |

---

## 4. Largest Subdirectories Breakdown

### Outputs Directory (`outputs/` — 45.90 GB)
| Subdirectory | Size | File Count | Purpose / Contents |
| :--- | :---: | :---: | :--- |
| `outputs/rendering_v2_controlnet/` | **44.49 GB** | 364 | Checkpoints, evaluations, and export weights |
| `outputs/controlnet_jewellery_300/` | **1.35 GB** | 4 | Checkpoints, evaluations, and export weights |
| `outputs/evaluation/` | **21.40 MB** | 129 | Checkpoints, evaluations, and export weights |
| `outputs/controlnet_evaluation_100_vs_300/` | **12.94 MB** | 24 | Checkpoints, evaluations, and export weights |
| `outputs/appearance_lora/` | **12.21 MB** | 3 | Checkpoints, evaluations, and export weights |
| `outputs/rendering/` | **10.35 MB** | 29 | Checkpoints, evaluations, and export weights |
| `outputs/investigation/` | **4.11 MB** | 8 | Checkpoints, evaluations, and export weights |
| `outputs/ab_test/` | **1.43 MB** | 5 | Checkpoints, evaluations, and export weights |
| `outputs/inference/` | **530.88 KB** | 12 | Checkpoints, evaluations, and export weights |

### AI Directory (`ai/` — 15.22 GB, 133,571 files)
| Subdirectory | Size | File Count | Purpose / Contents |
| :--- | :---: | :---: | :--- |
| `ai/rendering/datasets/rendering_final/` | **4.20 GB** | 21,374 | Initial curated target images (pre-correction) |
| `ai/rendering/datasets/rendering_final_conditioning/` | **2.78 GB** | 32,071 | Pre-correction LineArt conditioning maps |
| `ai/rendering/datasets/rendering_final_raw/` | **2.61 GB** | 19,366 | Raw uncurated scraped jewellery images |
| `ai/rendering/datasets/rendering_final_corrected_conditioning/` | **1.30 GB** | 23,126 | **Authoritative LineArt conditioning maps (PROTECTED)** |
| `ai/rendering/datasets/rendering_final_corrected/` | **1.22 GB** | 15,423 | **Authoritative quality-corrected images (PROTECTED)** |
| `ai/vision/datasets/raw/jewelry-dwpose/` | **1.36 GB** | 1,482 | Raw DWPose / Hugging Face source parquets |
| `ai/vision/datasets/jewellery_v2/` | **1.05 GB** | 15,581 | **Active YOLO V2 dataset in YOLO polygon format (PROTECTED)** |
| `ai/vision/datasets/rendering_v2/` | **378.39 MB** | 2,871 | YOLO segmentations from Rendering V2 |
| `ai/rendering/datasets/rendering_v2/` | **253.26 MB** | 2,020 | Sample rendering dataset |

### YOLO Runs Directory (`runs/segment/` — 3.99 GB)
| Subdirectory | Size | File Count | Purpose / Contents |
| :--- | :---: | :---: | :--- |
| `runs/segment/runs/segment/` | **3.44 GB** | 74 | YOLO v2 continued training (20 epoch checkpoints @ 171 MB each) |
| `runs/segment/runs/jewellery/` | **446.99 MB** | 51 | YOLO v1 training (epoch checkpoints + best.pt) |
| `runs/segment/runs/benchmark/` | **68.75 MB** | 44 | Benchmark test runs |
| `runs/segment/runs/smoke_test/` | **19.56 MB** | 3 | GPU smoke validation run |

---

## 5. Model Inventory & Integrity Verification

| Model Artifact | Path | Size | SHA256 (Primary Weights) | Status / Role |
| :--- | :--- | :---: | :--- | :--- |
| **FINAL_1000_CONTROLNET** | `outputs/rendering_v2_controlnet/controlnet_rendering_v2_final` | **4.04 GB** | `a86855742b2097fc...` | ✅ **ACTIVE PRODUCTION RENDERER (100% INTACT)** |
| **APPEARANCE_LORA** | `outputs/appearance_lora/jewellery_lora_final` | **12.21 MB** | `03236ea6f39691b8...` | ✅ **ACTIVE PRODUCTION LORA (100% INTACT)** |
| **OLD_300_CONTROLNET** | `outputs/controlnet_jewellery_300/controlnet_jewellery_final` | **1.35 GB** | `056b527ef535e768...` | ✅ **PRESERVED 300-STEP BASELINE (100% INTACT)** |
| **YOLO_V1** | `runs/segment/runs/jewellery/yolo11m-seg-jewelmind-v1/weights/best.pt` | **43.07 MB** | `62c4c7199e765c01...` | ✅ **PRESERVED YOLO V1 BASELINE (100% INTACT)** |
| **YOLO_V2** | `runs/segment/runs/segment/runs/jewellery/yolo11m-seg-jewelmind-v2-continued/weights/best.pt` | **43.05 MB** | `c15acb6844d7aae6...` | ✅ **ACTIVE PRODUCTION YOLO V2 (100% INTACT)** |

---

## 6. Dataset Inventory

| Dataset Name | Path | Size | File Count | Purpose | Status / Action |
| :--- | :--- | :---: | :---: | :--- | :--- |
| **Rendering Final Corrected Conditioning** | `ai/rendering/datasets/rendering_final_corrected_conditioning/` | **1.30 GB** | 23,126 | Authoritative lineart conditioning maps | **MUST KEEP (PROTECTED)** |
| **Rendering Final Corrected Targets** | `ai/rendering/datasets/rendering_final_corrected/` | **1.22 GB** | 15,423 | Authoritative curated & corrected images | **MUST KEEP (PROTECTED)** |
| **YOLO V2 Dataset** | `ai/vision/datasets/jewellery_v2/` | **1.05 GB** | 15,581 | Polygon segmentations for YOLO11m | **MUST KEEP (PROTECTED)** |
| **Appearance LoRA Dataset** | `datasets/appearance_lora/` | **23.40 MB** | 337 | LoRA training images & captions | **MUST KEEP (PROTECTED)** |
| **Rendering Final (Pre-Correction)** | `ai/rendering/datasets/rendering_final/` | **4.20 GB** | 21,374 | Initial curated set before aspect fix | **ARCHIVE CANDIDATE** |
| **Rendering Final Conditioning (Pre-Correction)** | `ai/rendering/datasets/rendering_final_conditioning/` | **2.78 GB** | 32,071 | Pre-correction lineart maps | **ARCHIVE CANDIDATE** |
| **Rendering Final Raw** | `ai/rendering/datasets/rendering_final_raw/` | **2.61 GB** | 19,366 | Raw uncurated scraped images | **ARCHIVE CANDIDATE** |
| **Vision Raw DWPose Parquets** | `ai/vision/datasets/raw/jewelry-dwpose/` | **1.36 GB** | 1,482 | Raw downloaded HuggingFace parquets | **ARCHIVE CANDIDATE** |
| **Curation Contact Sheets** | `datasets/curation/` | **141.08 MB** | 333 | Full resolution review contact sheets | **ARCHIVE CANDIDATE** |
| **Legacy Paired ControlNet** | `datasets/controlnet_paired/` | **32.88 MB** | 332 | Phase 10 300-step training sample set | **MUST KEEP (ARCHIVE)** |

---

## 7. Training Artifact Audit (Checkpoints & Optimizer States)

| Checkpoint Path | Weights Size | Optimizer Size | Total Size | Role / Recommendation |
| :--- | :---: | :---: | :---: | :--- |
| `outputs/rendering_v2_controlnet/checkpoints/checkpoint-100/` | 1.35 GB | 2.69 GB | **4.04 GB** | Intermediate Step (Optimizer is **SAFE TO DELETE**; weights **ARCHIVE**) |
| `outputs/rendering_v2_controlnet/checkpoints/checkpoint-200/` | 1.35 GB | 2.69 GB | **4.04 GB** | Intermediate Step (Optimizer is **SAFE TO DELETE**; weights **ARCHIVE**) |
| `outputs/rendering_v2_controlnet/checkpoints/checkpoint-300/` | 1.35 GB | 2.69 GB | **4.04 GB** | Intermediate Step (Optimizer is **SAFE TO DELETE**; weights **ARCHIVE**) |
| `outputs/rendering_v2_controlnet/checkpoints/checkpoint-400/` | 1.35 GB | 2.69 GB | **4.04 GB** | Intermediate Step (Optimizer is **SAFE TO DELETE**; weights **ARCHIVE**) |
| `outputs/rendering_v2_controlnet/checkpoints/checkpoint-500/` | 1.35 GB | 2.69 GB | **4.04 GB** | Intermediate Step (Optimizer is **SAFE TO DELETE**; weights **ARCHIVE**) |
| `outputs/rendering_v2_controlnet/checkpoints/checkpoint-600/` | 1.35 GB | 2.69 GB | **4.04 GB** | Intermediate Step (Optimizer is **SAFE TO DELETE**; weights **ARCHIVE**) |
| `outputs/rendering_v2_controlnet/checkpoints/checkpoint-700/` | 1.35 GB | 2.69 GB | **4.04 GB** | Intermediate Step (Optimizer is **SAFE TO DELETE**; weights **ARCHIVE**) |
| `outputs/rendering_v2_controlnet/checkpoints/checkpoint-800/` | 1.35 GB | 2.69 GB | **4.04 GB** | Intermediate Step (Optimizer is **SAFE TO DELETE**; weights **ARCHIVE**) |
| `outputs/rendering_v2_controlnet/checkpoints/checkpoint-900/` | 1.35 GB | 2.69 GB | **4.04 GB** | Intermediate Step (Optimizer is **SAFE TO DELETE**; weights **ARCHIVE**) |
| `outputs/rendering_v2_controlnet/checkpoints/checkpoint-1000/` | 1.35 GB | 2.69 GB | **4.04 GB** | Intermediate Step (Optimizer is **SAFE TO DELETE**; weights **ARCHIVE**) |
| `outputs/rendering_v2_controlnet/controlnet_rendering_v2_final/` | 1.35 GB | 2.69 GB | **4.04 GB** | **PRODUCTION MODEL** (Weights **MUST KEEP**; `optimizer.pt` is **SAFE TO DELETE**) |
| `runs/segment/runs/segment/runs/jewellery/yolo11m-seg-jewelmind-v2*/weights/epoch*.pt` (20 files) | 3.43 GB | — | **3.43 GB** | Intermediate YOLO epochs (**SAFE TO DELETE**) |
| `runs/segment/runs/jewellery/yolo11m-seg-jewelmind-v1/weights/epoch*.pt` (4 files) | 172.4 MB | — | **172.4 MB** | Intermediate YOLO epochs (**SAFE TO DELETE**) |

---

## 8. Cache Audit

| Cache Category | Total Size | File Count | Safe to Delete? | What Will Break If Deleted? |
| :--- | :---: | :---: | :---: | :--- |
| `.git_objects` | **169.37 MB** | 1,584 | **NO (KEEP)** | Git repository history and commit objects will be corrupted. |
| `.pytest_cache` | **20.92 KB** | 9 | **YES** | Nothing. Pytest recreates test execution cache on next run. |
| `__pycache__` | **25.39 MB** | 1,168 | **YES** | Nothing. Python auto-regenerates `.pyc` files on execution. |
| `python_virtualenv` | **333.16 MB** | 5,907 | **NO (KEEP)** | Backend Python runtime dependencies will need full `pip install`. |

---

## 9. Duplicate File Inventory (> 50 MB)

| Duplicate Group | Size | SHA256 Hash | Duplicate Paths | Safe to Delete? |
| :--- | :---: | :--- | :--- | :--- |
| **Final Optimizer Duplicate** | **2.69 GB** | `8167f8949439d06c...` | 1. `outputs/rendering_v2_controlnet/checkpoints/checkpoint-1000/optimizer.pt`<br>2. `outputs/rendering_v2_controlnet/controlnet_rendering_v2_final/optimizer.pt` | **YES** (Delete `controlnet_rendering_v2_final/optimizer.pt`; keep `checkpoint-1000/` or delete both if training complete) |

---

## 10. Top 100 Largest Files in JewelMind

| # | Size | File Path | File Type | Purpose | Safe Delete? | Recommendation / Reason |
| :-: | :---: | :--- | :--- | :--- | :---: | :--- |
| 1 | **2.69 GB** | `outputs/rendering_v2_controlnet/checkpoints/checkpoint-100/optimizer.pt` | `OPTIMIZER_STATE` | AdamW optimizer state for intermediate step | **YES** | Intermediate training state; training 100% complete |
| 2 | **2.69 GB** | `outputs/rendering_v2_controlnet/checkpoints/checkpoint-1000/optimizer.pt` | `OPTIMIZER_STATE` | AdamW optimizer state for intermediate step | **YES** | Intermediate training state; training 100% complete |
| 3 | **2.69 GB** | `outputs/rendering_v2_controlnet/checkpoints/checkpoint-200/optimizer.pt` | `OPTIMIZER_STATE` | AdamW optimizer state for intermediate step | **YES** | Intermediate training state; training 100% complete |
| 4 | **2.69 GB** | `outputs/rendering_v2_controlnet/checkpoints/checkpoint-300/optimizer.pt` | `OPTIMIZER_STATE` | AdamW optimizer state for intermediate step | **YES** | Intermediate training state; training 100% complete |
| 5 | **2.69 GB** | `outputs/rendering_v2_controlnet/checkpoints/checkpoint-400/optimizer.pt` | `OPTIMIZER_STATE` | AdamW optimizer state for intermediate step | **YES** | Intermediate training state; training 100% complete |
| 6 | **2.69 GB** | `outputs/rendering_v2_controlnet/checkpoints/checkpoint-500/optimizer.pt` | `OPTIMIZER_STATE` | AdamW optimizer state for intermediate step | **YES** | Intermediate training state; training 100% complete |
| 7 | **2.69 GB** | `outputs/rendering_v2_controlnet/checkpoints/checkpoint-600/optimizer.pt` | `OPTIMIZER_STATE` | AdamW optimizer state for intermediate step | **YES** | Intermediate training state; training 100% complete |
| 8 | **2.69 GB** | `outputs/rendering_v2_controlnet/checkpoints/checkpoint-700/optimizer.pt` | `OPTIMIZER_STATE` | AdamW optimizer state for intermediate step | **YES** | Intermediate training state; training 100% complete |
| 9 | **2.69 GB** | `outputs/rendering_v2_controlnet/checkpoints/checkpoint-800/optimizer.pt` | `OPTIMIZER_STATE` | AdamW optimizer state for intermediate step | **YES** | Intermediate training state; training 100% complete |
| 10 | **2.69 GB** | `outputs/rendering_v2_controlnet/checkpoints/checkpoint-900/optimizer.pt` | `OPTIMIZER_STATE` | AdamW optimizer state for intermediate step | **YES** | Intermediate training state; training 100% complete |
| 11 | **2.69 GB** | `outputs/rendering_v2_controlnet/controlnet_rendering_v2_final/optimizer.pt` | `OPTIMIZER_STATE` | AdamW optimizer state for final model | **YES** | Inference only requires model weights; duplicate of ckpt-1000 optimizer |
| 12 | **1.60 GB** | `models/diffusion/models--runwayml--stable-diffusion-v1-5/snapshots/451f4fe16113bff5a5d2269ed5ad43b0592e9a14/unet/diffusion_pytorch_model.fp16.safetensors` | `BASE_MODEL_WEIGHTS` | Hugging Face baseline model weights (SD 1.5 / LineArt) | **NO (PROTECTED)** | Required for local base generative diffusion inference |
| 13 | **1.35 GB** | `models/diffusion/models--lllyasviel--control_v11p_sd15_lineart/snapshots/8a158f547e031c5b8fbca19ead09a74767ff4db0/diffusion_pytorch_model.safetensors` | `BASE_MODEL_WEIGHTS` | Hugging Face baseline model weights (SD 1.5 / LineArt) | **NO (PROTECTED)** | Required for local base generative diffusion inference |
| 14 | **1.35 GB** | `outputs/controlnet_jewellery_300/controlnet_jewellery_final/diffusion_pytorch_model.safetensors` | `MODEL_WEIGHTS` | Legacy 300-step ControlNet model | **NO (PROTECTED)** | Protected legacy baseline model |
| 15 | **1.35 GB** | `outputs/rendering_v2_controlnet/checkpoints/checkpoint-100/diffusion_pytorch_model.safetensors` | `CHECKPOINT_WEIGHTS` | Intermediate ControlNet step weights | **ARCHIVE / OPTIONAL** | Intermediate training step; final model is in controlnet_rendering_v2_final/ |
| 16 | **1.35 GB** | `outputs/rendering_v2_controlnet/checkpoints/checkpoint-1000/diffusion_pytorch_model.safetensors` | `CHECKPOINT_WEIGHTS` | Intermediate ControlNet step weights | **ARCHIVE / OPTIONAL** | Intermediate training step; final model is in controlnet_rendering_v2_final/ |
| 17 | **1.35 GB** | `outputs/rendering_v2_controlnet/checkpoints/checkpoint-200/diffusion_pytorch_model.safetensors` | `CHECKPOINT_WEIGHTS` | Intermediate ControlNet step weights | **ARCHIVE / OPTIONAL** | Intermediate training step; final model is in controlnet_rendering_v2_final/ |
| 18 | **1.35 GB** | `outputs/rendering_v2_controlnet/checkpoints/checkpoint-300/diffusion_pytorch_model.safetensors` | `CHECKPOINT_WEIGHTS` | Intermediate ControlNet step weights | **ARCHIVE / OPTIONAL** | Intermediate training step; final model is in controlnet_rendering_v2_final/ |
| 19 | **1.35 GB** | `outputs/rendering_v2_controlnet/checkpoints/checkpoint-400/diffusion_pytorch_model.safetensors` | `CHECKPOINT_WEIGHTS` | Intermediate ControlNet step weights | **ARCHIVE / OPTIONAL** | Intermediate training step; final model is in controlnet_rendering_v2_final/ |
| 20 | **1.35 GB** | `outputs/rendering_v2_controlnet/checkpoints/checkpoint-500/diffusion_pytorch_model.safetensors` | `CHECKPOINT_WEIGHTS` | Intermediate ControlNet step weights | **ARCHIVE / OPTIONAL** | Intermediate training step; final model is in controlnet_rendering_v2_final/ |
| 21 | **1.35 GB** | `outputs/rendering_v2_controlnet/checkpoints/checkpoint-600/diffusion_pytorch_model.safetensors` | `CHECKPOINT_WEIGHTS` | Intermediate ControlNet step weights | **ARCHIVE / OPTIONAL** | Intermediate training step; final model is in controlnet_rendering_v2_final/ |
| 22 | **1.35 GB** | `outputs/rendering_v2_controlnet/checkpoints/checkpoint-700/diffusion_pytorch_model.safetensors` | `CHECKPOINT_WEIGHTS` | Intermediate ControlNet step weights | **ARCHIVE / OPTIONAL** | Intermediate training step; final model is in controlnet_rendering_v2_final/ |
| 23 | **1.35 GB** | `outputs/rendering_v2_controlnet/checkpoints/checkpoint-800/diffusion_pytorch_model.safetensors` | `CHECKPOINT_WEIGHTS` | Intermediate ControlNet step weights | **ARCHIVE / OPTIONAL** | Intermediate training step; final model is in controlnet_rendering_v2_final/ |
| 24 | **1.35 GB** | `outputs/rendering_v2_controlnet/checkpoints/checkpoint-900/diffusion_pytorch_model.safetensors` | `CHECKPOINT_WEIGHTS` | Intermediate ControlNet step weights | **ARCHIVE / OPTIONAL** | Intermediate training step; final model is in controlnet_rendering_v2_final/ |
| 25 | **1.35 GB** | `outputs/rendering_v2_controlnet/controlnet_rendering_v2_final/diffusion_pytorch_model.safetensors` | `PROD_MODEL_WEIGHTS` | Approved 1000-step ControlNet production renderer | **NO (PRODUCTION)** | Active production inference model |
| 26 | **430.86 MB** | `ai/vision/datasets/raw/jewelry-dwpose/data/train-00002-of-00003.parquet` | `PARQUET_RAW_DATA` | Raw downloaded DWPose parquet dataset | **ARCHIVE** | Raw source data from HF; converted dataset in jewellery_v2 |
| 27 | **430.24 MB** | `ai/vision/datasets/raw/jewelry-dwpose/data/train-00000-of-00003.parquet` | `PARQUET_RAW_DATA` | Raw downloaded DWPose parquet dataset | **ARCHIVE** | Raw source data from HF; converted dataset in jewellery_v2 |
| 28 | **429.87 MB** | `ai/vision/datasets/raw/jewelry-dwpose/data/train-00001-of-00003.parquet` | `PARQUET_RAW_DATA` | Raw downloaded DWPose parquet dataset | **ARCHIVE** | Raw source data from HF; converted dataset in jewellery_v2 |
| 29 | **234.74 MB** | `models/diffusion/models--runwayml--stable-diffusion-v1-5/snapshots/451f4fe16113bff5a5d2269ed5ad43b0592e9a14/text_encoder/model.fp16.safetensors` | `BASE_MODEL_WEIGHTS` | Hugging Face baseline model weights (SD 1.5 / LineArt) | **NO (PROTECTED)** | Required for local base generative diffusion inference |
| 30 | **171.38 MB** | `runs/segment/runs/jewellery/yolo11m-seg-jewelmind-v1/weights/epoch15.pt` | `YOLO_CHECKPOINT` | Intermediate YOLO training epoch checkpoint | **YES** | Intermediate training epoch; final weights preserved in best.pt |
| 31 | **171.37 MB** | `runs/segment/runs/segment/runs/jewellery/yolo11m-seg-jewelmind-v2/weights/epoch45.pt` | `YOLO_CHECKPOINT` | Intermediate YOLO training epoch checkpoint | **YES** | Intermediate training epoch; final weights preserved in best.pt |
| 32 | **171.37 MB** | `runs/segment/runs/segment/runs/jewellery/yolo11m-seg-jewelmind-v2-continued/weights/epoch45.pt` | `YOLO_CHECKPOINT` | Intermediate YOLO training epoch checkpoint | **YES** | Intermediate training epoch; final weights preserved in best.pt |
| 33 | **171.37 MB** | `runs/segment/runs/segment/runs/jewellery/yolo11m-seg-jewelmind-v2/weights/epoch40.pt` | `YOLO_CHECKPOINT` | Intermediate YOLO training epoch checkpoint | **YES** | Intermediate training epoch; final weights preserved in best.pt |
| 34 | **171.37 MB** | `runs/segment/runs/segment/runs/jewellery/yolo11m-seg-jewelmind-v2-continued/weights/epoch40.pt` | `YOLO_CHECKPOINT` | Intermediate YOLO training epoch checkpoint | **YES** | Intermediate training epoch; final weights preserved in best.pt |
| 35 | **171.37 MB** | `runs/segment/runs/segment/runs/jewellery/yolo11m-seg-jewelmind-v2/weights/epoch35.pt` | `YOLO_CHECKPOINT` | Intermediate YOLO training epoch checkpoint | **YES** | Intermediate training epoch; final weights preserved in best.pt |
| 36 | **171.37 MB** | `runs/segment/runs/segment/runs/jewellery/yolo11m-seg-jewelmind-v2-continued/weights/epoch35.pt` | `YOLO_CHECKPOINT` | Intermediate YOLO training epoch checkpoint | **YES** | Intermediate training epoch; final weights preserved in best.pt |
| 37 | **171.37 MB** | `runs/segment/runs/segment/runs/jewellery/yolo11m-seg-jewelmind-v2/weights/epoch30.pt` | `YOLO_CHECKPOINT` | Intermediate YOLO training epoch checkpoint | **YES** | Intermediate training epoch; final weights preserved in best.pt |
| 38 | **171.37 MB** | `runs/segment/runs/segment/runs/jewellery/yolo11m-seg-jewelmind-v2-continued/weights/epoch30.pt` | `YOLO_CHECKPOINT` | Intermediate YOLO training epoch checkpoint | **YES** | Intermediate training epoch; final weights preserved in best.pt |
| 39 | **171.37 MB** | `runs/segment/runs/segment/runs/jewellery/yolo11m-seg-jewelmind-v2/weights/epoch25.pt` | `YOLO_CHECKPOINT` | Intermediate YOLO training epoch checkpoint | **YES** | Intermediate training epoch; final weights preserved in best.pt |
| 40 | **171.37 MB** | `runs/segment/runs/segment/runs/jewellery/yolo11m-seg-jewelmind-v2-continued/weights/epoch25.pt` | `YOLO_CHECKPOINT` | Intermediate YOLO training epoch checkpoint | **YES** | Intermediate training epoch; final weights preserved in best.pt |
| 41 | **171.37 MB** | `runs/segment/runs/segment/runs/jewellery/yolo11m-seg-jewelmind-v2/weights/epoch20.pt` | `YOLO_CHECKPOINT` | Intermediate YOLO training epoch checkpoint | **YES** | Intermediate training epoch; final weights preserved in best.pt |
| 42 | **171.37 MB** | `runs/segment/runs/segment/runs/jewellery/yolo11m-seg-jewelmind-v2-continued/weights/epoch20.pt` | `YOLO_CHECKPOINT` | Intermediate YOLO training epoch checkpoint | **YES** | Intermediate training epoch; final weights preserved in best.pt |
| 43 | **171.36 MB** | `runs/segment/runs/segment/runs/jewellery/yolo11m-seg-jewelmind-v2/weights/epoch15.pt` | `YOLO_CHECKPOINT` | Intermediate YOLO training epoch checkpoint | **YES** | Intermediate training epoch; final weights preserved in best.pt |
| 44 | **171.36 MB** | `runs/segment/runs/segment/runs/jewellery/yolo11m-seg-jewelmind-v2-continued/weights/epoch15.pt` | `YOLO_CHECKPOINT` | Intermediate YOLO training epoch checkpoint | **YES** | Intermediate training epoch; final weights preserved in best.pt |
| 45 | **171.36 MB** | `runs/segment/runs/segment/runs/jewellery/yolo11m-seg-jewelmind-v2/weights/epoch10.pt` | `YOLO_CHECKPOINT` | Intermediate YOLO training epoch checkpoint | **YES** | Intermediate training epoch; final weights preserved in best.pt |
| 46 | **171.36 MB** | `runs/segment/runs/segment/runs/jewellery/yolo11m-seg-jewelmind-v2-continued/weights/epoch10.pt` | `YOLO_CHECKPOINT` | Intermediate YOLO training epoch checkpoint | **YES** | Intermediate training epoch; final weights preserved in best.pt |
| 47 | **171.36 MB** | `runs/segment/runs/segment/runs/jewellery/yolo11m-seg-jewelmind-v2/weights/epoch5.pt` | `YOLO_CHECKPOINT` | Intermediate YOLO training epoch checkpoint | **YES** | Intermediate training epoch; final weights preserved in best.pt |
| 48 | **171.36 MB** | `runs/segment/runs/segment/runs/jewellery/yolo11m-seg-jewelmind-v2-continued/weights/epoch5.pt` | `YOLO_CHECKPOINT` | Intermediate YOLO training epoch checkpoint | **YES** | Intermediate training epoch; final weights preserved in best.pt |
| 49 | **171.36 MB** | `runs/segment/runs/segment/runs/jewellery/yolo11m-seg-jewelmind-v2-continued/weights/epoch0.pt` | `YOLO_CHECKPOINT` | Intermediate YOLO training epoch checkpoint | **YES** | Intermediate training epoch; final weights preserved in best.pt |
| 50 | **171.36 MB** | `runs/segment/runs/segment/runs/jewellery/yolo11m-seg-jewelmind-v2/weights/epoch0.pt` | `YOLO_CHECKPOINT` | Intermediate YOLO training epoch checkpoint | **YES** | Intermediate training epoch; final weights preserved in best.pt |
| 51 | **159.58 MB** | `models/diffusion/models--runwayml--stable-diffusion-v1-5/snapshots/451f4fe16113bff5a5d2269ed5ad43b0592e9a14/vae/diffusion_pytorch_model.fp16.safetensors` | `BASE_MODEL_WEIGHTS` | Hugging Face baseline model weights (SD 1.5 / LineArt) | **NO (PROTECTED)** | Required for local base generative diffusion inference |
| 52 | **81.87 MB** | `backend/.venv/Lib/site-packages/cv2/cv2.pyd` | `PYTHON_BINARY` | Backend virtual environment binary / dependency | **NO (PROTECTED)** | Required for backend FastAPI execution |
| 53 | **77.50 MB** | `runs/segment/runs/jewellery/yolo11s-jewelmind-v2-smoke/weights/epoch0.pt` | `YOLO_CHECKPOINT` | Intermediate YOLO training epoch checkpoint | **YES** | Intermediate training epoch; final weights preserved in best.pt |
| 54 | **43.30 MB** | `yolo11m-seg.pt` | `PT` | Workspace asset or dataset file | **REVIEW** | General repository asset |
| 55 | **43.12 MB** | `runs/segment/runs/jewellery/yolo11m-seg-jewelmind-v1/weights/epoch10.pt` | `YOLO_CHECKPOINT` | Intermediate YOLO training epoch checkpoint | **YES** | Intermediate training epoch; final weights preserved in best.pt |
| 56 | **43.11 MB** | `runs/segment/runs/jewellery/yolo11m-seg-jewelmind-v1/weights/epoch5.pt` | `YOLO_CHECKPOINT` | Intermediate YOLO training epoch checkpoint | **YES** | Intermediate training epoch; final weights preserved in best.pt |
| 57 | **43.11 MB** | `runs/segment/runs/jewellery/yolo11m-seg-jewelmind-v1/weights/epoch0.pt` | `YOLO_CHECKPOINT` | Intermediate YOLO training epoch checkpoint | **YES** | Intermediate training epoch; final weights preserved in best.pt |
| 58 | **43.07 MB** | `runs/segment/runs/jewellery/yolo11m-seg-jewelmind-v1/weights/best.pt` | `YOLO_MODEL_WEIGHTS` | Best YOLO segmentation model weights | **NO (PRODUCTION)** | Active YOLO component detection weights |
| 59 | **43.07 MB** | `runs/segment/runs/benchmark/bench_yolo11m-seg/weights/best.pt` | `YOLO_MODEL_WEIGHTS` | Best YOLO segmentation model weights | **NO (PRODUCTION)** | Active YOLO component detection weights |
| 60 | **43.05 MB** | `runs/segment/runs/segment/runs/jewellery/yolo11m-seg-jewelmind-v2/weights/best.pt` | `YOLO_MODEL_WEIGHTS` | Best YOLO segmentation model weights | **NO (PRODUCTION)** | Active YOLO component detection weights |
| 61 | **43.05 MB** | `runs/segment/runs/segment/runs/jewellery/yolo11m-seg-jewelmind-v2-continued/weights/best.pt` | `YOLO_MODEL_WEIGHTS` | Best YOLO segmentation model weights | **NO (PRODUCTION)** | Active YOLO component detection weights |
| 62 | **32.92 MB** | `backend/.venv/Lib/site-packages/ortools/.libs/ortools.dll` | `PYTHON_BINARY` | Backend virtual environment binary / dependency | **NO (PROTECTED)** | Required for backend FastAPI execution |
| 63 | **29.45 MB** | `backend/.venv/Lib/site-packages/cv2/opencv_videoio_ffmpeg500_64.dll` | `PYTHON_BINARY` | Backend virtual environment binary / dependency | **NO (PROTECTED)** | Required for backend FastAPI execution |
| 64 | **19.94 MB** | `frontend/node_modules/@rolldown/binding-win32-x64-msvc/rolldown-binding.win32-x64-msvc.node` | `NODE_BINARY` | Frontend Vite / React build dependency | **NO (PROTECTED)** | Required for frontend compilation |
| 65 | **19.71 MB** | `yolo11s-seg.pt` | `PT` | Workspace asset or dataset file | **REVIEW** | General repository asset |
| 66 | **19.56 MB** | `runs/segment/runs/benchmark/bench_yolo11s-seg/weights/best.pt` | `YOLO_MODEL_WEIGHTS` | Best YOLO segmentation model weights | **NO (PRODUCTION)** | Active YOLO component detection weights |
| 67 | **19.56 MB** | `runs/segment/runs/smoke_test/gpu_smoke_run/weights/best.pt` | `YOLO_MODEL_WEIGHTS` | Best YOLO segmentation model weights | **NO (PRODUCTION)** | Active YOLO component detection weights |
| 68 | **19.55 MB** | `backend/.venv/Lib/site-packages/numpy.libs/libscipy_openblas64_-327b2e0bcffce2882e0dc04cdeb4eaa6.dll` | `PYTHON_BINARY` | Backend virtual environment binary / dependency | **NO (PROTECTED)** | Required for backend FastAPI execution |
| 69 | **19.52 MB** | `runs/segment/runs/jewellery/yolo11s-jewelmind-v2-smoke/weights/best.pt` | `YOLO_MODEL_WEIGHTS` | Best YOLO segmentation model weights | **NO (PRODUCTION)** | Active YOLO component detection weights |
| 70 | **14.44 MB** | `ai/rendering/notebooks/Rendering_V2_Dataset_Preparation.ipynb` | `IPYNB` | Workspace asset or dataset file | **REVIEW** | General repository asset |
| 71 | **12.95 MB** | `backend/.venv/Lib/site-packages/ortools/.libs/libprotobuf.dll` | `PYTHON_BINARY` | Backend virtual environment binary / dependency | **NO (PROTECTED)** | Required for backend FastAPI execution |
| 72 | **12.85 MB** | `datasets/curation/CONTACT_SHEET_REVIEW_REQUIRED.png` | `CONTACT_SHEET` | Visual curation review contact sheets | **ARCHIVE** | Curation review artifacts |
| 73 | **12.81 MB** | `.git/objects/40/cddd3343db9b69fc62afcda666ba6345e6a435` | `GIT_OBJECT` | Git commit history and repository object | **NO (PROTECTED)** | Git repository metadata |
| 74 | **12.21 MB** | `backend/.venv/Lib/site-packages/ortools/.libs/libscip.dll` | `PYTHON_BINARY` | Backend virtual environment binary / dependency | **NO (PROTECTED)** | Required for backend FastAPI execution |
| 75 | **12.20 MB** | `outputs/appearance_lora/jewellery_lora_final/adapter_model.safetensors` | `LORA_WEIGHTS` | Final approved appearance LoRA adapter | **NO (PRODUCTION)** | Active production appearance LoRA |
| 76 | **12.02 MB** | `datasets/curation/HUMAN_CURATION_MASTER_CONTACT_SHEET.png` | `CONTACT_SHEET` | Visual curation review contact sheets | **ARCHIVE** | Curation review artifacts |
| 77 | **11.98 MB** | `.git/objects/d7/9ad497356fb4eed829ea8a54f0f7b4fc7a354a` | `GIT_OBJECT` | Git commit history and repository object | **NO (PROTECTED)** | Git repository metadata |
| 78 | **11.02 MB** | `.git/objects/8e/46dabef1d0b7e30572668ac910844b99420e57` | `GIT_OBJECT` | Git commit history and repository object | **NO (PROTECTED)** | Git repository metadata |
| 79 | **11.01 MB** | `ai/rendering/datasets/rendering_final/images/other_jewellery/ds2_011981_the-stone-aisle-premium-beautiful-designer-set-of-.png` | `PRE_CORRECTION_IMAGE` | Initial curated dataset image (pre-correction) | **ARCHIVE / REVIEW** | Pre-correction dataset; corrected dataset is in rendering_final_corrected |
| 80 | **11.01 MB** | `ai/rendering/datasets/rendering_final/test/images/other_jewellery/ds2_011981_the-stone-aisle-premium-beautiful-designer-set-of-.png` | `PRE_CORRECTION_IMAGE` | Initial curated dataset image (pre-correction) | **ARCHIVE / REVIEW** | Pre-correction dataset; corrected dataset is in rendering_final_corrected |
| 81 | **11.01 MB** | `ai/rendering/datasets/rendering_final_raw/indian_traditional_artificial_jewellery/the-stone-aisle-premium-beautiful-designer-set-of-3-evil-eye-rakhi-for-brother-product-images-rvtub3akky-1-202408010053.png` | `RAW_DATASET_IMAGE` | Original raw uncurated dataset image | **ARCHIVE** | Raw dataset; curated/corrected versions exist |
| 82 | **10.72 MB** | `datasets/curation/CONTACT_SHEET_BROOCHES_OTHER.png` | `CONTACT_SHEET` | Visual curation review contact sheets | **ARCHIVE** | Curation review artifacts |
| 83 | **10.69 MB** | `.git/objects/dc/6a15643cedb5a9dff16d50dd56a3db53b4c433` | `GIT_OBJECT` | Git commit history and repository object | **NO (PROTECTED)** | Git repository metadata |
| 84 | **10.49 MB** | `ai/rendering/datasets/rendering_final/images/other_jewellery/ds2_007859_floral-and-lord-krishna-designer-rakhis-happy-rakh.png` | `PRE_CORRECTION_IMAGE` | Initial curated dataset image (pre-correction) | **ARCHIVE / REVIEW** | Pre-correction dataset; corrected dataset is in rendering_final_corrected |
| 85 | **10.49 MB** | `ai/rendering/datasets/rendering_final/train/images/other_jewellery/ds2_007859_floral-and-lord-krishna-designer-rakhis-happy-rakh.png` | `PRE_CORRECTION_IMAGE` | Initial curated dataset image (pre-correction) | **ARCHIVE / REVIEW** | Pre-correction dataset; corrected dataset is in rendering_final_corrected |
| 86 | **10.49 MB** | `ai/rendering/datasets/rendering_final_raw/indian_traditional_artificial_jewellery/floral-and-lord-krishna-designer-rakhis-happy-rakhi-wooden-with-roli-chawal-pack-rakhi-for-brother-bhaiya-bhai-product-images-rvavfye2x3-0-202407251934.png` | `RAW_DATASET_IMAGE` | Original raw uncurated dataset image | **ARCHIVE** | Raw dataset; curated/corrected versions exist |
| 87 | **9.76 MB** | `ai/rendering/datasets/rendering_final_raw/indian_traditional_artificial_jewellery/metadata.csv` | `RAW_DATASET_IMAGE` | Original raw uncurated dataset image | **ARCHIVE** | Raw dataset; curated/corrected versions exist |
| 88 | **9.53 MB** | `datasets/curation/FULL_CANDIDATE_CONTACT_SHEET.png` | `CONTACT_SHEET` | Visual curation review contact sheets | **ARCHIVE** | Curation review artifacts |
| 89 | **9.49 MB** | `.git/objects/e5/d7d2ee3e58460906eec99276387756878dc38d` | `GIT_OBJECT` | Git commit history and repository object | **NO (PROTECTED)** | Git repository metadata |
| 90 | **9.48 MB** | `backend/.venv/Lib/site-packages/cryptography/hazmat/bindings/_rust.pyd` | `PYTHON_BINARY` | Backend virtual environment binary / dependency | **NO (PROTECTED)** | Required for backend FastAPI execution |
| 91 | **9.47 MB** | `ai/rendering/datasets/rendering_final/images/other_jewellery/ds2_011972_the-stone-aisle-premium-beautiful-designer-set-of-.png` | `PRE_CORRECTION_IMAGE` | Initial curated dataset image (pre-correction) | **ARCHIVE / REVIEW** | Pre-correction dataset; corrected dataset is in rendering_final_corrected |
| 92 | **9.47 MB** | `ai/rendering/datasets/rendering_final/train/images/other_jewellery/ds2_011972_the-stone-aisle-premium-beautiful-designer-set-of-.png` | `PRE_CORRECTION_IMAGE` | Initial curated dataset image (pre-correction) | **ARCHIVE / REVIEW** | Pre-correction dataset; corrected dataset is in rendering_final_corrected |
| 93 | **9.47 MB** | `ai/rendering/datasets/rendering_final_raw/indian_traditional_artificial_jewellery/the-stone-aisle-premium-beautiful-designer-set-of-2-krishna-and-meenakari-rakhi-for-brother-product-images-rvgyirji2b-1-202407302353.png` | `RAW_DATASET_IMAGE` | Original raw uncurated dataset image | **ARCHIVE** | Raw dataset; curated/corrected versions exist |
| 94 | **9.06 MB** | `frontend/node_modules/@tailwindcss/node/node_modules/lightningcss-win32-x64-msvc/lightningcss.win32-x64-msvc.node` | `NODE_BINARY` | Frontend Vite / React build dependency | **NO (PROTECTED)** | Required for frontend compilation |
| 95 | **9.05 MB** | `frontend/node_modules/lightningcss-win32-x64-msvc/lightningcss.win32-x64-msvc.node` | `NODE_BINARY` | Frontend Vite / React build dependency | **NO (PROTECTED)** | Required for frontend compilation |
| 96 | **8.72 MB** | `frontend/node_modules/typescript/lib/typescript.js` | `NODE_BINARY` | Frontend Vite / React build dependency | **NO (PROTECTED)** | Required for frontend compilation |
| 97 | **8.54 MB** | `ai/vision/notebooks/YOLO_V2_Training_Analysis.ipynb` | `IPYNB` | Workspace asset or dataset file | **REVIEW** | General repository asset |
| 98 | **8.41 MB** | `ai/rendering/datasets/rendering_final/images/other_jewellery/ds2_011982_the-stone-aisle-premium-beautiful-designer-set-of-.png` | `PRE_CORRECTION_IMAGE` | Initial curated dataset image (pre-correction) | **ARCHIVE / REVIEW** | Pre-correction dataset; corrected dataset is in rendering_final_corrected |
| 99 | **8.41 MB** | `ai/rendering/datasets/rendering_final/train/images/other_jewellery/ds2_011982_the-stone-aisle-premium-beautiful-designer-set-of-.png` | `PRE_CORRECTION_IMAGE` | Initial curated dataset image (pre-correction) | **ARCHIVE / REVIEW** | Pre-correction dataset; corrected dataset is in rendering_final_corrected |
| 100 | **8.41 MB** | `ai/rendering/datasets/rendering_final_raw/indian_traditional_artificial_jewellery/the-stone-aisle-premium-beautiful-designer-set-of-3-evil-eye-rakhi-for-brother-product-images-rvtub3akky-2-202408010053.png` | `RAW_DATASET_IMAGE` | Original raw uncurated dataset image | **ARCHIVE** | Raw dataset; curated/corrected versions exist |

---

## 11. Git Tracking Audit

- **Current Branch:** `phase-final-renderer-integration`
- **Tracked Large Files:** No large training checkpoints or dataset images are tracked in Git.
- **`.gitignore` Rules:** Correctly ignores `.venv/`, `node_modules/`, `models/diffusion/`, and local training output directories.
- **Untracked Artifacts:** Large dataset caches and training checkpoints exist purely as untracked files on disk.

---

## 12. Storage Classification Framework (A through J)

| Category | Classification | Description | Total Size |
| :-: | :--- | :--- | :---: |
| **A** | **MUST KEEP — PRODUCTION** | Final 1000-step ControlNet weights, Appearance LoRA, YOLO best weights, SD 1.5 cache | **~6.08 GB** |
| **B** | **MUST KEEP — DATASETS** | Corrected training datasets (`rendering_final_corrected/` + `rendering_final_corrected_conditioning/`) & `jewellery_v2/` | **~3.57 GB** |
| **C** | **MUST KEEP — SOURCE CODE** | Backend, frontend, AI modules, tests, scripts, configs, migrations | **~150 MB** |
| **D** | **MUST KEEP — REPRODUCIBILITY** | Training scripts, Jupyter notebooks, YAML configurations, environment requirements | **~100 MB** |
| **E** | **ARCHIVE — CAN MOVE / COMPRESS** | Intermediate ControlNet step weights (9 $\times$ 1.35 GB) & raw/pre-correction datasets (8.2 GB) | **~24.59 GB** |
| **F** | **SAFE DELETE — CACHE** | `__pycache__`, `.pytest_cache`, `.ipynb_checkpoints` | **~25.4 MB** |
| **G** | **SAFE DELETE — TEMPORARY** | 10 AdamW optimizer states (`outputs/rendering_v2_controlnet/checkpoints/*/optimizer.pt`) & final duplicate | **~29.59 GB** |
| **H** | **SAFE DELETE — DUPLICATE** | Redundant intermediate YOLO epoch checkpoints (`epoch0.pt` ... `epoch45.pt`) | **~3.68 GB** |
| **I** | **REVIEW REQUIRED** | Validation image previews, evaluation contact sheets, smoke test outputs | **~100 MB** |
| **J** | **DO NOT TOUCH** | Git repository objects, `.env`, dependency lock files, database schemas | **~500 MB** |

---

## 13. Exact Actionable Cleanup Candidates

### Tier 1: Immediately Safe Deletions (Reclaim **~33.29 GB**, 0% Risk to Inference)
These files are post-training byproducts (optimizer momentum tensors and non-best epoch checkpoints) that are **never used in inference** and whose training run has successfully completed:
1. **`outputs/rendering_v2_controlnet/checkpoints/checkpoint-*/optimizer.pt`** (10 files) $\to$ **26.90 GB**
2. **`outputs/rendering_v2_controlnet/controlnet_rendering_v2_final/optimizer.pt`** (1 file) $\to$ **2.69 GB**
3. **`outputs/rendering_v2_controlnet/checkpoints/checkpoint-*/{scaler.pt,scheduler.pt}`** (20 files) $\to$ **~50 KB**
4. **`runs/segment/runs/segment/runs/jewellery/yolo11m-seg-jewelmind-v2*/weights/epoch*.pt`** (20 files) $\to$ **3.43 GB**
5. **`runs/segment/runs/jewellery/yolo11m-seg-jewelmind-v1/weights/epoch*.pt`** (4 files) $\to$ **172.4 MB**
6. **`runs/segment/runs/jewellery/yolo11s-jewelmind-v2-smoke/weights/epoch0.pt`** (1 file) $\to$ **77.5 MB**
7. **Python `__pycache__` and `.pytest_cache`** $\to$ **25.4 MB**

### Tier 2: Archiving to External Cold Storage (Reclaim **~24.59 GB**)
These files represent raw historical training inputs and intermediate step weights that can be backed up externally or deleted if raw reconstruction is not needed:
1. **Intermediate ControlNet Step Weights:** `outputs/rendering_v2_controlnet/checkpoints/checkpoint-{100..900}/diffusion_pytorch_model.safetensors` (9 files) $\to$ **12.15 GB**
2. **Pre-Correction Curated Dataset:** `ai/rendering/datasets/rendering_final/` $\to$ **4.20 GB**
3. **Pre-Correction LineArt Maps:** `ai/rendering/datasets/rendering_final_conditioning/` $\to$ **2.78 GB**
4. **Raw Uncurated Images:** `ai/rendering/datasets/rendering_final_raw/` $\to$ **2.61 GB**
5. **Raw DWPose Parquet Files:** `ai/vision/datasets/raw/jewelry-dwpose/` $\to$ **1.36 GB**
6. **Curation Contact Sheets:** `datasets/curation/` $\to$ **141.08 MB**

---

## 14. Very Important Protection List (Strict Do Not Delete)

The following assets are **100% PROTECTED** and must NEVER be deleted during any cleanup:
1. **Final 1000-Step ControlNet Model:** `outputs/rendering_v2_controlnet/controlnet_rendering_v2_final/` (`diffusion_pytorch_model.safetensors`, `config.json`)
2. **Appearance LoRA Model:** `outputs/appearance_lora/jewellery_lora_final/` (`adapter_model.safetensors`, `adapter_config.json`)
3. **Preserved 300-Step Baseline ControlNet:** `outputs/controlnet_jewellery_300/controlnet_jewellery_final/`
4. **YOLO V1 Best Model:** `runs/segment/runs/jewellery/yolo11m-seg-jewelmind-v1/weights/best.pt`
5. **YOLO V2 Best Model:** `runs/segment/runs/segment/runs/jewellery/yolo11m-seg-jewelmind-v2-continued/weights/best.pt`
6. **Base Diffusion Model Cache:** `models/diffusion/` (SD 1.5 + Pretrained LineArt)
7. **Final Corrected Target Dataset:** `ai/rendering/datasets/rendering_final_corrected/`
8. **Final Corrected Conditioning Dataset:** `ai/rendering/datasets/rendering_final_corrected_conditioning/`
9. **Active YOLO V2 Dataset:** `ai/vision/datasets/jewellery_v2/`
10. **Appearance LoRA Dataset:** `datasets/appearance_lora/`
11. **All Source Code, Configs, Migrations, Notebooks, and Documentation**
12. **Git Repository Objects (`.git/`) and `.env` configuration**

---

## 15. Estimated Storage After Recommended Cleanup

| Stage | Action Taken | Storage Size | Reduction |
| :--- | :--- | :---: | :---: |
| **Current State** | Read-Only Audit Completed | **69.33 GB** | — |
| **After Tier 1 Cleanup** | Delete optimizer states & intermediate YOLO epochs | **~36.04 GB** | **-33.29 GB (-48.0%)** |
| **After Tier 2 Cleanup** | Archive raw datasets & intermediate ControlNet step weights | **~11.45 GB** | **-57.88 GB (-83.5%)** |