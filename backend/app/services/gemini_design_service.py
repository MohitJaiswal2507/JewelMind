"""JewelMind Gemini Design Understanding Service.

Provides multimodal jewellery blueprint analysis, prompt enhancement,
and user-intent preservation via Google Gemini API with resilient fallback.
"""

import base64
import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple, Union
import httpx

from app.core.config import settings
from app.schemas.ai import (
    AnalyzeDesignRequest,
    AnalyzeDesignResponse,
    EnhancePromptRequest,
    EnhancePromptResponse,
    GemstoneItem,
    GemstoneSpec,
    JewelleryCategory,
    MaterialSpec,
    StructuralSpec,
    StructuredDesignUnderstanding,
    YoloGroundingContext,
)
from app.services.jewellery_prompt_compiler import JewelleryPromptCompiler

logger = logging.getLogger("jewelmind.gemini")

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

# Known jewellery keywords for client-side intent extraction
KNOWN_METALS = ["platinum", "18k yellow gold", "yellow gold", "white gold", "rose gold", "sterling silver", "silver", "gold"]
KNOWN_STONES = ["diamond", "sapphire", "blue sapphire", "emerald", "ruby", "amethyst", "pearl", "opal", "topaz", "aquamarine", "tanzanite"]
KNOWN_CUTS = ["round brilliant", "oval", "cushion", "emerald cut", "pear", "princess cut", "marquise", "baguette", "radiant", "heart"]
KNOWN_CATEGORIES = [c.value for c in JewelleryCategory]


