# JewelMind — AI Jewellery LoRA Training Subsystem

> **ABSOLUTE RULE**: Antigravity never launches, executes, or resumes model training automatically.
> All training commands must be manually executed by the human operator on the local RTX 4060 GPU.

---

## 1. Directory Structure

```
ai/training/
├── README.md               # This execution guide and architectural contract
├── prepare_dataset.py      # Formats raw jewellery imagery into pairs with metadata
├── validate_dataset.py     # Pre-training integrity check (dimensions, corruptions, labels)
├── train_lora.py           # Standard diffusers-based LoRA trainer with gradient checkpointing
├── evaluate_lora.py        # Validates checkpoint geometry and material rendering quality
├── inference.py            # Generates test samples with merged base model + LoRA
├── checkpoints/            # (Git-ignored) Saved step weights: checkpoint-200, 400, etc.
└── logs/                   # (Git-ignored) TensorBoard event telemetry
```

---

## 2. Prerequisites for Manual Execution

1. Activate your local GPU conda environment:
   ```bash
   conda activate tgpu
   ```

2. Verify CUDA & PyTorch:
   ```bash
   python -c "import torch; print(torch.cuda.get_device_name(0), 'VRAM:', torch.cuda.get_device_properties(0).total_memory / (1024**2), 'MiB')"
   ```

3. Ensure dependencies are present:
   ```bash
   pip install peft accelerate datasets pyyaml
   ```

---

## 3. Workflow Overview

1. **Prepare Dataset**:
   ```bash
   python ai/training/prepare_dataset.py --source datasets/raw/jewellery --output datasets/jewellery_lora
   ```

2. **Validate Dataset**:
   ```bash
   python ai/training/validate_dataset.py --data_dir datasets/jewellery_lora
   ```

3. **Manual Training Launch**:
   ```bash
   python ai/training/train_lora.py --config configs/jewellery_lora.yaml
   ```

4. **Monitor VRAM**:
   Open a separate PowerShell window and run:
   ```powershell
   nvidia-smi -l 2
   ```

5. **Resume if Interrupted**:
   `train_lora.py` automatically checks `checkpoints/` and resumes from `checkpoint-last` or the highest step folder without restarting from step 1.

6. **Inference with LoRA**:
   ```bash
   python ai/training/inference.py --lora_dir models/lora/jewellery_v1 --prompt "18k yellow gold solitaire ring with diamond"
   ```
