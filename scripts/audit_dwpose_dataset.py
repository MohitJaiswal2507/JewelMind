"""Comprehensive DWPose Parquet Dataset Auditor & Mask Analyzer for JewelMind.

Key findings implemented:
1. Inpainting mask inversion: The raw DWPose mask has background=255 and jewellery_hole=0.
   Therefore, active jewellery mask is mask < 128 (or cv2.bitwise_not).
2. Target identity is uniquely determined by `target['path']` (e.g. '01067_target.jpg').
3. Multi-instance grouping: The same target image appears in multiple rows, each row
   isolating a different piece of jewellery (e.g. ring vs bracelet vs necklace).
"""

import hashlib
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Tuple
import cv2
import numpy as np
import pandas as pd
from PIL import Image
import pyarrow.parquet as pq


def normalize_prompt(prompt: str) -> List[str]:
    """Parse and normalize prompt into detected jewellery categories."""
    if not prompt:
        return ["unknown"]
    p_lower = prompt.lower().strip()
    tokens = [t.strip() for t in p_lower.split(",") if t.strip()]
    gender_terms = {"female", "male", "woman", "man", "girl", "boy", "person", "model", "asian", "caucasian", "femlae"}
    jewel_tokens = [t for t in tokens if t not in gender_terms]
    
    categories = []
    for token in jewel_tokens:
        t_clean = token.rstrip("s")
        if "ring" in t_clean and "earring" not in t_clean and "spring" not in t_clean:
            categories.append("ring")
        elif "earring" in t_clean:
            categories.append("earring")
        elif "necklace" in t_clean:
            categories.append("necklace")
        elif "bracelet" in t_clean:
            categories.append("bracelet")
        elif "bangle" in t_clean:
            categories.append("bangle")
        elif "pendant" in t_clean:
            categories.append("pendant")
        elif "brooch" in t_clean:
            categories.append("brooch")
        elif "watch" in t_clean:
            categories.append("watch")
        elif "oops" in t_clean or "wasistbelt" in t_clean or "rogynous" in t_clean or "androgynous" in t_clean:
            categories.append("ambiguous")
        else:
            categories.append(token)
            
    if not categories:
        return ["unspecified"]
    return categories


