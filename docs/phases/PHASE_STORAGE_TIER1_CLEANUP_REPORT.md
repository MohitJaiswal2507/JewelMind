# JewelMind — Tier 1 Safe Storage Cleanup Report

**Date:** September 11, 2026  
**Phase:** Local Storage Size Optimization (Tier 1 Safe Deletions)  
**Branch:** `phase-final-renderer-integration`  
**Execution Status:** ✅ **PASS — Tier 1 Cleanup Complete & Verified**  

---

## 1. Storage Comparison Summary

| Metric | BEFORE Cleanup | AFTER Cleanup | NET RECLAIMED |
| :--- | :---: | :---: | :---: |
| **Total Folder Size** | **69.33 GB** (74,445,066,118 bytes) | **35.98 GB** (38,632,164,302 bytes) | **33.35 GB (48.1% reduction)** |
| **Total Files** | **149,646** | **148,411** | **-1,235 files** |
| **Total Directories** | **1,843** | **1,663** | **-180 directories** |

---

## 2. Deleted Artifacts Inventory

### A. ControlNet AdamW Optimizer States (10 Checkpoints)
Deleted intermediate optimizer states that were created during the 1000-step training loop:
- `outputs/rendering_v2_controlnet/checkpoints/checkpoint-100/optimizer.pt` (2.69 GB)
- `outputs/rendering_v2_controlnet/checkpoints/checkpoint-200/optimizer.pt` (2.69 GB)
- `outputs/rendering_v2_controlnet/checkpoints/checkpoint-300/optimizer.pt` (2.69 GB)
- `outputs/rendering_v2_controlnet/checkpoints/checkpoint-400/optimizer.pt` (2.69 GB)
- `outputs/rendering_v2_controlnet/checkpoints/checkpoint-500/optimizer.pt` (2.69 GB)
- `outputs/rendering_v2_controlnet/checkpoints/checkpoint-600/optimizer.pt` (2.69 GB)
- `outputs/rendering_v2_controlnet/checkpoints/checkpoint-700/optimizer.pt` (2.69 GB)
- `outputs/rendering_v2_controlnet/checkpoints/checkpoint-800/optimizer.pt` (2.69 GB)
- `outputs/rendering_v2_controlnet/checkpoints/checkpoint-900/optimizer.pt` (2.69 GB)
- `outputs/rendering_v2_controlnet/checkpoints/checkpoint-1000/optimizer.pt` (2.69 GB)  
**Subtotal Reclaimed:** **26.92 GB** (10 files)

### B. Final Model Export Redundant Optimizer State
Deleted unneeded duplicate optimizer state from final production model folder:
- `outputs/rendering_v2_controlnet/controlnet_rendering_v2_final/optimizer.pt` (2.69 GB)  
*Note: Production inference requires only `diffusion_pytorch_model.safetensors` and `config.json`.*  
**Subtotal Reclaimed:** **2.69 GB** (1 file)

### C. ControlNet Training State Metadata Artifacts
Deleted training-specific scaler and scheduler state tensors from checkpoints 100 through 1000:
- `outputs/rendering_v2_controlnet/checkpoints/checkpoint-*/scaler.pt` (10 files)
- `outputs/rendering_v2_controlnet/checkpoints/checkpoint-*/scheduler.pt` (10 files)  
**Subtotal Reclaimed:** **27.19 KB** (20 files)

### D. YOLO Intermediate Epoch Checkpoints (Preserving `best.pt`)
Deleted non-best training epoch weights across YOLO v1 and v2 training runs:
- `runs/segment/runs/segment/runs/jewellery/yolo11m-seg-jewelmind-v2/weights/epoch*.pt` (10 files @ 171.37 MB each)
- `runs/segment/runs/segment/runs/jewellery/yolo11m-seg-jewelmind-v2-continued/weights/epoch*.pt` (10 files @ 171.37 MB each)
- `runs/segment/runs/jewellery/yolo11m-seg-jewelmind-v1/weights/epoch*.pt` (4 files @ 43.11 MB - 171.38 MB)
- `runs/segment/runs/jewellery/yolo11s-jewelmind-v2-smoke/weights/epoch0.pt` (1 file @ 77.50 MB)  
**Subtotal Reclaimed:** **3.72 GB** (25 files)

