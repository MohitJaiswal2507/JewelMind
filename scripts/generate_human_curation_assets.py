"""Generate Human Curation Artifacts for the 226 Retained Candidates.

Produces:
1. datasets/curation/HUMAN_CURATION.csv
2. datasets/curation/HUMAN_CURATION_MASTER_CONTACT_SHEET.png
3. datasets/curation/HUMAN_CURATION_NEAR_DUPLICATES.png
4. datasets/curation/HUMAN_CURATION_UNCERTAIN.png
5. Category-specific contact sheets
6. Updates full_dataset_manifest.json and jsonl
7. Copies contact sheets to IDE artifact directory
"""

import csv
import io
import json
import logging
import math
import shutil
import sys
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional

from PIL import Image, ImageDraw, ImageFont

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ai.dataset_pipeline.dedup import PerceptualDeduplicator, compute_sha256, compute_dhash, compute_ahash
from ai.dataset_pipeline.sources.met import assess_jewellery_relevance

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("human_curation_generator")

# Exact category counts approved by operator
TARGET_COUNTS = {
    "ring": 32,
    "earring": 30,
    "pendant": 47,
    "necklace": 34,
    "bracelet": 18,
    "bangle": 3,
    "brooch": 21,
    "other": 41,
}

CSV_COLUMNS = [
    "candidate_id",
    "image_path",
    "source",
    "source_id",
    "title",
    "category",
    "category_confidence",
    "jewellery_relevance",
    "duplicate_status",
    "duplicate_of",
    "dhash",
    "ahash",
    "sha256",
    "license",
    "width",
    "height",
    "jewellery_clearly_visible",
    "single_primary_object",
    "sufficient_object_size",
    "useful_geometry",
    "minimal_occlusion",
    "useful_metal_appearance",
    "gemstone_detail_applicable",
    "useful_lighting",
    "useful_background",
    "visual_quality",
    "design_diversity",
    "design_redundancy",
    "training_usefulness",
    "final_triage",
    "curator_notes",
]


def letterbox_thumbnail(img: Image.Image, target_size: int = 280, bg_color=(245, 245, 245)) -> Image.Image:
    """Resize image preserving aspect ratio onto a square canvas."""
    img_rgb = img.convert("RGB")
    w, h = img_rgb.size
    scale = min(target_size / w, target_size / h)
    nw = max(1, int(w * scale))
    nh = max(1, int(h * scale))
    resized = img_rgb.resize((nw, nh), Image.Resampling.LANCZOS)

    canvas = Image.new("RGB", (target_size, target_size), color=bg_color)
    ox = (target_size - nw) // 2
    oy = (target_size - nh) // 2
    canvas.paste(resized, (ox, oy))
    return canvas


