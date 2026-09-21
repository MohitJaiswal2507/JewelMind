# Phase I.2 — AI Manufacturing Intelligence Service Implementation Report

**Project:** JewelMind  
**Branch:** `phase-i2-ai-manufacturing-intelligence`  
**Base:** `main` (with Phase I.1 merged)  
**Scope:** Backend AI Manufacturing-Intelligence Service Only  

---

## 1. Objective

Phase I.2 implements the dedicated backend AI manufacturing intelligence layer for JewelMind. It transforms an approved jewellery render and associated design parameters into an actionable, structured manufacturing blueprint (Production Specification).

The service evaluates:
1. Manufacturing material & Bill of Materials (BOM) estimates (metal type, alloy purity, color, finish, plating, rough/finished weights, casting loss factors).
2. Gemstone BOM (type, cut shape, stone count, carat weight estimate, approximate bracket dimensions, setting technique, center stone identification).
3. Structural and manufacturing atelier observations (component sub-assemblies, minimum wall thickness, fabrication guidelines).
4. Tailored manufacturing routing stages with sequential steps, primary artisan skill requirements, workshop machine requirements, setup/base hours, per-unit hours, and quality inspection checkpoints.
5. Overall estimated bench labor hours and manufacturing complexity classification (`simple`, `moderate`, `intricate`, `masterpiece`).
6. Fabrication caveats, geometric assumptions, and AI confidence scoring.
7. Explicit data origin tracking (`AI_ESTIMATE`, `SYSTEM_DERIVED`, `ARTISAN_OVERRIDE`, `BENCH_MEASURED`) to preserve integrity and avoid false precision.

---

## 2. Architecture

The AI manufacturing intelligence layer is implemented in a dedicated, decoupled service:
`backend/app/services/gemini_production_service.py`

It deliberately does NOT overload `gemini_design_service.py` (which is exclusively focused on aesthetic visual synthesis and image generation).

```
                 Approved DesignRender
                           │
    ┌──────────────────────┼──────────────────────┐
    ▼                      ▼                      ▼
Render Image      Design.category        Structured Visual State & Prompts
(bytes/base64)    (Authoritative)        (materials, gemstones, user text)
    │                      │                      │
    └──────────────────────┼──────────────────────┘
                           ▼
               GeminiProductionService
                           │
             ┌─────────────┴─────────────┐
             ▼                           ▼
       Gemini Available?         Gemini Unavailable / Error?
      (Gemini 2.5 Flash)         (Deterministic Fallback)
             │                           │
             │                           ▼
             │               Category Benchmarks & Rules
             │               - Metal/gemstone detection
             │               - Tailored routing stages
             │               - fallback_applied = True
             │                           │
             └─────────────┬─────────────┘
                           ▼
          User Intent Precedence Enforcement & Sanity Validation
             - Lock authoritative Design.category
             - Enforce user metals and gemstones
             - Strip gemstones if "no gemstones" requested
             - Tailor routing: omit stone setting if no gems, add plating
             - Round sensibly; prevent fake precision
                           ▼
           ProductionSpecificationAIResponse
                           │
                           ▼ (Optional / In-Memory)
     map_ai_response_to_production_specification()
                           ▼
             Phase I.1 Database ORM Models
   (ProductionSpecification, Materials, Gemstones, Steps)
```

---

## 3. Input Schema

Defined in `backend/app/schemas/production_intelligence.py` via `ProductionIntelligenceInput`:

```python
class ProductionIntelligenceInput(BaseModel):
    design_id: uuid.UUID
    render_id: uuid.UUID
    category: str
    image_url: Optional[str] = None
    image_bytes: Optional[bytes] = None
    image_base64: Optional[str] = None
    image_mime_type: str = "image/png"
    structured_state: Optional[Dict[str, Any]] = None
    user_prompt: Optional[str] = None
    enhanced_prompt: Optional[str] = None
    material_hint: Optional[str] = None
    gemstone_hint: Optional[str] = None
```

- **Category Normalization:** Automatically standardizes input categories into one of the 8 canonical categories (`ring`, `earring`, `pendant`, `necklace`, `bracelet`, `bangle`, `brooch`, `other_jewellery`).
- **No Fabricated CAD Metrics:** Only consumes data actually present in JewelMind; does not invent unavailable CAD solids.

---

## 4. Output Schema

Defined in `backend/app/schemas/production_intelligence.py` via `ProductionSpecificationAIResponse` and sub-models:

