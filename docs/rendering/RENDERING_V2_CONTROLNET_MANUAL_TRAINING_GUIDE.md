# JewelMind — Rendering V2 ControlNet Manual Training Guide
**Complete Step-by-Step Operator Guide for NVIDIA RTX 4060 (8GB VRAM) Execution**

---

## 1. Overview & Operational Principles

This document provides exact, copy-paste terminal commands to execute the **JewelMind Multi-Category ControlNet V2 Training** manually on your local workstation.

### Golden Rules & Safety Invariants:
1. **Isolated Output Directories:** All V2 training artifacts are written strictly to `outputs/rendering_v2_controlnet/` or `outputs/rendering_v2_controlnet_pilot/`.
2. **Untouched Baseline:** Production V1 models (`outputs/controlnet_jewellery_300/`), Appearance LoRA V1, and YOLO V2 weights will NEVER be modified or overwritten.
3. **Clean Initialization:** ControlNet V2 initializes cleanly from `lllyasviel/control_v11p_sd15_lineart` (local snapshot in `models/diffusion/`).
4. **VRAM Safety (8 GB RTX 4060):** Batch Size = 1, Gradient Accumulation = 4 (effective batch size = 4), FP16 mixed precision, SDPA attention.

---

## 2. Training Decision Tree

```
                      +-----------------------------+
                      |   Stage 0: Environment &    |
                      |    Dataset Verification     |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      |   Stage 1: 10-Step Smoke    |
                      |   Test (Verify Sanity)      |
                      +--------------+--------------+
                                     |
                             [If Successful]
                                     |
                                     v
                      +-----------------------------+
                      |   Stage 2: 100-Step Pilot   |
                      |    (Check VRAM & Loss)      |
                      +--------------+--------------+
                                     |
                             [If Loss Healthy]
                                     |
                                     v
                      +-----------------------------+
                      |   Stage 3: Main Training    |
                      |   (Steps 100 -> 300 / 500)  |
                      +--------------+--------------+
                                     |
                         [Evaluate Checkpoint-300]
                                     |
                  +------------------+------------------+
                  |                                     |
         [If Converged & Sharp]                 [If Still Improving]
                  |                                     |
                  v                                     v
       +--------------------+                +--------------------+
       | Stop Training &    |                | Continue Toward    |
       | Proceed to LoRA V2 |                | 600 / 1000 Steps   |
       +--------------------+                +--------------------+
```

> [!NOTE]
> **Candidate Stopping Points:** Do NOT assume 500 or 1000 steps is automatically optimal. Evaluate validation loss and structural clarity at Step 300, 500, and 600. If the model exhibits clean geometry and stable loss, stop to prevent overfitting.

---

## 3. Step-by-Step Execution Commands

> **Terminal Preparation (PowerShell):**  
> Ensure you are at the project root: `c:\Users\usern\Desktop\JewelMind`  
> Python executable: `C:\Users\usern\miniconda3\envs\tgpu\python.exe`

---

### A. Environment & Hardware Verification
Run this command to confirm that PyTorch detects the NVIDIA RTX 4060 GPU with CUDA acceleration:
```powershell
C:\Users\usern\miniconda3\envs\tgpu\python.exe -c "
import torch, diffusers, transformers
print('PyTorch Version:   ', torch.__version__)
print('CUDA Available:    ', torch.cuda.is_available())
if torch.cuda.is_available():
    print('Device Name:       ', torch.cuda.get_device_name(0))
    print('VRAM Total (GB):   ', round(torch.cuda.get_device_properties(0).total_memory / 1e9, 2))
print('Diffusers Version: ', diffusers.__version__)
print('Transformers:      ', transformers.__version__)
"
```

---

### B. Dataset & V1 Protection Verification
Verify dataset integrity (961 pairs across 8 classes) and confirm that all V1 production checkpoints are locked and intact:
```powershell
# 1. Verify Dataset Structure & Zero Leakage
C:\Users\usern\miniconda3\envs\tgpu\python.exe -c "
import os, json
data_dir = 'ai/rendering/datasets/rendering_v2'
for split, expected in [('train', 664), ('val', 152), ('test', 145)]:
    meta = os.path.join(data_dir, split, 'metadata.jsonl')
    with open(meta, 'r', encoding='utf-8') as f:
        count = len([line for line in f if line.strip()])
    print(f'Split {split.upper()}: {count}/{expected} samples -> PASS' if count == expected else f'FAIL {count}')
"

# 2. Verify V1 Checkpoint Protection
C:\Users\usern\miniconda3\envs\tgpu\python.exe scripts/verify_v1_protection.py
```

---

