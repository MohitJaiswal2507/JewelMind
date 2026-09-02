"""Generate readable visual contact sheets for accepted and rejected pilot candidates."""

import io
import json
import logging
import math
import shutil
import urllib.request
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("contact_sheets")


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


def create_contact_sheet(
    items: list,
    output_path: Path,
    title: str,
    is_rejected: bool = False,
    cols: int = 4,
    thumb_size: int = 320,
    caption_height: int = 85,
):
    """Build a visual grid contact sheet."""
    n = len(items)
    if n == 0:
        logger.warning("No items to render for %s", title)
        return

    rows = math.ceil(n / cols)
    pad = 20
    header_height = 80
    sheet_w = pad + cols * (thumb_size + pad)
    sheet_h = header_height + rows * (thumb_size + caption_height + pad) + pad

    sheet = Image.new("RGB", (sheet_w, sheet_h), color=(255, 255, 255))
    draw = ImageDraw.Draw(sheet)

    # Use default font or load TTF if available
    try:
        font_title = ImageFont.truetype("arial.ttf", 26)
        font_text = ImageFont.truetype("arial.ttf", 13)
        font_bold = ImageFont.truetype("arialbd.ttf", 13)
    except Exception:
        font_title = ImageFont.load_default()
        font_text = ImageFont.load_default()
        font_bold = ImageFont.load_default()

    # Header banner
    header_bg = (240, 244, 248) if not is_rejected else (255, 240, 240)
    header_border = (200, 215, 230) if not is_rejected else (255, 180, 180)
    title_color = (15, 45, 80) if not is_rejected else (160, 20, 20)

    draw.rectangle([(pad, pad), (sheet_w - pad, header_height)], fill=header_bg, outline=header_border, width=2)
    draw.text((pad + 20, pad + 15), title, fill=title_color, font=font_title)
    subtitle = f"Total Candidates: {n} | Resolution per tile: {thumb_size}x{thumb_size}px"
    draw.text((pad + 22, pad + 50), subtitle, fill=(90, 100, 110), font=font_text)

    # Render each item
    for idx, item in enumerate(items):
        r = idx // cols
        c = idx % cols
        x = pad + c * (thumb_size + pad)
        y = header_height + pad + r * (thumb_size + caption_height + pad)

        # Load or download image
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
            except Exception as err:
                logger.warning("Could not download item %s: %s", item.get("source_id"), err)
                img = None

        # Fallback placeholder if missing
        if img is None:
            tile = Image.new("RGB", (thumb_size, thumb_size), color=(230, 230, 230))
            d_tile = ImageDraw.Draw(tile)
            d_tile.text((50, 150), "[IMAGE UNAVAILABLE]", fill=(120, 120, 120), font=font_bold)
        else:
            tile = letterbox_thumbnail(img, target_size=thumb_size)

        # Paste thumbnail with border
        border_color = (210, 215, 220) if not is_rejected else (240, 170, 170)
        sheet.paste(tile, (x, y))
        draw.rectangle([(x, y), (x + thumb_size, y + thumb_size)], outline=border_color, width=1)

        # Caption box below thumbnail
        cap_y = y + thumb_size + 4
        item_title = item.get("title") or "Untitled"
        if len(item_title) > 36:
            item_title = item_title[:33] + "..."

        source_info = f"[{item.get('source', '').upper()}:{item.get('source_id', '')}] {item.get('category', 'unknown').capitalize()}"
        dims = item.get("original_dimensions", [0, 0])
        dim_info = f"Dims: {dims[0]}x{dims[1]}"

        if not is_rejected:
            draw.text((x + 2, cap_y), item_title, fill=(20, 30, 45), font=font_bold)
            draw.text((x + 2, cap_y + 18), source_info, fill=(60, 80, 110), font=font_text)
            draw.text((x + 2, cap_y + 36), dim_info, fill=(100, 110, 120), font=font_text)
            draw.text((x + 2, cap_y + 54), f"dHash: {item.get('dhash', '')[:12]}...", fill=(120, 130, 140), font=font_text)
        else:
            reason = item.get("rejection_reason") or "Rejected"
            if len(reason) > 42:
                reason = reason[:39] + "..."
            draw.text((x + 2, cap_y), item_title, fill=(30, 30, 30), font=font_bold)
            draw.text((x + 2, cap_y + 18), source_info, fill=(80, 80, 80), font=font_text)
            draw.text((x + 2, cap_y + 36), f"REASON:", fill=(180, 30, 30), font=font_bold)
            draw.text((x + 65, cap_y + 36), reason, fill=(180, 30, 30), font=font_text)
            if item.get("duplicate_of"):
                draw.text((x + 2, cap_y + 54), f"Duplicate of: {item.get('duplicate_of')}", fill=(130, 50, 50), font=font_text)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path, "PNG", quality=95)
    logger.info("Saved contact sheet: %s (%dx%d px)", output_path, sheet_w, sheet_h)


def main():
    manifest_file = Path("datasets/curation/pilot_manifest.json")
    if not manifest_file.exists():
        logger.error("Manifest not found: %s", manifest_file)
        return

    with open(manifest_file, "r", encoding="utf-8") as f:
        entries = json.load(f)

    accepted = [e for e in entries if e.get("status") == "ACCEPTED"]
    rejected = [e for e in entries if e.get("status") == "REJECTED"]

    # Generate Accepted Contact Sheet
    accepted_path = Path("datasets/curation/accepted_contact_sheet.png")
    create_contact_sheet(
        items=accepted,
        output_path=accepted_path,
        title="JewelMind Pilot Dataset — Accepted Candidates (13 Images)",
        is_rejected=False,
        cols=4,
        thumb_size=320,
    )

    # Generate Rejected Contact Sheet
    rejected_path = Path("datasets/curation/rejected_contact_sheet.png")
    create_contact_sheet(
        items=rejected,
        output_path=rejected_path,
        title="JewelMind Pilot Dataset — Rejected Candidates & Reasons (7 Images)",
        is_rejected=True,
        cols=4,
        thumb_size=320,
    )

    # Copy to artifact directory for visual preview
    artifact_dir = Path(r"C:\Users\usern\.gemini\antigravity-ide\brain\fe4ec3b4-12b6-4a0d-83a3-6a24a3ed1970")
    if artifact_dir.exists():
        shutil.copy(accepted_path, artifact_dir / "accepted_contact_sheet.png")
        shutil.copy(rejected_path, artifact_dir / "rejected_contact_sheet.png")
        logger.info("Copied contact sheets to artifact directory for IDE display.")


if __name__ == "__main__":
    main()
