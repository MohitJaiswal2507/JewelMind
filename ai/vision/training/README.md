# JewelMind Vision Training Infrastructure

This directory contains the training and benchmarking pipeline for YOLO11 instance segmentation:

## Scripts
- `scripts/prepare_dataset.py`: Synthesizes or normalizes jewellery blueprint segmentation datasets.
- `scripts/validate_dataset.py`: Checks polygon coordinate bounds $[0, 1]$, non-degeneracy, missing labels, and split leakage.
- `scripts/visualize_annotations.py`: Renders ground-truth polygon overlays to `ai/vision/datasets/previews/`.
- `scripts/smoke_test.py`: Fast 1-epoch GPU verification on RTX 4060 `device=0`.
- `scripts/benchmark_models.py`: Comparative benchmark measuring parameters, VRAM, and latency for `yolo11s-seg.pt` vs `yolo11m-seg.pt`.
- `scripts/train.py`: Full fine-tuning pipeline with checkpointing, early stopping, and `last.pt` resume support.

## Configs
- `configs/jewellery_components.yaml`: Ultralytics dataset definition and 7-class taxonomy.
