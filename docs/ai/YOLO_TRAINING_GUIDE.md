# JewelMind — YOLO11 Instance Segmentation Training Guide

This guide provides a step-by-step walkthrough for an undergraduate developer training JewelMind's jewellery component detector locally on Windows using an **NVIDIA GeForce RTX 4060 Laptop GPU (8GB VRAM)**.

---

## Prerequisites & Hardware Context
- **Operating System:** Windows 11
- **Target GPU:** NVIDIA GeForce RTX 4060 Laptop GPU (8,188 MiB VRAM)
- **Conda Environment:** `tgpu` (`C:\Users\usern\miniconda3\envs\tgpu`)
- **PyTorch Build:** `2.9.0+cu130` with CUDA acceleration
- **Ultralytics Version:** `8.4.138` (installed via `uv`)

---

## 20-Step Training & Inference Workflow

### Step 1: Open Terminal in Project Directory
Launch PowerShell or Windows Terminal and navigate to the JewelMind root:
```powershell
cd c:\Users\usern\Desktop\JewelMind
```

### Step 2: Activate the Python Training Environment
Activate the preconfigured `tgpu` Conda environment:
```powershell
conda activate tgpu
```
*(Or specify the absolute interpreter path: `C:\Users\usern\miniconda3\envs\tgpu\python.exe`)*

### Step 3: Verify Python & Package Tooling
Confirm your environment and tools:
```powershell
python --version
# Expected: Python 3.10.x
uv --version
# Expected: uv 0.11.x
```

### Step 4: Verify RTX 4060 and CUDA Acceleration
Run `nvidia-smi` and verify PyTorch can access your GPU:
```powershell
nvidia-smi
python -c "import torch; print('CUDA Available:', torch.cuda.is_available()); print('Device:', torch.cuda.get_device_name(0)); print('VRAM (GB):', round(torch.cuda.get_device_properties(0).total_memory / 1024**3, 2))"
```
> [!IMPORTANT]
> If `CUDA Available` returns `False`, stop immediately. Do not attempt training on CPU.

### Step 5: Install Required Dependencies (If Setting Up Fresh)
Dependencies are managed via `uv`:
```powershell
uv pip install --python C:\Users\usern\miniconda3\envs\tgpu\python.exe ultralytics pydantic pytest opencv-python pyyaml
```

### Step 6: Prepare/Verify the Dataset
To generate or re-seed the benchmark blueprint dataset:
```powershell
python ai/vision/training/scripts/prepare_dataset.py
```
This prepares a balanced 70% train, 20% validation, 10% test split at `ai/vision/datasets/sample/`.

### Step 7: Validate Annotations & Contours
Run the dataset integrity validator:
```powershell
python ai/vision/training/scripts/validate_dataset.py --config ai/vision/training/configs/jewellery_components.yaml
```
Verify that the output displays `DATASET VALIDATION SUMMARY: PASS` with `Errors Found: 0`.

### Step 8: Visually Inspect Ground-Truth Annotations
Generate visual inspection preview images with color-coded polygon masks:
```powershell
python ai/vision/training/scripts/visualize_annotations.py --config ai/vision/training/configs/jewellery_components.yaml --samples 5
```
Open `ai/vision/datasets/previews/` in Windows File Explorer. Confirm that:
- Gemstones are enclosed in cyan contours.
- Ring shanks have continuous orange masks.
- Prongs appear as small magenta tabs.
- Bezels appear as green rings.

### Step 9: Run the 1-Epoch GPU Smoke Test
Run the fast safety check to ensure your RTX 4060 can complete forward and backward passes without VRAM errors:
```powershell
python ai/vision/training/scripts/smoke_test.py
```
*Expected: Completion in ~25 seconds with ~1.4 GB VRAM allocated and >6.6 GB headroom.*

### Step 10: Benchmark YOLO11s-seg vs YOLO11m-seg
Run the comparative benchmark to review performance metrics:
```powershell
python ai/vision/training/scripts/benchmark_models.py --epochs 1 --batch 4
```
Results summary:
- **YOLO11s-seg:** 10.1M params, ~1.41 GB peak VRAM, ~10.6 ms inference latency. Ideal for interactive canvas feedback.
- **YOLO11m-seg:** 22.3M params, ~2.63 GB peak VRAM, ~18.5 ms inference latency. Ideal for batch blueprint extraction.

---

### Step 11: START REAL TRAINING MANUALLY
You are now ready to launch the full fine-tuning run!

