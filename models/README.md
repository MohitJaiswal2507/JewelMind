# Model Weights & Artifacts Registry

This directory is the local repository for model checkpoints and serializations.

> **Important Rule:** Trained neural network weights, safetensors, and checkpoints (`.pt`, `.pth`, `.safetensors`, `.onnx`, `.bin`) must NEVER be committed to version control. The `.gitignore` excludes all model binary formats.

---

## Planned Model Registry
- `yolo/`: Trained custom YOLO weights for component detection (`best.pt`).
- `diffusion/`: Base checkpoints and LoRA weights for jewellery photorealistic rendering.
- `prediction/`: Serialized XGBoost estimators (`.joblib` / `.json`) for material, cost, time, and wastage prediction.
- `evaluation/`: Model performance summaries and confusion matrices.
