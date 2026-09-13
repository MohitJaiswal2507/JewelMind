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
KNOWN_METALS = [
    "18k yellow gold", "14k yellow gold", "yellow gold",
    "18k white gold", "14k white gold", "white gold",
    "18k rose gold", "14k rose gold", "rose gold",
    "950 platinum", "platinum",
    "925 sterling silver", "sterling silver", "silver",
    "18k gold", "14k gold", "gold",
]

KNOWN_STONES_CANONICAL = [
    ("blue sapphire", ["blue sapphire", "blue sapphires"]),
    ("pink sapphire", ["pink sapphire", "pink sapphires"]),
    ("yellow sapphire", ["yellow sapphire", "yellow sapphires"]),
    ("sapphire", ["sapphire", "sapphires"]),
    ("emerald", ["emerald", "emeralds"]),
    ("black onyx", ["black onyx"]),
    ("onyx", ["onyx"]),
    ("ruby", ["ruby", "rubies"]),
    ("pearl", ["pearl", "pearls"]),
    ("topaz", ["topaz"]),
    ("amethyst", ["amethyst", "amethysts"]),
    ("opal", ["opal", "opals"]),
    ("aquamarine", ["aquamarine"]),
    ("tanzanite", ["tanzanite"]),
    ("diamond", ["diamond", "diamonds"]),
]

KNOWN_STONES = [
    "blue sapphire", "pink sapphire", "yellow sapphire", "sapphire",
    "emerald", "black onyx", "onyx", "ruby", "pearl", "topaz",
    "amethyst", "opal", "aquamarine", "tanzanite", "diamond",
]

KNOWN_CUTS_CANONICAL = [
    ("round brilliant", ["round brilliant cut", "round brilliant", "round cut", "round diamonds", "round diamond"]),
    ("emerald cut", ["emerald cut"]),
    ("pear", ["pear shaped", "pear cut", "pear shape", "pear stone", "pear"]),
    ("princess cut", ["princess cut", "princess"]),
    ("baguette", ["baguette cut", "baguette diamonds", "baguette diamond", "baguette cut diamonds", "baguette cut diamond", "baguette"]),
    ("cushion", ["cushion cut", "cushion"]),
    ("marquise", ["marquise cut", "marquise"]),
    ("heart", ["heart shaped", "heart cut", "heart shape", "heart"]),
    ("rose cut", ["rose cut"]),
    ("cabochon", ["cabochon"]),
    ("radiant", ["radiant cut", "radiant"]),
    ("oval", ["oval cut", "oval stone", "oval blue sapphire", "oval"]),
]

KNOWN_CUTS = [
    "round brilliant", "emerald cut", "pear", "princess cut",
    "baguette", "cushion", "marquise", "heart", "rose cut",
    "cabochon", "radiant", "oval",
]

KNOWN_CATEGORIES = [c.value for c in JewelleryCategory]

CATEGORY_CANONICAL_MAP = {
    "ring": "ring",
    "rings": "ring",
    "band": "ring",
    "earring": "earring",
    "earrings": "earring",
    "pendant": "pendant",
    "pendants": "pendant",
    "necklace": "necklace",
    "necklaces": "necklace",
    "bracelet": "bracelet",
    "bracelets": "bracelet",
    "bangle": "bangle",
    "bangles": "bangle",
    "brooch": "brooch",
    "brooches": "brooch",
    "other": "other_jewellery",
    "other_jewellery": "other_jewellery",
    "other jewellery": "other_jewellery",
}

