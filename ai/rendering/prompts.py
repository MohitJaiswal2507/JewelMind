"""Jewellery prompt builder and negative prompt management."""

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


def build_jewellery_prompt(
    material: str = "18k yellow gold",
    gemstone: str = "round brilliant diamond",
    user_prompt: Optional[str] = None,
) -> str:
    """Build positive prompt combining materials, gemstones, quality anchors, and user input.
    
    Guarantees that standard generated prompts stay well below the 77-token CLIP limit
    (typically 30-40 tokens), leaving sufficient headroom for user style notes.
    """
    material_desc = MATERIAL_PROMPTS.get(
        material.strip().lower(),
        f"polished {material}, precious metal"
    )
    gemstone_desc = GEMSTONE_PROMPTS.get(
        gemstone.strip().lower(),
        f"faceted {gemstone}, refractive clarity"
    )

    parts = [
        DEFAULT_STYLE_MODIFIERS,
        f"crafted in {material_desc}",
        f"embellished with {gemstone_desc}",
    ]

    if user_prompt and user_prompt.strip():
        parts.insert(0, user_prompt.strip())

    return ", ".join(parts)



def build_negative_prompt(user_negative_prompt: Optional[str] = None) -> str:
    """Build negative prompt with standard quality negatives and optional user overrides."""
    if user_negative_prompt and user_negative_prompt.strip():
        return f"{DEFAULT_NEGATIVE_PROMPT}, {user_negative_prompt.strip()}"
    return DEFAULT_NEGATIVE_PROMPT
