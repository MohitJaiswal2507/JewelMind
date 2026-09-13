"""JewelMind Jewellery Prompt Compiler.

Transforms structured design semantics from Gemini Vision into concise,
photorealistic diffusion prompts optimized for Stable Diffusion 1.5 + ControlNet v2,
while strictly preserving explicit user intent (Tier 1 Precedence).
"""

import re
from typing import List, Optional
from app.schemas.ai import StructuredDesignUnderstanding

# Standard high-quality negative prompt tailored to jewellery CAD diffusion synthesis
JEWELLERY_NEGATIVE_PROMPT = (
    "malformed jewellery, deformed ring, melted metal, broken geometry, distorted symmetry, "
    "extra gemstones, missing gemstones, floating stones, loose stones, extra prongs, missing prongs, "
    "misaligned prongs, cloudy stones, dull facets, duplicated components, distorted band, rough surface, "
    "porous casting, tarnished metal, low quality, blurry, pixelated, noisy, bad anatomy, "
    "hands, fingers, skin, mannequin, workbench, jeweler tools, background clutter, 3d render plastic look, "
    "text, watermark, signature, logo, stamp"
)

# Quality & lighting anchors that anchor SD1.5 without consuming excessive token budget
STUDIO_LIGHTING_ANCHOR = "studio lighting, sharp focus, clean neutral background"


