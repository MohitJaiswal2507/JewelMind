"""Runner for the fresh ~20-candidate Validation Pilot with contact sheet generation."""

import io
import json
import logging
import math
import shutil
import sys
import urllib.request
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PIL import Image, ImageDraw, ImageFont
from ai.dataset_pipeline.curator import DatasetCurator

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")
logger = logging.getLogger("validation_pilot_runner")


def letterbox_thumbnail(img: Image.Image, target_size: int = 320, bg_color=(245, 245, 245)) -> Image.Image:
    """Resize image preserving aspect ratio and pad onto square canvas."""
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


def render_contact_sheet(
    entries: list,
    output_path: Path,
    title: str,
    sheet_theme: str = "accepted",  # "accepted" or "review"
    cols: int = 4,
    thumb_size: int = 320,
    caption_height: int = 85,
):
    """Build high-resolution grid contact sheet for visual inspection."""
    n = len(entries)
    if n == 0:
        logger.info("No entries to render for %s", title)
        # Create empty placeholder card
        sheet = Image.new("RGB", (640, 240), color=(255, 255, 255))
        d = ImageDraw.Draw(sheet)
        d.text((40, 40), title, fill=(30, 30, 30))
        d.text((40, 100), "No candidates in this category (0 items).", fill=(100, 100, 100))
        output_path.parent.mkdir(parents=True, exist_ok=True)
        sheet.save(output_path, "PNG")
        return

    rows = math.ceil(n / cols)
    pad = 20
    header_height = 80
    sheet_w = pad + cols * (thumb_size + pad)
    sheet_h = header_height + rows * (thumb_size + caption_height + pad) + pad

    sheet = Image.new("RGB", (sheet_w, sheet_h), color=(255, 255, 255))
    draw = ImageDraw.Draw(sheet)

    try:
        font_title = ImageFont.truetype("arial.ttf", 24)
        font_text = ImageFont.truetype("arial.ttf", 12)
        font_bold = ImageFont.truetype("arialbd.ttf", 12)
    except Exception:
        font_title = ImageFont.load_default()
        font_text = ImageFont.load_default()
        font_bold = ImageFont.load_default()

    is_review = sheet_theme == "review"
    header_bg = (255, 244, 230) if is_review else (240, 248, 244)
    header_border = (255, 200, 150) if is_review else (180, 230, 200)
    title_color = (180, 90, 20) if is_review else (20, 100, 50)

    draw.rectangle([(pad, pad), (sheet_w - pad, header_height)], fill=header_bg, outline=header_border, width=2)
    draw.text((pad + 20, pad + 15), title, fill=title_color, font=font_title)
    subtitle = f"Candidates Count: {n} | Resolution per tile: {thumb_size}x{thumb_size}px"
    draw.text((pad + 22, pad + 48), subtitle, fill=(90, 90, 90), font=font_text)

    for idx, item in enumerate(entries):
        r = idx // cols
        c = idx % cols
        x = pad + c * (thumb_size + pad)
        y = header_height + pad + r * (thumb_size + caption_height + pad)

        img = None
        local_p = Path(item.get("local_path", ""))
        if local_p.exists() and local_p.is_file():
            try:
                img = Image.open(local_p)
            except Exception:
                img = None

        if img is None and item.get("image_url"):
            try:
                req = urllib.request.Request(item["image_url"], headers={"User-Agent": "JewelMind/1.0"})
                with urllib.request.urlopen(req, timeout=12) as resp:
                    img = Image.open(io.BytesIO(resp.read()))
            except Exception:
                img = None

        if img is None:
            tile = Image.new("RGB", (thumb_size, thumb_size), color=(230, 230, 230))
            d_tile = ImageDraw.Draw(tile)
            d_tile.text((50, 150), "[IMAGE UNAVAILABLE]", fill=(120, 120, 120), font=font_bold)
        else:
            tile = letterbox_thumbnail(img, target_size=thumb_size)

        border_color = (255, 180, 120) if is_review else (200, 220, 210)
        sheet.paste(tile, (x, y))
        draw.rectangle([(x, y), (x + thumb_size, y + thumb_size)], outline=border_color, width=1)

        cap_y = y + thumb_size + 4
        item_title = item.get("title") or "Untitled"
        if len(item_title) > 36:
            item_title = item_title[:33] + "..."

        source_info = f"[{item.get('source', '').upper()}:{item.get('source_id', '')}] {item.get('category', 'unknown').capitalize()}"
        relevance_info = f"Relevance: {item.get('jewellery_relevance')} ({item.get('category_confidence')})"
        dims = item.get("original_dimensions", [0, 0])
        dim_info = f"Dims: {dims[0]}x{dims[1]} | Query: {item.get('search_query', '')}"

        draw.text((x + 2, cap_y), item_title, fill=(20, 30, 45), font=font_bold)
        draw.text((x + 2, cap_y + 18), source_info, fill=(60, 80, 110), font=font_text)
        draw.text((x + 2, cap_y + 36), relevance_info, fill=(160, 80, 20) if is_review else (30, 110, 60), font=font_bold)
        draw.text((x + 2, cap_y + 54), dim_info, fill=(100, 110, 120), font=font_text)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path, "PNG", quality=95)
    logger.info("Saved contact sheet: %s (%dx%d px)", output_path, sheet_w, sheet_h)


