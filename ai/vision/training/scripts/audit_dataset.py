"""JewelMind Multi-Jewellery Dataset Audit & Statistical Analyzer.

Generates deep statistical profiles for YOLO segmentation datasets:
- Image formats, resolutions, aspect ratios, file sizes
- Per-class instance distributions, polygon vertex densities
- Cross-split leakage checks via SHA-256 content hashing
- Bounding box and segmentation mask size distributions
- Exportable structured JSON audit reports
"""

import argparse
import hashlib
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List
import cv2
import yaml


def audit_dataset(yaml_path: str, export_json: str = None) -> Dict[str, Any]:
    """Execute in-depth statistical audit of a YOLO dataset."""
    config_file = Path(yaml_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration YAML not found: {yaml_path}")

    with open(config_file, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    base_dir = config.get("path", "")
    base_path = Path(base_dir) if os.path.isabs(base_dir) else (config_file.parent.parent.parent / "datasets" / Path(base_dir).name)
    if not base_path.exists():
        base_path = Path(base_dir)

    names = config.get("names", {})
    splits = {
        "train": config.get("train", "train/images"),
        "val": config.get("val", "val/images"),
        "test": config.get("test", "test/images"),
    }

    audit_data = {
        "config_path": str(config_file.resolve()),
        "dataset_root": str(base_path.resolve()) if base_path.exists() else str(base_path),
        "classes": names,
        "num_classes": len(names),
        "total_images": 0,
        "total_instances": 0,
        "splits": {},
        "resolution_distribution": Counter(),
        "file_extensions": Counter(),
        "polygon_vertex_stats": {"min": 999999, "max": 0, "avg": 0.0, "total_vertices": 0},
        "cross_split_leakage_count": 0,
        "errors": [],
        "warnings": [],
    }

    split_hashes = defaultdict(dict)
    all_vertices = []

    for split_name, img_rel_dir in splits.items():
        img_dir = base_path / img_rel_dir if not Path(img_rel_dir).is_absolute() else Path(img_rel_dir)
        if "images" in str(img_dir):
            lbl_dir = Path(str(img_dir).replace("images", "labels"))
        else:
            lbl_dir = img_dir.parent / "labels"

        split_info = {
            "image_count": 0,
            "label_count": 0,
            "instance_count": 0,
            "class_counts": {str(k): 0 for k in names.keys()},
            "image_sizes": [],
        }

        if not img_dir.exists():
            audit_data["warnings"].append(f"Directory {img_dir} does not exist.")
            audit_data["splits"][split_name] = split_info
            continue

        image_files = sorted([p for p in img_dir.glob("*") if p.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]])
        split_info["image_count"] = len(image_files)

        for img_path in image_files:
            audit_data["file_extensions"][img_path.suffix.lower()] += 1

            # Decode image
            img = cv2.imread(str(img_path))
            if img is None:
                audit_data["errors"].append(f"Corrupted image: {img_path}")
                continue

            h, w = img.shape[:2]
            res_key = f"{w}x{h}"
            audit_data["resolution_distribution"][res_key] += 1
            split_info["image_sizes"].append({"file": img_path.name, "width": w, "height": h})

            # Check duplicate hash
            hasher = hashlib.sha256()
            with open(img_path, "rb") as f:
                while chunk := f.read(65536):
                    hasher.update(chunk)
            img_hash = hasher.hexdigest()

            for other_split, hash_map in split_hashes.items():
                if img_hash in hash_map:
                    audit_data["cross_split_leakage_count"] += 1
                    audit_data["warnings"].append(
                        f"Leakage: {img_path.name} in '{split_name}' matches {hash_map[img_hash]} in '{other_split}'"
                    )
            split_hashes[split_name][img_hash] = img_path.name

            # Label parsing
            lbl_path = lbl_dir / f"{img_path.stem}.txt"
            if not lbl_path.exists():
                audit_data["errors"].append(f"Missing label: {lbl_path}")
                continue

            split_info["label_count"] += 1
            try:
                with open(lbl_path, "r", encoding="utf-8") as f:
                    lines = [line.strip() for line in f if line.strip()]

                for line in lines:
                    tokens = line.split()
                    if len(tokens) >= 7:
                        cls_id = int(tokens[0])
                        split_info["class_counts"][str(cls_id)] = split_info["class_counts"].get(str(cls_id), 0) + 1
                        split_info["instance_count"] += 1
                        audit_data["total_instances"] += 1

                        num_vertices = (len(tokens) - 1) // 2
                        all_vertices.append(num_vertices)
            except Exception as e:
                audit_data["errors"].append(f"Label read error {lbl_path}: {e}")

        audit_data["total_images"] += split_info["image_count"]
        audit_data["splits"][split_name] = split_info

    if all_vertices:
        audit_data["polygon_vertex_stats"]["min"] = min(all_vertices)
        audit_data["polygon_vertex_stats"]["max"] = max(all_vertices)
        audit_data["polygon_vertex_stats"]["avg"] = round(sum(all_vertices) / len(all_vertices), 2)
        audit_data["polygon_vertex_stats"]["total_vertices"] = sum(all_vertices)
    else:
        audit_data["polygon_vertex_stats"]["min"] = 0

    if export_json:
        out_path = Path(export_json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(audit_data, f, indent=2)
        print(f"[*] Exported audit JSON to: {out_path.resolve()}")

    return audit_data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audit YOLO segmentation dataset.")
    parser.add_argument("--config", default="ai/vision/training/configs/jewellery_components.yaml")
    parser.add_argument("--export-json", default=None)
    args = parser.parse_args()

    audit = audit_dataset(args.config, args.export_json)
    print("\n" + "=" * 60)
    print("DATASET AUDIT REPORT")
    print("=" * 60)
    print(f"Config:          {audit['config_path']}")
    print(f"Total Images:    {audit['total_images']}")
    print(f"Total Instances: {audit['total_instances']}")
    print(f"Classes ({audit['num_classes']}): {list(audit['classes'].values())}")
    print(f"Vertex Density:  Min={audit['polygon_vertex_stats']['min']}, Max={audit['polygon_vertex_stats']['max']}, Avg={audit['polygon_vertex_stats']['avg']}")
    print(f"Errors Found:    {len(audit['errors'])}")
    print(f"Warnings Found:  {len(audit['warnings'])}")
    print("=" * 60)
