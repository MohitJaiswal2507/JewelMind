"""Script to generate the full paired ControlNet LineArt conditioning dataset."""

import hashlib
import json
import shutil
import sys
from pathlib import Path
import numpy as np
import cv2
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ai.rendering.preprocessing.structural import StructuralConditioningProcessor


def compute_sha256(file_path: Path) -> str:
    sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            sha.update(chunk)
    return sha.hexdigest()


def main():
    source_dir = Path("datasets/appearance_lora/images")
    output_root = Path("datasets/controlnet_paired")
    images_dir = output_root / "images"
    cond_dir = output_root / "conditioning"
    meta_dir = output_root / "metadata"

    images_dir.mkdir(parents=True, exist_ok=True)
    cond_dir.mkdir(parents=True, exist_ok=True)
    meta_dir.mkdir(parents=True, exist_ok=True)

    # Load split definitions
    train_meta_path = Path("datasets/appearance_lora/splits/train_metadata.jsonl")
    val_meta_path = Path("datasets/appearance_lora/splits/val_metadata.jsonl")

    train_records = [json.loads(line) for line in train_meta_path.read_text().strip().split("\n") if line.strip()]
    val_records = [json.loads(line) for line in val_meta_path.read_text().strip().split("\n") if line.strip()]

    print(f"Loaded {len(train_records)} train records and {len(val_records)} val records.")

    # Initialize Processor with exact Phase 9 validated parameters
    processor = StructuralConditioningProcessor(
        target_width=512,
        target_height=512,
        device="cuda",
        noise_floor=35,
        bilateral_d=9,
        bilateral_sigma=75.0,
        coarse=False,
        use_neural_lineart=True,
    )

    settings_dict = {
        "target_width": 512,
        "target_height": 512,
        "device": "cuda",
        "noise_floor": 35,
        "bilateral_d": 9,
        "bilateral_sigma": 75.0,
        "coarse": False,
        "use_neural_lineart": True,
    }

    all_records = []
    train_jsonl_entries = []
    val_jsonl_entries = []

    def process_split(records, split_name):
        jsonl_entries = []
        for idx, rec in enumerate(records, 1):
            stem = Path(rec["file_name"]).stem
            src_img_path = source_dir / f"{stem}.jpg"
            if not src_img_path.exists():
                raise FileNotFoundError(f"Source image not found: {src_img_path}")

            dst_img_path = images_dir / f"{stem}.jpg"
            dst_cond_path = cond_dir / f"{stem}.png"

            # Copy original source image to controlnet_paired/images
            if not dst_img_path.exists():
                shutil.copy2(src_img_path, dst_img_path)

            orig_img = Image.open(src_img_path)
            w_orig, h_orig = orig_img.size
            src_sha = compute_sha256(src_img_path)

            # Generate conditioning
            cond_img, meta = processor.process(orig_img)
            cond_img.save(dst_cond_path)
            cond_sha = compute_sha256(dst_cond_path)

            # Calculate background noise metric (outer 10-pixel border activity)
            cond_np = np.array(cond_img)
            cond_gray = cv2.cvtColor(cond_np, cv2.COLOR_RGB2GRAY) if cond_np.ndim == 3 else cond_np
            border_pixels = np.concatenate([
                cond_gray[:10, :].flatten(),
                cond_gray[-10:, :].flatten(),
                cond_gray[:, :10].flatten(),
                cond_gray[:, -10:].flatten(),
            ])
            border_noise_density = round(float(np.count_nonzero(border_pixels > 30)) / len(border_pixels), 4)

            record_entry = {
                "stem": stem,
                "split": split_name,
                "source_filename": f"{stem}.jpg",
                "source_path": f"images/{stem}.jpg",
                "conditioning_filename": f"{stem}.png",
                "conditioning_path": f"conditioning/{stem}.png",
                "original_width": w_orig,
                "original_height": h_orig,
                "conditioning_width": meta.processed_size[0],
                "conditioning_height": meta.processed_size[1],
                "jewellery_category": rec.get("category", "unknown"),
                "caption": rec.get("text", ""),
                "edge_density": meta.edge_density,
                "border_noise_density": border_noise_density,
                "source_sha256": src_sha,
                "conditioning_sha256": cond_sha,
                "preprocessing_settings": settings_dict,
                "success": True,
            }
            all_records.append(record_entry)

            # Standard paired jsonl format for ControlNet trainers
            jsonl_entry = {
                "source": f"conditioning/{stem}.png",
                "target": f"images/{stem}.jpg",
                "prompt": rec.get("text", ""),
                "category": rec.get("category", "unknown"),
                "edge_density": meta.edge_density,
            }
            jsonl_entries.append(jsonl_entry)

            print(f"[{split_name} {idx:03d}/{len(records):03d}] {stem} -> density={meta.edge_density:.4f}, bg_noise={border_noise_density:.4f}")
        return jsonl_entries

    print("\n--- Processing Training Split (147 images) ---")
    train_jsonl_entries = process_split(train_records, "train")

    print("\n--- Processing Validation Split (17 images) ---")
    val_jsonl_entries = process_split(val_records, "validation")

    # Save metadata files
    train_jsonl_path = meta_dir / "train.jsonl"
    val_jsonl_path = meta_dir / "validation.jsonl"
    full_meta_path = meta_dir / "dataset_metadata.json"

    with open(train_jsonl_path, "w", encoding="utf-8") as f:
        for entry in train_jsonl_entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    with open(val_jsonl_path, "w", encoding="utf-8") as f:
        for entry in val_jsonl_entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    with open(full_meta_path, "w", encoding="utf-8") as f:
        json.dump(all_records, f, indent=2, ensure_ascii=False)

    print("\n--- Quality Control & Verification ---")
    # 1. Verification of counts
    total_processed = len(all_records)
    total_images_in_dir = len(list(images_dir.glob("*.jpg")))
    total_cond_in_dir = len(list(cond_dir.glob("*.png")))
    train_count = len(train_jsonl_entries)
    val_count = len(val_jsonl_entries)

    print(f"Total processed: {total_processed}")
    print(f"Images in dir: {total_images_in_dir}")
    print(f"Conditioning in dir: {total_cond_in_dir}")
    print(f"Train pairs: {train_count}")
    print(f"Validation pairs: {val_count}")

    # 2. SHA-256 overlap check
    train_shas = {r["source_sha256"] for r in all_records if r["split"] == "train"}
    val_shas = {r["source_sha256"] for r in all_records if r["split"] == "validation"}
    overlap = train_shas.intersection(val_shas)
    print(f"SHA-256 Train/Val Overlap Count: {len(overlap)}")

    # 3. Conditioning format and dimensions check
    corrupted_count = 0
    dim_mismatch_count = 0
    non_rgb_count = 0

    for r in all_records:
        cond_p = output_root / r["conditioning_path"]
        try:
            im = Image.open(cond_p)
            if im.size != (512, 512):
                dim_mismatch_count += 1
            if im.mode != "RGB":
                non_rgb_count += 1
        except Exception as e:
            corrupted_count += 1
            print(f"Corrupted: {cond_p} - {e}")

    print(f"Corrupted: {corrupted_count}, Dimension Mismatches: {dim_mismatch_count}, Non-RGB: {non_rgb_count}")

    # 4. Statistical analysis
    densities = [r["edge_density"] for r in all_records]
    min_density = float(np.min(densities))
    max_density = float(np.max(densities))
    mean_density = float(np.mean(densities))
    median_density = float(np.median(densities))

    print(f"Edge Density Stats: min={min_density:.4f}, max={max_density:.4f}, mean={mean_density:.4f}, median={median_density:.4f}")

    # 5. Flagged samples
    flagged_low = [r for r in all_records if r["edge_density"] < 0.01]
    flagged_high = [r for r in all_records if r["edge_density"] > 0.15]
    flagged_noise = [r for r in all_records if r["border_noise_density"] > 0.10]

    print(f"Flagged Low Density (<0.01): {len(flagged_low)}")
    print(f"Flagged High Density (>0.15): {len(flagged_high)}")
    print(f"Flagged High BG Noise (>0.10): {len(flagged_noise)}")

    # Save summary stats
    summary_stats = {
        "total_source_images": 164,
        "total_processed": total_processed,
        "train_pairs": train_count,
        "validation_pairs": val_count,
        "sha256_overlap": len(overlap),
        "corrupted_images": corrupted_count,
        "all_512x512": dim_mismatch_count == 0,
        "all_rgb": non_rgb_count == 0,
        "edge_density_statistics": {
            "min": min_density,
            "max": max_density,
            "mean": mean_density,
            "median": median_density,
        },
        "flagged_samples_count": {
            "low_density": len(flagged_low),
            "high_density": len(flagged_high),
            "high_bg_noise": len(flagged_noise),
        },
        "flagged_samples": {
            "low_density": [r["stem"] for r in flagged_low],
            "high_density": [r["stem"] for r in flagged_high],
            "high_bg_noise": [r["stem"] for r in flagged_noise],
        },
    }
    with open(meta_dir / "dataset_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary_stats, f, indent=2)

    print("\nDataset generation and validation completed successfully!")


if __name__ == "__main__":
    main()