- `ProductionMaterialEstimate`: Metal alloy, purity, color, finish, plating, estimated net weight in grams, casting loss %, origin.
- `ProductionGemstoneEstimate`: Gemstone species, cut shape, stone count, carat weight, approximate dimensions, setting technique, center stone flag, origin.
- `ProductionStructureObservation`: Component breakdown, nominal sizing dimensions, minimum wall thickness, atelier fabrication notes, origin.
- `ProductionStepEstimate`: Sequential step number, stage name, required artisan skill, required machine equipment, base hours, per-unit hours, step description, quality checkpoint, origin.
- `ProductionSpecificationAIResponse`: Top-level composite schema including summary, totals, complexity rating, confidence score, warnings array, assumptions array, fallback flag, and provenance summary.

---

## 5. Gemini Integration

- **Infrastructure Reuse:** Reuses existing `settings.GEMINI_API_KEY`, `settings.GEMINI_MODEL`, and `settings.GEMINI_REQUEST_TIMEOUT`. No secondary API key or redundant configuration was introduced.
- **Server-Side Security:** Calls are executed via asynchronous `httpx.AsyncClient` exclusively on the backend. No credentials or keys are exposed to the client or frontend.
- **Structured JSON Mode:** Leverages `response_mime_type: "application/json"` with low temperature (`0.1`) to ensure deterministic, structured engineering reasoning.
- **Multimodal Visual Input:** Sends base64-encoded approved render visual alongside technical manufacturing mandates.

---

## 6. Manufacturing Prompt Strategy

The system prompt instructs Gemini as JewelMind's Lead Master Goldsmith & Manufacturing Director:
1. Mandates that the assistant is planning physical atelier fabrication, NOT redesigning the jewellery.
2. Instructs Gemini to preserve the authoritative category and user-specified metals/gemstones without silent substitution.
3. Explicitly instructs the model that 2D renders cannot yield caliper-level exactness; forces sensible rounding (1-2 decimal places) and caveats.
4. Requests tailored manufacturing stages that reflect specific construction methods (e.g. assembly for hinged earrings or multi-link necklaces, stone setting only when stones exist).

---

## 7. User-Intent Precedence

JewelMind's prompt-fidelity hierarchy is strictly enforced:
1. **Explicit User Requirement** (e.g., prompt specifying "18k yellow gold emerald pendant with 7 emerald stones").
2. **Approved Structured Design State** (from `DesignRender.structured_state`).
3. **Verified Design Category** (`Design.category`). If Gemini visual analysis disagrees, the authoritative category is preserved and a warning is logged:
   `"Visual analysis suggested category '...'; authoritative design category '...' was retained."`
4. **Gemini Visual Observation.**
5. **Conservative Atelier Defaults.**

Conflicts are automatically resolved in favor of user requirements, with conflict warnings attached:
- Gemstone conflicts (e.g. user requested emerald, AI suggested diamond) -> Preserves emerald + adds warning.
- Material conflicts (e.g. user requested platinum, AI suggested yellow gold) -> Preserves platinum + adds warning.
- Zero-gemstone requirements (e.g. user requested "plain gold band with no stones", but AI detected stones) -> Empties gemstone BOM, omits Stone Setting stage, and adds warning.

---

## 8. Fallback Strategy

The service is fully resilient against network partitions, API outages, timeouts, and quota limits:
- If `settings.GEMINI_API_KEY` is not set or empty: gracefully executes `_build_deterministic_production_spec()`.
- If Gemini API returns HTTP non-200 or connection errors: catches exception and executes fallback without throwing.
- If Gemini returns malformed or invalid JSON: catches parsing error and executes fallback.
- In all fallback cases:
  - `fallback_applied = True`
  - Warning is added: `"Gemini manufacturing analysis unavailable; deterministic domain rules were applied."`
  - Provenance is marked `SYSTEM_DERIVED`.

---

## 9. Routing Logic

Manufacturing routing is category-aware and conditionally generated:
- **All Categories:**
  - Stage 1: `CAD & 3D Wax Pattern Printing` (`cad_design`, `3d_wax_printer`)
  - Stage 2: `Investment Casting & Spruing` (`casting`, `casting_furnace`)
  - Stage 3: `De-spruing & Metal Preparation` (`polishing`, `ultrasonic_cleaner`)
- **Assembly Stages (Category-Specific):**
  - `necklace` -> `Chain Link Assembly & Articulation`
  - `bracelet` -> `Safety Clasp & Link Assembly`
  - `earring` -> `Ear Post & Hinge Alignment`
  - `bangle` -> `Hinge & Box Catch Assembly`
  - `brooch` -> `Pin & Catch Mechanism Soldering`
