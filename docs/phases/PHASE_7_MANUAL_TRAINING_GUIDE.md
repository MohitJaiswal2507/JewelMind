# JewelMind — Phase 7: Manual Jewellery LoRA Training Guide
# Local Execution Instructions for NVIDIA GeForce RTX 4060 (8 GB VRAM)

> **MANDATORY POLICY**: Antigravity never launches, schedules, resumes, or executes model training automatically.
> All training commands must be executed manually by the human operator using the step-by-step instructions below.

---

## 1. Hardware Budget & Operating Constraints

| Parameter | Specification | Training Implication |
| :--- | :--- | :--- |
| **GPU** | NVIDIA GeForce RTX 4060 Laptop GPU | 3,072 CUDA cores, Ada Lovelace architecture |
| **Total VRAM** | 8,188 MiB (8 GB) GDDR6 | Net usable VRAM under Windows WDDM is ~6.1 GB |
| **Target Architecture** | Stable Diffusion 1.5 + UNet LoRA (PEFT) | Low Rank Adaptation targeting cross-attention projections (`to_k`, `to_q`, `to_v`, `to_out.0`) |
| **Precision** | Float16 (`fp16`) | Halves model weights and activation memory |
| **Batch Size** | 1 (with Gradient Accumulation = 4) | Strictly batch size 1 to prevent CUDA OOM on 8GB hardware |
| **Gradient Checkpointing** | **ENABLED** | Essential: drops UNet activation memory footprint significantly |
| **Measured Inference VRAM** | **3,410.4 MiB (3.33 GiB)** | Measured empirically during Phase 7 smoke test (forward pass only) |
| **Estimated Training VRAM** | **~4.2 GB to ~5.2 GB (Estimated)** | Higher than inference due to backward pass activations and optimizer states; expected to fit within 6.1 GB net window |

---

## 2. Environment Activation & Dependencies

Open an Anaconda PowerShell Prompt or Windows Terminal and execute:

```powershell
# Step 1: Activate the existing Phase 6/7 CUDA environment
conda activate tgpu

# Step 2: Verify Python, PyTorch, and CUDA device recognition
python -c "import torch; print('PyTorch:', torch.__version__, '| CUDA:', torch.cuda.is_available(), '| Device:', torch.cuda.get_device_name(0))"
```
*Expected Output: `PyTorch: 2.x.x | CUDA: True | Device: NVIDIA GeForce RTX 4060 Laptop GPU`*

```powershell
# Step 3: Ensure required training packages are present
pip install peft accelerate datasets pyyaml
```

---

## 3. Dataset Requirements & Preparation

> **CRITICAL DATASET NOTICE**:  
> Do NOT train this model on the 35 Phase 6 YOLO sketches. Training on black-and-white sketches will corrupt the diffusion prior.  
> Prepare a dataset of **150–200 high-quality photorealistic jewellery images** (clean white background, centered rings/pendants/earrings) before running the training script.

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

> **Pre-flight check**: Close all heavy GPU software (games, 3D CAD, local LLMs) before launching training.

### Step Sizing Formula (Do Not Blindly Use 1000 Steps)
With `train_batch_size: 1` and `gradient_accumulation_steps: 4`, every optimizer step consumes **4 images**.

$$\text{Steps per Epoch} = \left\lceil \frac{N_{\text{train}}}{4} \right\rceil$$
$$\text{Max Train Steps} = \text{Target Epochs} \times \text{Steps per Epoch}$$

* **For 160 train images**: $\text{Steps/epoch} = 40$. Target 20–25 epochs $\to$ `max_train_steps: 800 - 1000`.
* **For 100 train images**: $\text{Steps/epoch} = 25$. Target 20–25 epochs $\to$ `max_train_steps: 500 - 625`.
* **For 50 train images**: $\text{Steps/epoch} = 13$. Target 20–25 epochs $\to$ `max_train_steps: 260 - 325`.

Edit `configs/jewellery_lora.yaml` to set `max_train_steps` according to your finalized image count.

### Exact Manual Training Command
```powershell
# Launch the training script manually on local GPU
python ai/training/train_lora.py --config configs/jewellery_lora.yaml
```

---

## 5. GPU Monitoring During Training

In a second terminal window, run:
```powershell
nvidia-smi -l 2
```
Monitor:
1. `Memory-Usage`: Expected to operate around **4,200 MiB – 5,200 MiB**.
2. If VRAM exceeds **7,600 MiB**, press `Ctrl + C` immediately to avoid Windows shared memory paging.

---

## 6. Checkpointing, Interruptions & Resuming

Checkpoints are automatically saved to `models/lora/jewellery_v1/checkpoints/`:
```
checkpoints/
├── checkpoint-200/
│   ├── adapter_config.json
│   ├── adapter_model.safetensors
│   ├── optimizer.pt               <-- Restores AdamW momentum buffers
│   ├── scheduler.pt               <-- Restores cosine LR schedule
│   ├── scaler.pt                  <-- Restores GradScaler state
│   └── trainer_state.json         <-- Stores global_step & epoch
└── checkpoint-last/               <-- Mirrored latest checkpoint
```

### Stopping Safely
Press `Ctrl + C` once in the training console. PyTorch will complete the active step and cleanly exit.

### Resuming Without Losing State
To resume from the latest saved checkpoint:
```powershell
python ai/training/train_lora.py --config configs/jewellery_lora.yaml --resume latest
```
Or specify an explicit folder:
```powershell
python ai/training/train_lora.py --config configs/jewellery_lora.yaml --resume models/lora/jewellery_v1/checkpoints/checkpoint-last
```
The script will log:
```
Resuming training from checkpoint: ...\checkpoint-200
Restored optimizer momentum and state.
Restored learning rate scheduler state.
Successfully resumed at optimizer step 200 / 1000 (epoch 5)
```

---

## 7. How to Recognize Successful Completion

When training reaches `max_train_steps`, the script will output:
```
Training complete! Saving final LoRA weights to: models/lora/jewellery_v1/jewellery_lora_final
SUCCESS: LoRA weights ready for inference.
```

---

## 8. Manual Evaluation Command

After training completes, evaluate the LoRA checkpoint on test prompts:
```powershell
python ai/training/evaluate_lora.py `
  --lora_dir models/lora/jewellery_v1/jewellery_lora_final `
  --output_dir outputs/evaluation/manual_run_01
```