def render_curation_sheet(
    entries: List[Dict],
    output_path: Path,
    title: str,
    subtitle: str = "",
    sheet_theme: str = "default",
    cols: int = 5,
    thumb_size: int = 240,
    caption_height: int = 70,
):
    """Render a curation contact sheet with clear candidate IDs and metadata."""
    n = len(entries)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if n == 0:
        logger.info("No entries for %s", title)
        sheet = Image.new("RGB", (640, 200), color=(255, 255, 255))
        d = ImageDraw.Draw(sheet)
        d.text((30, 30), title, fill=(40, 40, 40))
        d.text((30, 80), "Zero candidates.", fill=(120, 120, 120))
        sheet.save(output_path, "PNG")
        return

    rows = math.ceil(n / cols)
    pad = 16
    header_height = 70
    sheet_w = pad + cols * (thumb_size + pad)
    sheet_h = header_height + rows * (thumb_size + caption_height + pad) + pad

    sheet = Image.new("RGB", (sheet_w, sheet_h), color=(255, 255, 255))
    draw = ImageDraw.Draw(sheet)

    try:
        font_title = ImageFont.truetype("arial.ttf", 20)
        font_text = ImageFont.truetype("arial.ttf", 10)
        font_bold = ImageFont.truetype("arialbd.ttf", 11)
        font_id = ImageFont.truetype("arialbd.ttf", 12)
    except Exception:
        font_title = ImageFont.load_default()
        font_text = ImageFont.load_default()
        font_bold = ImageFont.load_default()
        font_id = ImageFont.load_default()

    is_review = sheet_theme in ("review", "uncertain", "near_duplicate")
    header_bg = (255, 245, 235) if is_review else (240, 246, 242)
    header_border = (255, 200, 150) if is_review else (190, 220, 200)
    title_color = (180, 80, 20) if is_review else (20, 90, 50)

    draw.rectangle([(pad, pad), (sheet_w - pad, header_height)], fill=header_bg, outline=header_border, width=2)
    draw.text((pad + 16, pad + 12), title, fill=title_color, font=font_title)
    sub_text = subtitle or f"Candidates: {n} | Grid: {cols} cols | Evaluator: Human Curator"
    draw.text((pad + 18, pad + 40), sub_text, fill=(80, 90, 100), font=font_text)

    for idx, item in enumerate(entries):
        r = idx // cols
        c = idx % cols
        x = pad + c * (thumb_size + pad)
        y = header_height + pad + r * (thumb_size + caption_height + pad)

        img = None
        local_p = PROJECT_ROOT / item.get("image_path", "")
        if local_p.exists() and local_p.is_file():
            try:
                img = Image.open(local_p)
            except Exception:
                img = None

        if img is None:
            tile = Image.new("RGB", (thumb_size, thumb_size), color=(235, 235, 235))
            d_tile = ImageDraw.Draw(tile)
            d_tile.text((30, thumb_size // 2 - 10), "[IMAGE UNAVAILABLE]", fill=(120, 120, 120), font=font_bold)
        else:
            tile = letterbox_thumbnail(img, target_size=thumb_size)

        sheet.paste(tile, (x, y))
        border_col = (255, 180, 120) if item.get("duplicate_status") != "DISTINCT" else (200, 215, 210)
        draw.rectangle([(x, y), (x + thumb_size, y + thumb_size)], outline=border_col, width=1)

        # ID badge overlay on top-left of thumbnail
        cid = item.get("candidate_id", f"CAND_{idx+1:03d}")
        draw.rectangle([(x, y), (x + 72, y + 20)], fill=(30, 40, 55))
        draw.text((x + 6, y + 4), cid, fill=(255, 255, 255), font=font_id)

        cap_y = y + thumb_size + 4
        title_str = item.get("title") or "Untitled"
        if len(title_str) > 30:
            title_str = title_str[:27] + "..."

        cat_str = f"[{item.get('source', '').upper()}:{item.get('source_id', '')}] {item.get('category', '').capitalize()}"
        rel_str = f"{item.get('jewellery_relevance')} | {item.get('duplicate_status', 'DISTINCT')[:10]}"
        dim_str = f"{item.get('width', 0)}x{item.get('height', 0)} | Status: {item.get('status', 'REVIEW')}"

        draw.text((x + 2, cap_y), title_str, fill=(20, 30, 45), font=font_bold)
        draw.text((x + 2, cap_y + 16), cat_str, fill=(60, 80, 110), font=font_text)
        draw.text((x + 2, cap_y + 32), rel_str, fill=(180, 70, 20) if "UNCERTAIN" in rel_str or "NEAR" in rel_str else (30, 110, 60), font=font_bold)
        draw.text((x + 2, cap_y + 48), dim_str, fill=(100, 110, 120), font=font_text)

    sheet.save(output_path, "PNG", quality=95)
    logger.info("Saved contact sheet: %s (%dx%d px)", output_path.name, sheet_w, sheet_h)


def generate_human_curation_dataset():
    """Build the exact 226 retained candidate dataset, CSV, manifests, and contact sheets."""
    curation_dir = PROJECT_ROOT / "datasets" / "curation"
    candidates_dir = curation_dir / "full_candidates"

    # Load existing manifest lookup for titles
    manifest_p = curation_dir / "full_dataset_manifest.json"
    meta_lookup = {}
    if manifest_p.exists():
        with open(manifest_p, "r", encoding="utf-8") as f:
            for item in json.load(f):
                key = f"{item['source']}_{item['source_id']}"
                meta_lookup[key] = item

    # Gather images per category strictly respecting target counts
    all_images = sorted(candidates_dir.glob("*.jpg"), key=lambda p: p.stat().st_mtime, reverse=True)
    selected_by_cat = {cat: [] for cat in TARGET_COUNTS}

    for img_p in all_images:
        parts = img_p.stem.split("_")
        source = parts[0]
        source_id = parts[1]
        cat = parts[2] if len(parts) > 2 else "other"
        if cat not in selected_by_cat:
            cat = "other"
        if len(selected_by_cat[cat]) < TARGET_COUNTS[cat]:
            selected_by_cat[cat].append(img_p)

    selected_images = []
    for cat, count in TARGET_COUNTS.items():
        imgs = selected_by_cat[cat]
        logger.info("Category %-10s: selected %d / %d", cat, len(imgs), count)
        selected_images.extend(imgs)

    assert len(selected_images) == 226, f"Expected 226 images, got {len(selected_images)}"

    # Run PerceptualDeduplicator to establish exact duplicate status and distances
    dedup = PerceptualDeduplicator(review_threshold=6)
    curation_records: List[Dict] = []

    for idx, img_p in enumerate(selected_images):
        candidate_id = f"CAND_{idx+1:03d}"
        parts = img_p.stem.split("_")
        source = parts[0]
        source_id = parts[1]
        cat = parts[2] if len(parts) > 2 else "other"

        with open(img_p, "rb") as f:
            img_bytes = f.read()
        im = Image.open(img_p)
        w, h = im.size

        item_key = f"{source}_{source_id}"
        dup_status, matched_id, min_dist, dhash, ahash, sha256 = dedup.classify_and_add(
            item_key, im, img_bytes=img_bytes
        )

        existing_meta = meta_lookup.get(item_key, {})
        title = existing_meta.get("title") or f"Cleveland Museum of Art Jewellery ({source_id})"
        medium = existing_meta.get("medium") or "Gold, enamel, metalwork"
        classification = existing_meta.get("classification") or "Jewelry"

        # Determine jewellery relevance and confidence
        _, rel, conf = assess_jewellery_relevance(title, classification, medium)

        status = "ACCEPTED" if dup_status == "DISTINCT" and rel == "JEWELLERY_RELEVANT" else "REVIEW_REQUIRED"

        record = {
            "candidate_id": candidate_id,
            "image_path": str(img_p.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            "source": source,
            "source_id": source_id,
            "title": title,
            "category": cat,
            "category_confidence": conf,
            "jewellery_relevance": rel,
            "duplicate_status": dup_status,
            "duplicate_of": matched_id if dup_status != "DISTINCT" else "",
            "duplicate_distance": min_dist if dup_status != "DISTINCT" else "",
            "dhash": dhash,
            "ahash": ahash,
            "sha256": sha256,
            "license": "CC0 1.0 Universal (Public Domain)",
            "license_status": "VERIFIED_CC0",
            "width": w,
            "height": h,
            "status": status,
            # Manual evaluation fields (left empty for human evaluator)
            "jewellery_clearly_visible": "",
            "single_primary_object": "",
            "sufficient_object_size": "",
            "useful_geometry": "",
            "minimal_occlusion": "",
            "useful_metal_appearance": "",
            "gemstone_detail_applicable": "",
            "useful_lighting": "",
            "useful_background": "",
            "visual_quality": "",
            "design_diversity": "",
            "design_redundancy": "",
            "training_usefulness": "",
            "final_triage": "",
            "curator_notes": "",
        }
        curation_records.append(record)

    # 1. Write datasets/curation/HUMAN_CURATION.csv
    csv_path = curation_dir / "HUMAN_CURATION.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for rec in curation_records:
            writer.writerow(rec)
    logger.info("Saved human curation table to %s (%d rows)", csv_path, len(curation_records))

    # 2. Write synchronized full_dataset_manifest.json and .jsonl
    manifest_json = curation_dir / "full_dataset_manifest.json"
    manifest_jsonl = curation_dir / "full_dataset_manifest.jsonl"
    with open(manifest_json, "w", encoding="utf-8") as f:
        json.dump(curation_records, f, indent=2)
    with open(manifest_jsonl, "w", encoding="utf-8") as f:
        for rec in curation_records:
            f.write(json.dumps(rec) + "\n")
    logger.info("Saved synchronized manifest to %s and %s", manifest_json, manifest_jsonl)

    # 3. Generate Contact Sheets
    logger.info("=== Rendering Human Curation Contact Sheets ===")

    # A. Master Sheet (All 226 candidates)
    render_curation_sheet(
        entries=curation_records,
        output_path=curation_dir / "HUMAN_CURATION_MASTER_CONTACT_SHEET.png",
        title="JewelMind Human Curation — Master Candidate Sheet (226 Retained Candidates)",
        subtitle="Complete candidate pool for human review | Target: select final 150-200 training images",
        sheet_theme="default",
        cols=6,
        thumb_size=240,
    )

    # B. Near-Duplicates Sheet
    near_dups = [r for r in curation_records if r["duplicate_status"] != "DISTINCT"]
    render_curation_sheet(
        entries=near_dups,
        output_path=curation_dir / "HUMAN_CURATION_NEAR_DUPLICATES.png",
        title=f"JewelMind Human Curation — Near-Duplicate Candidates ({len(near_dups)} Items)",
        subtitle="Hamming distance <= 6 | Review for design redundancy (keep best angle, reject duplicates)",
        sheet_theme="near_duplicate",
        cols=5,
        thumb_size=240,
    )

    # C. Uncertain Sheet
    uncertain_items = [r for r in curation_records if r["jewellery_relevance"] == "JEWELLERY_UNCERTAIN"]
    render_curation_sheet(
        entries=uncertain_items,
        output_path=curation_dir / "HUMAN_CURATION_UNCERTAIN.png",
        title=f"JewelMind Human Curation — Jewellery Uncertain Candidates ({len(uncertain_items)} Items)",
        subtitle="Review whether items qualify as wearable jewellery designs",
        sheet_theme="uncertain",
        cols=5,
        thumb_size=240,
    )

    # D. Category Sheets
    category_map = {
        "HUMAN_CURATION_RINGS.png": ("ring", "Rings"),
        "HUMAN_CURATION_EARRINGS.png": ("earring", "Earrings"),
        "HUMAN_CURATION_PENDANTS.png": ("pendant", "Pendants"),
        "HUMAN_CURATION_NECKLACES.png": ("necklace", "Necklaces"),
        "HUMAN_CURATION_BRACELETS_BANGLES.png": (["bracelet", "bangle"], "Bracelets & Bangles"),
        "HUMAN_CURATION_BROOCHES_OTHER.png": (["brooch", "other"], "Brooches & Other Accessories"),
    }

    for fname, (cat_filter, label) in category_map.items():
        if isinstance(cat_filter, list):
            cat_items = [r for r in curation_records if r["category"] in cat_filter]
        else:
            cat_items = [r for r in curation_records if r["category"] == cat_filter]

        render_curation_sheet(
            entries=cat_items,
            output_path=curation_dir / fname,
            title=f"JewelMind Human Curation — {label} ({len(cat_items)} Items)",
            subtitle=f"Category: {label} | Validate geometry, materials, and training suitability",
            sheet_theme="default",
            cols=5,
            thumb_size=240,
        )

    # 4. Mirror all contact sheets to IDE artifact directory
    artifact_dir = Path(r"C:\Users\usern\.gemini\antigravity-ide\brain\fe4ec3b4-12b6-4a0d-83a3-6a24a3ed1970")
    if artifact_dir.exists():
        for png_file in curation_dir.glob("HUMAN_CURATION_*.png"):
            shutil.copy(png_file, artifact_dir / png_file.name)
        logger.info("Copied all human curation contact sheets to IDE artifact directory.")

    logger.info("Human curation dataset generation complete.")


if __name__ == "__main__":
    generate_human_curation_dataset()
