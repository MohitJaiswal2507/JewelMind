# JewelMind Rendering V2 Paired Dataset

This directory contains the paired conditioning (Canny edge contours) and target photorealistic jewelry images across 8 canonical taxonomy categories:
- `ring`
- `earring`
- `pendant`
- `necklace`
- `bracelet`
- `bangle`
- `brooch`
- `other_jewellery`

## Dataset Structure
- `train/`: 994 paired samples (`conditioning/`, `target/`, `metadata.jsonl`)
- `val/`: 289 paired samples (`conditioning/`, `target/`, `metadata.jsonl`)
- `test/`: 146 paired samples (`conditioning/`, `target/`, `metadata.jsonl`)
- `contact_sheets/`: Multi-category verification grids
- `DATASET_MANIFEST.json`: Complete dataset split and taxonomy metadata

## Data Preparation & Validation Scripts
- `ai/vision/training/scripts/prepare_rendering_v2_dataset.py`
- `ai/vision/training/scripts/validate_rendering_v2_dataset.py`

*Note: Large image binaries in `train/`, `val/`, `test/`, and `contact_sheets/` are excluded from version control via `.gitignore`.*
