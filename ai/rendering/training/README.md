# JewelMind Generative Rendering V2 — Training & Evaluation Infrastructure

This package implements the end-to-end training and evaluation pipeline for **JewelMind Rendering V2**, fine-tuning a unified, category-aware ControlNet on the 8 canonical jewellery categories:
`ring`, `earring`, `pendant`, `necklace`, `bracelet`, `bangle`, `brooch`, and `other_jewellery`.

---

## 1. Architecture Overview

```
Conditioning Edge Map (512x512)
           +
Structured Category/Material Prompt
           ↓
+-------------------------------------------------------------+
| Stable Diffusion 1.5 (Frozen VAE, Text Encoder, Base UNet)  |
|                             +                               |
|        Category-Aware JewelMind ControlNet (Trainable)      |
+-------------------------------------------------------------+
           ↓
High-Fidelity Photorealistic Jewellery Render
```

- **Target Hardware**: NVIDIA GeForce RTX 4060 Laptop GPU (8,188 MiB VRAM).
- **VRAM Optimizations**: `fp16` mixed precision, gradient checkpointing on ControlNet & UNet, batch size = 1, gradient accumulation = 4 (effective batch = 4), native PyTorch Scaled Dot-Product Attention (SDPA), periodic VRAM cache emptying.
- **Data Isolation**: 100% isolated from Rendering V1 baseline artifacts (`outputs/controlnet_jewellery_300/`).

---

## 2. Dataset Structure

Dataset Location: `ai/vision/datasets/rendering_v2/`
- `train/` (994 pairs)
- `val/` (289 pairs)
- `test/` (146 pairs)

Every split contains:
- `conditioning/`: 512×512 8-bit RGB Canny edge maps (`[0.0, 1.0]`).
- `target/`: 512×512 8-bit RGB photorealistic images (`[-1.0, 1.0]`).
- `metadata.jsonl`: Structured JSONL records with tokenized prompts, canonical category, source, and filenames.

---

## 3. Usage & Execution Commands

### A. Lightweight Smoke Test (Verification Only)
Runs a 1-step verification pass asserting model loading, tensor shapes, gradient flow, and parameter freezing:
```bash
python ai/rendering/training/train_rendering_v2.py --config ai/rendering/training/config_rendering_v2.yaml --smoke_test
```

### B. Controlled Pilot Test (5 Steps)
Runs a 5-step pilot test verifying forward, backward, loss computation, checkpoint saving, and resume:
```bash
python ai/rendering/training/train_rendering_v2.py --config ai/rendering/training/config_rendering_v2.yaml --pilot
```

### C. Full Production Training (Manual Execution by Developer)
Runs the complete 1,000-step training loop with multi-category validation at step boundaries:
```bash
python ai/rendering/training/train_rendering_v2.py --config ai/rendering/training/config_rendering_v2.yaml
```

### D. Multi-Category Evaluation Suite
Evaluates a trained checkpoint on the held-out test split (146 samples) across all 8 canonical categories:
```bash
python ai/rendering/training/evaluate_rendering_v2.py --controlnet outputs/controlnet_rendering_v2/controlnet_rendering_v2_final
```
