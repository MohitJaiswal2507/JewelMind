"""
Gemini Production Intelligence Service
Dedicated service for AI-powered manufacturing reasoning, Bill of Materials (BOM) estimation,
jewellery routing generation, and deterministic domain fallback.
"""

import base64
import json
import logging
import re
import uuid
from typing import Any, Dict, List, Optional, Tuple
import httpx

from app.core.config import settings
from app.models.specification import (
    ProductionGemstone,
    ProductionMaterial,
    ProductionSpecification,
    ProductionStep,
)
from app.schemas.production_intelligence import (
    ComplexityRatingEnum,
    ProductionGemstoneEstimate,
    ProductionIntelligenceInput,
    ProductionMaterialEstimate,
    ProductionSpecificationAIResponse,
    ProductionStepEstimate,
    ProductionStructureObservation,
    ProvenanceOrigin,
)

logger = logging.getLogger("jewelmind.production_ai")

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

# Standard category benchmark weights and bench times for deterministic fallback
CATEGORY_BENCHMARKS = {
    "ring": {"rough_wt": 6.2, "net_wt": 5.5, "hours": 4.5, "comp": "moderate"},
    "earring": {"rough_wt": 4.8, "net_wt": 4.2, "hours": 4.0, "comp": "moderate"},
    "pendant": {"rough_wt": 5.0, "net_wt": 4.5, "hours": 3.5, "comp": "simple"},
    "necklace": {"rough_wt": 24.0, "net_wt": 21.5, "hours": 9.5, "comp": "intricate"},
    "bracelet": {"rough_wt": 18.0, "net_wt": 16.0, "hours": 7.5, "comp": "intricate"},
    "bangle": {"rough_wt": 22.0, "net_wt": 19.8, "hours": 6.0, "comp": "moderate"},
    "brooch": {"rough_wt": 12.0, "net_wt": 10.5, "hours": 5.5, "comp": "moderate"},
    "other_jewellery": {"rough_wt": 10.0, "net_wt": 9.0, "hours": 5.0, "comp": "moderate"},
}

KNOWN_METALS = [
    ("18k yellow gold", "gold", "18k", "yellow"),
    ("14k yellow gold", "gold", "14k", "yellow"),
    ("yellow gold", "gold", "18k", "yellow"),
    ("18k white gold", "gold", "18k", "white"),
    ("14k white gold", "gold", "14k", "white"),
    ("white gold", "gold", "18k", "white"),
    ("18k rose gold", "gold", "18k", "rose"),
    ("14k rose gold", "gold", "14k", "rose"),
    ("rose gold", "gold", "18k", "rose"),
    ("950 platinum", "platinum", "950", "white"),
    ("platinum", "platinum", "950", "white"),
    ("925 sterling silver", "silver", "925", "white"),
    ("sterling silver", "silver", "925", "white"),
    ("silver", "silver", "925", "white"),
    ("18k gold", "gold", "18k", "yellow"),
    ("14k gold", "gold", "14k", "yellow"),
    ("gold", "gold", "18k", "yellow"),
]

KNOWN_STONES = [
    "blue sapphire", "pink sapphire", "yellow sapphire", "sapphire",
    "emerald", "black onyx", "onyx", "ruby", "pearl", "topaz",
    "amethyst", "opal", "aquamarine", "tanzanite", "moissanite", "diamond",
]

NO_STONE_TRIGGERS = [
    "no gemstone", "no gemstones", "no stone", "no stones",
    "without gemstone", "without gemstones", "without stone", "without stones",
    "no gems", "without gems", "plain", "metal only", "pure metal",
    "unadorned", "zero gemstone", "no diamond", "without diamond",
    "zero stone", "no stones present",
]


