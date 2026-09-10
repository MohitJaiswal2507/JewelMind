"""JewelMind Generative Rendering — Final Dataset Quality Correction Module.

This module provides deterministic computer vision and multi-signal heuristics
to audit, filter, reclassify, and stage the rendering_final dataset into
rendering_final_corrected.

Strict Constraints:
- 100% Deterministic (Seed 42)
- Zero model training / Zero GPU fine-tuning
- All baseline datasets and model weights are strictly immutable
"""

import os
import re
import cv2
import numpy as np
import pandas as pd
from PIL import Image

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

# Neutral background padding for letterboxing
PADDING_COLOR = (128, 128, 128)
TARGET_SIZE = 512


def compute_directory_sha256_tree(dir_path):
    """Compute deterministic recursive file count, byte size, and aggregate SHA256."""
    import glob
    import hashlib
    files = sorted(glob.glob(os.path.join(dir_path, "**", "*"), recursive=True))
    files = [f for f in files if os.path.isfile(f)]
    total_bytes = 0
    h = hashlib.sha256()
    for f in files:
        total_bytes += os.path.getsize(f)
        with open(f, "rb") as fp:
            while chunk := fp.read(65536):
                h.update(chunk)
    return {"count": len(files), "total_bytes": total_bytes, "sha256": h.hexdigest()}


def letterbox_image(img_bgr, target_size=TARGET_SIZE, pad_color=PADDING_COLOR):
    """Deterministically letterbox an image to target_size x target_size with neutral padding."""
    h, w = img_bgr.shape[:2]
    scale = target_size / max(h, w)
    new_w = max(1, int(round(w * scale)))
    new_h = max(1, int(round(h * scale)))

    # High-quality Lanczos/area downsampling, cubic upsampling
    interp = cv2.INTER_AREA if scale < 1.0 else cv2.INTER_CUBIC
    resized = cv2.resize(img_bgr, (new_w, new_h), interpolation=interp)

    canvas = np.full((target_size, target_size, 3), pad_color, dtype=np.uint8)
    pad_top = (target_size - new_h) // 2
    pad_left = (target_size - new_w) // 2
    canvas[pad_top : pad_top + new_h, pad_left : pad_left + new_w] = resized
    return canvas


