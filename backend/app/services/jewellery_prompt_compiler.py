"""JewelMind Jewellery Prompt Compiler.

Transforms structured design semantics from Gemini Vision into concise,
photorealistic diffusion prompts optimized for Stable Diffusion 1.5 + ControlNet v2,
while strictly preserving explicit user intent (Tier 1 Precedence).
"""

from typing import List, Optional, Set
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
    def compile_renderer_prompt(
        cls,
        design: StructuredDesignUnderstanding,
        user_constraints: Optional[List[str]] = None,
    ) -> str:
        """Compile a concise, diffusion-optimized prompt from rich structured design understanding.
        
        Architecture:
            Gemini
              ↓
            Rich Structured Design Understanding (unconstrained semantic depth)
              ↓
            Prompt Compiler
              ↓
            Concise Renderer Prompt (optimized for ControlNet + SD1.5)
        
        Enforces strict precedence:
        1. Explicit User Constraints (locked keywords: metal, cut, stone, shank)
        2. Category & Core Architecture
        3. Gemstone Faceting & Refraction
        4. Precious Metal Specular Lustre
        5. Studio Lighting & Photographic Quality Anchors
        """
        category = design.jewellery_category.lower().replace("_", " ")
        if category == "other jewellery" or category == "other":
            category = "fine jewellery"

        # Collect user constraints
        applied_constraints = set(user_constraints or [])
        if design.user_constraints_applied:
            applied_constraints.update(design.user_constraints_applied)

        prompt_components: List[str] = []

        # 1. Subject & Category definition with style modifier
        subject_phrase = f"photorealistic {category} fine jewellery product photograph"
        prompt_components.append(subject_phrase)

        # 2. Material & Precious Metal specification
        material_spec = design.material
        metal_desc = material_spec.primary_metal.strip()
        finish_desc = material_spec.finish.strip() if material_spec.finish else "polished"
        
        metal_phrase = f"crafted in {finish_desc} {metal_desc}"
        if material_spec.accent_metal and material_spec.accent_metal.strip():
            metal_phrase += f" with {material_spec.accent_metal.strip()} accents"
        prompt_components.append(metal_phrase)

        # 3. Gemstones specification
        gem_spec = design.gemstones
        if gem_spec.has_gemstones:
            gem_phrases: List[str] = []
            if gem_spec.primary_gemstone:
                p_gem = gem_spec.primary_gemstone
                cut = p_gem.cut.strip()
                gtype = p_gem.gemstone_type.strip()
                stype = p_gem.setting_type.strip()
                count = p_gem.estimated_count
                
                if count > 1:
                    primary_phrase = f"{count} {cut} {gtype}s in {stype}"
                else:
                    primary_phrase = f"featured {cut} {gtype} in {stype}"
                gem_phrases.append(primary_phrase)

            if gem_spec.secondary_gemstones:
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
        if struct_spec.band_or_body_structure and struct_spec.band_or_body_structure not in ("classic band", "classic tapered band"):
            struct_parts.append(struct_spec.band_or_body_structure.strip())
        elif struct_spec.band_or_body_structure and not any("structure: " in c for c in applied_constraints):
            struct_parts.append(struct_spec.band_or_body_structure.strip())

        if struct_spec.setting_style and struct_spec.setting_style != "classic setting":
            struct_parts.append(struct_spec.setting_style.strip())
        if struct_spec.decorative_elements:
            struct_parts.extend([d.strip() for d in struct_spec.decorative_elements])

        # Strictly preserve any explicit structural constraints
        for c in applied_constraints:
            if c.startswith("structure: "):
                val = c.split("structure: ", 1)[1].strip()
                if not any(val in sp for sp in struct_parts):
                    struct_parts.append(val)

        if struct_parts:
            prompt_components.append(f"featuring {', '.join(struct_parts)}")

        # 5. Aesthetic Quality & Lighting Anchors
        prompt_components.append(STUDIO_LIGHTING_ANCHOR)

        # Assemble and clean
        final_prompt = ", ".join(prompt_components)
        return final_prompt

    @classmethod
    def compile_negative_prompt(cls, custom_negatives: Optional[str] = None) -> str:
        """Constructs negative prompt with optional user custom negative tokens."""
        if custom_negatives and custom_negatives.strip():
            return f"{JEWELLERY_NEGATIVE_PROMPT}, {custom_negatives.strip()}"
        return JEWELLERY_NEGATIVE_PROMPT

    @classmethod
    def compile_natural_enhanced_prompt(cls, design: StructuredDesignUnderstanding) -> str:
        """Constructs an elegant natural-language artisan description for UI display."""
        category = design.jewellery_category.capitalize().replace("_", " ")
        metal = design.material.primary_metal
        finish = design.material.finish or "polished"
        
        desc = f"A bespoke {category} expertly rendered in {finish} {metal}."
        
        if design.gemstones.has_gemstones and design.gemstones.primary_gemstone:
            p_gem = design.gemstones.primary_gemstone
            desc += f" It highlights a breathtaking {p_gem.cut} {p_gem.gemstone_type} held securely in a {p_gem.setting_type}."
            if design.gemstones.secondary_gemstones:
                sec_list = [f"{s.cut} {s.gemstone_type}s ({s.setting_type})" for s in design.gemstones.secondary_gemstones]
                desc += f" Complemented by {' and '.join(sec_list)}."
        
        if design.structure.band_or_body_structure:
            desc += f" The piece features a {design.structure.band_or_body_structure} with {design.structure.silhouette}."
            
        if design.design_motifs:
            desc += f" Inspired by {', '.join(design.design_motifs)} aesthetics."

        return desc