To train **YOLO11s-seg** (Recommended baseline for RTX 4060):
```powershell
python ai/vision/training/scripts/train.py --model yolo11s-seg.pt --data ai/vision/training/configs/jewellery_components.yaml --epochs 50 --batch 8 --imgsz 640 --device 0 --name yolo11s-seg-jewelmind-v1
```

To train **YOLO11m-seg** (Higher capacity):
```powershell
python ai/vision/training/scripts/train.py --model yolo11m-seg.pt --data ai/vision/training/configs/jewellery_components.yaml --epochs 50 --batch 4 --imgsz 640 --device 0 --name yolo11m-seg-jewelmind-v1
```

---

### Step 12: Monitor GPU in Real-Time
Open a separate PowerShell terminal window and run:
```powershell
nvidia-smi -l 2
```
What to observe:
- **GPU Utilization:** Typically oscillating between $70\%-98\%$ during training batches.
- **Memory-Usage:** Should remain stable between $1,500\text{ MiB}$ and $3,500\text{ MiB}$ (well below the $8,188\text{ MiB}$ capacity).
- **Temperature:** Should remain between $55^\circ\text{C}$ and $78^\circ\text{C}$.
- **Power Usage:** Fluctuating around $40\text{W}-85\text{W}$.

---

### Step 13: Understand Training Output
During training, Ultralytics prints epoch progress:
```text
Epoch   GPU_mem   box_loss   seg_loss   cls_loss   dfl_loss   Instances   Size
 1/50     1.48G      1.459      3.568      4.058      1.348          37    640
```
- `seg_loss`: Segmentation mask polygon loss (decreases as contours improve).
- `box_loss`: Bounding box regression loss.
- `cls_loss`: Component category cross-entropy loss.

### Step 14: Stop Safely (Interrupt Handling)
To pause or stop training at any time, press `Ctrl + C` in the training terminal.
Ultralytics automatically finishes the active batch and writes the current weights to:
`runs/jewellery/<run-name>/weights/last.pt`

---

## Resuming Interrupted Training (Section 17A)

If training is interrupted due to a power outage, computer reboot, or manual `Ctrl+C`, you do **NOT** need to restart from epoch 0.

### Workflow:
1. Re-open terminal and activate the environment:
   ```powershell
   conda activate tgpu
   ```
2. Verify that `last.pt` exists:
   ```powershell
   Test-Path runs/jewellery/yolo11s-seg-jewelmind-v1/weights/last.pt
   ```
3. Resume training using the `--resume` flag:
   ```powershell
   python ai/vision/training/scripts/train.py --resume --project runs/jewellery --name yolo11s-seg-jewelmind-v1
   ```
4. Verify in the output logs that training picks up at `Epoch (N+1)` and does not restart from `Epoch 1`.

---

### Step 15: Checkpoint Locations
Checkpoints are preserved under:
```text
runs/jewellery/<run-name>/
├── weights/
│   ├── best.pt    # Best validation mAP checkpoint
│   └── last.pt    # Most recent epoch checkpoint for resuming
├── results.csv    # Per-epoch loss and mAP metrics
└── results.png    # Metric convergence curves
```

### Step 16: Evaluate the Trained Model
Run the quantitative evaluation suite:
```powershell
python ai/vision/evaluation/evaluate.py --model runs/jewellery/yolo11s-seg-jewelmind-v1/weights/best.pt --split val
```
This saves `ai/vision/evaluation/eval_metrics.json` recording Box and Mask mAP50 and mAP50-95.

### Step 17: Run Inference on Blueprint Sketches
Perform component detection on a sketch:
```powershell
python ai/vision/inference/predict_components.py --model runs/jewellery/yolo11s-seg-jewelmind-v1/weights/best.pt --source ai/vision/datasets/sample/test/images/ring_test_000.jpg --output outputs/inference/my_prediction.jpg --json_output outputs/inference/my_prediction.json
```

### Step 18: Inspect Prediction Visualizations
Open `outputs/inference/my_prediction.jpg` to inspect the detected component contours and classification confidence.

### Step 19: Diagnose Failure Cases
Compare detections against the diagnostic rubric:
- **Good Detection:** High overlap ($\text{IoU} \ge 0.70$) hugging gemstone and shank borders.
- **Missed Component:** Small prong not segmented.
- **False Positive:** Canvas grid lines misclassified as a setting.

### Step 20: Git Safety Reminder
Confirm that no large model weights or datasets are staged:
```powershell
git status
git ls-files "*.pt"
git ls-files .env
```
All weights and checkpoints are safely excluded by `.gitignore`.