def extract_vision_quality_features(img_bgr):
    """Extract fast, deterministic computer vision features for graphic/text/chart/skin detection."""
    h, w = img_bgr.shape[:2]
    # Standardize to 512x512 for invariant thresholding
    img_512 = cv2.resize(img_bgr, (512, 512), interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(img_512, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(img_512, cv2.COLOR_BGR2HSV)
    ycrcb = cv2.cvtColor(img_512, cv2.COLOR_BGR2YCrCb)

    # 1. Table / Grid / Dimension line detection (Morphological line opening)
    horiz_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
    vert_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 25))
    horiz_lines = cv2.morphologyEx(gray, cv2.MORPH_OPEN, horiz_kernel)
    vert_lines = cv2.morphologyEx(gray, cv2.MORPH_OPEN, vert_kernel)
    horiz_density = float(np.sum(horiz_lines > 40) / (512 * 512))
    vert_density = float(np.sum(vert_lines > 40) / (512 * 512))
    grid_score = float(horiz_density * vert_density * 1000.0 + (horiz_density + vert_density))

    # 2. Text / Character stroke clustering
    morph_grad = cv2.morphologyEx(gray, cv2.MORPH_GRADIENT, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)))
    text_dilate = cv2.dilate(morph_grad, cv2.getStructuringElement(cv2.MORPH_RECT, (7, 2)))
    text_bin = (text_dilate > 35).astype(np.uint8)

    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(text_bin, connectivity=8)
    text_cc_count = 0
    text_area = 0
    for i in range(1, min(num_labels, 500)):
        area = stats[i, cv2.CC_STAT_AREA]
        cw = stats[i, cv2.CC_STAT_WIDTH]
        ch = stats[i, cv2.CC_STAT_HEIGHT]
        ar = cw / max(1, ch)
        if 15 < area < 2500 and 1.2 < ar < 12 and ch < 30:
            text_cc_count += 1
            text_area += area
    text_density = float(text_area / (512 * 512))

    # 3. Peripheral / Border noise (where promotional headers/footers/watermarks live)
    border_mask = np.zeros((512, 512), dtype=bool)
    border_mask[:90, :] = True
    border_mask[-90:, :] = True
    border_mask[:, :70] = True
    border_mask[:, -70:] = True

    grad_x = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    grad_mag = cv2.magnitude(grad_x, grad_y)

    border_edge_density = float(np.mean(grad_mag[border_mask] > 50))
    center_edge_density = float(np.mean(grad_mag[~border_mask] > 50))

    # Peripheral-to-Center edge ratio
    border_ratio = float(border_edge_density / max(0.001, center_edge_density))

    # 4. Skin color detection (YCrCb + HSV)
    cr = ycrcb[:, :, 1]
    cb = ycrcb[:, :, 2]
    skin_ycrcb = (cr >= 133) & (cr <= 173) & (cb >= 77) & (cb <= 127)
    hue = hsv[:, :, 0]
    sat = hsv[:, :, 1]
    skin_hsv = (hue >= 0) & (hue <= 25) & (sat >= 30) & (sat <= 200)
    skin_mask = skin_ycrcb & skin_hsv
    skin_ratio = float(np.mean(skin_mask))

    # 5. Background border uniformity
    border_val = gray[border_mask]
    border_val_std = float(np.std(border_val))

    # 6. Saliency / Foreground occupancy (Otsu thresholding on center)
    center_gray = gray[80:432, 80:432]
    _, otsu_thresh = cv2.threshold(center_gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    occupancy = float(np.mean(otsu_thresh > 0))

    # 7. Disconnected multi-component / collage detection
    # Strong foreground blobs
    fg_thresh = (gray < 235) & (grad_mag > 30)
    num_fg_blobs, _, fg_stats, _ = cv2.connectedComponentsWithStats(fg_thresh.astype(np.uint8), connectivity=8)
    large_fg_blobs = 0
    for i in range(1, min(num_fg_blobs, 50)):
        if fg_stats[i, cv2.CC_STAT_AREA] > (512 * 512 * 0.04):
            large_fg_blobs += 1

    return {
        "grid_score": grid_score,
        "horiz_density": horiz_density,
        "vert_density": vert_density,
        "text_density": text_density,
        "text_cc_count": text_cc_count,
        "border_edge_density": border_edge_density,
        "center_edge_density": center_edge_density,
        "border_ratio": border_ratio,
        "skin_ratio": skin_ratio,
        "border_val_std": border_val_std,
        "occupancy": occupancy,
        "large_fg_blobs": large_fg_blobs,
    }


def parse_semantic_category_signals(filename_str, rel_path_str, original_cat):
    """Multi-signal parsing of category tokens from path and filename."""
    text = f"{rel_path_str} {filename_str}".lower()

    # Specific subcategory tokens
    is_rakhi = bool(re.search(r"\b(rakhi|bhaiya|bhabhi-rakhi|lumba|chuda-rakhi|raksha-bandhan)\b", text))
    is_nath = bool(re.search(r"\b(nath|nose-ring|nose-stud|nose-pin|pressing-nath)\b", text))
    is_anklet = bool(re.search(r"\b(anklet|payal|pajeb|ghungroo-payal|foot-ornament)\b", text))
    is_toe_ring = bool(re.search(r"\b(toe-ring|bichiya|jodavi|toe-rings)\b", text))
    is_maang_tikka = bool(re.search(r"\b(maang-tikka|tikka|matha-patti|sheeshpatti|passa)\b", text))
    is_hairpin = bool(re.search(r"\b(hair-pin|juda-pin|hair-ornament|hair-accessory|tiara|diadem)\b", text))
    is_cufflinks = bool(re.search(r"\b(cufflinks|cuff-link|tie-pin|tie-clip)\b", text))
    is_mala_sherwani = bool(re.search(r"\b(sherwani|moti-mala|groom-necklace|dulha|groom-mala)\b", text))
    is_brooch_token = bool(re.search(r"\b(brooch|lapel-pin|saree-pin|coat-brooch)\b", text))

    # Standard core categories
    is_ring = bool(re.search(r"\b(ring|finger-ring|solitaire|anguthi|wedding-ring|band-ring)\b", text))
    is_earring = bool(re.search(r"\b(earring|jhumka|stud|bali|ear-drop|chandbali|latkan|kundan-earring)\b", text))
    is_necklace = bool(re.search(r"\b(necklace|choker|haar|mala|rani-haar|mangalsutra|hasli|tanmaniya-set)\b", text))
    is_pendant = bool(re.search(r"\b(pendant|locket|tanmaniya|om-pendant|cross-pendant)\b", text))
    is_bangle = bool(re.search(r"\b(bangle|kada|chuda|kangan)\b", text))
    is_bracelet = bool(re.search(r"\b(bracelet|wrist-chain|charm-bracelet|hand-chain)\b", text))

    # Measurement charts / marketing tokens
    is_chart_token = bool(re.search(r"\b(size-chart|size-guide|measurement|diameter-guide|ring-size-guide|how-to-measure)\b", text))
    is_marketing_token = bool(re.search(r"\b(combo|pack-of-\d+|pack-of|wholesale|free-gift|guarantee-card|certificate-of|offer)\b", text))

    return {
        "is_rakhi": is_rakhi,
        "is_nath": is_nath,
        "is_anklet": is_anklet,
        "is_toe_ring": is_toe_ring,
        "is_maang_tikka": is_maang_tikka,
        "is_hairpin": is_hairpin,
        "is_cufflinks": is_cufflinks,
        "is_mala_sherwani": is_mala_sherwani,
        "is_brooch_token": is_brooch_token,
        "is_ring": is_ring,
        "is_earring": is_earring,
        "is_necklace": is_necklace,
        "is_pendant": is_pendant,
        "is_bangle": is_bangle,
        "is_bracelet": is_bracelet,
        "is_chart_token": is_chart_token,
        "is_marketing_token": is_marketing_token,
    }


def evaluate_sample_quality(row, vision_feats):
    """Evaluate a single dataset sample using multi-signal heuristics.

    Returns:
        decision: 'ACCEPT', 'RECLASSIFY', 'REJECT'
        corrected_category: canonical category string
        rejection_reason: string explanation if rejected
        quality_tier: 'TIER_A', 'TIER_B', 'TIER_C'
    """
    orig_cat = row["canonical_category"]
    orig_tier = str(row.get("quality_tier", "TIER_B")).upper()
    filename_str = str(row.get("staged_filename", ""))
    rel_path = str(row.get("source_rel_path", ""))
    tokens = parse_semantic_category_signals(filename_str, rel_path, orig_cat)

    # 1. RAKHI REJECTION (Sacred threads / non-fine jewellery)
    if tokens["is_rakhi"]:
        return "REJECT", orig_cat, "rakhi_non_fine_jewellery", orig_tier

    # 2. MEASUREMENT CHARTS & INSTRUCTIONAL DIAGRAMS REJECTION
    if tokens["is_chart_token"]:
        return "REJECT", orig_cat, "measurement_chart_or_infographic", orig_tier

    # Visual grid/table line threshold for charts
    if vision_feats["grid_score"] > 880.0 and (vision_feats["horiz_density"] > 0.85 or vision_feats["vert_density"] > 0.85):
        if vision_feats["text_density"] > 0.02 or vision_feats["border_edge_density"] > 0.12:
            return "REJECT", orig_cat, "instruction_or_measurement_table", orig_tier

    # 3. MARKETING GRAPHICS & TEXT-DOMINANT IMAGES REJECTION
    if vision_feats["text_density"] > 0.045:
        return "REJECT", orig_cat, "text_dominant_marketing_graphic", orig_tier

    if vision_feats["border_edge_density"] > 0.22 and vision_feats["border_ratio"] > 2.0:
        return "REJECT", orig_cat, "promotional_border_or_banner_graphic", orig_tier

    # Combo packs with heavy advertising text/badges
    if tokens["is_marketing_token"] and (vision_feats["text_density"] > 0.025 or vision_feats["border_edge_density"] > 0.15):
        return "REJECT", orig_cat, "marketing_graphic_combo_card", orig_tier

    # 4. UNRELATED COLLAGES & MULTI-PRODUCT CATALOG PAGES REJECTION
    if vision_feats["large_fg_blobs"] >= 5 and tokens["is_marketing_token"]:
        return "REJECT", orig_cat, "multi_product_catalog_collage", orig_tier

    # 5. HUMAN / LIFESTYLE DOMINANCE REJECTION
    if vision_feats["skin_ratio"] > 0.35 and vision_feats["border_val_std"] > 35.0:
        return "REJECT", orig_cat, "human_lifestyle_dominant", orig_tier

    # 6. SEMANTIC AUDITS & RECLASSIFICATIONS

    # === BROOCH AUDIT ===
    if orig_cat == "brooch":
        if tokens["is_mala_sherwani"]:
            # Moti mala sherwani neck piece
            if vision_feats["text_density"] < 0.02 and vision_feats["border_edge_density"] < 0.15:
                return "RECLASSIFY", "necklace", "", "TIER_B"
            else:
                return "REJECT", "brooch", "mislabeled_brooch_marketing_necklace", orig_tier
        elif tokens["is_necklace"]:
            return "RECLASSIFY", "necklace", "", "TIER_B"
        elif not tokens["is_brooch_token"]:
            return "REJECT", "brooch", "ambiguous_or_non_brooch", orig_tier
        else:
            return "ACCEPT", "brooch", "", orig_tier

    # === BANGLE AUDIT ===
    if orig_cat == "bangle":
        if tokens["is_bracelet"] and not tokens["is_bangle"]:
            return "RECLASSIFY", "bracelet", "", orig_tier
        if tokens["is_necklace"] and not tokens["is_bangle"]:
            return "RECLASSIFY", "necklace", "", orig_tier
        if tokens["is_earring"] and not tokens["is_bangle"]:
            return "RECLASSIFY", "earring", "", orig_tier

    # === PENDANT AUDIT ===
    if orig_cat == "pendant":
        if vision_feats["text_density"] > 0.03 or vision_feats["border_edge_density"] > 0.18:
            return "REJECT", "pendant", "marketing_graphic_pendant_card", orig_tier
        if tokens["is_necklace"] and not tokens["is_pendant"]:
            return "RECLASSIFY", "necklace", "", orig_tier

    # === RING AUDIT ===
    if orig_cat == "ring":
        if tokens["is_anklet"] and not tokens["is_ring"]:
            return "RECLASSIFY", "other_jewellery", "", orig_tier
        if tokens["is_toe_ring"]:
            if tokens["is_anklet"] or tokens["is_marketing_token"]:
                if vision_feats["text_density"] > 0.02:
                    return "REJECT", "ring", "toe_ring_anklet_marketing_graphic", orig_tier
                return "RECLASSIFY", "other_jewellery", "", orig_tier

    # === OTHER_JEWELLERY AUDIT ===
    if orig_cat == "other_jewellery":
        if tokens["is_ring"] and not (tokens["is_anklet"] or tokens["is_toe_ring"] or tokens["is_nath"]):
            return "RECLASSIFY", "ring", "", orig_tier
        if tokens["is_earring"] and not (tokens["is_nath"] or tokens["is_maang_tikka"]):
            return "RECLASSIFY", "earring", "", orig_tier
        if tokens["is_necklace"] and not (tokens["is_maang_tikka"]):
            return "RECLASSIFY", "necklace", "", orig_tier
        if tokens["is_bangle"]:
            return "RECLASSIFY", "bangle", "", orig_tier
        if tokens["is_bracelet"] and not tokens["is_anklet"]:
            return "RECLASSIFY", "bracelet", "", orig_tier

        is_legit_other = (
            tokens["is_anklet"]
            or tokens["is_toe_ring"]
            or tokens["is_nath"]
            or tokens["is_maang_tikka"]
            or tokens["is_hairpin"]
            or tokens["is_cufflinks"]
        )
        if not is_legit_other:
            if vision_feats["text_density"] > 0.02 or vision_feats["border_edge_density"] > 0.15:
                return "REJECT", "other_jewellery", "ambiguous_marketing_other", orig_tier
            if vision_feats["occupancy"] > 0.10 and vision_feats["border_val_std"] < 25.0:
                return "ACCEPT", "other_jewellery", "", "TIER_C"
            else:
                return "REJECT", "other_jewellery", "uncertain_ambiguous_non_jewellery", orig_tier

    # DEFAULT: ACCEPT
    return "ACCEPT", orig_cat, "", orig_tier
