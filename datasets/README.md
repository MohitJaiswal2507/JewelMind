# Datasets Management

This directory holds dataset structures for JewelMind.

> **Important Rule:** Actual large image datasets and raw data files must NEVER be committed to Git. The `.gitignore` is preconfigured to exclude bulk data files in this directory.

---

## Directory Structure
```text
datasets/
├── raw/            # Original unprocessed jewellery images and sketches (gitignored)
├── processed/      # Normalized, resized, and augmented dataset files (gitignored)
├── annotations/    # YOLO bounding box label files and split metadata
└── README.md       # Documentation (this file)
```

---

## Data Protocol
- All dataset downloads will be scripted via `scripts/` in later phases.
- Data splits: $70\%$ Training, $15\%$ Validation, $15\%$ Testing.
- Synthetic manufacturing dataset generation formulas will be fully documented.
