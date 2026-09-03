"""JewelMind Dataset Integrity Validator for LoRA Fine-Tuning.

Verifies image readability, dimensions, missing files, empty captions,
checks for duplicate images, and ensures zero train/validation leakage
prior to user manual LoRA training.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Dict, Optional, Set, Tuple
from PIL import Image


def calculate_image_hash(image_path: Path) -> str:
    """Compute MD5 hash to flag duplicate images and cross-split leakage."""
    hasher = hashlib.md5()
    with open(image_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def resolve_image_path(data_dir: Path, images_dir: Path, file_name: str) -> Path:
    """Resolve image path supporting relative schemas."""
    # 1. Direct relative path from data_dir (e.g. "images/CAND_001.jpg")
    p1 = data_dir / file_name
    if p1.exists():
        return p1
    # 2. Path relative to images_dir (e.g. "CAND_001.jpg")
    p2 = images_dir / Path(file_name).name
    if p2.exists():
        return p2
    p3 = images_dir / file_name
    if p3.exists():
        return p3
    return p1


def validate_split(
    metadata_file: Path,
    images_dir: Path,
    split_name: str,
    data_dir: Optional[Path] = None,
) -> Tuple[bool, int, int, Dict[str, str]]:
    """Validate a single JSONL split manifest against the image directory.
    
    Returns:
        (is_valid, valid_count, issue_count, split_hashes)
    """
    print(f"\n[VALIDATING] Split: {split_name} ({metadata_file})")
    if not metadata_file.exists():
        print(f"  [ERROR] Manifest file does not exist: {metadata_file}")
        return False, 0, 1, {}

    if data_dir is None:
        data_dir = metadata_file.parent.parent

    seen_hashes: Dict[str, str] = {}
    valid_count = 0
    issues = 0

    with open(metadata_file, "r", encoding="utf-8") as f:
        for line_idx, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError as exc:
                print(f"  [ISSUE] Line {line_idx}: Invalid JSON syntax: {exc}")
                issues += 1
                continue

            file_name = data.get("file_name") or data.get("image") or data.get("target_image")
            text = data.get("text") or data.get("caption") or data.get("prompt") or ""
            text = text.strip()

            if not file_name:
                print(f"  [ISSUE] Line {line_idx}: Missing 'file_name' key.")
                issues += 1
                continue

            if not text:
                print(f"  [ISSUE] Line {line_idx}: Empty caption 'text' for {file_name}.")
                issues += 1

            img_path = resolve_image_path(data_dir, images_dir, file_name)
            if not img_path.exists():
                print(f"  [ISSUE] Line {line_idx}: Image file not found: {img_path}")
                issues += 1
                continue

            # Verify image integrity and readability
            try:
                with Image.open(img_path) as img:
                    img.verify()
                with Image.open(img_path) as img:
                    w, h = img.size
                    if w < 256 or h < 256:
                        print(f"  [WARNING] {file_name}: Resolution is {w}x{h} (undersized).")
            except Exception as e:
                print(f"  [ISSUE] Corrupted image {file_name}: {e}")
                issues += 1
                continue

            # Duplicate check within split
            img_hash = calculate_image_hash(img_path)
            if img_hash in seen_hashes:
                print(f"  [WARNING] Intra-split duplicate detected: {file_name} matches {seen_hashes[img_hash]}")
            else:
                seen_hashes[img_hash] = file_name

            valid_count += 1

    print(f"  [SUMMARY] Valid records: {valid_count} | Issues encountered: {issues}")
    return issues == 0, valid_count, issues, seen_hashes


def validate_dataset(data_dir_path: str = "datasets/appearance_lora") -> bool:
    """Validate full dataset layout (train and val splits + images) and check for cross-split leakage."""
    data_dir = Path(data_dir_path)
    print("=" * 65)
    print("  JEWELMIND LoRA DATASET INTEGRITY VALIDATOR")
    print(f"  Target Data Directory: {data_dir}")
    print("=" * 65)

    if not data_dir.exists():
        print(f"[ERROR] Data directory does not exist: {data_dir}")
        return False

    images_dir = data_dir / "images"
    if not images_dir.exists():
        print(f"[ERROR] Images directory does not exist: {images_dir}")
        return False

    # 1. Resolve train split manifest
    train_meta = data_dir / "splits" / "train_metadata.jsonl"
    if not train_meta.exists():
        # Fallbacks
        if (data_dir / "train" / "metadata.jsonl").exists():
            train_meta = data_dir / "train" / "metadata.jsonl"
        elif (data_dir / "metadata" / "metadata.jsonl").exists():
            train_meta = data_dir / "metadata" / "metadata.jsonl"
        elif (data_dir / "metadata.jsonl").exists():
            train_meta = data_dir / "metadata.jsonl"

    # 2. Resolve val split manifest
    val_meta = data_dir / "splits" / "val_metadata.jsonl"
    if not val_meta.exists():
        if (data_dir / "val" / "metadata.jsonl").exists():
            val_meta = data_dir / "val" / "metadata.jsonl"

    # Validate train split
    train_valid, train_count, train_issues, train_hashes = validate_split(
        metadata_file=train_meta,
        images_dir=images_dir,
        split_name="TRAIN",
        data_dir=data_dir,
    )

    # Validate validation split if present
    val_valid = True
    val_count = 0
    val_issues = 0
    val_hashes: Dict[str, str] = {}
    if val_meta.exists():
        val_valid, val_count, val_issues, val_hashes = validate_split(
            metadata_file=val_meta,
            images_dir=images_dir,
            split_name="VALIDATION",
            data_dir=data_dir,
        )

    # 3. Cross-split duplicate leakage check
    leakage_detected = False
    print("\n[CHECKING] Cross-Split Data Leakage (Train <-> Validation)...")
    if train_hashes and val_hashes:
        train_hash_set = set(train_hashes.keys())
        val_hash_set = set(val_hashes.keys())
        leakage_hashes = train_hash_set.intersection(val_hash_set)
        if leakage_hashes:
            leakage_detected = True
            print(f"  [ERROR] Cross-split leakage detected: {len(leakage_hashes)} identical image(s) present in BOTH train and validation splits!")
            for h in list(leakage_hashes)[:5]:
                print(f"    Hash {h}: Train '{train_hashes[h]}' <==> Val '{val_hashes[h]}'")
        else:
            print("  [PASSED] Zero cross-split leakage detected (train and validation splits are 100% disjoint).")
    else:
        print("  [SKIPPED] Validation split not populated or empty.")

    overall_pass = train_valid and val_valid and not leakage_detected

    print("\n" + "=" * 65)
    print("  VALIDATION SUMMARY REPORT")
    print(f"  - Train Split Records:      {train_count} (Issues: {train_issues})")
    print(f"  - Validation Split Records: {val_count} (Issues: {val_issues})")
    print(f"  - Cross-Split Leakage:      {'DETECTED' if leakage_detected else 'NONE'}")
    print("=" * 65)

    if overall_pass:
        print("[RESULT] PASS — Dataset is clean, formatted, and ready for training.")
    else:
        print("[RESULT] FAIL — Issues detected. Please review logs above.")
    print("=" * 65)

    return overall_pass


def main():
    parser = argparse.ArgumentParser(description="Validate dataset integrity before manual LoRA training.")
    parser.add_argument("--data_dir", type=str, default="datasets/appearance_lora", help="Dataset directory")
    args = parser.parse_args()

    success = validate_dataset(args.data_dir)
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