- **Conditional Stone Setting:**
  - Only generated if gemstones are present (`stone_setting`, handcraft benchwork). Omitted entirely for plain pieces.
- **Conditional Electroplating:**
  - Only generated if plating is required (e.g. rhodium flash for white gold, gold vermeil, silver).
- **Finishing & Quality Assurance:**
  - `Pre-polishing & Lapping`
  - `Final Rouge Polishing & Ultrasonic Wash`
  - `Quality Assurance & Assay Hallmarking` (`general`, `laser_engraver`)

---

## 10. Validation & Sanity Checks

Pydantic validators and service-level rules enforce:
- Non-negative metal weights (`estimated_weight_grams >= 0.0`).
- Non-negative casting loss percentages (`casting_loss_percentage >= 0.0`).
- Non-negative gemstone counts and carats (`stone_count >= 0`, `estimated_carat_weight >= 0.0`).
- Positive step numbers (`step_number > 0`).
- Non-negative base and per-unit hours (`base_hours >= 0.0`, `per_unit_hours >= 0.0`).
- Strict confidence rating bounding (`0.0 <= ai_confidence_score <= 1.0`).
- Non-empty routing (if AI routing is empty, fallback routing is automatically populated with a warning).
- Automatic roundings to 2 decimals for weights and bench hours to eliminate fake floating-point precision.

---

## 11. Provenance Strategy

Every manufacturing estimate carries an explicit provenance tag:
- `AI_ESTIMATE`: Values inferred by the Gemini multimodal manufacturing reasoning engine.
- `SYSTEM_DERIVED`: Values calculated from category benchmark tables, heuristic alloy densities, or deterministic fallback rules.
- `ARTISAN_OVERRIDE` & `BENCH_MEASURED`: Reserved for bench artisans and shopfloor calibration in subsequent phases; never fabricated or simulated by the AI service.

---

## 12. Database Mapping

A dedicated helper function `map_ai_response_to_production_specification` maps the in-memory `ProductionSpecificationAIResponse` into the Phase I.1 SQLAlchemy ORM models:
- Creates `ProductionSpecification` record with totals, summary, and complexity.
- Attaches children: `ProductionMaterial`, `ProductionGemstone`, `ProductionStep`.
- **Zero Automatic Persistence:** As mandated, this phase does not commit or persist to the database directly; persistence behavior is deferred to Phase I.3 endpoints.
- Integration tests verify that the mapped ORM instance commits cleanly to the SQLite test session with all relationships and foreign keys intact.

---

## 13. Test Results

The new dedicated test suite `backend/tests/test_gemini_production_service.py` executes 27 comprehensive unit and integration tests:

| Test Name | Description | Status |
| :--- | :--- | :---: |
| `test_01_valid_gemini_production_response` | Valid Gemini API parsing and schema instantiation | PASSED |
| `test_02_strict_schema_validation` | Pydantic model validation and invalid origin rejection | PASSED |
| `test_03_user_material_preserved` | User platinum requirement overrides AI yellow gold suggestion | PASSED |
| `test_04_user_gemstone_preserved` | User emerald requirement overrides AI diamond suggestion | PASSED |
| `test_05_user_category_preserved` | Authoritative earring category retained over visual pendant guess | PASSED |
| `test_06_category_conflict_warning` | Warning emitted when visual category differs from authoritative | PASSED |
| `test_07_material_conflict_warning` | Warning emitted when metal alloy conflict is corrected | PASSED |
| `test_08_gemstone_conflict_warning` | Warning emitted when gemstone conflict is corrected | PASSED |
| `test_09_no_gemstone_routing` | Plain band eliminates gemstones and omits Stone Setting stage | PASSED |
| `test_10_gemstone_routing` | Gemstone design incorporates Stone Setting stage | PASSED |
| `test_11_plating_routing` | Rhodium plating requirement generates electroplating stage | PASSED |
| `test_12_fallback_when_api_key_unavailable` | Deterministic fallback operates when API key is missing | PASSED |
| `test_13_fallback_when_gemini_request_fails` | Deterministic fallback operates on network/HTTP exception | PASSED |
| `test_14_fallback_when_gemini_json_is_malformed` | Deterministic fallback operates on malformed JSON payload | PASSED |
| `test_15_invalid_negative_weight_rejected` | Negative metal weight raises ValidationError | PASSED |
| `test_16_invalid_negative_hours_rejected` | Negative bench hours raises ValidationError | PASSED |
| `test_17_confidence_validation` | Confidence outside [0, 1] raises ValidationError | PASSED |
| `test_18_empty_routing_rejected` | Empty AI routing rejected and replaced with tailored routing | PASSED |
| `test_19_production_response_to_db_model_mapping` | Schema cleanly maps to Phase I.1 ORM object graph | PASSED |
| `test_20_provenance_labels` | AI_ESTIMATE provenance tags verified on all line items | PASSED |
| `test_21_sensible_precision_and_rounding` | Rounding to 2 decimal places verified; no fake 7-digit floats | PASSED |
| `test_22_all_eight_jewellery_categories` | All 8 categories tested for valid BOM and tailored routing | PASSED |
| `test_case_a_emerald_pendant_with_7_stones` | Case A: 18k yellow gold emerald pendant with 7 stones verified | PASSED |
| `test_case_b_platinum_ring_one_diamond` | Case B: Platinum ring with 1 round brilliant diamond verified | PASSED |
| `test_case_c_silver_bracelet_no_gemstones` | Case C: Silver bracelet with no gemstones and assembly verified | PASSED |
| `test_case_d_rose_gold_necklace_rhodium_plating` | Case D: Rose gold necklace with rhodium plating stage verified | PASSED |
| `test_23_db_session_integration` | Mapped ORM entity persists to database fixture with FKs & cascades | PASSED |

