"""JewelMind ControlNet Paired Dataset Validator.

Performs integrity checks on paired ControlNet datasets:
  - Validates JSONL structure and syntax for train & validation splits
  - Verifies image and conditioning map file existence & readability
  - Verifies RGB color mode and conditioning resolution (512x512)
  - Computes SHA-256 hashes to guarantee zero cross-split leakage
  - Checks for duplicate entries or empty prompts
"""

import argparse
import hashlib
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from PIL import Image

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%m/%d/%Y %H:%M:%S",
    level=logging.INFO,
)
logger = logging.getLogger("jewelmind.validate_controlnet_dataset")


def calculate_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def resolve_path(data_dir: Path, rel_path: str) -> Path:
    """Resolve file path relative to dataset root or subdirectories."""
    p = data_dir / rel_path
    if p.exists():
        return p
    p_img = data_dir / "images" / Path(rel_path).name
    if p_img.exists():
        return p_img
    p_cond = data_dir / "conditioning" / Path(rel_path).name
    if p_cond.exists():
        return p_cond
    p_root = Path(rel_path)
    if p_root.exists():
        return p_root
    return p


def validate_controlnet_split(
    manifest_path: Path,
    data_dir: Path,
    split_name: str,
) -> Tuple[bool, int, int, Dict[str, Dict[str, Any]]]:
    """Validate a single JSONL split manifest.

    Returns:
        (is_valid, valid_count, issue_count, split_records_dict)
    """
    logger.info("Validating %s split manifest: %s", split_name, manifest_path)
    if not manifest_path.exists():
        logger.error("Manifest file not found: %s", manifest_path)
        return False, 0, 1, {}

    valid_count = 0
    issue_count = 0
    records: Dict[str, Dict[str, Any]] = {}
    seen_sources: Set[str] = set()
    seen_targets: Set[str] = set()

    with open(manifest_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line_str = line.strip()
            if not line_str:
                continue

            try:
                data = json.loads(line_str)
            except json.JSONDecodeError as err:
                logger.error("Line %d: Invalid JSON in %s: %s", line_num, manifest_path.name, err)
                issue_count += 1
                continue

            source_rel = data.get("source") or data.get("conditioning") or data.get("conditioning_path")
            target_rel = data.get("target") or data.get("image") or data.get("target_image")
            prompt = (data.get("prompt") or data.get("caption") or data.get("text") or "").strip()

            if not source_rel:
                logger.error("Line %d: Missing 'source' (conditioning map) key.", line_num)
                issue_count += 1
                continue

            if not target_rel:
                logger.error("Line %d: Missing 'target' (image) key.", line_num)
                issue_count += 1
                continue

            if not prompt:
                logger.warning("Line %d: Empty prompt for source '%s'.", line_num, source_rel)
                issue_count += 1

            # Check intra-split duplicates
            if source_rel in seen_sources:
                logger.warning("Line %d: Duplicate conditioning map reference '%s'.", line_num, source_rel)
            seen_sources.add(source_rel)

            if target_rel in seen_targets:
                logger.warning("Line %d: Duplicate target image reference '%s'.", line_num, target_rel)
            seen_targets.add(target_rel)

            # Resolve paths
            source_path = resolve_path(data_dir, source_rel)
            target_path = resolve_path(data_dir, target_rel)

            if not source_path.exists():
                logger.error("Line %d: Conditioning file missing: %s", line_num, source_path)
                issue_count += 1
                continue

            if not target_path.exists():
                logger.error("Line %d: Target image file missing: %s", line_num, target_path)
                issue_count += 1
                continue

            # Verify conditioning image
            try:
                with Image.open(source_path) as cond_img:
                    cond_img.verify()
                with Image.open(source_path) as cond_img:
                    if cond_img.size != (512, 512):
                        logger.warning("Line %d: Conditioning image size is %s (expected 512x512).", line_num, cond_img.size)
                    if cond_img.mode != "RGB":
                        logger.warning("Line %d: Conditioning image mode is '%s' (expected RGB).", line_num, cond_img.mode)
            except Exception as exc:
                logger.error("Line %d: Corrupted conditioning image %s: %s", line_num, source_path, exc)
                issue_count += 1
                continue

            # Verify target image
            try:
                with Image.open(target_path) as tgt_img:
                    tgt_img.verify()
                with Image.open(target_path) as tgt_img:
                    if tgt_img.size[0] < 128 or tgt_img.size[1] < 128:
                        logger.warning("Line %d: Target image undersized: %s", line_num, tgt_img.size)
            except Exception as exc:
                logger.error("Line %d: Corrupted target image %s: %s", line_num, target_path, exc)
                issue_count += 1
                continue

            # Compute SHA-256
            target_sha = calculate_sha256(target_path)
            cond_sha = calculate_sha256(source_path)

            record_key = Path(target_rel).stem
            records[record_key] = {
                "source_path": str(source_path),
                "target_path": str(target_path),
                "target_sha256": target_sha,
                "conditioning_sha256": cond_sha,
                "prompt": prompt,
                "category": data.get("category", "unknown"),
            }
            valid_count += 1

    is_valid = (issue_count == 0)
    logger.info(
        "Split %s summary: %d valid records, %d issues (Status: %s)",
        split_name, valid_count, issue_count, "PASSED" if is_valid else "FAILED"
    )
    return is_valid, valid_count, issue_count, records


def validate_controlnet_dataset(data_dir_path: str = "datasets/controlnet_paired") -> bool:
    """Validate full paired ControlNet dataset (train + validation splits, SHA256 separation)."""
    data_dir = Path(data_dir_path).resolve()
    print("=" * 70)
    print("  JEWELMIND CONTROLNET PAIRED DATASET VALIDATOR")
    print(f"  Target Root: {data_dir}")
    print("=" * 70)

    if not data_dir.exists():
        logger.error("Dataset root directory does not exist: %s", data_dir)
        return False

    train_manifest = data_dir / "metadata" / "train.jsonl"
    if not train_manifest.exists():
        train_manifest = data_dir / "train.jsonl"

    val_manifest = data_dir / "metadata" / "validation.jsonl"
    if not val_manifest.exists():
        val_manifest = data_dir / "validation.jsonl"

    # 1. Validate train split
    train_valid, train_count, train_issues, train_records = validate_controlnet_split(
        manifest_path=train_manifest,
        data_dir=data_dir,
        split_name="TRAIN",
    )

    # 2. Validate validation split
    val_valid, val_count, val_issues, val_records = validate_controlnet_split(
        manifest_path=val_manifest,
        data_dir=data_dir,
        split_name="VALIDATION",
    )

    # 3. Cross-split SHA-256 leakage check
    print("\n[CHECKING] Cross-Split SHA-256 Leakage...")
    train_shas = {rec["target_sha256"]: stem for stem, rec in train_records.items()}
    val_shas = {rec["target_sha256"]: stem for stem, rec in val_records.items()}

    overlap_shas = set(train_shas.keys()).intersection(set(val_shas.keys()))
    has_leakage = len(overlap_shas) > 0

    if has_leakage:
        logger.error("CRITICAL: Detected %d overlapping image(s) between Train and Validation splits!", len(overlap_shas))
        for sha in list(overlap_shas)[:5]:
            logger.error("  Leakage: Train '%s' <==> Val '%s' (SHA256: %s)", train_shas[sha], val_shas[sha], sha)
    else:
        print("  [PASSED] Zero cross-split SHA-256 leakage detected (splits are 100% disjoint).")

    # Overall outcome
    overall_pass = train_valid and val_valid and not has_leakage and train_count > 0

    print("\n" + "=" * 70)
    print("  CONTROLNET DATASET VALIDATION SUMMARY")
    print(f"  - Training Pairs:         {train_count} (Issues: {train_issues})")
    print(f"  - Validation Pairs:       {val_count} (Issues: {val_issues})")
    print(f"  - Cross-Split Leakage:    {'DETECTED' if has_leakage else 'NONE (0 SHA-256 overlaps)'}")
    print(f"  - Overall Dataset Status: {'PASS' if overall_pass else 'FAIL'}")
    print("=" * 70)

    return overall_pass


def main():
    parser = argparse.ArgumentParser(description="Validate ControlNet paired dataset integrity.")
    parser.add_argument("--data_dir", type=str, default="datasets/controlnet_paired", help="Path to controlnet_paired dataset root")
    args = parser.parse_args()

    success = validate_controlnet_dataset(args.data_dir)
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