PROMPT_CATEGORY_PATTERNS = [
    ("earring", [r"\bearrings?\b", r"\bear\s*studs?\b", r"\bstud\s*earrings?\b", r"\bdrop\s*earrings?\b", r"\bchandelier\s*earrings?\b", r"\bhoop\s*earrings?\b"]),
    ("necklace", [r"\bnecklaces?\b", r"\bchokers?\b", r"\bcollars?\b"]),
    ("bracelet", [r"\bbracelets?\b", r"\btennis\s*bracelet\b", r"\bcharm\s*bracelet\b"]),
    ("bangle", [r"\bbangles?\b", r"\bkadas?\b"]),
    ("pendant", [r"\bpendants?\b", r"\blockets?\b", r"\bmedallions?\b"]),
    ("brooch", [r"\bbrooch(?:es)?\b", r"\bpin\b", r"\bpins\b"]),
    ("ring", [r"\brings?\b", r"\bsolitaire\s*ring\b", r"\bcocktail\s*ring\b"]),
    ("other_jewellery", [r"\bother\s*jewell?ery\b"]),
]


def canonicalize_category(cat: Optional[str]) -> Optional[str]:
    """Canonicalize jewellery category string to supported controlled taxonomy."""
    if not cat:
        return None
    cleaned = str(cat).strip().lower().replace("-", "_").replace(" ", "_")
    return CATEGORY_CANONICAL_MAP.get(cleaned, None)


def extract_explicit_category(user_prompt: Optional[str]) -> Optional[str]:
    """Deterministically extracts explicit jewellery category requested in prompt."""
    return GeminiDesignService.extract_explicit_category(user_prompt)


