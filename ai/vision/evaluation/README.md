# JewelMind Vision Evaluation Module

Provides tools to evaluate YOLO instance segmentation models against test and validation datasets.

## Script
- `evaluate.py`: Computes precision, recall, Box/Mask mAP50, Box/Mask mAP50-95, per-class breakdown, and qualitative error categorization.

Usage:
```powershell
python ai/vision/evaluation/evaluate.py --model runs/jewellery/yolo11s-seg-jewelmind-v1/weights/best.pt --split val
```
Outputs:
`eval_metrics.json`
