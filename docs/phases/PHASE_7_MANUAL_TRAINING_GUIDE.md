# JewelMind — Phase 7: Manual Jewellery LoRA Training Guide
# Local Execution Instructions for NVIDIA GeForce RTX 4060 (8 GB VRAM)

> **MANDATORY POLICY**: Antigravity never launches or executes model training automatically.
> All training commands must be executed manually by the human operator using the step-by-step instructions below.

---

## 1. Hardware Budget & Operating Constraints

| Parameter | Specification | Training Implication |
| :--- | :--- | :--- |
| **GPU** | NVIDIA GeForce RTX 4060 Laptop GPU | 3,072 CUDA cores, Ada Lovelace architecture |
| **VRAM** | 8,188 MiB (8 GB) GDDR6 | Net available under Windows WDDM is ~6.1 GB |
| **Target Architecture** | Stable Diffusion 1.5 + UNet LoRA (PEFT) | Low Rank Adaptation targeting cross-attention projections |
| **Precision** | Float16 (`fp16`) | Halves model weight & activation footprint |
| **Batch Size** | 1 (with Gradient Accumulation = 4) | Prevents VRAM exhaustion while maintaining effective batch size 4 |
| **Gradient Checkpointing** | **ENABLED** | Essential: drops UNet activation memory from ~7.5 GB to ~4.2 GB |
| **Expected Peak VRAM** | **~4.5 GB to 5.2 GB** | Safe operation within 8 GB envelope without shared RAM thrashing |

---

## 2. Environment Activation & Dependencies

Open an Anaconda PowerShell Prompt or Windows Terminal and execute:

```powershell
# Step 1: Activate the existing Phase 6 CUDA environment
conda activate tgpu

# Step 2: Verify Python, PyTorch, and CUDA device recognition
python -c "import torch; print('PyTorch:', torch.__version__, '| CUDA:', torch.cuda.is_available(), '| Device:', torch.cuda.get_device_name(0))"
```
*Expected Output: `PyTorch: 2.x.x | CUDA: True | Device: NVIDIA GeForce RTX 4060 Laptop GPU`*

```powershell
# Step 3: Ensure training dependencies are installed
pip install peft accelerate datasets pyyaml
```

---

## 3. Dataset Folder Structure

Organize your raw jewellery images (photographs, CAD renders, or clean sketches with target renders) into the following directory layout:

```
JewelMind/
└── datasets/
    ├── raw/
    │   └── jewellery/
    │       ├── ring_solitaire_01.jpg
    │       ├── pendant_sapphire_02.png
    │       └── bracelet_gold_03.jpg
    └── jewellery_lora/       <-- Generated automatically by prepare_dataset.py
        ├── train/
        │   ├── train_0001.jpg
        │   ├── train_0002.jpg
        │   └── metadata.jsonl
        └── val/
            ├── val_0001.jpg
            └── metadata.jsonl
```

### Dataset Preparation Command
```powershell
cd C:\Users\usern\Desktop\JewelMind

# Prepare and letterbox images to 512x512 with captions
python ai/training/prepare_dataset.py --source datasets/raw/jewellery --output datasets/jewellery_lora --val_ratio 0.1
```

### Dataset Validation Command
```powershell
# Verify image integrity, aspect ratios, and JSONL format
python ai/training/validate_dataset.py --data_dir datasets/jewellery_lora
```

---

## 4. Manual Training Execution

> **DO NOT start until you have closed heavy GPU applications (games, 3D CAD, local LLMs).**

### Recommended Hyperparameters (`configs/jewellery_lora.yaml`)
* **Base Model**: `runwayml/stable-diffusion-v1-5`
* **LoRA Rank ($r$)**: `16`
* **LoRA Alpha ($\alpha$)**: `32`
* **Learning Rate**: `1e-4` with cosine schedule
* **Batch Size**: `1`
* **Gradient Accumulation**: `4` steps
* **Gradient Checkpointing**: `true`
* **Checkpoint Interval**: Every `200` steps

### Exact Manual Training Command
```powershell
# Launch the training script on local GPU
python ai/training/train_lora.py --config configs/jewellery_lora.yaml
```

---

## 5. GPU Monitoring During Training

In a second terminal window, run:
```powershell
nvidia-smi -l 2
```
Verify that:
1. `Memory-Usage` remains below **6,200 MiB / 8,188 MiB**.
2. GPU compute utilization fluctuates between 60% and 95%.
3. If VRAM exceeds 7,800 MiB, immediately press `Ctrl + C` in the training terminal.

---

## 6. Checkpointing, Interruptions & Resuming

Training checkpoints are automatically written to:
```
models/lora/jewellery_v1/checkpoints/
├── checkpoint-200/
│   ├── adapter_config.json
│   └── adapter_model.safetensors
├── checkpoint-400/
├── checkpoint-last/       <-- Always points to the most recent completed step
```

### How to Stop Safely
Press `Ctrl + C` once in the training terminal. PyTorch will complete the current backward step and flush the latest checkpoint.

### How to Resume Without Restarting from Step 1
`train_lora.py` natively detects existing checkpoints. To resume from the latest saved step:
```powershell
python ai/training/train_lora.py --config configs/jewellery_lora.yaml --resume models/lora/jewellery_v1/checkpoints/checkpoint-last
```
The script will log:
```
Resuming training from checkpoint: ...\checkpoint-400
Successfully resumed at step: 400 (skipping steps 0 to 400)
```

---

## 7. How to Recognize Successful Completion

When training reaches `max_train_steps` (1000 steps), the script will output:
```
Training complete! Saving final LoRA weights to: models/lora/jewellery_v1/jewellery_lora_final
SUCCESS: LoRA weights ready for inference.
```
The final LoRA bundle will contain:
* `adapter_config.json` (~600 bytes)
* `adapter_model.safetensors` (~3.2 MB)

---

## 8. Validation & Inference with Trained LoRA

### Test Standalone LoRA Generation
```powershell
python ai/training/evaluate_lora.py --lora_dir models/lora/jewellery_v1/jewellery_lora_final
```

### Test LoRA + ControlNet Conditioning on a Jewellery Sketch
```powershell
python ai/training/inference.py --sketch ai/vision/datasets/sample/train/images/ring_train_000.jpg --lora_dir models/lora/jewellery_v1/jewellery_lora_final --prompt "photorealistic fine jewellery solitaire ring, 18k yellow gold with round diamond, studio lighting" --output outputs/lora_test_render.png
```

### Rollback Procedure
If the fine-tuned LoRA introduces artifacts or overfits (e.g. garbled gemstones or distorted ring bands), simply omit `--lora_dir` or delete `models/lora/jewellery_v1/`. The core JewelMind pipeline immediately falls back to pristine base Stable Diffusion 1.5.

---

## 9. What to Return to the Assistant After Training

Once you finish manual training, share the following summary in the chat:
1. **Total steps completed** (e.g. 1,000 steps).
2. **Peak VRAM observed** in `nvidia-smi` (e.g. 4,850 MiB).
3. **Training duration** (e.g. 24 minutes).
4. **Final loss value** (e.g. 0.082).
5. **Visual assessment** of `eval_lora_sample_1.png` and `outputs/lora_test_render.png`.
