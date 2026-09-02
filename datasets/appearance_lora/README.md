# JewelMind — Appearance LoRA Training Dataset

> **ABSOLUTE BOUNDARY**: DATASET PREPARATION ONLY — TRAINING NOT EXECUTED.

## 1. Overview & Purpose
This dataset contains **164 curated, high-resolution jewellery photographs** selected through human visual curation from an initial pool of 226 candidates. It is engineered to train the **JewelMind Jewellery Appearance LoRA (Stable Diffusion 1.5)** to learn realistic jewellery textures:
- Polished yellow gold, silver, and platinum specular highlights
- Gemstone clarity, facets, and refraction
- Fine filigree, engravings, bezels, and prongs
- Clean studio object photography aesthetics

## 2. Directory Structure
```text
datasets/appearance_lora/
├── images/           # 164 original-aspect JPEG images (CAND_001.jpg...) + captions (CAND_001.txt...)
├── metadata/         # dataset_metadata.csv, metadata.jsonl, MANIFEST.json
├── splits/           # train.csv, validation.csv, train_metadata.jsonl, val_metadata.jsonl
├── validation/       # APPEARANCE_LORA_DATASET_REPORT.md
└── README.md         # This documentation
```

## 3. Split Summary
- **Training**: 147 images (90.2%)
- **Validation**: 17 images (9.8%)
- **Random Seed**: 42 (deterministic)
- **Leakage Protection**: Near-duplicate clusters partitioned atomically.

## 4. How to Regenerate
To deterministically reproduce this dataset:
```bash
python scripts/prepare_appearance_lora_dataset.py
```