class GeminiProductionService:
    """
    Service responsible for converting approved jewellery renders and design parameters
    into structured Production Specifications.
    """

    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.GEMINI_MODEL
        self.timeout = settings.GEMINI_REQUEST_TIMEOUT

    def is_available(self) -> bool:
        """Returns True if the Gemini API key is configured."""
        return bool(self.api_key and self.api_key.strip())

    # -----------------------------------------------------------------------
    # User Intent Extraction
    # -----------------------------------------------------------------------

    def extract_user_intent_metals(self, text: Optional[str]) -> Optional[Tuple[str, str, str]]:
        """Extracts (metal_type, purity, color) from user text."""
        if not text:
            return None
        lowered = text.lower()
        for phrase, m_type, purity, color in KNOWN_METALS:
            if re.search(rf"\b{re.escape(phrase)}\b", lowered):
                return (m_type, purity, color)
        return None

    def extract_user_intent_stones(self, text: Optional[str]) -> List[str]:
        """Extracts gemstone names from user text."""
        if not text:
            return []
        lowered = text.lower()
        if any(t in lowered for t in NO_STONE_TRIGGERS):
            return []
        found = []
        for s in KNOWN_STONES:
            if re.search(rf"\b{re.escape(s)}\b", lowered):
                if not any(s in x for x in found):
                    found.append(s)
        return found

    def has_no_stone_requirement(self, text: Optional[str]) -> bool:
        """Returns True if user explicitly requests a piece without gemstones."""
        if not text:
            return False
        lowered = text.lower()
        return any(t in lowered for t in NO_STONE_TRIGGERS)

    def extract_stone_count_hint(self, text: Optional[str]) -> Optional[int]:
        """Extracts approximate stone count from prompt text (e.g. '7 emerald stones' -> 7)."""
        if not text:
            return None
        lowered = text.lower()
        m = re.search(r"\b(\d+)\s*(?:pieces?|stones?|gems?|gemstones?|diamonds?|emeralds?|sapphires?)\b", lowered)
        if m:
            try:
                return int(m.group(1))
            except ValueError:
                pass
        return None

    def has_plating_requirement(self, text: Optional[str]) -> Optional[str]:
        """Detects if electroplating is requested (rhodium, gold vermeil, etc.)."""
        if not text:
            return None
        lowered = text.lower()
        if "rhodium" in lowered:
            return "rhodium"
        if "vermeil" in lowered:
            return "gold_vermeil"
        if "gold plate" in lowered or "gold plating" in lowered:
            return "18k_gold_plate"
        return None

    # -----------------------------------------------------------------------
    # Gemini Multimodal API Interaction
    # -----------------------------------------------------------------------

    async def _call_gemini_manufacturing_api(
        self,
        prompt_text: str,
        image_bytes: Optional[bytes] = None,
        image_mime_type: str = "image/png",
    ) -> Dict[str, Any]:
        """Calls the Gemini 2.5 Flash API with strict JSON schema instructions."""
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
                "temperature": 0.1,  # Low temperature for deterministic engineering reasoning
                "response_mime_type": "application/json",
            },
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code != 200:
                raise RuntimeError(f"Gemini API returned HTTP {resp.status_code}: {resp.text[:300]}")

            data = resp.json()
            candidates = data.get("candidates", [])
            if not candidates:
                raise ValueError("Gemini returned empty candidate list.")

            content_parts = candidates[0].get("content", {}).get("parts", [])
            if not content_parts:
                raise ValueError("Gemini returned empty content parts.")

            raw_text = content_parts[0].get("text", "{}")
            return json.loads(raw_text)

    # -----------------------------------------------------------------------
    # Prompt Construction
    # -----------------------------------------------------------------------

    def _build_manufacturing_prompt(self, input_data: ProductionIntelligenceInput) -> str:
        """Builds a rigorous manufacturing engineering prompt for Gemini."""
        prompt = (
            "You are JewelMind's Lead Master Goldsmith and Fine Jewellery Manufacturing Director. "
            "Analyze this approved photorealistic jewellery render and design context to formulate "
            "an actionable production blueprint for our atelier workshop.\n\n"
            "CRITICAL MANDATES:\n"
            "1. You are NOT redesigning the piece. You are planning its physical fabrication.\n"
            f"2. AUTHORITATIVE CATEGORY: '{input_data.category}'. Retain this category.\n"
            "3. USER INTENT PRECEDENCE: Explicit user requirements for metal alloy, purity, gemstones, "
            "and stone counts must be strictly preserved. Do NOT substitute diamonds if emerald was requested.\n"
            "4. NO FAKE MEASUREMENT PRECISION: You are observing a 2D render. State estimated weights in grams "
            "(rounded to 1-2 decimals, e.g. 5.8g). Do not invent micrometer millimeter thicknesses if uncertain.\n"
            "5. TAILORED ROUTING: Generate manufacturing stages appropriate to the specific category. "
            "Only include 'Stone Setting' if gemstones exist. Include 'Plating' if electroplating is specified.\n\n"
            "CONTEXT DATA:\n"
        )
        if input_data.user_prompt:
            prompt += f"- User Prompt: \"{input_data.user_prompt}\"\n"
        if input_data.enhanced_prompt:
            prompt += f"- Enhanced Synthesis Prompt: \"{input_data.enhanced_prompt}\"\n"
        if input_data.structured_state:
            prompt += f"- Structured Visual State: {json.dumps(input_data.structured_state)}\n"
        if input_data.material_hint:
            prompt += f"- Material Hint: {input_data.material_hint}\n"
        if input_data.gemstone_hint:
            prompt += f"- Gemstone Hint: {input_data.gemstone_hint}\n"

        prompt += (
            "\nReturn a valid JSON object matching the following structure:\n"
            "{\n"
            '  "category": "' + input_data.category + '",\n'
            '  "specification_summary": "Concise summary of manufacturing requirements",\n'
            '  "materials": [\n'
            '    {\n'
            '      "metal_type": "gold | platinum | silver",\n'
            '      "metal_purity": "18k | 14k | 950 | 925",\n'
            '      "metal_color": "yellow | white | rose",\n'
            '      "metal_finish": "high_polish | matte | satin",\n'
            '      "plating": "rhodium | none",\n'
            '      "estimated_weight_grams": 5.8,\n'
            '      "casting_loss_percentage": 10.0\n'
            '    }\n'
            '  ],\n'
            '  "gemstones": [\n'
            '    {\n'
            '      "gemstone_type": "diamond | emerald | sapphire | ruby | etc.",\n'
            '      "cut_shape": "round | cushion | oval | etc.",\n'
            '      "stone_count": 1,\n'
            '      "estimated_carat_weight": 1.2,\n'
            '      "approximate_dimensions_mm": "6.5mm",\n'
            '      "setting_type": "prong | bezel | channel | pave",\n'
            '      "is_center_stone": true\n'
            '    }\n'
            '  ],\n'
            '  "structure": {\n'
            '    "component_breakdown": ["shank", "collet", "bail"],\n'
            '    "estimated_dimensions": "Approximate nominal size",\n'
            '    "minimum_thickness": "Recommended minimum thickness (e.g. 1.4mm)",\n'
            '    "fabrication_notes": "Atelier bench observations"\n'
            '  },\n'
            '  "routing": [\n'
            '    {\n'
            '      "step_number": 1,\n'
            '      "stage_name": "CAD & 3D Wax Modeling",\n'
            '      "required_skill": "cad_design",\n'
            '      "required_machine_type": "3d_wax_printer",\n'
            '      "base_hours": 1.5,\n'
            '      "per_unit_hours": 0.25,\n'
            '      "description": "Prepare wax pattern",\n'
            '      "quality_checkpoint": "Check symmetry and prong thickness"\n'
            '    }\n'
            '  ],\n'
            '  "estimated_rough_metal_weight_grams": 6.5,\n'
            '  "estimated_finished_metal_weight_grams": 5.8,\n'
            '  "estimated_total_bench_hours": 4.5,\n'
            '  "complexity_rating": "simple | moderate | intricate | masterpiece",\n'
            '  "ai_confidence_score": 0.88,\n'
            '  "warnings": ["Array of engineering caveats or uncertainties"],\n'
            '  "assumptions": ["Array of geometric assumptions made"]\n'
            "}\n"
        )
        return prompt

    # -----------------------------------------------------------------------
    # Deterministic Domain Fallback Engine
    # -----------------------------------------------------------------------

    def _build_deterministic_production_spec(
        self,
        input_data: ProductionIntelligenceInput,
        fallback_reason: str = "Gemini manufacturing analysis unavailable",
    ) -> ProductionSpecificationAIResponse:
        """
        Conservative category-aware deterministic manufacturing fallback.
        Ensures the production workflow is never blocked when Gemini is offline.
        """
        cat = input_data.category
        bm = CATEGORY_BENCHMARKS.get(cat, CATEGORY_BENCHMARKS["other_jewellery"])

        combined_text = f"{input_data.user_prompt or ''} {input_data.enhanced_prompt or ''} {input_data.material_hint or ''}"
        metal_intent = self.extract_user_intent_metals(combined_text)
        if metal_intent:
            metal_type, purity, color = metal_intent
        else:
            # Check structured state
            struct_mat = (input_data.structured_state or {}).get("material", {})
            metal_type = struct_mat.get("metal", "gold").lower()
            purity = struct_mat.get("purity", "18k").lower()
            color = "yellow" if "yellow" in str(struct_mat).lower() else ("white" if "white" in str(struct_mat).lower() else "yellow")

        # Plating detection
        plating = self.has_plating_requirement(combined_text)
        if not plating and "white" in color and metal_type == "gold":
            plating = "rhodium"

        # Gemstone detection
        no_stones = self.has_no_stone_requirement(combined_text)
        gemstones: List[ProductionGemstoneEstimate] = []

        if not no_stones:
            stones_found = self.extract_user_intent_stones(combined_text)
            if not stones_found and input_data.gemstone_hint:
                stones_found = [input_data.gemstone_hint.lower()]
            if not stones_found and input_data.structured_state:
                raw_gems = (input_data.structured_state.get("gemstones") or [])
                if raw_gems and isinstance(raw_gems, list):
                    for g in raw_gems:
                        if isinstance(g, dict) and g.get("gemstone_type"):
                            stones_found.append(g["gemstone_type"].lower())

            if stones_found:
                count_hint = self.extract_stone_count_hint(combined_text) or 1
                for idx, stone in enumerate(stones_found):
                    is_center = (idx == 0)
                    stone_qty = count_hint if is_center and len(stones_found) == 1 else 1
                    gemstones.append(
                        ProductionGemstoneEstimate(
                            gemstone_type=stone,
                            cut_shape="round" if "round" in combined_text.lower() else "cushion",
                            stone_count=stone_qty,
                            estimated_carat_weight=round(0.75 * stone_qty, 2),
                            approximate_dimensions_mm="6.0mm" if is_center else "2.0mm",
                            setting_type="prong" if "bezel" not in combined_text.lower() else "bezel",
                            is_center_stone=is_center,
                            origin=ProvenanceOrigin.SYSTEM_DERIVED,
                        )
                    )

        # Build Material Line Item
        rough_wt = bm["rough_wt"]
        net_wt = bm["net_wt"]
        if metal_type == "platinum":
            rough_wt = round(rough_wt * 1.35, 1)
            net_wt = round(net_wt * 1.35, 1)
        elif metal_type == "silver":
            rough_wt = round(rough_wt * 0.70, 1)
            net_wt = round(net_wt * 0.70, 1)

        materials = [
            ProductionMaterialEstimate(
                metal_type=metal_type,
                metal_purity=purity,
                metal_color=color,
                metal_finish="high_polish",
                plating=plating,
                estimated_weight_grams=net_wt,
                casting_loss_percentage=10.0,
                origin=ProvenanceOrigin.SYSTEM_DERIVED,
            )
        ]

        # Build Tailored Routing
        routing = self._generate_routing_steps(
            category=cat,
            has_gemstones=bool(gemstones),
            has_plating=bool(plating and plating != "none"),
        )

        total_hours = sum(s.base_hours + s.per_unit_hours for s in routing)

        warnings = [
            f"{fallback_reason}; deterministic domain rules were applied.",
            "Weight and dimensional metrics are statistical atelier approximations; physically verify prior to casting.",
        ]
        if cat == "other_jewellery":
            warnings.append("Generic category assigned; custom artisan routing review recommended.")

        assumptions = [
            f"Alloy density assumed for {purity} {color} {metal_type}.",
            "Lost-wax investment casting path assumed.",
        ]

        return ProductionSpecificationAIResponse(
            design_id=input_data.design_id,
            render_id=input_data.render_id,
            category=cat,
            specification_summary=f"Deterministic manufacturing plan for {purity} {color} {metal_type} {cat}.",
            materials=materials,
            gemstones=gemstones,
            structure=ProductionStructureObservation(
                component_breakdown=["main_body", "collet"] if gemstones else ["main_body"],
                estimated_dimensions=f"Standard nominal {cat} sizing",
                minimum_thickness="1.4mm (minimum recommended wall thickness)",
                fabrication_notes="Execute spruing at thickest cross-section to eliminate shrink porosity.",
                origin=ProvenanceOrigin.SYSTEM_DERIVED,
            ),
            routing=routing,
            estimated_rough_metal_weight_grams=rough_wt,
            estimated_finished_metal_weight_grams=net_wt,
            estimated_total_bench_hours=round(total_hours, 2),
            complexity_rating=bm["comp"],
            ai_confidence_score=0.75,
            warnings=warnings,
            assumptions=assumptions,
            fallback_applied=True,
            provenance_summary={"engine": "DeterministicProductionEngine", "data_origin": "SYSTEM_DERIVED"},
        )

    # -----------------------------------------------------------------------
    # Routing Generator
    # -----------------------------------------------------------------------

    def _generate_routing_steps(
        self,
        category: str,
        has_gemstones: bool,
        has_plating: bool,
    ) -> List[ProductionStepEstimate]:
        """Constructs category-aware workshop stages."""
        steps: List[ProductionStepEstimate] = []
        step_num = 1

        # 1. CAD & Pattern
        steps.append(
            ProductionStepEstimate(
                step_number=step_num,
                stage_name="CAD & 3D Wax Pattern Printing",
                required_skill="cad_design",
                required_machine_type="3d_wax_printer",
                base_hours=1.5,
                per_unit_hours=0.25,
                description=f"Validate CAD solid geometry and print high-resolution castable wax pattern for {category}.",
                quality_checkpoint="Check support placement and dimensional accuracy.",
                origin=ProvenanceOrigin.SYSTEM_DERIVED,
            )
        )
        step_num += 1

        # 2. Investment Casting
        steps.append(
            ProductionStepEstimate(
                step_number=step_num,
                stage_name="Investment Casting & Spruing",
                required_skill="casting",
                required_machine_type="casting_furnace",
                base_hours=2.0,
                per_unit_hours=0.5,
                description="Flask investing, dewaxing, and vacuum pressure casting.",
                quality_checkpoint="Zero surface porosity or cold shut inclusions.",
                origin=ProvenanceOrigin.SYSTEM_DERIVED,
            )
        )
        step_num += 1

        # 3. Cleanup & Surface Filing
        steps.append(
            ProductionStepEstimate(
                step_number=step_num,
                stage_name="De-spruing & Metal Preparation",
                required_skill="polishing",
                required_machine_type="ultrasonic_cleaner",
                base_hours=0.75,
                per_unit_hours=0.35,
                description="Cut sprues, ultrasonic pickle wash, file seam lines, and pre-finish surfaces.",
                quality_checkpoint="Smooth clean surfaces conforming to blueprint tolerances.",
                origin=ProvenanceOrigin.SYSTEM_DERIVED,
            )
        )
        step_num += 1

        # 4. Assembly & Articulation (if category has multi-component assembly)
        if category in ("necklace", "bracelet", "earring", "bangle", "brooch"):
            stage_title = {
                "necklace": "Chain Link Assembly & Articulation",
                "bracelet": "Safety Clasp & Link Assembly",
                "earring": "Ear Post & Hinge Alignment",
                "bangle": "Hinge & Box Catch Assembly",
                "brooch": "Pin & Catch Mechanism Soldering",
            }.get(category, "Component Assembly")

            steps.append(
                ProductionStepEstimate(
                    step_number=step_num,
                    stage_name=stage_title,
                    required_skill="general",
                    required_machine_type="laser_engraver",
                    base_hours=1.25,
                    per_unit_hours=0.5,
                    description=f"Precision laser assemble and solder joint linkages for {category}.",
                    quality_checkpoint="Verify mechanical flexure, catch engagement, and joint strength.",
                    origin=ProvenanceOrigin.SYSTEM_DERIVED,
                )
            )
            step_num += 1

        # 5. Stone Setting (Only if gemstones are present!)
        if has_gemstones:
            steps.append(
                ProductionStepEstimate(
                    step_number=step_num,
                    stage_name="Precision Stone Setting",
                    required_skill="stone_setting",
                    required_machine_type=None,  # Benchwork handcraft
                    base_hours=1.5,
                    per_unit_hours=0.75,
                    description="Cut seats, bur collets, set gemstones securely, and finish prongs.",
                    quality_checkpoint="All stones tight under microscope; zero girdle chipping.",
                    origin=ProvenanceOrigin.SYSTEM_DERIVED,
                )
            )
            step_num += 1

        # 6. Pre-polish & Surface Lapping
        steps.append(
            ProductionStepEstimate(
                step_number=step_num,
                stage_name="Pre-polishing & Lapping",
                required_skill="polishing",
                required_machine_type="polishing_lathe",
                base_hours=0.75,
                per_unit_hours=0.4,
                description="Tripoli compounding and precision flat lapping.",
                quality_checkpoint="Crisp edges preserved without rounding.",
                origin=ProvenanceOrigin.SYSTEM_DERIVED,
            )
        )
        step_num += 1

        # 7. Electroplating (Only if plating required)
        if has_plating:
            steps.append(
                ProductionStepEstimate(
                    step_number=step_num,
                    stage_name="Electroplating & Surface Treatment",
                    required_skill="polishing",
                    required_machine_type="ultrasonic_cleaner",
                    base_hours=0.5,
                    per_unit_hours=0.25,
                    description="Ultrasonic electrocleaning followed by precious metal electroplating flash.",
                    quality_checkpoint="Uniform plating adhesion without discoloration.",
                    origin=ProvenanceOrigin.SYSTEM_DERIVED,
                )
            )
            step_num += 1

        # 8. Final Polish & Ultrasonic Cleaning
        steps.append(
            ProductionStepEstimate(
                step_number=step_num,
                stage_name="Final Rouge Polishing & Ultrasonic Wash",
                required_skill="polishing",
                required_machine_type="polishing_lathe",
                base_hours=0.5,
                per_unit_hours=0.3,
                description="High-luster rouge buffing followed by steam cleaning.",
                quality_checkpoint="Flawless mirror finish with zero residual buffing compound.",
                origin=ProvenanceOrigin.SYSTEM_DERIVED,
            )
        )
        step_num += 1

        # 9. Quality Assurance & Hallmarking
        steps.append(
            ProductionStepEstimate(
                step_number=step_num,
                stage_name="Quality Assurance & Assay Hallmarking",
                required_skill="general",
                required_machine_type="laser_engraver",
                base_hours=0.5,
                per_unit_hours=0.2,
                description="Inspection under 10x magnification, caliper verification, and legal alloy hallmarking.",
                quality_checkpoint="Formal QA signoff and karat hallmark verification.",
                origin=ProvenanceOrigin.SYSTEM_DERIVED,
            )
        )

        return steps

    # -----------------------------------------------------------------------
    # Enforcement & Sanity Validation
    # -----------------------------------------------------------------------

    def _enforce_user_intent_and_validate(
        self,
        ai_data: Dict[str, Any],
        input_data: ProductionIntelligenceInput,
    ) -> ProductionSpecificationAIResponse:
        """
        Validates Gemini output, enforces Tier-1 user intent locks,
        resolves conflicts with warnings, and prevents fake physical precision.
        """
        warnings = list(ai_data.get("warnings") or [])
        assumptions = list(ai_data.get("assumptions") or [])
        combined_text = f"{input_data.user_prompt or ''} {input_data.enhanced_prompt or ''} {input_data.material_hint or ''}"

        # 1. Authoritative Category Enforcement
        gemini_cat = ai_data.get("category", "").lower().replace(" ", "_")
        if gemini_cat != input_data.category:
            warnings.append(
                f"Visual analysis suggested category '{gemini_cat}'; authoritative design category "
                f"'{input_data.category}' was retained."
            )
        category = input_data.category

        # 2. Material Enforcement & Conflict Detection
        user_metal = self.extract_user_intent_metals(combined_text)
        materials_data = ai_data.get("materials") or []
        materials: List[ProductionMaterialEstimate] = []

        for m_dict in materials_data:
            m_type = m_dict.get("metal_type", "gold")
            purity = m_dict.get("metal_purity", "18k")
            color = m_dict.get("metal_color", "yellow")

            # Check for conflict with user requirement
            if user_metal:
                req_type, req_purity, req_color = user_metal
                if req_type != m_type or req_color != color:
                    warnings.append(
                        f"Material conflict detected: Gemini suggested '{m_type} {color}', "
                        f"but user intent requested '{req_type} {req_color}'. User requirement was preserved."
                    )
                    m_type = req_type
                    purity = req_purity
                    color = req_color

            wt = m_dict.get("estimated_weight_grams")
            if wt is not None:
                wt = max(0.1, round(float(wt), 2))

            loss = m_dict.get("casting_loss_percentage")
            if loss is not None:
                loss = max(0.0, round(float(loss), 1))

            materials.append(
                ProductionMaterialEstimate(
                    metal_type=m_type,
                    metal_purity=purity,
                    metal_color=color,
                    metal_finish=m_dict.get("metal_finish", "high_polish"),
                    plating=m_dict.get("plating"),
                    estimated_weight_grams=wt,
                    casting_loss_percentage=loss or 10.0,
                    origin=ProvenanceOrigin.AI_ESTIMATE,
                )
            )

        if not materials:
            # Fallback material
            if user_metal:
                m_type, purity, color = user_metal
            else:
                m_type, purity, color = ("gold", "18k", "yellow")
            materials.append(
                ProductionMaterialEstimate(
                    metal_type=m_type,
                    metal_purity=purity,
                    metal_color=color,
                    metal_finish="high_polish",
                    estimated_weight_grams=CATEGORY_BENCHMARKS.get(category, {}).get("net_wt", 5.0),
                    origin=ProvenanceOrigin.SYSTEM_DERIVED,
                )
            )

        # 3. Gemstone Enforcement & Conflict Detection
        user_stones = self.extract_user_intent_stones(combined_text)
        no_stones_requested = self.has_no_stone_requirement(combined_text)
        raw_gemstones = ai_data.get("gemstones") or []
        gemstones: List[ProductionGemstoneEstimate] = []

        if no_stones_requested:
            if raw_gemstones:
                warnings.append(
                    "Visual analysis detected potential gemstones, but user explicitly specified no gemstones. "
                    "Gemstones were removed from the manufacturing BOM."
                )
            gemstones = []
        else:
            for g_dict in raw_gemstones:
                g_type = g_dict.get("gemstone_type", "diamond").lower()

                # Detect gemstone conflict
                if user_stones and g_type not in user_stones:
                    expected_stone = user_stones[0]
                    warnings.append(
                        f"Gemstone conflict detected: Gemini suggested '{g_type}', "
                        f"but user intent requested '{expected_stone}'. User requirement was preserved."
                    )
                    g_type = expected_stone

                cnt = max(0, int(g_dict.get("stone_count", 1)))
                carat = g_dict.get("estimated_carat_weight")
                if carat is not None:
                    carat = max(0.0, round(float(carat), 3))

                gemstones.append(
                    ProductionGemstoneEstimate(
                        gemstone_type=g_type,
                        cut_shape=g_dict.get("cut_shape", "round"),
                        stone_count=cnt,
                        estimated_carat_weight=carat,
                        approximate_dimensions_mm=g_dict.get("approximate_dimensions_mm"),
                        setting_type=g_dict.get("setting_type", "prong"),
                        is_center_stone=bool(g_dict.get("is_center_stone", False)),
                        origin=ProvenanceOrigin.AI_ESTIMATE,
                    )
                )

            # If user explicitly requested stones but Gemini omitted them, restore them
            if user_stones and not gemstones:
                count_hint = self.extract_stone_count_hint(combined_text) or 1
                for idx, stone in enumerate(user_stones):
                    gemstones.append(
                        ProductionGemstoneEstimate(
                            gemstone_type=stone,
                            cut_shape="round",
                            stone_count=count_hint if idx == 0 else 1,
                            estimated_carat_weight=round(0.5 * count_hint, 2),
                            setting_type="prong",
                            is_center_stone=(idx == 0),
                            origin=ProvenanceOrigin.SYSTEM_DERIVED,
                        )
                    )

        # 4. Routing Validation
        raw_routing = ai_data.get("routing") or []
        routing: List[ProductionStepEstimate] = []
        has_gems = bool(gemstones)
        has_plat = any(m.plating and m.plating.lower() != "none" for m in materials)

        if not raw_routing:
            # Generate deterministic routing if AI returned empty routing
            routing = self._generate_routing_steps(category, has_gems, has_plat)
            warnings.append("Gemini provided empty routing; category-tailored manufacturing stages were generated.")
        else:
            step_idx = 1
            for r_dict in raw_routing:
                stage = r_dict.get("stage_name", f"Manufacturing Stage {step_idx}")
                # Omit Stone Setting if zero stones
                if not has_gems and any(k in stage.lower() for k in ("stone setting", "setting stones", "collet setting")):
                    continue

                b_hours = max(0.0, round(float(r_dict.get("base_hours", 1.0)), 2))
                u_hours = max(0.0, round(float(r_dict.get("per_unit_hours", 0.25)), 2))

                routing.append(
                    ProductionStepEstimate(
                        step_number=step_idx,
                        stage_name=stage,
                        required_skill=r_dict.get("required_skill", "general"),
                        required_machine_type=r_dict.get("required_machine_type"),
                        base_hours=b_hours,
                        per_unit_hours=u_hours,
                        description=r_dict.get("description"),
                        quality_checkpoint=r_dict.get("quality_checkpoint"),
                        origin=ProvenanceOrigin.AI_ESTIMATE,
                    )
                )
                step_idx += 1

            if not routing:
                routing = self._generate_routing_steps(category, has_gems, has_plat)

        # 5. Structure & Weight Sanity Checks
        struct_data = ai_data.get("structure") or {}
        structure = ProductionStructureObservation(
            component_breakdown=struct_data.get("component_breakdown", ["main_piece"]),
            estimated_dimensions=struct_data.get("estimated_dimensions"),
            minimum_thickness=struct_data.get("minimum_thickness", "1.4mm"),
            fabrication_notes=struct_data.get("fabrication_notes"),
            origin=ProvenanceOrigin.AI_ESTIMATE,
        )

        rough_wt = ai_data.get("estimated_rough_metal_weight_grams")
        if rough_wt is not None:
            rough_wt = max(0.1, round(float(rough_wt), 1))
        else:
            rough_wt = CATEGORY_BENCHMARKS.get(category, {}).get("rough_wt")

        net_wt = ai_data.get("estimated_finished_metal_weight_grams")
        if net_wt is not None:
            net_wt = max(0.1, round(float(net_wt), 1))
        else:
            net_wt = CATEGORY_BENCHMARKS.get(category, {}).get("net_wt")

        total_hours = ai_data.get("estimated_total_bench_hours")
        if total_hours is not None:
            total_hours = max(0.5, round(float(total_hours), 2))
        else:
            total_hours = round(sum(s.base_hours + s.per_unit_hours for s in routing), 2)

        conf = float(ai_data.get("ai_confidence_score", 0.85))
        conf = max(0.0, min(1.0, round(conf, 2)))

        comp = ai_data.get("complexity_rating", "moderate")
        if comp not in ("simple", "moderate", "intricate", "masterpiece"):
            comp = "moderate"

        return ProductionSpecificationAIResponse(
            design_id=input_data.design_id,
            render_id=input_data.render_id,
            category=category,
            specification_summary=ai_data.get(
                "specification_summary",
                f"Manufacturing blueprint for {category} with {len(materials)} material(s) and {len(gemstones)} stone type(s).",
            ),
            materials=materials,
            gemstones=gemstones,
            structure=structure,
            routing=routing,
            estimated_rough_metal_weight_grams=rough_wt,
            estimated_finished_metal_weight_grams=net_wt,
            estimated_total_bench_hours=total_hours,
            complexity_rating=comp,
            ai_confidence_score=conf,
            warnings=warnings,
            assumptions=assumptions,
            fallback_applied=False,
            provenance_summary={"engine": "Gemini 2.5 Flash Manufacturing Reasoner", "data_origin": "AI_ESTIMATE"},
        )

    # -----------------------------------------------------------------------
    # Main Service API
    # -----------------------------------------------------------------------

    async def analyze_production(
        self,
        input_data: ProductionIntelligenceInput,
    ) -> ProductionSpecificationAIResponse:
        """
        Analyzes an approved render and design context to produce a structured
        ProductionSpecificationAIResponse.
        Uses Gemini multimodal reasoning with robust fallback to deterministic atelier rules.
        """
        logger.info(
            "Analyzing production intelligence for design %s, render %s (category: %s)",
            input_data.design_id,
            input_data.render_id,
            input_data.category,
        )

        if not self.is_available():
            logger.info("Gemini API key not configured. Applying deterministic manufacturing engine.")
            return self._build_deterministic_production_spec(
                input_data, fallback_reason="Gemini API key is not configured"
            )

        # Resolve image bytes if provided as base64
        image_bytes = input_data.image_bytes
        if not image_bytes and input_data.image_base64:
            try:
                b64 = input_data.image_base64
                if "," in b64:
                    b64 = b64.split(",", 1)[1]
                image_bytes = base64.b64decode(b64)
            except Exception as b64_err:
                logger.warning("Failed to decode base64 image: %s", b64_err)

        prompt_text = self._build_manufacturing_prompt(input_data)

        try:
            raw_json = await self._call_gemini_manufacturing_api(
                prompt_text=prompt_text,
                image_bytes=image_bytes,
                image_mime_type=input_data.image_mime_type,
            )
            return self._enforce_user_intent_and_validate(raw_json, input_data)
        except Exception as exc:
            logger.warning("Gemini production reasoning call failed: %s. Engaging deterministic fallback.", exc)
            return self._build_deterministic_production_spec(
                input_data, fallback_reason=f"Gemini manufacturing analysis error ({str(exc)})"
            )


