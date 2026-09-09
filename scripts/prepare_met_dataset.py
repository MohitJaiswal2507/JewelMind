"""JewelMind Met Open Access (CC0) Dataset Preparation Pipeline.

Ingests, filters, segments, and converts museum jewellery artefacts for:
- 2: pendant
- 5: bangle
- 6: brooch
- 7: other_jewellery

Features:
- Queries Met Museum Open Access API (CC0 1.0 Universal)
- Strict metadata validation against non-jewellery exclusions
- Studio background multi-cue GrabCut segmentation
- Exact YOLO polygon extraction with approxPolyDP contour simplification
- Deterministic 70/20/10 split by image hash (0% split leakage)
- Merges cleanly into ai/vision/datasets/jewellery_v2/ preserving DWPose foundation
"""

import argparse
import hashlib
import json
import os
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import cv2
import numpy as np
import requests

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

# Strict Query & Department Mapping for Met Collection
CATEGORY_SEARCH_TERMS = {
    "pendant": [
        "pendant",
        "locket",
        "gold pendant",
        "silver pendant",
        "jeweled pendant",
    ],
    "bangle": [
        "bangle",
        "armlet",
        "gold bangle",
        "silver bangle",
        "bangle bracelet",
        "torque bracelet",
    ],
    "brooch": [
        "brooch",
        "fibula",
        "gold brooch",
        "diamond brooch",
        "cameo brooch",
        "ornamental pin",
    ],
    "other_jewellery": [
        "tiara",
        "diadem",
        "hairpin",
        "hair ornament",
        "aigrette",
        "anklet",
        "cufflink",
        "cameo gem",
        "cameo",
        "intaglio",
    ],
}

# Strict Non-Jewellery Keywords to Discard
NON_JEWELLERY_KEYWORDS = [
    "watch", "clock", "painting", "drawing", "print", "textile", "rug", "carpet",
    "furniture", "chair", "table", "vessel", "pottery", "ceramic container", "vase",
    "bottle", "cup", "chalice", "bowl", "statue", "statuette", "relief", "fragment",
    "coin", "medal", "sculpture", "armor", "sword", "dagger", "shield", "helmet",
    "book", "manuscript", "photograph", "box", "case", "tray", "basket"
]


def is_valid_jewellery_metadata(obj_data: dict, target_category: str) -> bool:
    """Validate object metadata to ensure it is authentic jewellery and not a miscellaneous object."""
    if not obj_data.get("isPublicDomain", False):
        return False
        
    title = (obj_data.get("title") or "").lower()
    object_name = (obj_data.get("objectName") or "").lower()
    classification = (obj_data.get("classification") or "").lower()
    department = (obj_data.get("department") or "").lower()
    
    # Check title, object_name, classification for exclusions
    core_meta = f"{title} {object_name} {classification}"
    
    # Strictly reject non-jewellery exclusions
    for kw in ["painting", "drawing", "print", "furniture", "statue", "vase", "bowl", "watch", "clock", "coin", "armor", "dagger", "sword"]:
        if kw in core_meta:
            return False
            
    # Sculpture check: exclude only if in object_name or classification (not museum department)
    if "sculpture" in object_name or "sculpture" in classification:
        return False
        
    # Exclude drawings & prints department entirely
    if "drawings and prints" in department or "photographs" in department:
        return False
        
    # Category-specific validation
    combined_meta = f"{title} {object_name} {classification} {department}"
    if target_category == "pendant":
        return any(term in combined_meta for term in ["pendant", "locket", "medallion"])
    elif target_category == "bangle":
        return any(term in combined_meta for term in ["bangle", "armlet", "torque", "cuff"]) and "necklace" not in title
    elif target_category == "brooch":
        return any(term in combined_meta for term in ["brooch", "fibula", "badge", "pin"])
    elif target_category == "other_jewellery":
        return any(term in combined_meta for term in ["tiara", "diadem", "hairpin", "hair ornament", "aigrette", "anklet", "cufflink", "cameo", "intaglio"])
        
    return True


