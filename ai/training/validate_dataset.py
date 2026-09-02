"""JewelMind Dataset Integrity Validator for LoRA Fine-Tuning.

Verifies image readability, dimensions (512x512), missing files, empty captions,
and checks for duplicate or corrupt images prior to user manual training.
"""

import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image


def calculate_image_hash(image_path: Path) -> str:
    """Compute MD5 hash to flag duplicate images."""
    hasher = hashlib.md5()
    with open(image_path, "rb") as f:
        buf = f.read(65536)
        while len(buf) > 0:
            hasher.update(buf)
            buf = f.read(65536)
    return hasher.hexdigest()


def validate_split(split_dir: Path) -> bool:
    print(f"\n[VALIDATING] Directory: {split_dir}")
    if not split_dir.exists():
        print(f"  [ERROR] Folder does not exist: {split_dir}")
        return False

    meta_file = split_dir / "metadata.jsonl"
    if not meta_file.exists():
        print(f"  [ERROR] metadata.jsonl not found in: {split_dir}")
        return False

    seen_hashes = {}
    valid_count = 0
    issues = 0

    with open(meta_file, "r", encoding="utf-8") as f:
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

            file_name = data.get("file_name")
            text = data.get("text", "").strip()

            if not file_name:
                print(f"  [ISSUE] Line {line_idx}: Missing 'file_name' key.")
                issues += 1
                continue

            if not text:
                print(f"  [ISSUE] Line {line_idx}: Empty caption 'text' for {file_name}.")
                issues += 1

            img_path = split_dir / file_name
            if not img_path.exists():
                print(f"  [ISSUE] Line {line_idx}: Image file not found: {img_path}")
                issues += 1
                continue

            # Verify image integrity and dimensions
            try:
                with Image.open(img_path) as img:
                    img.verify()
                with Image.open(img_path) as img:
                    w, h = img.size
                    if w != 512 or h != 512:
                        print(f"  [WARNING] {file_name}: Resolution is {w}x{h} (expected 512x512).")
            except Exception as e:
                print(f"  [ISSUE] Corrupted image {file_name}: {e}")
                issues += 1
                continue

            # Duplicate check
            img_hash = calculate_image_hash(img_path)
            if img_hash in seen_hashes:
                print(f"  [WARNING] Duplicate image detected: {file_name} matches {seen_hashes[img_hash]}")
            else:
                seen_hashes[img_hash] = file_name

            valid_count += 1

    print(f"  [SUMMARY] Valid pairs: {valid_count} | Issues encountered: {issues}")
    return issues == 0


def main():
    parser = argparse.ArgumentParser(description="Validate dataset integrity before manual LoRA training.")
    parser.add_argument("--data_dir", type=str, default="datasets/jewellery_lora", help="Dataset directory")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    print("=" * 60)
    print("  JEWELMIND DATASET INTEGRITY VALIDATION")
    print("=" * 60)

    train_valid = validate_split(data_dir / "train")
    val_valid = True
    if (data_dir / "val").exists():
        val_valid = validate_split(data_dir / "val")

    print("\n" + "=" * 60)
    if train_valid and val_valid:
        print("[RESULT] PASS — Dataset is clean, formatted, and ready for training.")
    else:
        print("[RESULT] FAIL — Issues detected. Please review logs above.")
    print("=" * 60)


if __name__ == "__main__":
    main()