class CategoryResolutionResult(tuple):
    """Enriched 3-tuple preserving backward compatibility while carrying conflict metadata."""
    resolved: str
    conflict: bool
    warnings: List[str]
    category_source: str
    conflict_reason: Optional[str]
    requested_category: Optional[str]
    source_blueprint_category: Optional[str]

    def __new__(
        cls,
        resolved: str,
        conflict: bool,
        warnings: List[str],
        category_source: str = "default",
        conflict_reason: Optional[str] = None,
        requested_category: Optional[str] = None,
        source_blueprint_category: Optional[str] = None,
    ):
        inst = super().__new__(cls, (resolved, conflict, warnings))
        inst.resolved = resolved
        inst.conflict = conflict
        inst.warnings = warnings
        inst.category_source = category_source
        inst.conflict_reason = conflict_reason
        inst.requested_category = requested_category or resolved
        inst.source_blueprint_category = source_blueprint_category
        return inst


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
    def extract_explicit_category(user_prompt: Optional[str]) -> Optional[str]:
        """Deterministically extracts explicit jewellery category requested in prompt."""
        if not user_prompt or not user_prompt.strip():
            return None
        p_lower = user_prompt.lower()
        matches = []
        for cat, patterns in PROMPT_CATEGORY_PATTERNS:
            for pat in patterns:
                for m in re.finditer(pat, p_lower):
                    matches.append((m.start(), cat))
        if not matches:
            return None
        matches.sort(key=lambda x: x[0])
        return matches[0][1]

    @staticmethod
    def extract_explicit_user_constraints(user_prompt: Optional[str]) -> List[str]:
        """Extracts immutable Tier-1 constraints from user input preserving prompt appearance order."""
        if not user_prompt or not user_prompt.strip():
            return []
        
        lower = user_prompt.lower()
        constraints: List[str] = []

        # 1. Metals (ordered by appearance and phrase length)
        found_metals = []
        for metal in KNOWN_METALS:
            idx = lower.find(metal)
            if idx != -1:
                found_metals.append((idx, len(metal), metal))
        if found_metals:
            found_metals.sort(key=lambda x: (x[0], -x[1]))
            constraints.append(f"metal: {found_metals[0][2]}")

        # 2. Gemstones (sorted by order of appearance in prompt)
        found_stones = []
        for canonical, aliases in KNOWN_STONES_CANONICAL:
            for alias in aliases:
                pattern = r"\b" + re.escape(alias) + r"\b"
                for m in re.finditer(pattern, lower):
                    found_stones.append((m.start(), canonical))
        
        found_stones.sort(key=lambda x: x[0])
        seen_stones = set()
        for _, stone in found_stones:
            if stone not in seen_stones:
                seen_stones.add(stone)
                constraints.append(f"gemstone: {stone}")

        # 3. Cuts (sorted by order of appearance in prompt)
        found_cuts = []
        for canonical, aliases in KNOWN_CUTS_CANONICAL:
            for alias in aliases:
                pattern = r"\b" + re.escape(alias) + r"\b"
                for m in re.finditer(pattern, lower):
                    found_cuts.append((m.start(), canonical))
        
        found_cuts.sort(key=lambda x: x[0])
        seen_cuts = set()
        for _, cut in found_cuts:
            if cut not in seen_cuts:
                seen_cuts.add(cut)
                constraints.append(f"cut: {cut}")

        # 4. Setting, structural, & styling keywords
        KNOWN_STRUCTURAL_PHRASES = [
            "thin shank", "wide band", "thick band", "thick shank", "wide shank",
            "minimalist", "delicate diamond halo", "diamond halo", "delicate halo", "halo",
            "solitaire", "bezel", "pavé", "pave", "channel", "prong", "filigree", "milgrain",
            "engraved floral pattern", "engraved floral", "floral pattern", "engraved", "floral",
            "tennis bracelet", "tennis", "cuff", "hoop", "drop", "articulated",
            "black onyx inlays", "onyx inlays", "inlays", "petal diamond accents",
            "diamond accents", "accents", "art deco", "geometric", "vintage",
        ]
        found_structs = []
        for struct in KNOWN_STRUCTURAL_PHRASES:
            pattern = r"\b" + re.escape(struct) + r"\b"
            for m in re.finditer(pattern, lower):
                found_structs.append((m.start(), len(struct), struct))
        
        found_structs.sort(key=lambda x: (x[0], -x[1]))
        seen_structs = set()
        for _, _, struct in found_structs:
            if not any(struct in s for s in seen_structs):
                seen_structs.add(struct)
                constraints.append(f"structure: {struct}")

        return constraints

    def _resolve_category(
        self,
        gemini_category: Optional[str] = None,
        yolo_context: Optional[YoloGroundingContext] = None,
        user_prompt: Optional[str] = None,
        source_blueprint_category: Optional[str] = None,
        user_selected_category: Optional[str] = None,
    ) -> CategoryResolutionResult:
        """Resolves category conflicts adhering to the authoritative precedence hierarchy:
        
        HIGHEST PRIORITY:
        1. Explicit user intent/category in user_prompt
        2. Explicit user-selected UI category
        3. High-confidence YOLO V2 category (confidence >= 0.70)
        4. Gemini Vision visual category
        5. Fallback/default (blueprint category or 'other_jewellery')
        
        Crucially detects category conflicts when requested category differs from
        the source blueprint category.
        """
        warnings: List[str] = []
        
        # Determine source blueprint category canonical form
        clean_blueprint = canonicalize_category(source_blueprint_category)
        if not clean_blueprint and yolo_context and yolo_context.detected_category:
            clean_blueprint = canonicalize_category(yolo_context.detected_category)

        # 1. Check explicit user category in prompt (Tier 1 Authority)
        explicit_user_cat = self.extract_explicit_category(user_prompt)
        if explicit_user_cat:
            resolved = explicit_user_cat
            requested_cat = explicit_user_cat
            cat_source = "user_prompt"
            conflict = False
            conflict_reason = None
            if clean_blueprint and clean_blueprint != resolved:
                conflict = True
                conflict_reason = f"User requested '{resolved}' but supplied blueprint is classified as '{clean_blueprint}'."
                warnings.append(
                    f"Category conflict detected: User requested category '{resolved}' in prompt, "
                    f"conflicting with source blueprint '{clean_blueprint}'. "
                    f"Conditioning on this blueprint will strongly influence render geometry."
                )
            return CategoryResolutionResult(
                resolved=resolved,
                conflict=conflict,
                warnings=warnings,
                category_source=cat_source,
                conflict_reason=conflict_reason,
                requested_category=requested_cat,
                source_blueprint_category=clean_blueprint,
            )

        # 2. Check explicit user manual selection in UI (Tier 2 Authority)
        clean_manual = canonicalize_category(user_selected_category)
        if clean_manual and clean_manual not in ("other", "other_jewellery", "default", ""):
            resolved = clean_manual
            requested_cat = clean_manual
            cat_source = "user_selected"
            conflict = False
            conflict_reason = None
            if clean_blueprint and clean_blueprint != resolved:
                conflict = True
                conflict_reason = f"User selected '{resolved}' in UI but supplied blueprint is classified as '{clean_blueprint}'."
                warnings.append(
                    f"Category conflict detected: User selected '{resolved}' in UI, "
                    f"conflicting with source blueprint '{clean_blueprint}'."
                )
            return CategoryResolutionResult(
                resolved=resolved,
                conflict=conflict,
                warnings=warnings,
                category_source=cat_source,
                conflict_reason=conflict_reason,
                requested_category=requested_cat,
                source_blueprint_category=clean_blueprint,
            )

        # 3. High-confidence YOLO V2 Grounding (confidence >= 0.70)
        clean_gemini = canonicalize_category(gemini_category)
        clean_yolo = canonicalize_category(yolo_context.detected_category) if (yolo_context and yolo_context.detected_category) else None

        if yolo_context and clean_yolo and yolo_context.confidence >= 0.70:
            resolved = clean_yolo
            requested_cat = clean_yolo
            cat_source = "yolo"
            conflict = False
            conflict_reason = None
            if clean_gemini and clean_gemini != clean_yolo:
                conflict = True
                conflict_reason = (
                    f"Category conflict detected: Local YOLO V2 predicted '{clean_yolo}' (conf: {yolo_context.confidence:.2f}) "
                    f"while Gemini Vision interpreted '{clean_gemini}'."
                )
                warnings.append(conflict_reason)
                warnings.append(f"Grounded on local YOLO V2 detector ({clean_yolo}) due to high confidence ({yolo_context.confidence:.2f}).")
            return CategoryResolutionResult(
                resolved=resolved,
                conflict=conflict,
                warnings=warnings,
                category_source=cat_source,
                conflict_reason=conflict_reason,
                requested_category=requested_cat,
                source_blueprint_category=clean_blueprint,
            )

        # 4. Gemini Vision visual interpretation
        if clean_gemini and clean_gemini != "other_jewellery":
            resolved = clean_gemini
            requested_cat = clean_gemini
            cat_source = "gemini"
            conflict = False
            conflict_reason = None
            if clean_yolo and clean_yolo != clean_gemini:
                conflict = True
                y_conf = yolo_context.confidence if yolo_context else 0.0
                conflict_reason = (
                    f"Category conflict detected: Local YOLO V2 predicted '{clean_yolo}' (conf: {y_conf:.2f}) "
                    f"while Gemini Vision interpreted '{clean_gemini}'."
                )
                warnings.append(conflict_reason)
                warnings.append(f"Grounded on Gemini Vision ({clean_gemini}) because YOLO confidence was below threshold ({y_conf:.2f}).")
            return CategoryResolutionResult(
                resolved=resolved,
                conflict=conflict,
                warnings=warnings,
                category_source=cat_source,
                conflict_reason=conflict_reason,
                requested_category=requested_cat,
                source_blueprint_category=clean_blueprint,
            )

        # 5. Fallback grounding
        if clean_blueprint:
            resolved = clean_blueprint
            requested_cat = clean_blueprint
            cat_source = "default"
        else:
            resolved = "other_jewellery"
            requested_cat = "other_jewellery"
            cat_source = "default"

        return CategoryResolutionResult(
            resolved=resolved,
            conflict=False,
            warnings=warnings,
            category_source=cat_source,
            conflict_reason=None,
            requested_category=requested_cat,
            source_blueprint_category=clean_blueprint,
        )

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
        """Generates deterministic heuristic design understanding from text prompt only (CASE A).
        
        Strictly preserves explicit user attributes (Tier 1 precedence).
        Never invents default gemstones when none were specified.
        Never replaces explicit cuts (oval, emerald cut, baguette, pear) with round brilliant.
        """
        explicit_cat = self.extract_explicit_category(user_prompt)
        cat = "ring"
        if explicit_cat:
            cat = explicit_cat
        elif category_hint:
            cat = canonicalize_category(category_hint) or "ring"
        elif yolo_context and yolo_context.detected_category:
            cat = canonicalize_category(yolo_context.detected_category) or "ring"

        constraints = self.extract_explicit_user_constraints(user_prompt)

        # Detect metals from prompt or default
        metal = "18k yellow gold"
        for c in constraints:
            if c.startswith("metal: "):
                metal = c.split("metal: ", 1)[1]
                break

        # Detect stones and cuts from prompt
        stones = [c.split("gemstone: ", 1)[1] for c in constraints if c.startswith("gemstone: ")]
        cuts = [c.split("cut: ", 1)[1] for c in constraints if c.startswith("cut: ")]

        has_gems = False
        primary_gem: Optional[GemstoneItem] = None
        secondary_gems: List[GemstoneItem] = []
        gemstone_details: Optional[str] = None

        if stones:
            has_gems = True
            primary_stone = stones[0]
            # Preserve explicit cut; only default to round brilliant if explicitly mentioned
            primary_cut = cuts[0] if cuts else ("round brilliant" if "round" in user_prompt.lower() else "faceted")

            count = 1
            p_lower = user_prompt.lower()
            if "three diamonds" in p_lower or "3 diamonds" in p_lower or "three " in p_lower:
                count = 3
            elif "two diamonds" in p_lower or "2 diamonds" in p_lower or "pair" in p_lower:
                count = 2

            setting = "prong setting"
            for c in constraints:
                if c.startswith("structure: "):
                    val = c.split("structure: ", 1)[1]
                    if any(s in val for s in ["bezel", "pave", "pavé", "channel", "prong", "basket"]):
                        setting = f"{val} setting" if "setting" not in val else val

            primary_gem = GemstoneItem(
                gemstone_type=primary_stone,
                cut=primary_cut,
                estimated_count=count,
                setting_type=setting,
            )
            gemstone_details = f"Featured {primary_cut} {primary_stone}"

            # Secondary stones (e.g. halo diamonds, onyx inlays, petal accents)
            if len(stones) > 1:
                for idx, s in enumerate(stones[1:], start=1):
                    sec_cut = cuts[idx] if len(cuts) > idx else ("round brilliant" if "round" in p_lower else "accent")
                    sec_setting = "halo setting" if "halo" in p_lower else ("inlay setting" if "inlay" in p_lower else "accent setting")
                    secondary_gems.append(
                        GemstoneItem(
                            gemstone_type=s,
                            cut=sec_cut,
                            estimated_count=16 if "halo" in p_lower else (1 if "inlay" in p_lower else 8),
                            setting_type=sec_setting,
                        )
                    )

        band_structure = "classic tapered band"
        setting_style = "classic setting"
        decorative_elements: List[str] = []

        for c in constraints:
            if c.startswith("structure: "):
                val = c.split("structure: ", 1)[1].strip()
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
                secondary_gemstones=secondary_gems,
                gemstone_details=gemstone_details,
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
        explicit_cat = self.extract_explicit_category(user_prompt)
        cat = "other_jewellery"
        if explicit_cat:
            cat = explicit_cat
        elif yolo_context and yolo_context.detected_category:
            cat = canonicalize_category(yolo_context.detected_category) or "other_jewellery"

        constraints = self.extract_explicit_user_constraints(user_prompt)

        # Check explicit user constraints for metal; do not invent if absent
        metal = "precious metal"
        for c in constraints:
            if c.startswith("metal: "):
                metal = c.split("metal: ", 1)[1]
                break

        # Check explicit user constraints for gemstones; DO NOT invent stones if not in user prompt!
        stones = [c.split("gemstone: ", 1)[1] for c in constraints if c.startswith("gemstone: ")]
        cuts = [c.split("cut: ", 1)[1] for c in constraints if c.startswith("cut: ")]

        has_gems = False
        primary_gem: Optional[GemstoneItem] = None
        secondary_gems: List[GemstoneItem] = []

        if stones:
            has_gems = True
            primary_stone = stones[0]
            primary_cut = cuts[0] if cuts else ("round brilliant" if user_prompt and "round" in user_prompt.lower() else "faceted")
            primary_gem = GemstoneItem(
                gemstone_type=primary_stone,
                cut=primary_cut,
                estimated_count=1,
                setting_type="prong setting",
            )
            if len(stones) > 1:
                for idx, s in enumerate(stones[1:], start=1):
                    sec_cut = cuts[idx] if len(cuts) > idx else "accent"
                    secondary_gems.append(
                        GemstoneItem(
                            gemstone_type=s,
                            cut=sec_cut,
                            estimated_count=8,
                            setting_type="accent setting",
                        )
                    )

        # Check explicit user constraints for structure; DO NOT invent structural details if not in prompt!
        band_structure = "standard mount"
        setting_style = "standard setting"
        decorative_elements: List[str] = []

        for c in constraints:
            if c.startswith("structure: "):
                val = c.split("structure: ", 1)[1].strip()
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
                secondary_gemstones=secondary_gems,
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
        source_blueprint_category: Optional[str] = None,
        user_selected_category: Optional[str] = None,
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
        cat_res = self._resolve_category(
            gemini_cat,
            yolo_context,
            user_prompt,
            source_blueprint_category=source_blueprint_category,
            user_selected_category=user_selected_category,
        )
        resolved_cat = cat_res.resolved
        warnings.extend(cat_res.warnings)
        design_understanding.jewellery_category = resolved_cat

        # Compile diffusion and natural prompts
        renderer_prompt = JewelleryPromptCompiler.compile_renderer_prompt(design_understanding, constraints)
        negative_prompt = JewelleryPromptCompiler.compile_negative_prompt(user_constraints=constraints)
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
            source_blueprint_category=cat_res.source_blueprint_category,
            requested_category=cat_res.requested_category,
            resolved_category=resolved_cat,
            category_source=cat_res.category_source,
            category_conflict=cat_res.conflict,
            category_conflict_reason=cat_res.conflict_reason,
            warnings=warnings,
            fallback_applied=fallback_applied,
        )

    async def enhance_prompt(
        self,
        user_prompt: str,
        image_bytes: Optional[bytes] = None,
        yolo_context: Optional[YoloGroundingContext] = None,
        image_mime_type: str = "image/png",
        source_blueprint_category: Optional[str] = None,
        user_selected_category: Optional[str] = None,
    ) -> EnhancePromptResponse:
        """Enhances a user-written prompt with rich jewellery terminology and structured specifications."""
        analysis_resp = await self.analyze_design(
            image_bytes=image_bytes,
            user_prompt=user_prompt,
            yolo_context=yolo_context,
            image_mime_type=image_mime_type,
            source_blueprint_category=source_blueprint_category,
            user_selected_category=user_selected_category,
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
            source_blueprint_category=analysis_resp.source_blueprint_category,
            requested_category=analysis_resp.requested_category,
            resolved_category=analysis_resp.resolved_category,
            category_source=analysis_resp.category_source,
            category_conflict=analysis_resp.category_conflict,
            category_conflict_reason=analysis_resp.category_conflict_reason,
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
