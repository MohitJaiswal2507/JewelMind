"""JewelMind Rendering V2 Dataset Validator.

Strict validation utility for the Rendering V2 paired diffusion dataset.
Verifies file existence, image integrity, 512x512 dimensions, RGB modes,
cross-split leakage, taxonomy conformance, and metadata accuracy.

Exit Codes:
  0 = 100% VALID (Ready for pilot/training)
  1 = ERROR(S) DETECTED
"""

import argparse
import hashlib
import json
import logging
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

import cv2
import numpy as np
from PIL import Image

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("jewelmind.validate_rendering_v2")

CANONICAL_CATEGORIES = {
    "ring",
    "earring",
    "pendant",
    "necklace",
    "bracelet",
    "bangle",
    "brooch",
    "other_jewellery",
}


def compute_file_sha256(filepath: Path) -> str:
    """Compute SHA-256 digest of file on disk."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def validate_dataset(dataset_dir: Path, target_resolution: int = 512) -> Tuple[bool, Dict[str, Any]]:
    logger.info("==================================================")
    logger.info("VALIDATING RENDERING V2 DATASET: %s", dataset_dir.resolve())
    logger.info("==================================================")

    errors: List[str] = []
    warnings: List[str] = []

    if not dataset_dir.exists():
        errors.append(f"Dataset root directory does not exist: {dataset_dir}")
        return False, {"errors": errors, "warnings": warnings}

    manifest_file = dataset_dir / "DATASET_MANIFEST.json"
    if not manifest_file.exists():
        errors.append("DATASET_MANIFEST.json is missing in dataset root!")

    splits = ["train", "val", "test"]
    split_records: Dict[str, List[Dict]] = {}
    split_target_hashes: Dict[str, Set[str]] = defaultdict(set)
    split_cond_hashes: Dict[str, Set[str]] = defaultdict(set)
    category_counts = defaultdict(lambda: Counter())

    total_validated_pairs = 0

    for split in splits:
        split_dir = dataset_dir / split
        if not split_dir.exists():
            errors.append(f"Missing split directory: {split_dir}")
            continue

        meta_file = split_dir / "metadata.jsonl"
        if not meta_file.exists():
            errors.append(f"Missing metadata.jsonl in split: {split}")
            continue

        cond_dir = split_dir / "conditioning"
        target_dir = split_dir / "target"

        if not cond_dir.exists():
            errors.append(f"Missing conditioning directory in split: {split}")
        if not target_dir.exists():
            errors.append(f"Missing target directory in split: {split}")

        # Read JSONL records
        records = []
        with open(meta_file, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    records.append(data)
                except Exception as e:
                    errors.append(f"Corrupted JSON on line {line_no} of {meta_file}: {e}")

        split_records[split] = records
        logger.info("Split [%s]: Found %d metadata records", split, len(records))

        # Validate individual records and physical image files
        for r_idx, rec in enumerate(records):
            rec_id = rec.get("id", f"record_{r_idx}")
            cat = rec.get("canonical_category")

            # 1. Category taxonomy validation
            if not cat or cat not in CANONICAL_CATEGORIES:
                errors.append(f"[{split}/{rec_id}] Invalid canonical_category '{cat}'. Must be one of {sorted(CANONICAL_CATEGORIES)}")
            else:
                category_counts[split][cat] += 1

            # 2. File path resolution
            rel_cond_path = rec.get("conditioning_path")
            rel_target_path = rec.get("target_path")

            if not rel_cond_path or not rel_target_path:
                errors.append(f"[{split}/{rec_id}] Missing conditioning_path or target_path in metadata")
                continue

            cond_path = dataset_dir / rel_cond_path
            target_path = dataset_dir / rel_target_path

            if not cond_path.exists():
                errors.append(f"[{split}/{rec_id}] Conditioning file missing on disk: {cond_path}")
                continue
            if not target_path.exists():
                errors.append(f"[{split}/{rec_id}] Target file missing on disk: {target_path}")
                continue

            # 3. Non-empty file check
            if cond_path.stat().st_size == 0:
                errors.append(f"[{split}/{rec_id}] Empty 0-byte conditioning file: {cond_path}")
            if target_path.stat().st_size == 0:
                errors.append(f"[{split}/{rec_id}] Empty 0-byte target file: {target_path}")

            # 4. Target image opening, dimensions, and RGB check
            try:
                with Image.open(target_path) as t_img:
                    tw, th = t_img.size
                    t_mode = t_img.mode
                    if (tw, th) != (target_resolution, target_resolution):
                        errors.append(f"[{split}/{rec_id}] Target resolution ({tw}x{th}) != expected ({target_resolution}x{target_resolution})")
                    if t_mode != "RGB":
                        errors.append(f"[{split}/{rec_id}] Target mode '{t_mode}' != 'RGB'")
            except Exception as e:
                errors.append(f"[{split}/{rec_id}] Target image decoding failed: {e}")

            # 5. Conditioning image opening, dimensions, and RGB check
            try:
                with Image.open(cond_path) as c_img:
                    cw, ch = c_img.size
                    c_mode = c_img.mode
                    if (cw, ch) != (target_resolution, target_resolution):
                        errors.append(f"[{split}/{rec_id}] Conditioning resolution ({cw}x{ch}) != expected ({target_resolution}x{target_resolution})")
                    if c_mode != "RGB":
                        errors.append(f"[{split}/{rec_id}] Conditioning mode '{c_mode}' != 'RGB'")
            except Exception as e:
                errors.append(f"[{split}/{rec_id}] Conditioning image decoding failed: {e}")

            # 6. Hash check & deduplication within split
            t_sha = compute_file_sha256(target_path)
            c_sha = compute_file_sha256(cond_path)

            if t_sha != rec.get("sha256_target"):
                errors.append(f"[{split}/{rec_id}] Target SHA mismatch. Recorded: {rec.get('sha256_target')}, Actual: {t_sha}")
            if c_sha != rec.get("sha256_conditioning"):
                errors.append(f"[{split}/{rec_id}] Conditioning SHA mismatch. Recorded: {rec.get('sha256_conditioning')}, Actual: {c_sha}")

            split_target_hashes[split].add(t_sha)
            split_cond_hashes[split].add(c_sha)
            total_validated_pairs += 1

    # 7. Cross-Split Leakage Check
    train_targets = split_target_hashes["train"]
    val_targets = split_target_hashes["val"]
    test_targets = split_target_hashes["test"]

    train_val_leakage = train_targets.intersection(val_targets)
    train_test_leakage = train_targets.intersection(test_targets)
    val_test_leakage = val_targets.intersection(test_targets)

    if train_val_leakage:
        errors.append(f"LEAKAGE DETECTED: {len(train_val_leakage)} targets overlap between train and val splits!")
    if train_test_leakage:
        errors.append(f"LEAKAGE DETECTED: {len(train_test_leakage)} targets overlap between train and test splits!")
    if val_test_leakage:
        errors.append(f"LEAKAGE DETECTED: {len(val_test_leakage)} targets overlap between val and test splits!")

    is_valid = len(errors) == 0

    print("\n" + "=" * 65)
    print("  JEWELMIND RENDERING V2 DATASET VALIDATION REPORT")
    print("=" * 65)
    print(f"  Total Validated Pairs: {total_validated_pairs}")
    print(f"  Train Pairs:           {len(split_records.get('train', []))}")
    print(f"  Val Pairs:             {len(split_records.get('val', []))}")
    print(f"  Test Pairs:            {len(split_records.get('test', []))}")
    print("-" * 65)
    print("  Category Distribution across Splits:")
    print(f"  {'Category':<18} | {'Train':>6} | {'Val':>6} | {'Test':>6} | {'Total':>6}")
    print("  " + "-" * 55)

    all_cats = sorted(CANONICAL_CATEGORIES)
    for cat in all_cats:
        tr = category_counts["train"][cat]
        va = category_counts["val"][cat]
        te = category_counts["test"][cat]
        tot = tr + va + te
        print(f"  {cat:<18} | {tr:>6} | {va:>6} | {te:>6} | {tot:>6}")

    print("-" * 65)
    print("  Integrity & Leakage:")
    print(f"  - Train / Val Target Overlap:  {len(train_val_leakage)} (Expected: 0)")
    print(f"  - Train / Test Target Overlap: {len(train_test_leakage)} (Expected: 0)")
    print(f"  - Val / Test Target Overlap:   {len(val_test_leakage)} (Expected: 0)")
    print("=" * 65)

    if errors:
        print(f"\n[FAILED] {len(errors)} Validation Error(s) Encountered:")
        for err in errors[:20]:
            print(f"  ❌ {err}")
        if len(errors) > 20:
            print(f"  ... and {len(errors) - 20} more errors")
    else:
        print("\n[SUCCESS] Dataset passed all validation checks with 0 errors!")

    if warnings:
        print(f"\n[WARNING] {len(warnings)} Warning(s):")
        for w in warnings[:10]:
            print(f"  ⚠️  {w}")

    summary = {
        "is_valid": is_valid,
        "total_pairs": total_validated_pairs,
        "splits": {s: len(split_records.get(s, [])) for s in splits},
        "category_counts": {c: {s: category_counts[s][c] for s in splits} for c in all_cats},
        "errors": errors,
        "warnings": warnings,
    }
    return is_valid, summary


def main():
    parser = argparse.ArgumentParser(description="Validate JewelMind Rendering V2 Dataset")
    parser.add_argument("--dataset-dir", type=str, default="ai/vision/datasets/rendering_v2", help="Dataset directory to validate")
    parser.add_argument("--resolution", type=int, default=512, help="Expected image resolution")
    args = parser.parse_args()

    is_valid, _ = validate_dataset(Path(args.dataset_dir), target_resolution=args.resolution)
    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()