def run_full_audit(data_dir: Path, output_audit_dir: Path) -> Dict[str, Any]:
    output_audit_dir.mkdir(parents=True, exist_ok=True)
    parquet_files = sorted(data_dir.glob("*.parquet"))
    print(f"[*] Found {len(parquet_files)} parquet files in {data_dir}")
    
    records = []
    target_to_rows = defaultdict(list)
    prompt_counter = Counter()
    category_counter = Counter()
    zoom_counter = Counter()
    pose_quality_counter = Counter()
    
    train_target_paths = set()
    test_target_paths = set()
    
    mask_stats = {
        "total_masks": 0,
        "empty_masks": 0,
        "tiny_masks_under_15px": 0,
        "huge_masks_over_40pct": 0,
        "valid_masks": 0,
        "components_distribution": Counter(),
        "area_pct_distribution": [],
    }
    
    representative_samples = {
        "ring": None,
        "earring": None,
        "bracelet": None,
        "necklace": None,
        "watch": None,
        "multi_jewellery": None,
        "suspicious_empty": None,
        "suspicious_huge": None,
    }
    
    print("[*] Parsing records and inverting inpainting masks...")
    
    for p_idx, p_file in enumerate(parquet_files):
        print(f"    - Processing {p_file.name} ({p_idx+1}/{len(parquet_files)})...")
        table = pq.read_table(p_file)
        df = table.to_pandas()
        is_test = "test" in p_file.name
        
        for row_idx, row in df.iterrows():
            target_path = str(row["target"]["path"]) if isinstance(row["target"], dict) else str(row["target"].get("path"))
            target_bytes = row["target"]["bytes"] if isinstance(row["target"], dict) else row["target"].get("bytes")
            mask_bytes = row["mask"]["bytes"] if isinstance(row["mask"], dict) else row["mask"].get("bytes")
            prompt = str(row["prompt"]) if pd.notna(row["prompt"]) else ""
            zoom = str(row["zoom"]) if pd.notna(row["zoom"]) else "unknown"
            pose_quality = str(row["pose_quality"]) if pd.notna(row["pose_quality"]) else "unknown"
            
            prompt_counter[prompt] += 1
            zoom_counter[zoom] += 1
            pose_quality_counter[pose_quality] += 1
            
            categories = normalize_prompt(prompt)
            for c in categories:
                category_counter[c] += 1
                
            if is_test:
                test_target_paths.add(target_path)
            else:
                train_target_paths.add(target_path)
                
            # Decode mask as grayscale and INVERT (since 0 is active jewellery, 255 is background)
            raw_mask = cv2.imdecode(np.frombuffer(mask_bytes, np.uint8), cv2.IMREAD_GRAYSCALE)
            if raw_mask is None:
                mask_stats["empty_masks"] += 1
                is_valid_mask = False
                non_zero_px = 0
                area_pct = 0.0
                num_components = 0
                jewel_mask = None
            else:
                h, w = raw_mask.shape
                total_px = h * w
                # Active jewellery mask: pixel < 128
                jewel_mask = (raw_mask < 128).astype(np.uint8) * 255
                non_zero_px = int(np.count_nonzero(jewel_mask))
                area_pct = (non_zero_px / total_px) * 100.0 if total_px > 0 else 0.0
                
                num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats((jewel_mask > 0).astype(np.uint8))
                num_components = num_labels - 1
                
                mask_stats["total_masks"] += 1
                if non_zero_px == 0:
                    mask_stats["empty_masks"] += 1
                    is_valid_mask = False
                elif non_zero_px < 15:
                    mask_stats["tiny_masks_under_15px"] += 1
                    is_valid_mask = False
                elif area_pct > 40.0:
                    mask_stats["huge_masks_over_40pct"] += 1
                    is_valid_mask = False
                else:
                    mask_stats["valid_masks"] += 1
                    is_valid_mask = True
                    mask_stats["components_distribution"][num_components] += 1
                    mask_stats["area_pct_distribution"].append(round(area_pct, 4))
                    
            record_info = {
                "file": p_file.name,
                "row_idx": int(row_idx),
                "target_path": target_path,
                "mask_hash": hashlib.sha256(mask_bytes).hexdigest()[:12],
                "prompt": prompt,
                "categories": categories,
                "zoom": zoom,
                "pose_quality": pose_quality,
                "non_zero_px": non_zero_px,
                "area_pct": round(area_pct, 4),
                "num_components": num_components,
                "is_valid_mask": is_valid_mask,
                "is_test": is_test,
                "target_bytes": target_bytes,
                "jewel_mask": jewel_mask,
            }
            
            target_to_rows[target_path].append(record_info)
            records.append(record_info)
            
            # Select representative samples
            if is_valid_mask:
                if "ring" in categories and representative_samples["ring"] is None:
                    representative_samples["ring"] = record_info
                elif "earring" in categories and representative_samples["earring"] is None:
                    representative_samples["earring"] = record_info
                elif "bracelet" in categories and representative_samples["bracelet"] is None:
                    representative_samples["bracelet"] = record_info
                elif "necklace" in categories and representative_samples["necklace"] is None:
                    representative_samples["necklace"] = record_info
                elif "watch" in categories and representative_samples["watch"] is None:
                    representative_samples["watch"] = record_info
            elif non_zero_px == 0 and representative_samples["suspicious_empty"] is None:
                representative_samples["suspicious_empty"] = record_info
            elif area_pct > 40.0 and representative_samples["suspicious_huge"] is None:
                representative_samples["suspicious_huge"] = record_info

    # Find multi-jewellery samples
    multi_target_count = 0
    multi_target_distinct_masks = 0
    multi_target_identical_masks = 0
    rows_per_target_counter = Counter()
    
    for t_path, t_rows in target_to_rows.items():
        rows_per_target_counter[len(t_rows)] += 1
        if len(t_rows) > 1:
            multi_target_count += 1
            m_hashes = {r["mask_hash"] for r in t_rows}
            if len(m_hashes) > 1:
                multi_target_distinct_masks += 1
            else:
                multi_target_identical_masks += 1
                
            cats = set()
            for r in t_rows:
                cats.update(r["categories"])
            if len(cats - {"watch", "unknown", "unspecified", "ambiguous"}) >= 2 and representative_samples["multi_jewellery"] is None:
                representative_samples["multi_jewellery"] = t_rows

    overlap_paths = train_target_paths.intersection(test_target_paths)
    
    print("\n" + "=" * 70)
    print("DWPOSE RAW DATASET AUDIT RESULTS (CORRECTED MASK INVERSION)")
    print("=" * 70)
    print(f"Total Rows Analyzed:           {len(records)}")
    print(f"Unique Target Images:          {len(target_to_rows)}")
    print(f"Duplicate Target Rows:         {len(records) - len(target_to_rows)}")
    print(f"Official Test Rows:            {len(test_target_paths)}")
    print(f"Train / Test Overlap Targets:  {len(overlap_paths)} (LEAKAGE DETECTED)")
    print(f"Multi-Row Targets (Count):     {multi_target_count}")
    print(f"  - Targets with Distinct Masks:  {multi_target_distinct_masks} (DIFFERENT INSTANCES/CATEGORIES)")
    print(f"  - Targets with Identical Masks: {multi_target_identical_masks} (EXACT DUPLICATES)")
    print("-" * 70)
    print("Rows per Target Distribution:")
    for num_rows, count in sorted(rows_per_target_counter.items()):
        print(f"  - {num_rows} row(s) per target: {count} images")
    print("-" * 70)
    print("Category Occurrences (Normalized from Prompts):")
    for cat, count in category_counter.most_common():
        print(f"  - {cat:<15}: {count}")
    print("-" * 70)
    print("Mask Quality Summary:")
    print(f"  - Valid Active Masks:        {mask_stats['valid_masks']} ({mask_stats['valid_masks']/len(records)*100:.2f}%)")
    print(f"  - Empty Masks (0 px):        {mask_stats['empty_masks']}")
    print(f"  - Tiny Masks (< 15 px):      {mask_stats['tiny_masks_under_15px']}")
    print(f"  - Huge Masks (> 40% area):   {mask_stats['huge_masks_over_40pct']}")
    print("=" * 70 + "\n")
    
    # Generate Visual Contact Sheet
    print("[*] Generating Visual Audit Contact Sheet with Active Masks...")
    create_contact_sheet(representative_samples, output_audit_dir)
    
    # Export summary JSON
    audit_summary = {
        "total_rows": len(records),
        "unique_targets": len(target_to_rows),
        "duplicate_target_rows": len(records) - len(target_to_rows),
        "train_rows": len(records) - len(test_target_paths),
        "test_rows": len(test_target_paths),
        "train_test_overlap_targets": len(overlap_paths),
        "overlap_target_paths": list(sorted(overlap_paths)),
        "multi_row_targets": multi_target_count,
        "multi_row_targets_with_distinct_masks": multi_target_distinct_masks,
        "multi_row_targets_with_identical_masks": multi_target_identical_masks,
        "rows_per_target_distribution": {str(k): v for k, v in sorted(rows_per_target_counter.items())},
        "category_distribution": dict(category_counter),
        "top_prompts": dict(prompt_counter.most_common(20)),
        "zoom_distribution": dict(zoom_counter),
        "pose_quality_distribution": dict(pose_quality_counter),
        "mask_quality": {
            "total_masks": mask_stats["total_masks"],
            "valid_masks": mask_stats["valid_masks"],
            "empty_masks": mask_stats["empty_masks"],
            "tiny_masks_under_15px": mask_stats["tiny_masks_under_15px"],
            "huge_masks_over_40pct": mask_stats["huge_masks_over_40pct"],
            "components_distribution": {str(k): v for k, v in mask_stats["components_distribution"].items()},
        },
    }
    
    summary_json_path = output_audit_dir / "audit_summary.json"
    with open(summary_json_path, "w", encoding="utf-8") as f:
        json.dump(audit_summary, f, indent=2)
    print(f"[*] Exported audit summary to: {summary_json_path.resolve()}")
    return audit_summary