**Test Suite Summary:** `27 passed in 0.39s` (100% success).

---

## 14. Regression Results

- **Backend Regression Suite:**
  - Before Phase I.2: 217 tests passing.
  - After Phase I.2: **244 tests passing** (217 existing + 27 new Phase I.2 tests, 0 failures).
- **Frontend Regression Suite:**
  - Ran `npm test -- --run` across 6 test suites: **62 passed (62)**.
  - Zero regressions across the entire application stack.

---

## 15. Security Considerations

- `settings.GEMINI_API_KEY` is loaded exclusively from backend environment configurations and is never returned in API models or exposed to frontend code.
- No sensitive user prompt data or raw image binary payloads are written to standard logs.
- Safe, sanitized error messages are emitted upon Gemini connection failures.

---

## 16. Performance Considerations

- **On-Demand Only:** The service executes strictly when explicitly invoked; it does NOT run during normal render preview generation or Studio page loads.
- **Low-Latency Deterministic Fallback:** In the absence of an API key or upon network failure, the deterministic engine generates full production specifications in under 2ms.
- **Asynchronous Execution:** Multimodal API calls utilize asynchronous HTTP requests with configurable timeouts to prevent blocking event loops.

---

## 17. Files Changed / Created

### New Files Created:
1. `backend/app/schemas/production_intelligence.py` — Pydantic models for input, BOM estimates, routing steps, structure observations, provenance, and output schemas.
2. `backend/app/services/gemini_production_service.py` — Core AI manufacturing intelligence service with prompt builder, Gemini caller, deterministic fallback engine, intent locks, and ORM mapper.
3. `backend/tests/test_gemini_production_service.py` — Comprehensive unit and integration test suite covering 27 test scenarios.
4. `docs/PHASE_I_2_IMPLEMENTATION_REPORT.md` — Complete Phase I.2 architectural and implementation report.

### Modified Files:
- None. (Zero existing files modified).

---

## 18. Systems Explicitly Untouched

In strict adherence to Phase I.2 boundaries:
- **No Production Specification UI** or Studio UI modifications.
- **No REST API Endpoints created** (`POST /production-specifications/generate`, etc. belong to Phase I.3).
- **No Database Persistence** executed automatically in workflows.
- **No CP-SAT Optimizer Changes** (`production_optimization_service.py` and `OPERATION_DEFS` untouched; Phase I.5).
- **No Frontend Changes** (no files under `frontend/` modified).
- **No AI Model Weights or GPU Training** (no changes to YOLO weights, ControlNet, SD1.5, RealVisXL, or LoRA scripts).
- **No Git Commits or Pushes** made.

---

## 19. Known Limitations

1. **2D Visual Scale Approximation:** Because input visual references are 2D renders rather than full 3D CAD B-reps, estimated metal weights and dimensions are planning approximations (`AI_ESTIMATE`), which must be verified at the bench before casting.
2. **Shopfloor Overrides:** Bench calibration and manual artisan overrides will be enabled once the Phase I.3/I.4 editing UI and persistence APIs are delivered.

---

## 20. Final Status

Phase I.2 is **COMPLETE and FULLY VERIFIED**.
All acceptance criteria are satisfied, test suites are green (244 backend / 62 frontend), and the service is ready for consumption by Phase I.3 API endpoints.