# ---------------------------------------------------------------------------
# Database Model Mapper Helper (Section 20)
# ---------------------------------------------------------------------------

def map_ai_response_to_production_specification(
    ai_response: ProductionSpecificationAIResponse,
    user_id: uuid.UUID,
    design_id: uuid.UUID,
    render_id: uuid.UUID,
    version_number: int = 1,
    status: str = "draft",
) -> ProductionSpecification:
    """
    Constructs an unpersisted Phase I.1 ProductionSpecification ORM model
    populated with child ProductionMaterial, ProductionGemstone, and ProductionStep records.
    Persistence is deferred to API routers or calling workflows (Phase I.3).
    """
    total_gems = sum(g.stone_count for g in ai_response.gemstones)

    spec = ProductionSpecification(
        id=uuid.uuid4(),
        user_id=user_id,
        design_id=design_id,
        render_id=render_id,
        version_number=version_number,
        status=status,
        category=ai_response.category,
        estimated_rough_metal_weight_grams=ai_response.estimated_rough_metal_weight_grams,
        estimated_finished_metal_weight_grams=ai_response.estimated_finished_metal_weight_grams,
        total_gemstone_count=total_gems,
        estimated_total_bench_hours=ai_response.estimated_total_bench_hours,
        complexity_rating=ai_response.complexity_rating,
        fabrication_notes=ai_response.structure.fabrication_notes,
        ai_confidence_score=ai_response.ai_confidence_score,
        approved_at=None,
    )

    # Attach Materials
    for m in ai_response.materials:
        mat_row = ProductionMaterial(
            id=uuid.uuid4(),
            specification_id=spec.id,
            metal_type=m.metal_type,
            metal_purity=m.metal_purity,
            metal_color=m.metal_color,
            metal_finish=m.metal_finish,
            plating=m.plating,
            estimated_weight_grams=m.estimated_weight_grams,
            casting_loss_percentage=m.casting_loss_percentage,
        )
        spec.materials.append(mat_row)

    # Attach Gemstones
    for g in ai_response.gemstones:
        gem_row = ProductionGemstone(
            id=uuid.uuid4(),
            specification_id=spec.id,
            gemstone_type=g.gemstone_type,
            cut_shape=g.cut_shape,
            stone_count=g.stone_count,
            estimated_carat_weight=g.estimated_carat_weight,
            approximate_dimensions_mm=g.approximate_dimensions_mm,
            setting_type=g.setting_type,
            is_center_stone=g.is_center_stone,
        )
        spec.gemstones.append(gem_row)

    # Attach Routing Steps
    for s in ai_response.routing:
        step_row = ProductionStep(
            id=uuid.uuid4(),
            specification_id=spec.id,
            step_number=s.step_number,
            stage_name=s.stage_name,
            required_skill=s.required_skill,
            required_machine_type=s.required_machine_type,
            base_hours=s.base_hours,
            per_unit_hours=s.per_unit_hours,
            description=s.description,
            quality_checkpoint=s.quality_checkpoint,
        )
        spec.steps.append(step_row)

    return spec


# Singleton instance helper
_gemini_production_service_instance: Optional[GeminiProductionService] = None


def get_gemini_production_service() -> GeminiProductionService:
    """Returns the singleton instance of GeminiProductionService."""
    global _gemini_production_service_instance
    if _gemini_production_service_instance is None:
        _gemini_production_service_instance = GeminiProductionService()
    return _gemini_production_service_instance