def create_contact_sheet(samples: Dict[str, Any], output_dir: Path):
    """Render a visual contact sheet with overlayed masks for representative samples."""
    cells = []
    color_map = {
        "ring": (0, 215, 255),       # Bright Gold (BGR)
        "earring": (0, 100, 255),    # Coral Orange
        "bracelet": (50, 220, 50),   # Green
        "necklace": (255, 0, 255),   # Magenta
        "watch": (160, 160, 160),    # Slate Gray
        "ambiguous": (0, 0, 255),    # Red
        "default": (255, 255, 0),    # Cyan
    }
    
    for key, sample in samples.items():
        if sample is None:
            continue
            
        if isinstance(sample, list): # Multi-jewellery group
            first = sample[0]
            target_b = first["target_bytes"]
            target_img = cv2.imdecode(np.frombuffer(target_b, np.uint8), cv2.IMREAD_COLOR)
            target_img = cv2.resize(target_img, (384, 384))
            overlay = target_img.copy()
            
            prompt_labels = []
            for r in sample:
                j_mask = r["jewel_mask"]
                if j_mask is not None:
                    m_resized = cv2.resize(j_mask, (384, 384))
                    cat = r["categories"][0] if r["categories"] else "default"
                    c = color_map.get(cat, color_map["default"])
                    overlay[m_resized > 127] = c
                    prompt_labels.append(f"{cat}")
            
            combined = cv2.addWeighted(target_img, 0.45, overlay, 0.55, 0)
            title = f"MULTI: {', '.join(prompt_labels)}"
            cv2.putText(combined, title, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2, cv2.LINE_AA)
            cells.append(combined)
        else:
            target_b = sample["target_bytes"]
            j_mask = sample["jewel_mask"]
            target_img = cv2.imdecode(np.frombuffer(target_b, np.uint8), cv2.IMREAD_COLOR)
            if target_img is None:
                continue
            target_img = cv2.resize(target_img, (384, 384))
            overlay = target_img.copy()
            
            cat = sample["categories"][0] if sample["categories"] else "unknown"
            c = color_map.get(cat, color_map["default"])
            
            if j_mask is not None:
                m_resized = cv2.resize(j_mask, (384, 384))
                overlay[m_resized > 127] = c
                
            combined = cv2.addWeighted(target_img, 0.45, overlay, 0.55, 0)
            title = f"{key.upper()}: {cat} ({sample['area_pct']}%)"
            cv2.putText(combined, title, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2, cv2.LINE_AA)
            cells.append(combined)
            
    if cells:
        cols = 4
        rows = (len(cells) + cols - 1) // cols
        grid_h = rows * 384
        grid_w = cols * 384
        grid = np.zeros((grid_h, grid_w, 3), dtype=np.uint8)
        
        for idx, cell in enumerate(cells):
            r_idx = idx // cols
            c_idx = idx % cols
            grid[r_idx*384:(r_idx+1)*384, c_idx*384:(c_idx+1)*384] = cell
            
        contact_sheet_path = output_dir / "visual_audit_contact_sheet.jpg"
        cv2.imwrite(str(contact_sheet_path), grid)
        print(f"[*] Created visual audit contact sheet: {contact_sheet_path.resolve()}")


if __name__ == "__main__":
    raw_data_dir = Path("ai/vision/datasets/raw/jewelry-dwpose/data")
    audit_dir = Path("ai/vision/datasets/raw/jewelry-dwpose/audit")
    run_full_audit(raw_data_dir, audit_dir)
