"""JewelMind DWPose to YOLO11 Instance Segmentation Dataset Converter.

Pipeline:
1. Groups multi-row parquet records by unique target image.
2. Inverts inpainting masks (0 -> 255 foreground jewellery).
3. Normalizes prompts into JewelMind 8-category taxonomy.
4. Excludes watch-only records and ambiguous non-jewellery prompts.
5. Extracts precise, simplified polygon contours (cv2.findContours + approxPolyDP).
6. Enforces 0-leakage 70/20/10 split at UNIQUE TARGET IMAGE level.
7. Generates YOLO instance segmentation dataset in ai/vision/datasets/jewellery_v2/.
"""

import argparse
import hashlib
import json
import os
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import cv2
import numpy as np
import pandas as pd
import pyarrow.parquet as pq


JEWELMIND_CATEGORIES = {
    "ring": 0,
    "earring": 1,
    "pendant": 2,
    "necklace": 3,
    "bracelet": 4,
    "bangle": 5,
    "brooch": 6,
    "other_jewellery": 7,
}

CLASS_NAMES = {v: k for k, v in JEWELMIND_CATEGORIES.items()}


def normalize_prompt(prompt: str) -> Optional[str]:
    """Extract single primary JewelMind category from prompt, or None if unsupported/ambiguous."""
    if not prompt:
        return None
    p_lower = prompt.lower().strip()
    tokens = [t.strip() for t in p_lower.split(",") if t.strip()]
    gender_terms = {"female", "male", "woman", "man", "girl", "boy", "person", "model", "asian", "caucasian", "femlae"}
    jewel_tokens = [t for t in tokens if t not in gender_terms]
    
    # Priority matching
    for token in jewel_tokens:
        t_clean = token.rstrip("s")
        if "ring" in t_clean and "earring" not in t_clean and "spring" not in t_clean:
            return "ring"
        elif "earring" in t_clean:
            return "earring"
        elif "necklace" in t_clean:
            return "necklace"
        elif "bracelet" in t_clean:
            return "bracelet"
        elif "bangle" in t_clean:
            return "bangle"
        elif "pendant" in t_clean:
            return "pendant"
        elif "brooch" in t_clean:
            return "brooch"
        elif "watch" in t_clean:
            return None # Watch explicitly excluded from JewelMind
            
    return None


def mask_to_yolo_polygons(mask_img: np.ndarray, class_id: int, min_area_px: int = 15) -> List[str]:
    """Convert binary mask (255 for object, 0 for bg) to normalized YOLO polygon lines."""
    h, w = mask_img.shape[:2]
    if h == 0 or w == 0:
        return []
        
    contours, _ = cv2.findContours(mask_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_TC89_KCOS)
    yolo_lines = []
    
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < min_area_px:
            continue
            
        # Simplify contour to reduce vertex count while preserving shape fidelity
        epsilon = 0.003 * cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, max(epsilon, 1.0), True)
        
        # Must have at least 3 points
        if len(approx) < 3:
            continue
            
        coords = []
        for pt in approx:
            x, y = pt[0]
            norm_x = min(max(float(x) / w, 0.0), 1.0)
            norm_y = min(max(float(y) / h, 0.0), 1.0)
            coords.extend([f"{norm_x:.6f}", f"{norm_y:.6f}"])
            
        line = f"{class_id} " + " ".join(coords)
        yolo_lines.append(line)
        
    return yolo_lines


def get_deterministic_split(target_name: str) -> str:
    """Deterministic hash split: 70% train, 20% val, 10% test."""
    hash_val = int(hashlib.md5(target_name.encode("utf-8")).hexdigest(), 16) % 100
    if hash_val < 70:
        return "train"
    elif hash_val < 90:
        return "val"
    else:
        return "test"