def segment_museum_object(img_bgr: np.ndarray) -> np.ndarray:
    """Robust multi-cue segmentation for studio museum artefacts on neutral backgrounds."""
    h, w = img_bgr.shape[:2]
    if h < 20 or w < 20:
        return np.zeros((h, w), dtype=np.uint8)
        
    # Profile background from border
    bw_pct = 0.04
    bx = max(4, int(w * bw_pct))
    by = max(4, int(h * bw_pct))
    
    border_mask = np.zeros((h, w), dtype=np.uint8)
    border_mask[:by, :] = 255
    border_mask[-by:, :] = 255
    border_mask[:, :bx] = 255
    border_mask[:, -bx:] = 255
    
    bg_pixels_bgr = img_bgr[border_mask > 0].astype(np.float32)
    bg_mean_bgr = np.median(bg_pixels_bgr, axis=0)
    
    bgr_dist = np.linalg.norm(img_bgr.astype(np.float32) - bg_mean_bgr, axis=2)
    
    lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
    bg_lab = cv2.cvtColor(np.uint8([[bg_mean_bgr]]), cv2.COLOR_BGR2LAB)[0, 0].astype(np.float32)
    lab_dist = np.linalg.norm(lab - bg_lab, axis=2)
    
    hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    sat = hsv[:, :, 1].astype(np.float32)
    
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 25, 90)
    edge_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    dilated_edges = cv2.dilate(edges, edge_kernel, iterations=1)
    
    bgr_norm = bgr_dist / (np.percentile(bgr_dist, 98) + 1e-4)
    lab_norm = lab_dist / (np.percentile(lab_dist, 98) + 1e-4)
    sat_norm = sat / (np.percentile(sat, 98) + 1e-4)
    
    combined_score = (bgr_norm * 0.45) + (lab_norm * 0.40) + (sat_norm * 0.15)
    combined_score = np.clip(combined_score, 0, 1.0)
    
    roi_score = combined_score[by:-by, bx:-bx]
    otsu_val, _ = cv2.threshold((roi_score * 255).astype(np.uint8), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    t = otsu_val / 255.0
    
    gc_mask = np.full((h, w), cv2.GC_PR_BGD, dtype=np.uint8)
    gc_mask[border_mask > 0] = cv2.GC_BGD
    
    fg_thresh = max(0.10, t * 0.80)
    bg_thresh = min(0.06, t * 0.30)
    
    gc_mask[combined_score > fg_thresh] = cv2.GC_PR_FGD
    gc_mask[(combined_score > fg_thresh * 1.25) | (dilated_edges > 0)] = cv2.GC_FGD
    gc_mask[combined_score < bg_thresh] = cv2.GC_BGD
    gc_mask[border_mask > 0] = cv2.GC_BGD
    
    bgd_model = np.zeros((1, 65), np.float64)
    fgd_model = np.zeros((1, 65), np.float64)
    rect = (bx, by, w - 2*bx, h - 2*by)
    
    try:
        if np.any(gc_mask == cv2.GC_PR_FGD) or np.any(gc_mask == cv2.GC_FGD):
            cv2.grabCut(img_bgr, gc_mask, rect, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_MASK)
        else:
            cv2.grabCut(img_bgr, gc_mask, rect, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_RECT)
        bin_mask = np.where((gc_mask == cv2.GC_FGD) | (gc_mask == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
    except Exception:
        # Fallback to otsu if GrabCut fails on uniform image
        bin_mask = (combined_score > t).astype(np.uint8) * 255
        
    clean_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    bin_mask = cv2.morphologyEx(bin_mask, cv2.MORPH_CLOSE, clean_kernel, iterations=2)
    bin_mask = cv2.morphologyEx(bin_mask, cv2.MORPH_OPEN, clean_kernel, iterations=1)
    
    # Filter out stand / isolated edge artifacts
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(bin_mask)
    if num_labels > 1:
        min_comp_area = (h * w) * 0.005 # At least 0.5% image size
        filtered_mask = np.zeros_like(bin_mask)
        for label_idx in range(1, num_labels):
            area = stats[label_idx, cv2.CC_STAT_AREA]
            left = stats[label_idx, cv2.CC_STAT_LEFT]
            top = stats[label_idx, cv2.CC_STAT_TOP]
            width = stats[label_idx, cv2.CC_STAT_WIDTH]
            height = stats[label_idx, cv2.CC_STAT_HEIGHT]
            
            # Reject bottom base stand
            if top + height >= h - by - 2 and height < (h * 0.15) and width > (w * 0.4):
                continue
            if area >= min_comp_area:
                filtered_mask[labels == label_idx] = 255
        bin_mask = filtered_mask
        
    return bin_mask


def mask_to_yolo_polygons(mask_img: np.ndarray, class_id: int, min_area_px: int = 50) -> List[str]:
    """Convert binary mask into normalized YOLO polygon contour lines."""
    h, w = mask_img.shape[:2]
    if h == 0 or w == 0:
        return []
        
    contours, _ = cv2.findContours(mask_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_TC89_KCOS)
    yolo_lines = []
    
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < min_area_px:
            continue
            
        epsilon = 0.0025 * cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, max(epsilon, 1.0), True)
        
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


def build_missing_categories_dataset(
    target_counts: Dict[str, int],
    raw_save_dir: Path,
    output_dataset_dir: Path,
    previews_dir: Path,
) -> Dict[str, Any]:
    print("=" * 75)
    print("JEWELMIND MULTI-JEWELLERY YOLO V2 MISSING CATEGORIES DATASET BUILDER")
    print("Source: Metropolitan Museum of Art Open Access Collection (CC0 1.0 Universal)")
    print("=" * 75)
    
    raw_save_dir.mkdir(parents=True, exist_ok=True)
    previews_dir.mkdir(parents=True, exist_ok=True)
    
    stats = {
        "source": "The Metropolitan Museum of Art Open Access Collection",
        "license": "Creative Commons Zero (CC0 1.0 Universal Public Domain)",
        "downloaded_per_category": Counter(),
        "usable_per_category": Counter(),
        "rejected_per_category": Counter(),
        "instances_per_category": Counter(),
        "per_split_images": Counter(),
        "per_split_instances": Counter(),
        "rejection_reasons": defaultdict(int),
        "total_new_images": 0,
        "total_new_instances": 0,
    }
    
    contact_sheet_samples = defaultdict(list)
    seen_image_hashes = set()
    
    # Load existing non-Met images in dataset to prevent duplicate hashes across sources
    for split in ["train", "val", "test"]:
        split_img_dir = output_dataset_dir / split / "images"
        if split_img_dir.exists():
            for p in split_img_dir.glob("*.*"):
                if not p.name.startswith("met_"):
                    hasher = hashlib.sha256()
                    with open(p, "rb") as f:
                        hasher.update(f.read())
                    seen_image_hashes.add(hasher.hexdigest())
                
    print(f"[*] Registered {len(seen_image_hashes)} foundation image hashes in {output_dataset_dir.name}")
    
    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(max_retries=3)
    session.mount("https://", adapter)
    
    for category, target_count in target_counts.items():
        class_id = JEWELMIND_CATEGORIES[category]
        print(f"\n[*] Processing Category: [{class_id}] '{category}' (Target: {target_count} usable images)...")
        
        usable_in_cat = 0
        cat_raw_dir = raw_save_dir / category
        cat_raw_dir.mkdir(parents=True, exist_ok=True)
        
        # Check already existing met images in dataset splits
        existing_split_images = []
        for split in ["train", "val", "test"]:
            for img_file in (output_dataset_dir / split / "images").glob(f"met_{category}_*.jpg"):
                lbl_file = output_dataset_dir / split / "labels" / f"{img_file.stem}.txt"
                if lbl_file.exists() and lbl_file.stat().st_size > 0:
                    existing_split_images.append((split, img_file, lbl_file))
                    
        if len(existing_split_images) >= target_count:
            print(f"    - Found {len(existing_split_images)} already prepared in {output_dataset_dir.name}. Loading...")
            for split, img_file, lbl_file in existing_split_images:
                usable_in_cat += 1
                stats["usable_per_category"][category] += 1
                with open(lbl_file, "r", encoding="utf-8") as lf:
                    lines = [ln.strip() for ln in lf if ln.strip()]
                stats["instances_per_category"][category] += len(lines)
                stats["per_split_images"][split] += 1
                stats["per_split_instances"][split] += len(lines)
                stats["total_new_images"] += 1
                stats["total_new_instances"] += len(lines)
                
                if len(contact_sheet_samples[category]) < 16:
                    img = cv2.imread(str(img_file))
                    if img is not None:
                        thumb = cv2.resize(img, (200, 200))
                        cv2.putText(thumb, f"{category} {img_file.stem.split('_')[-1]}", (6, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (0, 255, 0), 1)
                        contact_sheet_samples[category].append(thumb)
                        
            print(f"    [OK] '{category}': {usable_in_cat} usable images loaded ({stats['instances_per_category'][category]} polygon instances)")
            continue
            
        search_terms = CATEGORY_SEARCH_TERMS.get(category, [category])
        object_ids = []
        
        for term in search_terms:
            search_url = f"https://collectionapi.metmuseum.org/public/collection/v1/search?hasImages=true&isPublicDomain=true&q={term}"
            try:
                r = session.get(search_url, timeout=12)
                if r.status_code == 200:
                    ids = r.json().get("objectIDs") or []
                    for oid in ids:
                        if oid not in object_ids:
                            object_ids.append(oid)
            except Exception as e:
                print(f"    [WARN] Failed to search term '{term}': {e}")
                
        print(f"    - Found {len(object_ids)} public domain candidate objects for '{category}'")
        
        from concurrent.futures import ThreadPoolExecutor
        
        def fetch_candidate(oid: int) -> Optional[Tuple[int, dict, bytes]]:
            obj_url = f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{oid}"
            try:
                obj_r = requests.get(obj_url, timeout=(5, 10))
                if obj_r.status_code != 200:
                    return None
                obj_data = obj_r.json()
                if not is_valid_jewellery_metadata(obj_data, category):
                    return None
                img_url = obj_data.get("primaryImageSmall") or obj_data.get("primaryImage")
                if not img_url:
                    return None
                img_res = requests.get(img_url, timeout=(5, 15))
                if img_res.status_code != 200 or len(img_res.content) < 2000:
                    return None
                return oid, obj_data, img_res.content
            except Exception:
                return None
                
        # Process in parallel batches of 30
        batch_size = 30
        for i in range(0, len(object_ids), batch_size):
            if usable_in_cat >= target_count:
                break
            batch_ids = object_ids[i:i+batch_size]
            with ThreadPoolExecutor(max_workers=8) as executor:
                results = list(executor.map(fetch_candidate, batch_ids))
                
            for res in results:
                if res is None:
                    stats["rejected_per_category"][category] += 1
                    continue
                if usable_in_cat >= target_count:
                    break
                    
                oid, obj_data, img_bytes = res
                stem = f"met_{category}_{oid:07d}"
                raw_img_path = cat_raw_dir / f"{stem}.jpg"
                raw_mask_path = cat_raw_dir / f"{stem}_mask.png"
                
                # Check SHA-256
                img_sha256 = hashlib.sha256(img_bytes).hexdigest()
                if img_sha256 in seen_image_hashes:
                    stats["rejected_per_category"][category] += 1
                    stats["rejection_reasons"]["duplicate_image_hash"] += 1
                    continue
                    
                img_bgr = cv2.imdecode(np.frombuffer(img_bytes, np.uint8), cv2.IMREAD_COLOR)
                if img_bgr is None:
                    stats["rejected_per_category"][category] += 1
                    stats["rejection_reasons"]["image_decode_failed"] += 1
                    continue
                    
                h, w = img_bgr.shape[:2]
                if h < 100 or w < 100:
                    stats["rejected_per_category"][category] += 1
                    stats["rejection_reasons"]["image_too_small"] += 1
                    continue
                    
                # Multi-cue segmentation
                mask = segment_museum_object(img_bgr)
                mask_px = np.count_nonzero(mask)
                total_px = h * w
                mask_ratio = mask_px / total_px
                
                # Mask validation
                if mask_ratio < 0.005 or mask_ratio > 0.90:
                    stats["rejected_per_category"][category] += 1
                    stats["rejection_reasons"]["invalid_mask_area"] += 1
                    continue
                    
                # 5. Extract polygons
                yolo_polys = mask_to_yolo_polygons(mask, class_id=class_id)
                if not yolo_polys:
                    stats["rejected_per_category"][category] += 1
                    stats["rejection_reasons"]["degenerate_polygons"] += 1
                    continue
                    
                # Valid object!
                seen_image_hashes.add(img_sha256)
                usable_in_cat += 1
                stats["usable_per_category"][category] += 1
                stats["instances_per_category"][category] += len(yolo_polys)
                stats["total_new_images"] += 1
                stats["total_new_instances"] += len(yolo_polys)
                
                split = get_deterministic_split(stem)
                
                # Write to raw directory
                cv2.imwrite(str(raw_img_path), img_bgr)
                cv2.imwrite(str(raw_mask_path), mask)
                
                # Write to output YOLO dataset
                dest_img_path = output_dataset_dir / split / "images" / f"{stem}.jpg"
                dest_lbl_path = output_dataset_dir / split / "labels" / f"{stem}.txt"
                
                dest_img_path.parent.mkdir(parents=True, exist_ok=True)
                dest_lbl_path.parent.mkdir(parents=True, exist_ok=True)
                
                cv2.imwrite(str(dest_img_path), img_bgr)
                with open(dest_lbl_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(yolo_polys) + "\n")
                    
                stats["per_split_images"][split] += 1
                stats["per_split_instances"][split] += len(yolo_polys)
                
                # Save for contact sheet
                if len(contact_sheet_samples[category]) < 16:
                    overlay = img_bgr.copy()
                    overlay[mask > 0] = cv2.addWeighted(img_bgr[mask > 0], 0.5, np.full_like(img_bgr[mask > 0], (0, 220, 255)), 0.5, 0)
                    thumb = cv2.resize(overlay, (200, 200))
                    cv2.putText(thumb, f"{category} #{oid}", (6, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 2)
                    cv2.putText(thumb, f"{category} #{oid}", (6, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
                    contact_sheet_samples[category].append(thumb)
                    
                if usable_in_cat % 25 == 0:
                    print(f"      - {category}: {usable_in_cat}/{target_count} prepared...", flush=True)
                
        print(f"    [COMPLETED] '{category}': {usable_in_cat} usable images ({stats['instances_per_category'][category]} polygon instances)")
        
    # Generate Visual Contact Sheets for every new category
    print("\n[*] Generating visual contact sheets for new categories...")
    for category, thumbs in contact_sheet_samples.items():
        if not thumbs:
            continue
        # Grid 4x4 or 4xN
        n = len(thumbs)
        cols = 4
        rows = (n + cols - 1) // cols
        
        grid_img = np.full((rows * 200, cols * 200, 3), 30, dtype=np.uint8)
        for i, thumb in enumerate(thumbs):
            r = i // cols
            c = i % cols
            grid_img[r*200:(r+1)*200, c*200:(c+1)*200] = thumb
            
        sheet_path = previews_dir / f"contact_sheet_{category}.jpg"
        cv2.imwrite(str(sheet_path), grid_img)
        print(f"    - Saved contact sheet: {sheet_path}")
        
    return stats


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Harvest and prepare Met CC0 jewellery data for missing classes.")
    parser.add_argument("--pendant-count", type=int, default=200)
    parser.add_argument("--bangle-count", type=int, default=160)
    parser.add_argument("--brooch-count", type=int, default=200)
    parser.add_argument("--other-count", type=int, default=180)
    parser.add_argument("--raw-dir", default="ai/vision/datasets/raw/met_jewellery")
    parser.add_argument("--dataset-dir", default="ai/vision/datasets/jewellery_v2")
    parser.add_argument("--previews-dir", default="ai/vision/datasets/previews/new_categories")
    args = parser.parse_args()
    
    target_counts = {
        "pendant": args.pendant_count,
        "bangle": args.bangle_count,
        "brooch": args.brooch_count,
        "other_jewellery": args.other_count,
    }
    
    build_missing_categories_dataset(
        target_counts=target_counts,
        raw_save_dir=Path(args.raw_dir),
        output_dataset_dir=Path(args.dataset_dir),
        previews_dir=Path(args.previews_dir),
    )
