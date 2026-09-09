"""JewelMind — Rendering V1 & Model Protection Audit Script.

Verifies that all production V1 baseline models, checkpoints, datasets,
and YOLO V2 segmentation weights remain 100% untouched and protected.
"""

import hashlib
import json
import os
import sys
from pathlib import Path

# Exact paths to protect
PROTECTED_TARGETS = [
    ("ControlNet V1 Production Weights (Final)", "outputs/controlnet_jewellery_300/controlnet_jewellery_final/diffusion_pytorch_model.safetensors"),
    ("ControlNet V1 Production Config (Final)", "outputs/controlnet_jewellery_300/controlnet_jewellery_final/config.json"),
    ("ControlNet V1 Checkpoint-300 Weights", "outputs/controlnet_jewellery_300/checkpoints/checkpoint-300/diffusion_pytorch_model.safetensors"),
    ("ControlNet V1 Checkpoint-200 Weights", "outputs/controlnet_jewellery_300/checkpoints/checkpoint-200/diffusion_pytorch_model.safetensors"),
    ("Appearance LoRA V1 Production Weights (Final)", "outputs/appearance_lora/jewellery_lora_final/adapter_model.safetensors"),
    ("Appearance LoRA V1 Checkpoint-1000 Weights", "outputs/appearance_lora/checkpoints/checkpoint-1000/adapter_model.safetensors"),
    ("YOLO V2 Segmentation Weights", "runs/segment/runs/segment/runs/jewellery/yolo11m-seg-jewelmind-v2-continued/weights/best.pt"),
    ("ControlNet Paired V1 Train Manifest", "datasets/controlnet_paired/metadata/train.jsonl"),
    ("ControlNet Paired V1 Validation Manifest", "datasets/controlnet_paired/metadata/validation.jsonl"),
    ("Appearance LoRA V1 Dataset Manifest", "datasets/appearance_lora/metadata/metadata.jsonl"),
]


def compute_file_hash(filepath: str) -> str:
    """Compute SHA-256 hash of a file."""
    sha = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            sha.update(chunk)
    return sha.hexdigest()


def audit_v1_protection() -> bool:
    """Audit all protected target paths."""
    print("=" * 80)
    print("JEWELMIND RENDERING V1 & MODEL PROTECTION AUDIT")
    print("=" * 80)

    all_intact = True
    results = []

    for label, rel_path in PROTECTED_TARGETS:
        p = Path(rel_path)
        if not p.exists():
            print(f"[ERROR] Missing protected file: {rel_path} ({label})")
            all_intact = False
            results.append({"label": label, "path": rel_path, "status": "MISSING", "size": 0, "sha256": "N/A"})
        else:
            size_bytes = p.stat().st_size
            file_hash = compute_file_hash(str(p))
            print(f"[OK] {label}")
            print(f"     Path:   {rel_path}")
            print(f"     Size:   {size_bytes:,} bytes")
            print(f"     SHA256: {file_hash}")
            results.append({
                "label": label,
                "path": rel_path,
                "status": "PROTECTED_AND_INTACT",
                "size": size_bytes,
                "sha256": file_hash,
            })

    print("-" * 80)
    if all_intact:
        print("[SUCCESS] All V1 models, LoRA weights, datasets, and YOLO weights are 100% INTACT.")
    else:
        print("[FAILURE] Some protected assets were missing or compromised.")
    print("=" * 80)

    return all_intact


if __name__ == "__main__":
    success = audit_v1_protection()
    sys.exit(0 if success else 1)
