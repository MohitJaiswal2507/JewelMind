"""Jewellery prompt builder and negative prompt management."""

import re
from typing import Optional

# Standard negative prompt strictly discouraging jewellery rendering deformities
DEFAULT_NEGATIVE_PROMPT = (
    "malformed jewellery, deformed ring, melted metal, broken geometry, distorted symmetry, "
    "extra gemstones, missing gemstones, floating stones, loose stones, extra prongs, missing prongs, "
    "duplicated components, distorted band, rough surface, porous casting, tarnished metal, "
    "low quality, blurry, pixelated, noisy, bad anatomy, text, watermark, signature, logo, stamp, "
    "hands, fingers, skin, mannequin, workbench, jeweler tools, background clutter, 3d render plastic look"
)

# Base quality and lighting anchors (concise to remain safely under CLIP 77-token ceiling)
DEFAULT_STYLE_MODIFIERS = (
    "photorealistic fine jewellery product photograph, studio lighting, sharp focus, clean background"
)

# Preset material descriptions (concise & distinctive)
MATERIAL_PROMPTS = {
    "18k yellow gold": "polished 18k yellow gold, warm golden luster",
    "yellow gold": "polished 18k yellow gold, warm golden luster",
    "white gold": "polished 18k white gold, brilliant specular highlights",
    "platinum": "polished 950 platinum, dense silvery sheen",
    "rose gold": "polished 18k rose gold, warm pink metallic luster",
    "sterling silver": "polished 925 sterling silver, lustrous reflective finish",
}

# Preset gemstone descriptions (concise & physically grounded)
GEMSTONE_PROMPTS = {
    "round brilliant diamond": "round brilliant diamond, refractive fire and dispersion",
    "diamond": "brilliant cut diamond, sharp refractive facets",
    "blue sapphire": "royal blue sapphire, vivid transparent saturation",
    "emerald": "rich green emerald, precision faceted luster",
    "ruby": "crimson ruby, intense red transparent luster",
    "amethyst": "royal purple amethyst, transparent violet brilliance",
}


# Supported controlled jewellery categories
SUPPORTED_CATEGORIES = {
    "ring",
    "earring",
    "pendant",
    "necklace",
    "bracelet",
    "bangle",
    "brooch",
    "other_jewellery",
    "other",
}


def build_jewellery_prompt(
    material: str = "18k yellow gold",
    gemstone: str = "round brilliant diamond",
    category: Optional[str] = None,
    user_prompt: Optional[str] = None,
) -> str:
    """Build positive prompt combining category, materials, gemstones, quality anchors, and user input.
    
    Guarantees strict Tier-1 user intent precedence:
    1. If user_prompt is a fully compiled prompt (contains style modifiers or studio lighting),
       it is preserved without appending duplicate quality anchors or conflicting defaults.
    2. If user explicitly specifies a design attribute, defaults are NOT appended.
    3. Defaults are fallback values only when attributes are absent.
    """
    material_desc = MATERIAL_PROMPTS.get(
        material.strip().lower(),
        f"polished {material}, precious metal"
    )
    gemstone_desc = GEMSTONE_PROMPTS.get(
        gemstone.strip().lower(),
        f"faceted {gemstone}, refractive clarity"
    )

    if category is not None and category.strip():
        cat_clean = category.strip().lower()
        if cat_clean not in SUPPORTED_CATEGORIES:
            valid_list = ", ".join(sorted(SUPPORTED_CATEGORIES))
            raise ValueError(
                f"Unsupported jewellery category '{category}'. Supported categories: {valid_list}"
            )
        if cat_clean not in ("other", "other_jewellery"):
            style_modifiers = (
                f"photorealistic fine jewellery {cat_clean} product photograph, studio lighting, sharp focus, clean background"
            )
        else:
            style_modifiers = DEFAULT_STYLE_MODIFIERS
    else:
        style_modifiers = DEFAULT_STYLE_MODIFIERS

    # Case 1: No user prompt provided (standard baseline generation)
    if not user_prompt or not user_prompt.strip():
        parts = [
            style_modifiers,
            f"crafted in {material_desc}",
            f"embellished with {gemstone_desc}",
        ]
        return ", ".join(parts)

    u_prompt = user_prompt.strip()
    u_lower = u_prompt.lower()

    # Case 2: user_prompt is already a complete compiled renderer prompt
    if ("studio lighting" in u_lower or "photorealistic" in u_lower) and ("fine jewellery" in u_lower or "crafted in" in u_lower):
        return u_prompt

    # Case 3: user_prompt is artisan text
    has_explicit_metal = any(m in u_lower for m in [
        "platinum", "gold", "silver", "white gold", "yellow gold", "rose gold"
    ])
    has_explicit_gem = any(g in u_lower for g in [
        "diamond", "sapphire", "emerald", "ruby", "onyx", "pearl", "topaz", "amethyst", "opal", "aquamarine", "tanzanite"
    ])

    parts = [u_prompt, style_modifiers]

    # Only append default material if user did NOT specify metal
    if not has_explicit_metal:
        parts.append(f"crafted in {material_desc}")

    # Only append default gemstone if user did NOT specify gemstone AND prompt is not explicitly minimalist/metal-only
    if not has_explicit_gem and not any(k in u_lower for k in ["minimalist", "plain", "unadorned", "band", "bangle", "solid"]):
        parts.append(f"embellished with {gemstone_desc}")

    return ", ".join(parts)


def build_negative_prompt(
    user_negative_prompt: Optional[str] = None,
    positive_prompt: Optional[str] = None,
) -> str:
    """Build negative prompt with standard quality negatives and optional user overrides.
    
    Ensures user-requested positive design attributes are never penalized in the negative prompt.
    """
    neg = DEFAULT_NEGATIVE_PROMPT
    if user_negative_prompt and user_negative_prompt.strip():
        neg = f"{neg}, {user_negative_prompt.strip()}"

    if positive_prompt:
        p_lower = positive_prompt.lower()
        for token in ["emerald", "sapphire", "diamond", "baguette", "platinum", "gold", "silver", "onyx", "ruby", "pearl", "oval", "cushion", "pear"]:
            if token in p_lower:
                neg = re.sub(r"\b" + re.escape(token) + r"\b,?\s*", "", neg, flags=re.IGNORECASE)

    neg = re.sub(r",\s*,", ", ", neg)
    neg = re.sub(r",\s*$", "", neg).strip()
    return neg
