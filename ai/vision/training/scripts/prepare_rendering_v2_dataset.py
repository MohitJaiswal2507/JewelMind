"""JewelMind Rendering V2 Dataset Preparation Pipeline.

Ingests, filters, pairs, preprocesses, and splits local jewellery data into the
canonical Rendering V2 dataset structure (ai/vision/datasets/rendering_v2).

Features:
- 100% local operation: Zero network downloads, zero model training.
- Ingests from 3 local sources:
    1. V1 Paired Dataset (datasets/controlnet_paired/): 164 curated baseline pairs.
    2. MET Museum Archive (ai/vision/datasets/raw/met_jewellery/): High-res museum objects.
    3. DWPose Jewellery Crops (ai/vision/datasets/raw/jewelry-dwpose/): Masked jewelry crops.
- Excludes watches, ambiguous prompts, invalid/empty masks, corrupted files.
- Generates 512x512 letterboxed RGB targets and matching structural LineArt conditioning.
- Strict deduplication (SHA-256) and deterministic ~70/20/10 split by source object hash.
- Produces metadata.jsonl per split, DATASET_MANIFEST.json, and visual QA contact sheets.
"""

import argparse
import hashlib
import json
import logging
import os
import random
import shutil
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import cv2
import numpy as np
import pandas as pd
from PIL import Image

# Ensure workspace root is in sys.path
_ROOT = Path(__file__).resolve().parents[4]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from ai.rendering.preprocessing.structural import StructuralConditioningProcessor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("jewelmind.prepare_rendering_v2")

# Canonical 8-Category Taxonomy for JewelMind V2
CANONICAL_CATEGORIES = [
    "ring",
    "earring",
    "pendant",
    "necklace",
    "bracelet",
    "bangle",
    "brooch",
    "other_jewellery",
]

CATEGORY_ALIASES = {
    "ring": "ring",
    "earring": "earring",
    "pendant": "pendant",
    "necklace": "necklace",
    "bracelet": "bracelet",
    "bangle": "bangle",
    "brooch": "brooch",
    "other": "other_jewellery",
    "other_jewellery": "other_jewellery",
    "earrings": "earring",
    "rings": "ring",
    "pendants": "pendant",
    "necklaces": "necklace",
    "bracelets": "bracelet",
    "bangles": "bangle",
    "brooches": "brooch",
}


def compute_sha256(data_bytes: bytes) -> str:
    """Compute SHA-256 digest of binary bytes."""
    return hashlib.sha256(data_bytes).hexdigest()