def convert_dataset(
    raw_data_dir: Path,
    output_dir: Path,
    max_images: Optional[int] = None,
) -> Dict[str, Any]:
    print("=" * 70)
    print("JEWELMIND MULTI-JEWELLERY YOLO V2 CONVERSION PIPELINE")
    print("=" * 70)
    
    parquet_files = sorted(raw_data_dir.glob("*.parquet"))
    if not parquet_files:
        raise FileNotFoundError(f"No parquet files found in {raw_data_dir}")
        
    # Prepare clean directory structure
    for split in ["train", "val", "test"]:
        (output_dir / split / "images").mkdir(parents=True, exist_ok=True)
        (output_dir / split / "labels").mkdir(parents=True, exist_ok=True)
        
    print(f"[*] Aggregating records from {len(parquet_files)} parquet shards...")
    target_groups = defaultdict(list)
    total_raw_rows = 0
    
    for p_file in parquet_files:
        table = pq.read_table(p_file)
        df = table.to_pandas()
        for _, row in df.iterrows():
            total_raw_rows += 1
            t_path = str(row["target"]["path"]) if isinstance(row["target"], dict) else str(row["target"].get("path"))
            t_bytes = row["target"]["bytes"] if isinstance(row["target"], dict) else row["target"].get("bytes")
            m_bytes = row["mask"]["bytes"] if isinstance(row["mask"], dict) else row["mask"].get("bytes")
            prompt = str(row["prompt"]) if pd.notna(row["prompt"]) else ""
            
            target_groups[t_path].append({
                "target_bytes": t_bytes,
                "mask_bytes": m_bytes,
                "prompt": prompt,
            })
            
    print(f"[*] Total Raw Rows:        {total_raw_rows}")
    print(f"[*] Unique Target Images:  {len(target_groups)}")
    
    conversion_stats = {
        "total_raw_rows": total_raw_rows,
        "unique_target_images": len(target_groups),
        "usable_images": 0,
        "discarded_images_watch_only": 0,
        "discarded_images_empty_masks": 0,
        "total_instances": 0,
        "per_split_images": Counter(),
        "per_split_instances": Counter(),
        "per_category_instances": Counter(),
        "multi_instance_images": 0,
    }
    
    print("[*] Processing and writing YOLO instance segmentation dataset...")
    
    processed_count = 0
    for target_name, rows in target_groups.items():
        if max_images and processed_count >= max_images:
            break
            
        target_bytes = rows[0]["target_bytes"]
        target_img = cv2.imdecode(np.frombuffer(target_bytes, np.uint8), cv2.IMREAD_COLOR)
        if target_img is None:
            continue
            
        all_yolo_lines = []
        categories_in_image = []
        
        for r in rows:
            cat = normalize_prompt(r["prompt"])
            if cat is None or cat not in JEWELMIND_CATEGORIES:
                continue
                
            class_id = JEWELMIND_CATEGORIES[cat]
            mask_bytes = r["mask_bytes"]
            raw_mask = cv2.imdecode(np.frombuffer(mask_bytes, np.uint8), cv2.IMREAD_GRAYSCALE)
            if raw_mask is None:
                continue
                
            # Invert inpainting mask
            jewel_mask = (raw_mask < 128).astype(np.uint8) * 255
            lines = mask_to_yolo_polygons(jewel_mask, class_id)
            if lines:
                all_yolo_lines.extend(lines)
                categories_in_image.append(cat)
                conversion_stats["per_category_instances"][cat] += len(lines)
                conversion_stats["total_instances"] += len(lines)
                
        if not all_yolo_lines:
            # Check if watch only
            prompts = [r["prompt"].lower() for r in rows]
            if any("watch" in p for p in prompts):
                conversion_stats["discarded_images_watch_only"] += 1
            else:
                conversion_stats["discarded_images_empty_masks"] += 1
            continue
            
        split = get_deterministic_split(target_name)
        stem = Path(target_name).stem
        
        img_out_path = output_dir / split / "images" / f"{stem}.jpg"
        lbl_out_path = output_dir / split / "labels" / f"{stem}.txt"
        
        cv2.imwrite(str(img_out_path), target_img)
        with open(lbl_out_path, "w", encoding="utf-8") as f:
            f.write("\n".join(all_yolo_lines) + "\n")
            
        conversion_stats["usable_images"] += 1
        conversion_stats["per_split_images"][split] += 1
        conversion_stats["per_split_instances"][split] += len(all_yolo_lines)
        if len(all_yolo_lines) > 1:
            conversion_stats["multi_instance_images"] += 1
            
        processed_count += 1
        if processed_count % 1000 == 0:
            print(f"    - Processed {processed_count} images (Usable: {conversion_stats['usable_images']})...")
            
    print("\n" + "=" * 70)
    print("CONVERSION SUMMARY RESULTS")
    print("=" * 70)
    print(f"Total Usable Images Written:     {conversion_stats['usable_images']}")
    print(f"Total Polygon Instances:         {conversion_stats['total_instances']}")
    print(f"Multi-Instance Images:           {conversion_stats['multi_instance_images']}")
    print(f"Discarded (Watch-Only):          {conversion_stats['discarded_images_watch_only']}")
    print(f"Discarded (Empty/Ambiguous):     {conversion_stats['discarded_images_empty_masks']}")
    print("-" * 70)
    print("Per-Split Distribution:")
    for sp in ["train", "val", "test"]:
        imgs = conversion_stats["per_split_images"][sp]
        insts = conversion_stats["per_split_instances"][sp]
        print(f"  - {sp.upper():<5}: {imgs:>5} images | {insts:>5} instances ({imgs/max(conversion_stats['usable_images'],1)*100:.1f}%)")
    print("-" * 70)
    print("Per-Category Instances in Generated Dataset:")
    for cat_name, cat_id in JEWELMIND_CATEGORIES.items():
        c_count = conversion_stats["per_category_instances"][cat_name]
        print(f"  - [{cat_id}] {cat_name:<16}: {c_count:>5} instances")
    print("=" * 70 + "\n")
    
    # Save conversion report JSON
    stats_path = output_dir / "conversion_stats.json"
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(conversion_stats, f, indent=2)
    print(f"[*] Saved conversion stats to: {stats_path.resolve()}")
    
    return conversion_stats


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert DWPose Parquet to YOLO11 segmentation.")
    parser.add_argument("--raw-dir", default="ai/vision/datasets/raw/jewelry-dwpose/data")
    parser.add_argument("--output-dir", default="ai/vision/datasets/jewellery_v2")
    parser.add_argument("--max-images", type=int, default=None)
    args = parser.parse_args()
    
    convert_dataset(Path(args.raw_dir), Path(args.output_dir), args.max_images)
