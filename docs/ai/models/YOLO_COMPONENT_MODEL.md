# JewelMind Model Versioning Card — YOLO11 Component Detection

| Attribute | Specification |
| :--- | :--- |
| **Model Name** | `yolo11s-seg-jewelmind-v1` |
| **Model Family** | YOLO11 Instance Segmentation (`yolo11-seg`) |
| **Architecture Base** | `yolo11s-seg.pt` (COCO-pretrained weights) |
| **Ultralytics Version** | `8.4.138` |
| **PyTorch & CUDA Build** | PyTorch `2.9.0+cu130`, CUDA `13.0` |
| **Hardware Platform** | NVIDIA GeForce RTX 4060 Laptop GPU (8,188 MiB VRAM) |
| **Dataset Version** | `jewelmind-blueprint-sample-v1` (50 images, 500 masks) |
| **Class Taxonomy** | 7 Classes: `gemstone`, `ring_shank`, `ring_head`, `prong`, `bezel`, `setting`, `shoulder` |
| **Local Checkpoint Path** | `runs/jewellery/yolo11s-seg-jewelmind-v1/weights/best.pt` (Local, gitignored) |
| **Git Exclusion Status** | Verified gitignored via `.gitignore` (`*.pt`, `*.pth`, `runs/`) |

---

## Benchmark Profile (RTX 4060)

```text
Model:              YOLO11s-seg
Parameters:         10,069,525
Inference Latency:  10.62 ms / image
VRAM Allocation:    1,447.7 MiB (1.41 GiB)
FLOPs:              32.9 GFLOPs
```

---

## Checkpointing and Reproducibility

Checkpoints are saved automatically by Ultralytics during training:
- `runs/jewellery/<run-name>/weights/best.pt`: Checkpoint achieving the highest validation mask mAP.
- `runs/jewellery/<run-name>/weights/last.pt`: Saved every epoch, used to resume interrupted training via `python ai/vision/training/scripts/train.py --resume`.
- Model binaries (`.pt`, `.pth`, `.onnx`) are never committed to version control.