def compute_file_sha256(filepath: Path) -> str:
    """Compute SHA-256 digest of a file on disk."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def get_deterministic_split(source_key: str) -> str:
    """Deterministic hash split: 70% train, 20% val, 10% test."""
    hash_val = int(hashlib.md5(source_key.encode("utf-8")).hexdigest(), 16) % 100
    if hash_val < 70:
        return "train"
    elif hash_val < 90:
        return "val"
    else:
        return "test"


def letterbox_image(
    img_bgr: np.ndarray,
    target_size: int = 512,
    bg_color: Tuple[int, int, int] = (255, 255, 255),
) -> Tuple[np.ndarray, Tuple[int, int, int, int]]:
    """Letterbox resize preserving aspect ratio."""
    h, w = img_bgr.shape[:2]
    scale = target_size / max(h, w)
    nw, nh = int(round(w * scale)), int(round(h * scale))
    resized = cv2.resize(img_bgr, (nw, nh), interpolation=cv2.INTER_AREA)

    pad_top = (target_size - nh) // 2
    pad_bottom = target_size - nh - pad_top
    pad_left = (target_size - nw) // 2
    pad_right = target_size - nw - pad_left

    canvas = cv2.copyMakeBorder(
        resized,
        pad_top,
        pad_bottom,
        pad_left,
        pad_right,
        cv2.BORDER_CONSTANT,
        value=bg_color,
    )
    return canvas, (pad_top, pad_bottom, pad_left, pad_right)


def parse_dwpose_prompt(prompt: str) -> Optional[str]:
    """Parse DWPose prompt into a single canonical category, or None if watch/ambiguous."""
    if not prompt:
        return None
    p_lower = prompt.lower().strip()

    # Strict exclusions
    if "watch" in p_lower or "clock" in p_lower:
        return None
    if "oops" in p_lower or "wasistbelt" in p_lower or "androgynous" in p_lower:
        return None

    # Priority parsing
    if "ring" in p_lower and "earring" not in p_lower and "spring" not in p_lower:
        return "ring"
    elif "earring" in p_lower:
        return "earring"
    elif "necklace" in p_lower:
        return "necklace"
    elif "bracelet" in p_lower:
        return "bracelet"
    elif "bangle" in p_lower:
        return "bangle"
    elif "pendant" in p_lower:
        return "pendant"
    elif "brooch" in p_lower:
        return "brooch"

    return None


class RenderingV2DatasetBuilder:
    """Manages ingestion, extraction, conditioning generation, and dataset creation."""

    def __init__(
        self,
        output_dir: Path,
        v1_data_dir: Path,
        met_data_dir: Path,
        dwpose_data_dir: Path,
        resolution: int = 512,
        seed: int = 42,
        dry_run: bool = False,
    ):
        self.output_dir = output_dir
        self.v1_data_dir = v1_data_dir
        self.met_data_dir = met_data_dir
        self.dwpose_data_dir = dwpose_data_dir
        self.resolution = resolution
        self.seed = seed
        self.dry_run = dry_run

        # Structural conditioning processor (running on CPU for zero GPU interference)
        self.processor = StructuralConditioningProcessor(
            target_width=resolution,
            target_height=resolution,
            device="cpu",
            use_neural_lineart=False,  # High-speed bilateral + Canny algorithmic LineArt
        )

        self.stats = {
            "sources": {
                "v1_paired": {"candidates": 0, "accepted": 0, "rejected": 0},
                "met_jewellery": {"candidates": 0, "accepted": 0, "rejected": 0},
                "dwpose_jewellery": {"candidates": 0, "accepted": 0, "rejected": 0},
            },
            "rejection_reasons": defaultdict(int),
            "splits": {"train": 0, "val": 0, "test": 0},
            "categories": defaultdict(lambda: {"train": 0, "val": 0, "test": 0, "total": 0}),
            "seen_target_hashes": set(),
            "accepted_records": [],
        }

        random.seed(seed)
        np.random.seed(seed)

    def process_v1_paired(self) -> List[Dict[str, Any]]:
        """Ingest existing 164 V1 paired samples."""
        records = []
        meta_file = self.v1_data_dir / "metadata" / "dataset_metadata.json"
        if not meta_file.exists():
            logger.warning("V1 paired metadata file not found at: %s", meta_file)
            return records

        with open(meta_file, "r", encoding="utf-8") as f:
            v1_items = json.load(f)

        logger.info("Found %d V1 paired candidate items", len(v1_items))
        self.stats["sources"]["v1_paired"]["candidates"] = len(v1_items)

        for item in v1_items:
            stem = item["stem"]
            cat_raw = item.get("jewellery_category", "other")
            canonical_cat = CATEGORY_ALIASES.get(cat_raw.lower(), "other_jewellery")

            source_img_rel = item.get("source_path") or f"images/{item['source_filename']}"
            source_img_path = self.v1_data_dir / source_img_rel
            cond_img_rel = item.get("conditioning_path") or f"conditioning/{item['conditioning_filename']}"
            cond_img_path = self.v1_data_dir / cond_img_rel

            if not source_img_path.exists() or not cond_img_path.exists():
                self.stats["sources"]["v1_paired"]["rejected"] += 1
                self.stats["rejection_reasons"]["missing_v1_file"] += 1
                continue

            # Load target image and compute hash
            target_bgr = cv2.imread(str(source_img_path))
            if target_bgr is None:
                self.stats["sources"]["v1_paired"]["rejected"] += 1
                self.stats["rejection_reasons"]["unreadable_target"] += 1
                continue

            # Letterbox target to 512x512
            target_512, _ = letterbox_image(target_bgr, target_size=self.resolution, bg_color=(255, 255, 255))
            target_bytes = cv2.imencode(".png", target_512)[1].tobytes()
            target_hash = compute_sha256(target_bytes)

            if target_hash in self.stats["seen_target_hashes"]:
                self.stats["sources"]["v1_paired"]["rejected"] += 1
                self.stats["rejection_reasons"]["duplicate_target_hash"] += 1
                continue

            # Load conditioning map
            cond_pil = Image.open(cond_img_path).convert("RGB")
            if cond_pil.size != (self.resolution, self.resolution):
                cond_pil = cond_pil.resize((self.resolution, self.resolution), Image.Resampling.LANCZOS)
            cond_bytes = io_pil_to_bytes(cond_pil)
            cond_hash = compute_sha256(cond_bytes)

            split = get_deterministic_split(f"v1_{stem}")

            record = {
                "id": f"R2_V1_{stem}",
                "source_dataset": "jewelmind_v1_paired",
                "source_id": stem,
                "canonical_category": canonical_cat,
                "source_category": cat_raw,
                "conditioning_type": "lineart",
                "prompt": item.get("caption") or f"photorealistic fine jewellery {canonical_cat} product photograph, studio lighting, clean background, sharp focus",
                "material": "polished precious metal",
                "gemstone": "faceted diamond",
                "width": self.resolution,
                "height": self.resolution,
                "sha256_target": target_hash,
                "sha256_conditioning": cond_hash,
                "edge_density": item.get("edge_density", 0.035),
                "split": split,
                "_target_img": target_512,
                "_cond_pil": cond_pil,
            }

            self.stats["seen_target_hashes"].add(target_hash)
            self.stats["sources"]["v1_paired"]["accepted"] += 1
            records.append(record)

        logger.info("Accepted %d V1 paired samples", len(records))
        return records

    def process_met_archive(self) -> List[Dict[str, Any]]:
        """Ingest MET museum jewellery archive."""
        records = []
        if not self.met_data_dir.exists():
            logger.warning("MET data directory not found at: %s", self.met_data_dir)
            return records

        all_met_files = []
        for cat_dir in self.met_data_dir.iterdir():
            if cat_dir.is_dir():
                cat_name = cat_dir.name
                for f in cat_dir.glob("*.jpg"):
                    all_met_files.append((f, cat_name))

        logger.info("Found %d MET candidate images across categories", len(all_met_files))
        self.stats["sources"]["met_jewellery"]["candidates"] = len(all_met_files)

        for img_path, cat_raw in all_met_files:
            canonical_cat = CATEGORY_ALIASES.get(cat_raw.lower(), "other_jewellery")

            img_bgr = cv2.imread(str(img_path))
            if img_bgr is None:
                self.stats["sources"]["met_jewellery"]["rejected"] += 1
                self.stats["rejection_reasons"]["unreadable_target"] += 1
                continue

            h, w = img_bgr.shape[:2]
            if h < 80 or w < 80:
                self.stats["sources"]["met_jewellery"]["rejected"] += 1
                self.stats["rejection_reasons"]["image_too_small"] += 1
                continue

            # Letterbox target to 512x512
            target_512, _ = letterbox_image(img_bgr, target_size=self.resolution, bg_color=(255, 255, 255))
            target_bytes = cv2.imencode(".png", target_512)[1].tobytes()
            target_hash = compute_sha256(target_bytes)

            if target_hash in self.stats["seen_target_hashes"]:
                self.stats["sources"]["met_jewellery"]["rejected"] += 1
                self.stats["rejection_reasons"]["duplicate_target_hash"] += 1
                continue

            # Generate structural lineart conditioning using CPU preprocessor
            target_pil = Image.fromarray(cv2.cvtColor(target_512, cv2.COLOR_BGR2RGB))
            cond_pil, cond_meta = self.processor.process(target_pil, target_width=self.resolution, target_height=self.resolution)

            edge_density = cond_meta.edge_density or 0.0
            if edge_density < 0.005:
                self.stats["sources"]["met_jewellery"]["rejected"] += 1
                self.stats["rejection_reasons"]["edge_density_too_low"] += 1
                continue
            if edge_density > 0.40:
                self.stats["sources"]["met_jewellery"]["rejected"] += 1
                self.stats["rejection_reasons"]["edge_density_too_high"] += 1
                continue

            cond_bytes = io_pil_to_bytes(cond_pil)
            cond_hash = compute_sha256(cond_bytes)

            stem = img_path.stem
            split = get_deterministic_split(f"met_{stem}")

            # Observable caption based on category
            cat_label = canonical_cat.replace("_", " ")
            caption = (
                f"photorealistic fine jewellery {cat_label} product photograph, "
                f"crafted in polished precious metal, museum artefact, studio lighting, clean neutral background, sharp focus"
            )

            record = {
                "id": f"R2_MET_{stem}",
                "source_dataset": "met_open_access",
                "source_id": stem,
                "canonical_category": canonical_cat,
                "source_category": cat_raw,
                "conditioning_type": "lineart",
                "prompt": caption,
                "material": "polished precious metal",
                "gemstone": "precious gemstone",
                "width": self.resolution,
                "height": self.resolution,
                "sha256_target": target_hash,
                "sha256_conditioning": cond_hash,
                "edge_density": round(edge_density, 4),
                "split": split,
                "_target_img": target_512,
                "_cond_pil": cond_pil,
            }

            self.stats["seen_target_hashes"].add(target_hash)
            self.stats["sources"]["met_jewellery"]["accepted"] += 1
            records.append(record)

        logger.info("Accepted %d MET archive samples", len(records))
        return records

    def process_dwpose_crops(self, max_per_category: int = 150) -> List[Dict[str, Any]]:
        """Ingest isolated high-quality jewellery crops from DWPose dataset."""
        records = []
        parquet_dir = self.dwpose_data_dir / "data"
        if not parquet_dir.exists():
            logger.warning("DWPose parquet data directory not found at: %s", parquet_dir)
            return records

        parquet_files = sorted(parquet_dir.glob("*.parquet"))
        logger.info("Scanning %d DWPose parquet files for ring, earring, necklace, bracelet crops...", len(parquet_files))

        category_counts = Counter()

        for p_file in parquet_files:
            if all(category_counts[c] >= max_per_category for c in ["ring", "earring", "necklace", "bracelet"]):
                logger.info("Reached quota (%d) across all DWPose categories. Concluding DWPose scanning.", max_per_category)
                break
            try:
                df = pd.read_parquet(p_file)
            except Exception as e:
                logger.warning("Error reading parquet %s: %s", p_file.name, e)
                continue

            self.stats["sources"]["dwpose_jewellery"]["candidates"] += len(df)

            for _, row in df.iterrows():
                prompt = str(row.get("prompt", ""))
                canonical_cat = parse_dwpose_prompt(prompt)
                if not canonical_cat:
                    self.stats["sources"]["dwpose_jewellery"]["rejected"] += 1
                    self.stats["rejection_reasons"]["watch_or_ambiguous_prompt"] += 1
                    continue

                if category_counts[canonical_cat] >= max_per_category:
                    continue

                target_data = row.get("target")
                mask_data = row.get("mask")

                target_bytes = target_data.get("bytes") if isinstance(target_data, dict) else target_data
                mask_bytes = mask_data.get("bytes") if isinstance(mask_data, dict) else mask_data

                if not target_bytes or not mask_bytes:
                    self.stats["sources"]["dwpose_jewellery"]["rejected"] += 1
                    self.stats["rejection_reasons"]["missing_bytes"] += 1
                    continue

                raw_img = cv2.imdecode(np.frombuffer(target_bytes, np.uint8), cv2.IMREAD_COLOR)
                raw_mask = cv2.imdecode(np.frombuffer(mask_bytes, np.uint8), cv2.IMREAD_GRAYSCALE)

                if raw_img is None or raw_mask is None:
                    self.stats["sources"]["dwpose_jewellery"]["rejected"] += 1
                    self.stats["rejection_reasons"]["decode_failure"] += 1
                    continue

                # Invert mask: active jewellery is mask < 128
                jewel_mask = (raw_mask < 128).astype(np.uint8) * 255
                non_zero = int(np.count_nonzero(jewel_mask))
                h, w = raw_img.shape[:2]
                area_pct = (non_zero / (h * w)) * 100.0

                # Reject invalid masks
                if non_zero < 30:
                    self.stats["sources"]["dwpose_jewellery"]["rejected"] += 1
                    self.stats["rejection_reasons"]["empty_or_tiny_mask"] += 1
                    continue
                if area_pct > 35.0:
                    self.stats["sources"]["dwpose_jewellery"]["rejected"] += 1
                    self.stats["rejection_reasons"]["huge_mask_over_35pct"] += 1
                    continue

                # Extract bounding box around jewelry mask
                coords = np.argwhere(jewel_mask > 0)
                y0, x0 = coords.min(axis=0)
                y1, x1 = coords.max(axis=0)
                bw, bh = x1 - x0, y1 - y0

                if bw < 30 or bh < 30:
                    self.stats["sources"]["dwpose_jewellery"]["rejected"] += 1
                    self.stats["rejection_reasons"]["jewellery_crop_too_small"] += 1
                    continue

                # Add 35% margin around bounding box for context
                margin = max(bw, bh) * 0.35
                cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
                side = max(bw, bh) + 2 * margin

                crop_x0 = max(0, int(cx - side / 2))
                crop_y0 = max(0, int(cy - side / 2))
                crop_x1 = min(w, int(cx + side / 2))
                crop_y1 = min(h, int(cy + side / 2))

                crop_img = raw_img[crop_y0:crop_y1, crop_x0:crop_x1]
                if crop_img.shape[0] < 30 or crop_img.shape[1] < 30:
                    self.stats["sources"]["dwpose_jewellery"]["rejected"] += 1
                    self.stats["rejection_reasons"]["crop_dimension_invalid"] += 1
                    continue

                # Letterbox crop to 512x512
                target_512, _ = letterbox_image(crop_img, target_size=self.resolution, bg_color=(0, 0, 0))
                target_bytes_512 = cv2.imencode(".png", target_512)[1].tobytes()
                target_hash = compute_sha256(target_bytes_512)

                if target_hash in self.stats["seen_target_hashes"]:
                    self.stats["sources"]["dwpose_jewellery"]["rejected"] += 1
                    self.stats["rejection_reasons"]["duplicate_target_hash"] += 1
                    continue

                # Generate conditioning
                target_pil = Image.fromarray(cv2.cvtColor(target_512, cv2.COLOR_BGR2RGB))
                cond_pil, cond_meta = self.processor.process(target_pil, target_width=self.resolution, target_height=self.resolution)
                edge_density = cond_meta.edge_density or 0.0

                if edge_density < 0.005 or edge_density > 0.40:
                    self.stats["sources"]["dwpose_jewellery"]["rejected"] += 1
                    self.stats["rejection_reasons"]["invalid_edge_density"] += 1
                    continue

                cond_bytes = io_pil_to_bytes(cond_pil)
                cond_hash = compute_sha256(cond_bytes)

                target_path_val = str(row["target"].get("path") if isinstance(row["target"], dict) else "dwpose_sample")
                stem = Path(target_path_val).stem
                item_id = f"R2_DW_{stem}_{canonical_cat}_{category_counts[canonical_cat]}"
                split = get_deterministic_split(f"dw_{stem}")

                record = {
                    "id": item_id,
                    "source_dataset": "jewelry_dwpose",
                    "source_id": stem,
                    "canonical_category": canonical_cat,
                    "source_category": prompt,
                    "conditioning_type": "lineart",
                    "prompt": f"photorealistic fine jewellery {canonical_cat} product photograph, studio lighting, crisp metallic highlights, sharp focus",
                    "material": "polished precious metal",
                    "gemstone": "faceted gemstone",
                    "width": self.resolution,
                    "height": self.resolution,
                    "sha256_target": target_hash,
                    "sha256_conditioning": cond_hash,
                    "edge_density": round(edge_density, 4),
                    "split": split,
                    "_target_img": target_512,
                    "_cond_pil": cond_pil,
                }

                self.stats["seen_target_hashes"].add(target_hash)
                self.stats["sources"]["dwpose_jewellery"]["accepted"] += 1
                category_counts[canonical_cat] += 1
                records.append(record)

        logger.info("Accepted %d DWPose crop samples (Distribution: %s)", len(records), dict(category_counts))
        return records

    def build_dataset(self) -> Dict[str, Any]:
        """Execute full dataset construction and export."""
        logger.info("==================================================")
        logger.info("STARTING JEWELMIND RENDERING V2 DATASET BUILDER")
        logger.info("Target Output Directory: %s", self.output_dir)
        logger.info("Dry Run Mode: %s", self.dry_run)
        logger.info("==================================================")

        all_records = []

        # 1. Ingest V1 Paired
        v1_records = self.process_v1_paired()
        all_records.extend(v1_records)

        # 2. Ingest MET Archive
        met_records = self.process_met_archive()
        all_records.extend(met_records)

        # 3. Ingest DWPose Crops (balanced per category)
        dw_records = self.process_dwpose_crops(max_per_category=150)
        all_records.extend(dw_records)

        # Update split and category metrics
        for rec in all_records:
            split = rec["split"]
            cat = rec["canonical_category"]
            self.stats["splits"][split] += 1
            self.stats["categories"][cat][split] += 1
            self.stats["categories"][cat]["total"] += 1

        self.stats["accepted_records"] = all_records
        total_accepted = len(all_records)
        logger.info("==================================================")
        logger.info("DATASET EXTRACTION COMPLETE: %d Total Accepted Pairs", total_accepted)
        logger.info("Splits: %s", dict(self.stats["splits"]))
        logger.info("==================================================")

        if self.dry_run:
            logger.info("[DRY RUN ACTIVE] Skipping physical disk writing.")
            return self.stats

        # Create output directories
        for split in ["train", "val", "test"]:
            (self.output_dir / split / "conditioning").mkdir(parents=True, exist_ok=True)
            (self.output_dir / split / "target").mkdir(parents=True, exist_ok=True)

        contact_dir = self.output_dir / "contact_sheets"
        contact_dir.mkdir(parents=True, exist_ok=True)

        split_file_handles = {
            "train": open(self.output_dir / "train" / "metadata.jsonl", "w", encoding="utf-8"),
            "val": open(self.output_dir / "val" / "metadata.jsonl", "w", encoding="utf-8"),
            "test": open(self.output_dir / "test" / "metadata.jsonl", "w", encoding="utf-8"),
        }

        contact_sheet_samples = defaultdict(list)

        try:
            for rec in all_records:
                split = rec["split"]
                rec_id = rec["id"]

                target_filename = f"{rec_id}.png"
                cond_filename = f"{rec_id}.png"

                target_out_path = self.output_dir / split / "target" / target_filename
                cond_out_path = self.output_dir / split / "conditioning" / cond_filename

                # Save Target Image (PNG)
                cv2.imwrite(str(target_out_path), rec["_target_img"])

                # Save Conditioning Image (PNG)
                rec["_cond_pil"].save(cond_out_path, format="PNG")

                # Prepare Clean JSONL record
                meta_record = {
                    "id": rec["id"],
                    "source_dataset": rec["source_dataset"],
                    "source_id": rec["source_id"],
                    "canonical_category": rec["canonical_category"],
                    "source_category": rec["source_category"],
                    "conditioning_type": rec["conditioning_type"],
                    "conditioning_path": f"{split}/conditioning/{cond_filename}",
                    "target_path": f"{split}/target/{target_filename}",
                    "prompt": rec["prompt"],
                    "material": rec["material"],
                    "gemstone": rec["gemstone"],
                    "width": rec["width"],
                    "height": rec["height"],
                    "sha256_conditioning": rec["sha256_conditioning"],
                    "sha256_target": rec["sha256_target"],
                    "edge_density": rec["edge_density"],
                    "split": rec["split"],
                }

                split_file_handles[split].write(json.dumps(meta_record) + "\n")

                # Save for visual contact sheets
                cat = rec["canonical_category"]
                if len(contact_sheet_samples[cat]) < 12:
                    contact_sheet_samples[cat].append((rec["_cond_pil"], rec["_target_img"], rec_id, cat))

        finally:
            for handle in split_file_handles.values():
                handle.close()

        # Write DATASET_MANIFEST.json
        manifest_data = {
            "dataset_name": "jewelmind_rendering_v2",
            "dataset_version": "2.0.0-candidate",
            "creation_timestamp": datetime.now(timezone.utc).isoformat(),
            "target_resolution": [self.resolution, self.resolution],
            "total_accepted_pairs": total_accepted,
            "split_distribution": dict(self.stats["splits"]),
            "category_distribution": {k: dict(v) for k, v in self.stats["categories"].items()},
            "source_statistics": {k: dict(v) for k, v in self.stats["sources"].items()},
            "rejection_reasons": dict(self.stats["rejection_reasons"]),
            "canonical_taxonomy": CANONICAL_CATEGORIES,
            "licensing": {
                "v1_paired": "CC0 1.0 Universal / Public Domain",
                "met_open_access": "CC0 1.0 Universal (Metropolitan Museum of Art)",
                "jewelry_dwpose": "Research Open Access",
            },
        }

        with open(self.output_dir / "DATASET_MANIFEST.json", "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2)
        logger.info("Saved DATASET_MANIFEST.json")

        # Generate Visual Contact Sheets
        self.generate_contact_sheets(contact_sheet_samples, contact_dir)

        return self.stats

    def generate_contact_sheets(self, samples_by_cat: Dict[str, List[Any]], output_dir: Path):
        """Render side-by-side [conditioning | target] contact sheets."""
        logger.info("Generating Visual QA contact sheets in %s...", output_dir)

        for cat, items in samples_by_cat.items():
            if not items:
                continue

            cells = []
            for cond_pil, target_bgr, rec_id, category in items:
                cond_np = cv2.cvtColor(np.array(cond_pil), cv2.COLOR_RGB2BGR)
                c_thumb = cv2.resize(cond_np, (180, 180))
                t_thumb = cv2.resize(target_bgr, (180, 180))

                pair_cell = np.hstack([c_thumb, t_thumb])
                cv2.putText(pair_cell, f"{rec_id[:18]}", (5, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 0), 1)
                cv2.putText(pair_cell, "LineArt | Target", (5, 175), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 255), 1)
                cells.append(pair_cell)

            if cells:
                cols = 2
                rows = (len(cells) + cols - 1) // cols
                cell_h, cell_w = 180, 360
                grid = np.full((rows * cell_h, cols * cell_w, 3), 25, dtype=np.uint8)

                for idx, cell in enumerate(cells):
                    r = idx // cols
                    c = idx % cols
                    grid[r * cell_h : (r + 1) * cell_h, c * cell_w : (c + 1) * cell_w] = cell

                out_path = output_dir / f"contact_sheet_{cat}.jpg"
                cv2.imwrite(str(out_path), grid)
                logger.info("Saved category contact sheet: %s", out_path.name)


def io_pil_to_bytes(pil_img: Image.Image, format: str = "PNG") -> bytes:
    """Serialize PIL Image to binary bytes."""
    import io
    buf = io.BytesIO()
    pil_img.save(buf, format=format)
    return buf.getvalue()


def main():
    parser = argparse.ArgumentParser(description="JewelMind Rendering V2 Dataset Builder")
    parser.add_argument("--output-dir", type=str, default="ai/vision/datasets/rendering_v2", help="Output dataset path")
    parser.add_argument("--v1-dir", type=str, default="datasets/controlnet_paired", help="V1 paired dataset path")
    parser.add_argument("--met-dir", type=str, default="ai/vision/datasets/raw/met_jewellery", help="MET archive path")
    parser.add_argument("--dwpose-dir", type=str, default="ai/vision/datasets/raw/jewelry-dwpose", help="DWPose path")
    parser.add_argument("--resolution", type=int, default=512, help="Target image size")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without writing images")
    args = parser.parse_args()

    builder = RenderingV2DatasetBuilder(
        output_dir=Path(args.output_dir),
        v1_data_dir=Path(args.v1_dir),
        met_data_dir=Path(args.met_dir),
        dwpose_data_dir=Path(args.dwpose_dir),
        resolution=args.resolution,
        seed=args.seed,
        dry_run=args.dry_run,
    )

    stats = builder.build_dataset()
    print("\nDataset Engineering Complete. Summary:")
    print(json.dumps({
        "total_accepted": len(stats["accepted_records"]),
        "splits": dict(stats["splits"]),
        "categories": {k: dict(v) for k, v in stats["categories"].items()},
        "sources": {k: dict(v) for k, v in stats["sources"].items()},
    }, indent=2))


if __name__ == "__main__":
    main()
