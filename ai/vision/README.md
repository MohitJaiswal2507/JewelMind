# JewelMind Computer Vision & Component Detection Module

This module houses JewelMind's YOLO11 instance segmentation pipelines, dataset tooling, training automation, and inference services.

---

## Directory Organization

```text
ai/vision/
├── datasets/
│   ├── raw/                  # Ingested external archives (gitignored)
│   ├── processed/            # Normalized datasets (gitignored)
│   ├── sample/               # Benchmark blueprint dataset (gitignored)
│   ├── jewelmind_components/ # User-submitted sketch blueprints
│   ├── previews/             # Visual inspection polygon previews
│   └── README.md
├── models/
│   └── README.md             # Model binary storage & Git safety policy
├── training/
│   ├── configs/              # Ultralytics dataset YAML configurations
│   ├── scripts/
│   │   ├── prepare_dataset.py       # Benchmark dataset generator
│   │   ├── validate_dataset.py      # Split integrity & polygon validator
│   │   ├── visualize_annotations.py # Translucent mask overlay generator
│   │   ├── smoke_test.py            # RTX 4060 GPU smoke test
│   │   ├── benchmark_models.py      # YOLO11s-seg vs YOLO11m-seg benchmark
│   │   └── train.py                 # Full local training with resume support
│   └── README.md
├── inference/
│   ├── schemas.py            # Pydantic schemas (DetectionResult)
│   ├── detector.py           # Reusable JewelleryComponentDetector class
│   └── predict_components.py # CLI inference runner
└── evaluation/
    ├── evaluate.py           # Comprehensive mAP & qualitative evaluator
    └── README.md
```

---

## Quickstart

Verify GPU:
```powershell
python ai/vision/training/scripts/smoke_test.py
```

Run inference on a blueprint sketch:
```powershell
python ai/vision/inference/predict_components.py --source ai/vision/datasets/sample/test/images/ring_test_000.jpg --output outputs/inference/result.jpg
```

See [YOLO_TRAINING_GUIDE.md](../../docs/ai/YOLO_TRAINING_GUIDE.md) for complete 20-step instructions.