class JewelleryPromptCompiler:
    """Compiles structured design semantics into diffusion-ready prompts."""

    @classmethod
    def sanitize_prompt_conflicts(cls, prompt: str, applied_constraints: List[str]) -> str:
        """Deterministic conflict & substitution detection (Phase E.1 Hardening).
        
        Guarantees:
        - If user explicitly requested emerald, do NOT substitute diamond.
        - If user explicitly requested sapphire, do NOT substitute diamond.
        - If user explicitly requested baguette, do NOT substitute round brilliant.
        - If user explicitly requested oval, do NOT substitute round brilliant.
        - If user explicitly requested pear, do NOT substitute round brilliant.
        - If user explicitly requested platinum / silver, do NOT substitute yellow gold.
        - If user explicitly requested yellow gold, do NOT substitute platinum / white gold.
        - If user explicitly requested thin shank, do NOT substitute thick/wide shank.
        - If user specified NO gemstone, do NOT inject diamond or gemstone phrases.
        """
        explicit_metals = [c.split("metal: ", 1)[1].strip().lower() for c in applied_constraints if c.startswith("metal: ")]
        explicit_stones = [c.split("gemstone: ", 1)[1].strip().lower() for c in applied_constraints if c.startswith("gemstone: ")]
        explicit_cuts = [c.split("cut: ", 1)[1].strip().lower() for c in applied_constraints if c.startswith("cut: ")]
        explicit_structs = [c.split("structure: ", 1)[1].strip().lower() for c in applied_constraints if c.startswith("structure: ")]

        res = prompt

        # 1. Gemstone conflicts:
        # If user specified stones, and "diamond" was NOT one of them:
        if explicit_stones and not any("diamond" in s for s in explicit_stones):
            # Check if diamond or round brilliant diamond crept in:
            res = re.sub(r"\bround brilliant diamond\b", explicit_stones[0], res, flags=re.IGNORECASE)
            res = re.sub(r"\bfeatured round brilliant diamond in [a-z\s]+ setting\b", f"featured {explicit_stones[0]}", res, flags=re.IGNORECASE)
            res = re.sub(r"\bfeatured round brilliant diamond\b", f"featured {explicit_stones[0]}", res, flags=re.IGNORECASE)
            # Replace standalone round brilliant if not requested
            if not any("round" in c for c in explicit_cuts):
                res = re.sub(r"\bround brilliant\b", explicit_cuts[0] if explicit_cuts else "", res, flags=re.IGNORECASE)
            # Scrub standalone diamond if not requested
            res = re.sub(r"\bdiamond(?:s)?\b", explicit_stones[0], res, flags=re.IGNORECASE)

        # If user did NOT specify any gemstone, remove any generic gemstone phrases injected by defaults:
        if not explicit_stones and any(c.startswith("structure: ") or c.startswith("metal: ") for c in applied_constraints):
            if "diamond" in res.lower() and not any("diamond" in c for c in applied_constraints):
                res = re.sub(r",\s*embellished with [^,]+", "", res, flags=re.IGNORECASE)
                res = re.sub(r"\b(?:round brilliant )?diamond(?:s)?\b", "", res, flags=re.IGNORECASE)

        # 2. Cut conflicts:
        if explicit_cuts and not any("round" in c for c in explicit_cuts):
            res = re.sub(r"\bround brilliant\b", explicit_cuts[0], res, flags=re.IGNORECASE)

        # 3. Metal conflicts:
        if explicit_metals:
            primary_metal = explicit_metals[0]
            if any(m in primary_metal for m in ["platinum", "silver", "white gold"]):
                res = re.sub(r"\b(?:18k )?yellow gold\b", primary_metal, res, flags=re.IGNORECASE)
                res = re.sub(r"\b(?:18k )?rose gold\b", primary_metal, res, flags=re.IGNORECASE)
            elif "yellow gold" in primary_metal:
                res = re.sub(r"\b(?:950 )?platinum\b", primary_metal, res, flags=re.IGNORECASE)
                res = re.sub(r"\bwhite gold\b", primary_metal, res, flags=re.IGNORECASE)

        # 4. Shank / Structural conflicts:
        if any("thin shank" in s for s in explicit_structs):
            res = re.sub(r"\b(?:thick|wide) (?:shank|band)\b", "thin shank", res, flags=re.IGNORECASE)
        elif any(s in ("thick band", "wide band", "thick shank", "wide shank") for s in explicit_structs):
            res = re.sub(r"\bthin (?:shank|band)\b", "wide band", res, flags=re.IGNORECASE)

        # Clean up double commas, extra spaces
        res = re.sub(r",\s*,", ", ", res)
        res = re.sub(r"\s+", " ", res).strip()
        return res

    @classmethod
    def compile_renderer_prompt(
        cls,
        design: StructuredDesignUnderstanding,
        user_constraints: Optional[List[str]] = None,
    ) -> str:
        """Compile a concise, diffusion-optimized prompt from rich structured design understanding.
        
        Enforces strict Tier-1 precedence:
        1. Explicit User Constraints (metal, cut, stone, shank)
        2. Category & Core Architecture
        3. Gemstone Faceting & Refraction
        4. Precious Metal Specular Lustre
        5. Studio Lighting & Photographic Quality Anchors
        """
        category = design.jewellery_category.lower().replace("_", " ")
        if category == "other jewellery" or category == "other":
            category = "fine jewellery"

        # Maintain order of constraints
        applied_constraints_list: List[str] = []
        if user_constraints:
            for c in user_constraints:
                if c not in applied_constraints_list:
                    applied_constraints_list.append(c)
        if design.user_constraints_applied:
            for c in design.user_constraints_applied:
                if c not in applied_constraints_list:
                    applied_constraints_list.append(c)

        prompt_components: List[str] = []

        # 1. Subject & Category definition with style modifier
        subject_phrase = f"photorealistic {category} fine jewellery product photograph"
        prompt_components.append(subject_phrase)

        # 2. Material & Precious Metal specification
        explicit_metal = None
        for c in applied_constraints_list:
            if c.startswith("metal: "):
                explicit_metal = c.split("metal: ", 1)[1].strip()
                break

        material_spec = design.material
        metal_desc = explicit_metal if explicit_metal else material_spec.primary_metal.strip()
        finish_desc = material_spec.finish.strip() if material_spec.finish else "polished"
        
        metal_phrase = f"crafted in {finish_desc} {metal_desc}"
        if material_spec.accent_metal and material_spec.accent_metal.strip():
            metal_phrase += f" with {material_spec.accent_metal.strip()} accents"
        prompt_components.append(metal_phrase)

        # 3. Gemstones specification
        explicit_stones = [c.split("gemstone: ", 1)[1].strip() for c in applied_constraints_list if c.startswith("gemstone: ")]
        explicit_cuts = [c.split("cut: ", 1)[1].strip() for c in applied_constraints_list if c.startswith("cut: ")]

        gem_spec = design.gemstones
        # If user explicitly provided constraints with NO gemstone, do NOT invent gemstones!
        has_gemstones = gem_spec.has_gemstones
        if explicit_stones:
            has_gemstones = True
        elif applied_constraints_list and not explicit_stones:
            has_gemstones = False

        if has_gemstones and (gem_spec.primary_gemstone or explicit_stones):
            gem_phrases: List[str] = []
            
            # Primary gemstone:
            primary_stone = explicit_stones[0] if explicit_stones else (gem_spec.primary_gemstone.gemstone_type.strip() if gem_spec.primary_gemstone else "gemstone")
            
            # Primary cut:
            if explicit_cuts:
                primary_cut = explicit_cuts[0]
            elif gem_spec.primary_gemstone and gem_spec.primary_gemstone.cut and gem_spec.primary_gemstone.cut != "round brilliant":
                primary_cut = gem_spec.primary_gemstone.cut.strip()
            elif gem_spec.primary_gemstone and gem_spec.primary_gemstone.cut == "round brilliant" and ("round" in primary_stone or any("round" in c for c in applied_constraints_list)):
                primary_cut = "round brilliant"
            elif gem_spec.primary_gemstone and gem_spec.primary_gemstone.cut == "round brilliant" and not explicit_stones:
                primary_cut = "round brilliant"
            else:
                primary_cut = None

            count = gem_spec.primary_gemstone.estimated_count if gem_spec.primary_gemstone else 1
            stype = gem_spec.primary_gemstone.setting_type.strip() if gem_spec.primary_gemstone else "prong setting"

            cut_prefix = f"{primary_cut} " if primary_cut else ""
            if count > 1:
                primary_phrase = f"{count} {cut_prefix}{primary_stone}s in {stype}"
            else:
                primary_phrase = f"featured {cut_prefix}{primary_stone} in {stype}"
            gem_phrases.append(primary_phrase)

            # Secondary gemstones:
            if len(explicit_stones) > 1:
                for idx, s in enumerate(explicit_stones[1:], start=1):
                    s_cut = explicit_cuts[idx] if len(explicit_cuts) > idx else ("round" if "round" in s else "")
                    s_cut_prefix = f"{s_cut} " if s_cut else ""
                    s_setting = "halo" if any("halo" in c for c in applied_constraints_list) else ("inlays" if any("inlay" in c for c in applied_constraints_list) else ("accents" if any("accent" in c for c in applied_constraints_list) else "setting"))
                    gem_phrases.append(f"{s_cut_prefix}{s} {s_setting}".strip())
            elif gem_spec.secondary_gemstones:
                for s_gem in gem_spec.secondary_gemstones:
                    s_cut = s_gem.cut.strip()
                    s_type = s_gem.gemstone_type.strip()
                    s_setting = s_gem.setting_type.strip()
                    gem_phrases.append(f"{s_cut} {s_type} {s_setting}")

            if gem_phrases:
                prompt_components.append(f"embellished with {', '.join(gem_phrases)}")
            elif gem_spec.gemstone_details:
                prompt_components.append(f"set with {gem_spec.gemstone_details.strip()}")
        else:
            prompt_components.append("solid unadorned precious metal sculpture")

        # 4. Structural details & Band / Setting architecture
        struct_spec = design.structure
        struct_parts: List[str] = []
        if struct_spec.band_or_body_structure and struct_spec.band_or_body_structure not in ("classic band", "classic tapered band", "standard mount"):
            struct_parts.append(struct_spec.band_or_body_structure.strip())

        if struct_spec.setting_style and struct_spec.setting_style not in ("classic setting", "standard setting"):
            struct_parts.append(struct_spec.setting_style.strip())
        if struct_spec.decorative_elements:
            struct_parts.extend([d.strip() for d in struct_spec.decorative_elements])

        # Strictly preserve any explicit structural constraints
        for c in applied_constraints_list:
            if c.startswith("structure: "):
                val = c.split("structure: ", 1)[1].strip()
                if not any(val in sp for sp in struct_parts):
                    struct_parts.append(val)

        if struct_parts:
            prompt_components.append(f"featuring {', '.join(struct_parts)}")

        # 5. Aesthetic Quality & Lighting Anchors
        prompt_components.append(STUDIO_LIGHTING_ANCHOR)

        # Assemble
        final_prompt = ", ".join(prompt_components)
        
        # Apply deterministic conflict / substitution check
        final_prompt = cls.sanitize_prompt_conflicts(final_prompt, applied_constraints_list)
        return final_prompt

    @classmethod
    def compile_negative_prompt(
        cls,
        custom_negatives: Optional[str] = None,
        user_constraints: Optional[List[str]] = None,
    ) -> str:
        """Constructs negative prompt and strictly scrubs user-requested attributes."""
        neg = JEWELLERY_NEGATIVE_PROMPT
        if custom_negatives and custom_negatives.strip():
            neg = f"{neg}, {custom_negatives.strip()}"

        if user_constraints:
            for c in user_constraints:
                val = c.split(":", 1)[1].strip() if ":" in c else c.strip()
                tokens = val.split()
                for t in tokens:
                    if len(t) > 3:
                        neg = re.sub(r"\b" + re.escape(t) + r"\b,?\s*", "", neg, flags=re.IGNORECASE)

        neg = re.sub(r",\s*,", ", ", neg)
        neg = re.sub(r",\s*$", "", neg).strip()
        return neg

    @classmethod
    def compile_natural_enhanced_prompt(cls, design: StructuredDesignUnderstanding) -> str:
        """Constructs an elegant natural-language artisan description for UI display."""
        category = design.jewellery_category.capitalize().replace("_", " ")
        metal = design.material.primary_metal
        finish = design.material.finish or "polished"
        
        desc = f"A bespoke {category} expertly rendered in {finish} {metal}."
        
        if design.gemstones.has_gemstones and design.gemstones.primary_gemstone:
            p_gem = design.gemstones.primary_gemstone
            cut_str = f"{p_gem.cut} " if p_gem.cut else ""
            desc += f" It highlights a breathtaking {cut_str}{p_gem.gemstone_type} held securely in a {p_gem.setting_type}."
            if design.gemstones.secondary_gemstones:
                sec_list = [f"{s.cut} {s.gemstone_type}s ({s.setting_type})" for s in design.gemstones.secondary_gemstones]
                desc += f" Complemented by {' and '.join(sec_list)}."
        elif not design.gemstones.has_gemstones:
            desc += " Designed as an unadorned, sculptural precious metal masterpiece."
        
        if design.structure.band_or_body_structure:
            desc += f" The piece features a {design.structure.band_or_body_structure} with {design.structure.silhouette}."
            
        if design.design_motifs:
            desc += f" Inspired by {', '.join(design.design_motifs)} aesthetics."

        return desc