class GeminiDesignService:
    """Service handling Gemini Vision design understanding and prompt enhancement."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout: Optional[float] = None,
    ):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = model_name or settings.GEMINI_MODEL
        self.timeout = timeout or settings.GEMINI_REQUEST_TIMEOUT

    def is_available(self) -> bool:
        """Returns True if Gemini API key is configured and non-empty."""
        return bool(self.api_key and self.api_key.strip() and "placeholder" not in self.api_key.lower())

    @staticmethod
    def extract_explicit_user_constraints(user_prompt: Optional[str]) -> List[str]:
        """Extracts immutable Tier-1 constraints from user input."""
        if not user_prompt or not user_prompt.strip():
            return []
        
        lower = user_prompt.lower()
        constraints: List[str] = []

        for metal in KNOWN_METALS:
            if metal in lower and metal not in constraints:
                constraints.append(f"metal: {metal}")
                break

        for stone in KNOWN_STONES:
            if stone in lower and stone not in constraints:
                constraints.append(f"gemstone: {stone}")

        for cut in KNOWN_CUTS:
            if cut in lower and cut not in constraints:
                constraints.append(f"cut: {cut}")

        # Setting & structural keywords
        for struct in ["thin shank", "wide band", "cathedral", "halo", "solitaire", "bezel", "pavé", "pave", "channel", "prong", "filigree", "milgrain"]:
            if struct in lower:
                constraints.append(f"structure: {struct}")

        return constraints

    def _resolve_category(
        self,
        gemini_category: Optional[str],
        yolo_context: Optional[YoloGroundingContext],
        user_prompt: Optional[str],
    ) -> Tuple[str, bool, List[str]]:
        """Resolves category conflicts between user intent, YOLO V2, and Gemini Vision.
        
        Precedence:
        1. Explicit user category mention (e.g. user says 'ring' or 'earrings')
        2. High-confidence YOLO V2 grounding (confidence >= 0.70)
        3. Gemini Vision visual interpretation
        4. Lower-confidence YOLO V2
        5. Fallback ('other_jewellery')
        """
        warnings: List[str] = []

        # 1. Check explicit user mention with strict word boundaries
        if user_prompt:
            p_lower = user_prompt.lower()
            sorted_categories = sorted(KNOWN_CATEGORIES, key=len, reverse=True)
            for cat in sorted_categories:
                cat_phrase = cat.replace("_", " ")
                pattern = r"\b" + re.escape(cat_phrase) + r"(?:s)?\b"
                if re.search(pattern, p_lower):
                    if yolo_context and yolo_context.detected_category != cat:
                        warnings.append(
                            f"User explicitly requested category '{cat}', overriding local YOLO V2 detection '{yolo_context.detected_category}'."
                        )
                    return cat, False, warnings

        # 2. If Gemini category is not available (e.g. visual analysis was skipped or failed)
        if not gemini_category:
            if yolo_context and yolo_context.detected_category:
                clean_yolo = yolo_context.detected_category.strip().lower().replace(" ", "_")
                if clean_yolo in KNOWN_CATEGORIES:
                    return clean_yolo, False, warnings
            return "other_jewellery", False, warnings

        clean_gemini = gemini_category.strip().lower().replace(" ", "_")
        if clean_gemini not in KNOWN_CATEGORIES:
            clean_gemini = "other_jewellery"

        # 3. If no YOLO context, ground on Gemini
        if not yolo_context:
            return clean_gemini, False, warnings

        clean_yolo = yolo_context.detected_category.strip().lower().replace(" ", "_")
        conflict = clean_yolo != clean_gemini

        if conflict:
            warnings.append(
                f"Category conflict detected: Local YOLO V2 predicted '{clean_yolo}' (conf: {yolo_context.confidence:.2f}) "
                f"while Gemini Vision interpreted '{clean_gemini}'."
            )
            # YOLO V2 is treated as strong grounding/context
            if yolo_context.confidence >= 0.70:
                resolved = clean_yolo
                warnings.append(f"Grounded on local YOLO V2 detector ({clean_yolo}) due to high confidence ({yolo_context.confidence:.2f}).")
            else:
                resolved = clean_gemini
                warnings.append(f"Grounded on Gemini Vision ({clean_gemini}) because YOLO confidence was below threshold ({yolo_context.confidence:.2f}).")
        else:
            resolved = clean_yolo

        return resolved, conflict, warnings

    async def _call_gemini_api(
        self,
        prompt_text: str,
        image_bytes: Optional[bytes] = None,
        image_mime_type: str = "image/png",
    ) -> Dict[str, Any]:
        """Executes raw HTTP request to Google Gemini REST API with structured JSON output."""
        if not self.is_available():
            raise RuntimeError("Gemini API key is not configured.")

        url = f"{GEMINI_API_BASE}/{self.model_name}:generateContent?key={self.api_key}"

        parts: List[Dict[str, Any]] = [{"text": prompt_text}]
        if image_bytes:
            b64_data = base64.b64encode(image_bytes).decode("utf-8")
            parts.append({
                "inline_data": {
                    "mime_type": image_mime_type,
                    "data": b64_data,
                }
            })

        payload = {
            "contents": [{"parts": parts}],
            "generationConfig": {
                "temperature": 0.2,  # Low temperature for precise, deterministic design analysis
                "response_mime_type": "application/json",
            },
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 429:
                raise RuntimeError("Gemini free-tier rate limit exceeded. Please retry shortly.")
            elif resp.status_code != 200:
                raise RuntimeError(f"Gemini API returned error HTTP {resp.status_code}: {resp.text}")

            res_json = resp.json()

        try:
            candidates = res_json.get("candidates", [])
            if not candidates:
                raise ValueError("No candidate completions returned by Gemini.")
            text_content = candidates[0]["content"]["parts"][0]["text"]
            data = json.loads(text_content)
            return data
        except Exception as e:
            raise ValueError(f"Failed to parse Gemini structured JSON response: {str(e)}") from e

    def _generate_text_fallback_analysis(
        self,
        user_prompt: str,
        yolo_context: Optional[YoloGroundingContext] = None,
        category_hint: Optional[str] = None,
    ) -> StructuredDesignUnderstanding:
        """Generates deterministic heuristic design understanding from text prompt only (CASE A)."""
        cat = "ring"
        if yolo_context and yolo_context.detected_category:
            cat = yolo_context.detected_category
        elif category_hint:
            cat = category_hint

        constraints = self.extract_explicit_user_constraints(user_prompt)

        # Detect metals from prompt or default
        metal = "18k yellow gold"
        for c in constraints:
            if c.startswith("metal: "):
                metal = c.split("metal: ")[1]
                break

        # Detect stones from prompt or default
        stone = "round brilliant diamond"
        has_gems = True
        for c in constraints:
            if c.startswith("gemstone: "):
                stone = c.split("gemstone: ")[1]
                break

        primary_gem = GemstoneItem(
            gemstone_type=stone if "diamond" not in stone else "diamond",
            cut="round brilliant",
            estimated_count=1,
            setting_type="prong setting",
        )

        band_structure = "classic tapered band"
        setting_style = "classic setting"
        decorative_elements: List[str] = []

        for c in constraints:
            if c.startswith("structure: "):
                val = c.split("structure: ")[1].strip()
                if any(k in val for k in ["shank", "band"]):
                    band_structure = val
                elif any(k in val for k in ["solitaire", "halo", "cathedral", "bezel", "pave", "pavé", "channel", "prong"]):
                    setting_style = f"{val} setting" if "setting" not in val else val
                else:
                    decorative_elements.append(val)

        return StructuredDesignUnderstanding(
            jewellery_category=cat,
            category_confidence=yolo_context.confidence if yolo_context else 0.85,
            design_summary=f"Text-derived specification for {cat} in {metal} with a {band_structure}.",
            material=MaterialSpec(primary_metal=metal, finish="polished high-shine"),
            gemstones=GemstoneSpec(
                has_gemstones=has_gems,
                primary_gemstone=primary_gem,
                gemstone_details=f"Centered {stone}",
            ),
            structure=StructuralSpec(
                band_or_body_structure=band_structure,
                setting_style=setting_style,
                decorative_elements=decorative_elements,
                silhouette="balanced architectural silhouette",
            ),
            design_motifs=["Classic Atelier"],
            user_intent_preserved=True,
            user_constraints_applied=constraints,
        )

    def _generate_image_fallback_analysis(
        self,
        user_prompt: Optional[str] = None,
        yolo_context: Optional[YoloGroundingContext] = None,
    ) -> StructuredDesignUnderstanding:
        """Controlled fallback for image/sketch when Gemini is unavailable (CASE B).
        
        DOES NOT pretend the image was visually analyzed.
        DOES NOT fabricate visual gemstones, prongs, or cuts from the image using regex.
        Preserves explicit user text constraints (Tier 1) and grounding context so the
        existing rendering workflow remains fully usable.
        """
        cat = "other_jewellery"
        if yolo_context and yolo_context.detected_category:
            cat = yolo_context.detected_category

        constraints = self.extract_explicit_user_constraints(user_prompt)

        # Check explicit user constraints for metal; do not invent if absent
        metal = "precious metal"
        for c in constraints:
            if c.startswith("metal: "):
                metal = c.split("metal: ")[1]
                break

        # Check explicit user constraints for gemstones; DO NOT invent stones if not in user prompt!
        has_gems = False
        primary_gem = None
        for c in constraints:
            if c.startswith("gemstone: "):
                has_gems = True
                stone = c.split("gemstone: ")[1]
                primary_gem = GemstoneItem(
                    gemstone_type=stone,
                    cut="round brilliant",
                    estimated_count=1,
                    setting_type="prong setting",
                )
                break

        # Check explicit user constraints for structure; DO NOT invent structural details if not in prompt!
        band_structure = "standard mount"
        setting_style = "standard setting"
        decorative_elements: List[str] = []

        for c in constraints:
            if c.startswith("structure: "):
                val = c.split("structure: ")[1].strip()
                if any(k in val for k in ["shank", "band"]):
                    band_structure = val
                elif any(k in val for k in ["solitaire", "halo", "cathedral", "bezel", "pave", "pavé", "channel", "prong"]):
                    setting_style = f"{val} setting" if "setting" not in val else val
                else:
                    decorative_elements.append(val)

        if user_prompt:
            summary = (
                f"Visual analysis unavailable for image/sketch. Fallback design structure for {cat} grounded on "
                f"user prompt notes and local context for rendering workflow."
            )
        else:
            summary = (
                f"Visual analysis unavailable for image/sketch. Preserved {cat} baseline geometry from local "
                f"grounding context for rendering workflow."
            )

        return StructuredDesignUnderstanding(
            jewellery_category=cat,
            category_confidence=yolo_context.confidence if yolo_context else None,
            design_summary=summary,
            material=MaterialSpec(primary_metal=metal, finish="polished"),
            gemstones=GemstoneSpec(
                has_gemstones=has_gems,
                primary_gemstone=primary_gem,
                gemstone_details=f"Specified {primary_gem.gemstone_type}" if primary_gem else None,
            ),
            structure=StructuralSpec(
                band_or_body_structure=band_structure,
                setting_style=setting_style,
                decorative_elements=decorative_elements,
                silhouette="balanced silhouette",
            ),
            design_motifs=[],
            user_intent_preserved=True,
            user_constraints_applied=constraints,
        )

    async def analyze_design(
        self,
        image_bytes: Optional[bytes] = None,
        user_prompt: Optional[str] = None,
        yolo_context: Optional[YoloGroundingContext] = None,
        image_mime_type: str = "image/png",
    ) -> AnalyzeDesignResponse:
        """Analyzes an uploaded jewellery sketch or photo, returning rich structured understanding and diffusion prompts."""
        constraints = self.extract_explicit_user_constraints(user_prompt)
        warnings: List[str] = []
        fallback_applied = False
        gemini_cat: Optional[str] = None
        has_image = bool(image_bytes and len(image_bytes) > 0)

        if not self.is_available():
            fallback_applied = True
            if has_image:
                logger.info("Gemini API key not configured. Visual understanding skipped; applying controlled image fallback.")
                warnings.append(
                    "Gemini visual understanding service is unavailable. Visual feature extraction was not performed "
                    "on the image/sketch; controlled fallback design metadata generated from available context for rendering continuity."
                )
                design_understanding = self._generate_image_fallback_analysis(user_prompt, yolo_context)
            else:
                logger.info("Gemini API key not configured. Applying text heuristic prompt enhancement.")
                warnings.append("Gemini service is unavailable. Text-derived heuristic design understanding applied from user prompt.")
                design_understanding = self._generate_text_fallback_analysis(user_prompt or "", yolo_context)
        else:
            system_prompt = (
                "You are an expert master jeweller, CAD designer, and gemologist. "
                "Analyze this jewellery sketch blueprint or image with meticulous geometric accuracy. "
                "Describe only what is visually supported. Do not invent details not present. "
                "CRITICAL PRECEDENCE RULE: All explicit user constraints must be strictly preserved and locked. "
                f"\nLOCKED USER CONSTRAINTS: {json.dumps(constraints)}\n"
            )
            if yolo_context:
                system_prompt += f"LOCAL YOLO V2 GROUNDING: Detected Category = '{yolo_context.detected_category}' (conf: {yolo_context.confidence:.2f})\n"
            if user_prompt:
                system_prompt += f"USER INTENT NOTES: \"{user_prompt}\"\n"

            system_prompt += (
                "\nRespond with a valid JSON object matching the following structure:\n"
                "{\n"
                '  "jewellery_category": "ring | earring | pendant | necklace | bracelet | bangle | brooch | other_jewellery",\n'
                '  "category_confidence": 0.95,\n'
                '  "design_summary": "Comprehensive artisan description of the jewellery design",\n'
                '  "material": {\n'
                '    "primary_metal": "18k yellow gold | 950 platinum | etc",\n'
                '    "finish": "polished | matte | etc",\n'
                '    "accent_metal": null\n'
                '  },\n'
                '  "gemstones": {\n'
                '    "has_gemstones": true,\n'
                '    "primary_gemstone": {\n'
                '      "gemstone_type": "diamond | sapphire | etc",\n'
                '      "cut": "round brilliant | cushion | etc",\n'
                '      "estimated_count": 1,\n'
                '      "setting_type": "4-prong basket | bezel | etc"\n'
                '    },\n'
                '    "secondary_gemstones": []\n'
                '  },\n'
                '  "structure": {\n'
                '    "silhouette": "...",\n'
                '    "symmetry": "...",\n'
                '    "setting_style": "...",\n'
                '    "band_or_body_structure": "...",\n'
                '    "decorative_elements": []\n'
                '  },\n'
                '  "design_motifs": ["..."],\n'
                '  "user_intent_preserved": true,\n'
                f'  "user_constraints_applied": {json.dumps(constraints)}\n'
                "}"
            )

            try:
                raw_json = await self._call_gemini_api(system_prompt, image_bytes, image_mime_type)
                raw_json["user_constraints_applied"] = constraints
                raw_json["user_intent_preserved"] = True
                design_understanding = StructuredDesignUnderstanding.model_validate(raw_json)
                gemini_cat = design_understanding.jewellery_category
            except Exception as exc:
                logger.warning("Gemini API call failed: %s. Using controlled fallback.", exc)
                fallback_applied = True
                if has_image:
                    warnings.append(
                        f"Gemini API unavailable ({str(exc)}). Visual feature extraction was skipped on image/sketch; "
                        "controlled fallback design metadata generated from available context."
                    )
                    design_understanding = self._generate_image_fallback_analysis(user_prompt, yolo_context)
                else:
                    warnings.append(f"Gemini API unavailable ({str(exc)}). Text-derived heuristic fallback applied.")
                    design_understanding = self._generate_text_fallback_analysis(user_prompt or "", yolo_context)

        # Resolve category with grounding precedence
        resolved_cat, conflict, cat_warnings = self._resolve_category(gemini_cat, yolo_context, user_prompt)
        warnings.extend(cat_warnings)
        design_understanding.jewellery_category = resolved_cat

        # Compile diffusion and natural prompts
        renderer_prompt = JewelleryPromptCompiler.compile_renderer_prompt(design_understanding, constraints)
        negative_prompt = JewelleryPromptCompiler.compile_negative_prompt()
        enhanced_prompt = JewelleryPromptCompiler.compile_natural_enhanced_prompt(design_understanding)

        return AnalyzeDesignResponse(
            success=True,
            design_understanding=design_understanding,
            renderer_prompt=renderer_prompt,
            negative_prompt=negative_prompt,
            original_prompt=user_prompt,
            enhanced_prompt=enhanced_prompt,
            yolo_category=yolo_context.detected_category if yolo_context else None,
            gemini_category=gemini_cat,
            resolved_category=resolved_cat,
            category_conflict=conflict,
            warnings=warnings,
            fallback_applied=fallback_applied,
        )

    async def enhance_prompt(
        self,
        user_prompt: str,
        image_bytes: Optional[bytes] = None,
        yolo_context: Optional[YoloGroundingContext] = None,
        image_mime_type: str = "image/png",
    ) -> EnhancePromptResponse:
        """Enhances a user-written prompt with rich jewellery terminology and structured specifications."""
        analysis_resp = await self.analyze_design(
            image_bytes=image_bytes,
            user_prompt=user_prompt,
            yolo_context=yolo_context,
            image_mime_type=image_mime_type,
        )

        return EnhancePromptResponse(
            success=analysis_resp.success,
            original_prompt=user_prompt,
            enhanced_prompt=analysis_resp.enhanced_prompt or user_prompt,
            design_understanding=analysis_resp.design_understanding,
            renderer_prompt=analysis_resp.renderer_prompt,
            negative_prompt=analysis_resp.negative_prompt,
            yolo_category=analysis_resp.yolo_category,
            gemini_category=analysis_resp.gemini_category,
            resolved_category=analysis_resp.resolved_category,
            category_conflict=analysis_resp.category_conflict,
            warnings=analysis_resp.warnings,
            fallback_applied=analysis_resp.fallback_applied,
        )


# Singleton instance helper
_gemini_service_instance: Optional[GeminiDesignService] = None


def get_gemini_design_service() -> GeminiDesignService:
    """Returns the singleton instance of GeminiDesignService."""
    global _gemini_service_instance
    if _gemini_service_instance is None:
        _gemini_service_instance = GeminiDesignService()
    return _gemini_service_instance