def main():
    logger.info("=== JewelMind Validation Pilot Runner ===")

    # 1. Identify previous pilot object IDs to strictly exclude (ensuring fresh candidates)
    exclude_ids = set()
    old_manifest_p = Path("datasets/curation/pilot_manifest.json")
    if old_manifest_p.exists():
        try:
            with open(old_manifest_p, "r", encoding="utf-8") as f:
                old_entries = json.load(f)
                for e in old_entries:
                    exclude_ids.add(str(e.get("source_id")))
            logger.info("Excluding %d previously fetched object IDs to guarantee fresh candidates.", len(exclude_ids))
        except Exception as err:
            logger.warning("Could not read previous pilot manifest: %s", err)

    # 2. Run fresh pilot with DatasetCurator
    curator = DatasetCurator(
        output_dir="datasets/curation",
        review_threshold=6,
        subfolder="validation_pilot_images",
    )

    manifest_entries = curator.run_pilot(
        target_limit=20,
        exclude_ids=exclude_ids,
        report_filename="VALIDATION_PILOT_REPORT.md",
        manifest_prefix="validation_pilot",
    )

    # 3. Partition entries for Contact Sheets
    accepted_entries = [e.to_dict() for e in manifest_entries if e.status == "ACCEPTED"]
    review_entries = [
        e.to_dict() for e in manifest_entries
        if e.status == "REVIEW_REQUIRED" or e.jewellery_relevance == "JEWELLERY_UNCERTAIN"
    ]

    accepted_sheet_path = Path("datasets/curation/VALIDATION_PILOT_ACCEPTED_CONTACT_SHEET.png")
    review_sheet_path = Path("datasets/curation/VALIDATION_PILOT_REVIEW_CONTACT_SHEET.png")

    logger.info("Rendering Accepted Contact Sheet (%d candidates)...", len(accepted_entries))
    render_contact_sheet(
        entries=accepted_entries,
        output_path=accepted_sheet_path,
        title="JewelMind Validation Pilot — Accepted Jewellery Candidates",
        sheet_theme="accepted",
        cols=4,
    )

    logger.info("Rendering Review Contact Sheet (%d candidates)...", len(review_entries))
    render_contact_sheet(
        entries=review_entries,
        output_path=review_sheet_path,
        title="JewelMind Validation Pilot — Manual Review Candidates (Near-Dups / Uncertain)",
        sheet_theme="review",
        cols=4,
    )

    # 4. Copy contact sheets to IDE artifact directory for visual display
    artifact_dir = Path(r"C:\Users\usern\.gemini\antigravity-ide\brain\fe4ec3b4-12b6-4a0d-83a3-6a24a3ed1970")
    if artifact_dir.exists():
        shutil.copy(accepted_sheet_path, artifact_dir / "VALIDATION_PILOT_ACCEPTED_CONTACT_SHEET.png")
        shutil.copy(review_sheet_path, artifact_dir / "VALIDATION_PILOT_REVIEW_CONTACT_SHEET.png")
        logger.info("Copied validation contact sheets to IDE artifact directory.")

    logger.info("=== Validation Pilot Complete: %d candidates processed ===", len(manifest_entries))


if __name__ == "__main__":
    main()
