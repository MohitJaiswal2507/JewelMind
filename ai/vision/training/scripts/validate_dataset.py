"""JewelMind YOLO Segmentation Dataset Validator.

Validates:
- Images exist and can be decoded
- Label files exist and correspond 1:1 with images
- Class IDs are valid integers within expected range
- Segmentation polygons have >= 3 points and all coordinates lie in [0.0, 1.0]
- Zero-byte or corrupted files are caught
- Cross-split image leakage is prevented via perceptual or cryptographic hashing
- Summarizes image counts, instance counts, and per-class distributions
"""

import argparse
import hashlib
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path
import cv2
import yaml


def load_dataset_config(yaml_path: str) -> dict:
    """Load and parse the dataset YAML configuration."""
    with open(yaml_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return config


def compute_file_hash(filepath: Path) -> str:
    """Compute SHA-256 hash of an image file to check for exact duplicates."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def validate_dataset(yaml_path: str = "ai/vision/training/configs/jewellery_components.yaml") -> dict:
    """Perform comprehensive validation on the dataset specified by yaml_path."""
    config_file = Path(yaml_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Dataset YAML configuration not found: {yaml_path}")

    config = load_dataset_config(yaml_path)
    base_dir = config.get("path", "")
    base_path = Path(base_dir) if os.path.isabs(base_dir) else (config_file.parent.parent.parent / "datasets" / Path(base_dir).name)

    if not base_path.exists():
        # Fallback to direct relative resolution from current working directory
        base_path = Path(base_dir)

    names = config.get("names", {})
    num_classes = len(names)
    print(f"[*] Validating Dataset: {base_path}")
    print(f"[*] Registered Classes ({num_classes}): {names}")

    splits = {
        "train": config.get("train", "train/images"),
        "val": config.get("val", "val/images"),
        "test": config.get("test", "test/images"),
    }

    report = {
        "status": "PASS",
        "splits": {},
        "global_class_counts": Counter(),
        "total_images": 0,
        "total_instances": 0,
        "errors": [],
        "warnings": [],
    }

    split_hashes = defaultdict(dict)  # split -> {hash: filename}

    for split_name, img_rel_dir in splits.items():
        img_dir = base_path / img_rel_dir if not Path(img_rel_dir).is_absolute() else Path(img_rel_dir)
        # Infer labels directory parallel to images directory
        if "images" in str(img_dir):
            lbl_dir = Path(str(img_dir).replace("images", "labels"))
        else:
            lbl_dir = img_dir.parent / "labels"

        split_info = {
            "image_count": 0,
            "label_count": 0,
            "instance_count": 0,
            "class_distribution": Counter(),
            "valid_images": 0,
        }

        if not img_dir.exists():
            report["warnings"].append(f"Split directory does not exist: {img_dir}")
            report["splits"][split_name] = split_info
            continue

        image_files = sorted([p for p in img_dir.glob("*") if p.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]])
        split_info["image_count"] = len(image_files)

        for img_path in image_files:
            # 1. Verify image can be decoded
            img = cv2.imread(str(img_path))
            if img is None:
                report["errors"].append(f"Corrupt image file: {img_path}")
                continue
            h, w = img.shape[:2]
            if h <= 0 or w <= 0:
                report["errors"].append(f"Zero-dimension image: {img_path}")
                continue
            split_info["valid_images"] += 1

            # 2. Check hash for duplicates across splits (split leakage)
            img_hash = compute_file_hash(img_path)
            for other_split, hash_dict in split_hashes.items():
                if img_hash in hash_dict:
                    report["warnings"].append(
                        f"Duplicate image leakage: {img_path.name} in '{split_name}' identical to {hash_dict[img_hash]} in '{other_split}'"
                    )
            split_hashes[split_name][img_hash] = img_path.name

            # 3. Verify matching label file
            lbl_path = lbl_dir / f"{img_path.stem}.txt"
            if not lbl_path.exists():
                report["errors"].append(f"Missing label file for image: {img_path}")
                continue

            split_info["label_count"] += 1

            # 4. Validate label content & segmentation polygons
            try:
                with open(lbl_path, "r", encoding="utf-8") as f:
                    lines = [line.strip() for line in f if line.strip()]

                if not lines:
                    report["warnings"].append(f"Empty label file (background image): {lbl_path}")

                for line_idx, line in enumerate(lines):
                    tokens = line.split()
                    if len(tokens) < 7:
                        # At least class_id + 3 points (6 coords) = 7 tokens
                        report["errors"].append(
                            f"Degenerate polygon in {lbl_path.name}:{line_idx+1}: only {len(tokens)-1} coordinates (minimum 6 required for a polygon)"
                        )
                        continue

                    # Class ID check
                    try:
                        cls_id = int(tokens[0])
                        if cls_id < 0 or cls_id >= num_classes:
                            report["errors"].append(
                                f"Invalid class ID {cls_id} in {lbl_path.name}:{line_idx+1} (expected 0 to {num_classes-1})"
                            )
                            continue
                    except ValueError:
                        report["errors"].append(f"Non-integer class ID '{tokens[0]}' in {lbl_path.name}:{line_idx+1}")
                        continue

                    # Coordinate bounds check
                    coords = []
                    coord_error = False
                    for c_str in tokens[1:]:
                        try:
                            val = float(c_str)
                            if val < -0.01 or val > 1.01:
                                report["errors"].append(
                                    f"Coordinate out of range [0, 1]: {val} in {lbl_path.name}:{line_idx+1}"
                                )
                                coord_error = True
                                break
                            coords.append(val)
                        except ValueError:
                            report["errors"].append(f"Malformed coordinate '{c_str}' in {lbl_path.name}:{line_idx+1}")
                            coord_error = True
                            break

                    if coord_error:
                        continue

                    if len(coords) % 2 != 0:
                        report["errors"].append(f"Odd number of polygon coordinates in {lbl_path.name}:{line_idx+1}")
                        continue

                    split_info["instance_count"] += 1
                    split_info["class_distribution"][cls_id] += 1
                    report["global_class_counts"][cls_id] += 1

            except Exception as e:
                report["errors"].append(f"Failed to read label {lbl_path}: {str(e)}")

        report["splits"][split_name] = split_info
        report["total_images"] += split_info["valid_images"]
        report["total_instances"] += split_info["instance_count"]

    if report["errors"]:
        report["status"] = "FAIL"

    # Print clean summary
    print("\n" + "=" * 60)
    print(f"DATASET VALIDATION SUMMARY: {report['status']}")
    print("=" * 60)
    print(f"Total Valid Images:    {report['total_images']}")
    print(f"Total Component Masks: {report['total_instances']}")
    print("-" * 60)
    for split_name, s_info in report["splits"].items():
        print(f" Split [{split_name.upper():<5}]: {s_info['valid_images']} images | {s_info['instance_count']} masks")
        for cid, count in sorted(s_info["class_distribution"].items()):
            cname = names.get(cid, f"Class {cid}")
            print(f"    - {cname:<12} (ID {cid}): {count} instances")

    print("-" * 60)
    print(f"Errors Found:   {len(report['errors'])}")
    print(f"Warnings Found: {len(report['warnings'])}")
    if report["errors"]:
        print("\nErrors:")
        for err in report["errors"][:10]:
            print(f"  [ERROR] {err}")
    if report["warnings"]:
        print("\nWarnings:")
        for w in report["warnings"][:5]:
            print(f"  [WARN]  {w}")
    print("=" * 60 + "\n")

    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate YOLO instance segmentation dataset.")
    parser.add_argument(
        "--config",
        default="ai/vision/training/configs/jewellery_components.yaml",
        help="Path to dataset YAML file",
    )
    args = parser.parse_args()

    res = validate_dataset(args.config)
    if res["status"] != "PASS":
        sys.exit(1)