### E. Python Cache Directories
Purged Python bytecode and testing caches:
- `**/__pycache__/**`
- `**/.pytest_cache/**`
- `**/.ipynb_checkpoints/**`  
**Subtotal Reclaimed:** **25.41 MB** (1,177 files / 180 directories)

---

## 3. Protected Production Assets Verification

All core production models, baseline weights, authoritative datasets, source code, and configuration files were verified intact:

| Protected Asset | Exact Path | Size | Verification Status |
| :--- | :--- | :---: | :---: |
| **Final 1000-Step ControlNet Model** | `outputs/rendering_v2_controlnet/controlnet_rendering_v2_final/diffusion_pytorch_model.safetensors` | **1.35 GB** (1,445,157,120 bytes) | ✅ **PASS (INTACT)** |
| **Final ControlNet Config** | `outputs/rendering_v2_controlnet/controlnet_rendering_v2_final/config.json` | **1.45 KB** | ✅ **PASS (INTACT)** |
| **Appearance LoRA Weights** | `outputs/appearance_lora/jewellery_lora_final/adapter_model.safetensors` | **12.20 MB** | ✅ **PASS (INTACT)** |
| **Preserved 300-Step ControlNet** | `outputs/controlnet_jewellery_300/controlnet_jewellery_final/diffusion_pytorch_model.safetensors` | **1.35 GB** | ✅ **PASS (INTACT)** |
| **YOLO V1 Best Model** | `runs/segment/runs/jewellery/yolo11m-seg-jewelmind-v1/weights/best.pt` | **43.07 MB** | ✅ **PASS (INTACT)** |
| **YOLO V2 Best Model** | `runs/segment/runs/segment/runs/jewellery/yolo11m-seg-jewelmind-v2-continued/weights/best.pt` | **43.05 MB** | ✅ **PASS (INTACT)** |
| **Base SD 1.5 UNet** | `models/diffusion/models--runwayml--stable-diffusion-v1-5/.../unet/diffusion_pytorch_model.fp16.safetensors` | **1.60 GB** | ✅ **PASS (INTACT)** |
| **LineArt Pretrained Base** | `models/diffusion/models--lllyasviel--control_v11p_sd15_lineart/.../diffusion_pytorch_model.safetensors` | **1.35 GB** | ✅ **PASS (INTACT)** |
| **Rendering Final Corrected Dataset** | `ai/rendering/datasets/rendering_final_corrected/` | **1.22 GB** (15,423 files) | ✅ **PASS (INTACT)** |
| **Rendering Final Corrected Conditioning** | `ai/rendering/datasets/rendering_final_corrected_conditioning/` | **1.30 GB** (23,126 files) | ✅ **PASS (INTACT)** |
| **Active YOLO V2 Dataset** | `ai/vision/datasets/jewellery_v2/` | **1.05 GB** (15,581 files) | ✅ **PASS (INTACT)** |
| **Appearance LoRA Dataset** | `datasets/appearance_lora/` | **23.40 MB** (337 files) | ✅ **PASS (INTACT)** |
| **Intermediate ControlNet Weights (Preserved)** | `outputs/rendering_v2_controlnet/checkpoints/checkpoint-{100..1000}/diffusion_pytorch_model.safetensors` | **13.50 GB** (10 $\times$ 1.35 GB) | ✅ **PASS (INTACT)** |

---

## 4. Tier 2 Datasets & Weights Protection (Untouched)

As instructed, Tier 2 archival candidates were **100% untouched and preserved on disk**:
- `ai/rendering/datasets/rendering_final/` (4.20 GB) — **Preserved**
- `ai/rendering/datasets/rendering_final_conditioning/` (2.78 GB) — **Preserved**
- `ai/rendering/datasets/rendering_final_raw/` (2.61 GB) — **Preserved**
- `ai/vision/datasets/raw/jewelry-dwpose/` (1.36 GB) — **Preserved**
- `datasets/curation/` (141.08 MB) — **Preserved**
- All 10 intermediate ControlNet model weights — **Preserved**

---

## 5. Git Safety Verification

- **Current Branch:** `phase-final-renderer-integration`
- **Working Tree State:** Clean local state (zero source code modifications made for cleanup)
- **Staging / Commits:** **0 files staged, 0 commits created, 0 pushes executed**