### C. Stage 1 — 10-Step Smoke Test
Runs a rapid 10-step smoke test using `ai/rendering/training/configs/rendering_v2_controlnet_smoke.yaml`:
```powershell
C:\Users\usern\miniconda3\envs\tgpu\python.exe ai/rendering/training/train_rendering_v2.py --config ai/rendering/training/configs/rendering_v2_controlnet_smoke.yaml
```
* **Expected Output Directory:** `outputs/rendering_v2_controlnet_smoke/`
* **Success Criteria:** Exit code 0, peak VRAM < 6.5 GB, non-NaN loss logged, checkpoint saved in `checkpoints/checkpoint-10/`.

---

### D. Stage 2 — 100-Step Pilot Run
Executes a controlled 100-step pilot on the training set:
```powershell
C:\Users\usern\miniconda3\envs\tgpu\python.exe ai/rendering/training/train_rendering_v2.py --config ai/rendering/training/configs/rendering_v2_controlnet_pilot.yaml
```
* **Expected Output Directory:** `outputs/rendering_v2_controlnet_pilot/`
* **Checkpoints:** `checkpoints/checkpoint-50/` and `checkpoints/checkpoint-100/`
* **Validation Previews:** `outputs/rendering_v2_controlnet_pilot/validation/step-0050/` and `step-0100/`

---

### E. Stage 3 — Main ControlNet V2 Training
Runs the full multi-category ControlNet V2 training pipeline:
```powershell
C:\Users\usern\miniconda3\envs\tgpu\python.exe ai/rendering/training/train_rendering_v2.py --config ai/rendering/training/configs/rendering_v2_controlnet.yaml
```
* **Expected Output Directory:** `outputs/rendering_v2_controlnet/`
* **Checkpoints:** Saved every 100 steps (`checkpoint-100`, `checkpoint-200`, `checkpoint-300`, etc.)
* **Multi-Category Validation:** Automatically generated every 100 steps across all 8 canonical categories.

---

### F. Resume Training from Checkpoint
If training was interrupted or you wish to extend training beyond step 300:
```powershell
# Option 1: Automatically resume from latest checkpoint
C:\Users\usern\miniconda3\envs\tgpu\python.exe ai/rendering/training/train_rendering_v2.py --config ai/rendering/training/configs/rendering_v2_controlnet.yaml --resume latest

# Option 2: Resume from specific checkpoint (e.g., step 300) with new step ceiling (e.g., 500)
C:\Users\usern\miniconda3\envs\tgpu\python.exe ai/rendering/training/train_rendering_v2.py --config ai/rendering/training/configs/rendering_v2_controlnet.yaml --resume outputs/rendering_v2_controlnet/checkpoints/checkpoint-300 --max_train_steps 500
```

---

### G. Held-Out Test Evaluation
Evaluate the trained ControlNet V2 checkpoint against the 145 held-out test samples:
```powershell
C:\Users\usern\miniconda3\envs\tgpu\python.exe ai/rendering/evaluation/evaluate_controlnet_v2.py --controlnet_path outputs/rendering_v2_controlnet/checkpoints/checkpoint-300 --output_dir outputs/rendering_v2_controlnet/eval_test_300
```
* **Outputs:** `evaluation_results.csv`, `category_summary.csv`, and rendered images in `generated_samples/`.

---

### H. V1 Production Baseline vs V2 Candidate Comparison
Generate side-by-side visual contact sheets comparing V1 vs V2 under identical prompt, seed, and inference parameters:
```powershell
C:\Users\usern\miniconda3\envs\tgpu\python.exe ai/rendering/evaluation/compare_v1_v2.py --v1_controlnet_path outputs/controlnet_jewellery_300/controlnet_jewellery_final --v2_controlnet_path outputs/rendering_v2_controlnet/checkpoints/checkpoint-300 --output_dir outputs/rendering_v2_controlnet/v1_vs_v2_comparison
```
* **Outputs:** Side-by-side comparison images (`compare_<category>_<sample_id>.png`) saved in `outputs/rendering_v2_controlnet/v1_vs_v2_comparison/`.

---

### I. Real-Time GPU & VRAM Monitoring
Open a second PowerShell window to watch GPU utilization and temperature during training:
```powershell
nvidia-smi -l 2
```

---

## 4. Post-Training Analysis Notebook

Once you have completed manual training:
1. Open and run the pre-configured analysis notebook:  
   [`ai/rendering/notebooks/Rendering_V2_ControlNet_Training_Analysis.ipynb`](file:///c:/Users/usern/Desktop/JewelMind/ai/rendering/notebooks/Rendering_V2_ControlNet_Training_Analysis.ipynb)
2. The notebook will automatically ingest your saved `trainer_state.json` logs, plot loss curves, display validation samples across all 8 classes, and compare V1 vs V2.
