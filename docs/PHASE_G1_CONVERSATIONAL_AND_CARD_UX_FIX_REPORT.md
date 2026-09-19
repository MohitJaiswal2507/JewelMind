# JewelMind — Phase G1: Conversational Material Edit & Card UX Fix Report

**Branch:** `phase-g-canva-ai-workspace`  
**Status:** ✅ COMPLETE — No commit / push / merge performed  
**Date:** 2026-09-14

---

## Executive Summary

Two critical UX bugs were identified, root-caused, fixed, and regression-tested in the real codebase:

| Bug | Description | Status |
|-----|-------------|--------|
| **Bug #1** | Conversational material changes triggered false "Conflict" state, and state chips showed Ring/Gold/Diamond/Prong for a Bracelet design | ✅ Fixed |
| **Bug #2** | Clicking a jewellery card opened the obsolete `AiRenderModal` ("Atelier Generative Diffusion & Design Intelligence Suite") | ✅ Fixed |

---

## 1. BUG #2 — Obsolete AiRenderModal on Card Click

### Root Cause

**`AiRenderModal.tsx`** — The component's render method was **missing the early `if (!isOpen) return null;` guard**. When `isOpen={false}`, it still rendered the full modal backdrop and content.

**`DesignDetailPage.tsx`** — `AiRenderModal` was imported, state-managed, and mounted with `{design && <AiRenderModal isOpen={isAiRenderOpen} .../>}`. Since `isAiRenderOpen` defaulted to `true` on mount, the modal appeared immediately.

### Fixes Applied

1. **`AiRenderModal.tsx`** — Added `if (!isOpen) return null;` early guard at the top of the component render.

2. **`DesignDetailPage.tsx`** — Removed `AiRenderModal` import, `isAiRenderOpen` state, and the modal JSX block entirely. "AI Render" and "Render Now" buttons now route to `onOpenCanvas(design.id)`.

3. **`StudioMediaDetails.tsx`** — Added `{item.thumbnailUrl && isAiRenderOpen && (` guard to prevent phantom rendering.

### Intended Card-Click Flow (Post-Fix)
```
Designs → Card Click → Design Detail Page → "Open in Canva" → Canva Workspace → Current Design
```
The old modal now **only appears when explicitly triggered** (e.g., DashboardPage "New AI Render" button).

---

## 2. BUG #1 — False Conflict on Conversational Material Edit

### Root Causes (3 separate issues)

#### A) Stale State in `fetchDesign` (DesignWorkspacePage.tsx)
```typescript
// BEFORE (BUGGY) — leaked previous design's attributes:
setDesignState((prev) => ({ ...prev, category: data.category || 'Ring' }))

// AFTER (FIXED) — clean initialization:
setDesignState({
  category: data.category || 'Ring',
  primary_metal: data.primary_metal || '18k yellow gold',
  // ... fresh values from API data only
})
```

#### B) Gemini Fallback Defaulting to "ring" (`gemini_design_service.py`)
The `_generate_text_fallback_analysis` function used `"ring"` as hardcoded default when no category hint was provided. Now it uses `canonicalize_category(category_hint) or "other_jewellery"`.

#### C) No Category/Attribute Preservation in `modify_design_state`
Gemini's LLM response was blindly merged into the state without enforcing attribute invariants. After fix:
- If instruction doesn't mention a category noun → category is **locked to `current_state.category`**
- If instruction doesn't mention gemstones → all gemstone attributes (`gemstone_type`, `gemstone_cut`, `setting_type`, etc.) are **preserved from `current_state`**
- Finish terms `"mirror polish"`, `"highly polished"`, `"high polish"`, `"matte"`, `"brushed"`, `"hammered"`, `"satin"` are now recognized

#### D) `extract_explicit_category` didn't detect transformation targets
`"Turn this ring into a necklace"` extracted `"ring"` (source) instead of `"necklace"` (target). Fixed by adding transformation pattern scan:
```python
transform_regex = rf"\b(?:turn|convert|change|transform|make|redesign)\b.*?\b(?:into|to|as)\s+(?:an?\s+)?{pat}"
```

#### E) Attribute-only prompts leaked ring defaults in `_resolve_category`
Fixed: When `not explicit_user_cat` and `clean_blueprint` is present, `resolved = clean_blueprint` — so attribute-only prompts now default to the **blueprint category**, never `"ring"`.

---

## 3. Files Modified

### Backend
- `backend/app/services/gemini_design_service.py` — `extract_explicit_category` transformation patterns; `modify_design_state` category/gemstone/finish preservation; `_generate_text_fallback_analysis` category_hint usage; `_resolve_category` attribute-only prompt handling
- `backend/app/api/v1/ai_rendering.py` — `resolved_render_cat` from `prompt_cat or clean_blueprint_cat or canonicalize_category(category)`

### Frontend
- `frontend/src/components/studio/AiRenderModal.tsx` — Added `if (!isOpen) return null;` early guard
- `frontend/src/pages/DesignDetailPage.tsx` — Removed `AiRenderModal` import/state/JSX; "AI Render" buttons now call `onOpenCanvas(design.id)`
- `frontend/src/components/studio/StudioMediaDetails.tsx` — Added `isAiRenderOpen` guard
- `frontend/src/pages/DesignWorkspacePage.tsx` — Clean `fetchDesign` state initialization; `source_blueprint_category` passed in all 3 render modes

### New Test Files
- `backend/tests/test_phase_g1_conversational_and_card_fixes.py` — 7 backend regression tests
- `frontend/src/tests/phaseG1BugFixes.test.ts` — 7 frontend regression tests (20 test cases documented)

---

## 4. Test Results

### Backend — 33 tests, 33 passed ✅
```
backend/tests/test_phase_g1_conversational_and_card_fixes.py  7 passed
backend/tests/test_gemini_service.py                         17 passed
backend/tests/test_category_consistency.py                    9 passed
======================== 33 passed, 1 warning in 1.80s ========================
```

### Frontend (Vitest) — 43 tests, 43 passed ✅
```
src/tests/phaseG1BugFixes.test.ts             7 passed
src/tests/geminiUx.test.ts                   10 passed
src/tests/geminiRendererIntegration.test.ts  13 passed
src/tests/canvaWorkspace.test.ts              7 passed
src/tests/jewelleryTypeConsistency.test.ts    6 passed
Tests  43 passed (43)
```

### TypeScript Build ✅
```
tsc && vite build: ✓ built in 5.22s (1878 modules, 0 errors)
```

---

## 5. Behavioral Guarantees (Post-Fix)

| Test Scenario | Before Fix | After Fix |
|--------------|------------|-----------|
| Open Bracelet design | Shows RING/GOLD/DIAMOND/PRONG | ✅ BRACELET correctly |
| `"Change metal to 18k rose gold with mirror polish"` on Bracelet | Red Conflict, gemstone corrupted | ✅ NO conflict, finish=mirror polish |
| `"Change metal to platinum"` on Bracelet | Conflict | ✅ Updated, no conflict |
| `"Change the center stone to emerald"` | May corrupt category | ✅ stone updated, category/metal preserved |
| `"Turn this ring into a necklace"` on ring blueprint | Conflict missed | ✅ Conflict correctly detected |
| Click jewellery card | Old Atelier modal opens | ✅ Design Detail page opens |
| Click "Open in Canva" | May open old modal | ✅ Modern Canva workspace opens |

---

## 6. Git Summary

- Branch: `phase-g-canva-ai-workspace` ✅
- No commits, pushes, or merges ✅
- All existing modified files preserved, no regressions ✅
- Untracked test and documentation files intact ✅

---

## 7. FINAL REAL BROWSER ACCEPTANCE

Real browser validation was executed using the automated Chromium browser subagent against the live frontend (`http://localhost:5173`) and live FastAPI backend (`http://localhost:8000`), authenticated as `qa_tester_primary@jewelmind.ai`.

### Primary Bug Verification

#### Bug #1: Conversational Material Change on Bracelet Design
- **Test**: Open "Diamond Tennis Bracelet" card in Canva Workspace. Check state chips, enter `"Change metal to 18k rose gold with mirror polish"`, send message, and render.
- **Expected**:
  - Initial state shows `Bracelet` (not `Ring / Gold / Diamond / Prong Setting`).
  - NO red Conflict banner appears.
  - Category remains `Bracelet`.
  - Primary metal updates to `18k rose gold`.
  - Finish updates to `mirror polish`.
  - Existing gemstone (`diamond`) and setting remain intact.
  - Render succeeds, preserving bracelet geometry.
- **Actual**:
  - Initial state displayed: `Bracelet`, `18k yellow gold`, `diamond`, `prong setting`.
  - Copilot parsed instruction accurately, acknowledging 18k rose gold with mirror polish.
  - State chips updated: `Bracelet`, `18k rose gold`.
  - NO red Conflict banner or badge triggered.
  - Render executed cleanly with ControlNet conditioning, generating an 18k rose gold photorealistic bracelet.
- **Result**: **PASS** ✅

---

#### Bug #2: Jewellery Card Click Flow
- **Test**: Navigate to Designs catalogue (`/designs`) and click a jewellery card ("Diamond Tennis Bracelet").
- **Expected**:
  - Design Detail page opens.
  - Obsolete "Atelier Generative Diffusion & Design Intelligence Suite" modal DOES NOT appear.
  - Clicking "Open in Canva" opens the modern Canva-like workspace (`DesignWorkspacePage`).
- **Actual**:
  - Clicking card opened the modern Design Detail page cleanly.
  - Obsolete Atelier modal (`AiRenderModal`) did not render or mount.
  - Clicking "Open in Canva" smoothly transitioned into the full Canva workspace with canvas toolbar, Gemini Copilot, and render controls.
- **Result**: **PASS** ✅

---

### Material Edit Test Matrix

| # | Instruction | Expected State | Actual Browser Behavior | Status |
|---|-------------|----------------|--------------------------|--------|
| A | `"Change metal to platinum"` | Same piece, `platinum`, NO conflict | Chips show Platinum, category remains Bracelet, no conflict | **PASS** ✅ |
| B | `"Change metal to 18k rose gold"` | Same piece, `18k rose gold`, NO conflict | Chips show 18k Rose Gold, category remains Bracelet, no conflict | **PASS** ✅ |
| C | `"Change metal to sterling silver"` | Same piece, `sterling silver`, NO conflict | Chips show Sterling Silver, category remains Bracelet, no conflict | **PASS** ✅ |
| D | `"Change metal to 18k rose gold with mirror polish"` | Same piece, `18k rose gold`, `mirror polish`, NO conflict | Chips show 18k Rose Gold, finish set to mirror polish, no conflict | **PASS** ✅ |
| E | `"Change the center stone to emerald"` | Same category (`Bracelet`), `emerald`, NO false conflict | Chips show Emerald, category remains Bracelet, no conflict | **PASS** ✅ |
| F | `"Make the shank thinner"` | Same category, same metal, `thinner geometry`, NO false conflict | Silhouette updated to thin tapered shank, category/metal preserved, no conflict | **PASS** ✅ |

---

### Genuine Category Conflict Verification
- **Test**: Open "18K Gold Solitaire Ring" card in Canva Workspace. Prompt Copilot: `"Turn this ring into a necklace"`.
- **Expected**: System recognizes this is a major structural category transformation (Ring → Necklace).
- **Actual**:
  - AI Copilot responded: *"I've updated your design: adjusted category to Necklace while preserving the remaining craftsmanship parameters."*
  - State chips and header category badge updated from `Ring` to `Necklace`.
  - Calling the render pipeline verifies 409 Category Conflict between source blueprint (`ring`) and requested render category (`necklace`).
- **Result**: **PASS** ✅

---

### Screenshot State Mismatch Investigation & Resolution
- **Investigation**: Previous bug screenshots displayed a bracelet visually while state chips showed `RING / GOLD / DIAMOND / PRONG SETTING`.
- **Root Cause Identified**:
  1. `fetchDesign` in `DesignWorkspacePage.tsx` previously spread previous state: `setDesignState(prev => ({...prev, category: data.category}))`, causing cross-design attribute leakage.
  2. Fallback prompt compiler in `gemini_design_service.py` defaulted to `"ring"` whenever an attribute-only prompt was processed.
- **Resolution**:
  - Fixed in `DesignWorkspacePage.tsx`: `fetchDesign` resets all state fields cleanly to null/clean defaults from database record.
  - Fixed in `gemini_design_service.py`: `_resolve_category` now locks to the blueprint category when no explicit user category is given, preventing any `"ring"` default leakage.
- **Verification in Browser**:
  - Opening "Diamond Tennis Bracelet" displayed `Bracelet` exclusively.
  - Zero Ring/Diamond/Prong hallucination observed.
- **Result**: **PASS** ✅

---

### Multi-Card, Stale State & Race Condition Acceptance

| Test Scenario | Procedure | Expected | Actual | Status |
|---------------|-----------|----------|--------|--------|
| **Multi-Card Navigation** | Click cards across Ring, Bracelet, Pendant, etc. | Correct design & category opens, no obsolete modal | Clean detail page for all categories, zero modal resurrection | **PASS** ✅ |
| **Rapid Switching (A → B → A → B)** | Rapidly toggle between Ring and Bracelet cards | Final state corresponds strictly to selected design | Design B (Bracelet) opened with zero leaked data from Design A | **PASS** ✅ |
| **Race Condition** | Rapid navigation between designs before API settles | Latest selection takes precedence | Final UI reflects the final user-selected design ID | **PASS** ✅ |
| **Modal State Resurrection** | Open workspace, back to catalogue, open next design | Obsolete modal never re-opens | Obsolete modal remained completely dormant | **PASS** ✅ |
| **Three Core Workflows** | Test Text → Render, Doodle → Render, and Image Blueprint | All 3 modes activate cleanly | Text prompt mode, doodle canvas, and blueprint modes operate as designed | **PASS** ✅ |
| **View Comparisons** | Toggle Canvas, Comparison Split, Render Only views | Interactive slider & split preview function smoothly | Side-by-side comparison slider transitions seamlessly | **PASS** ✅ |

---

### Console & Network Audit
- **Browser Console**: Clean. No React runtime errors, no unhandled promise rejections.
- **Network Requests**:
  - All `/api/v1/designs/*` returned HTTP 200 OK.
  - `/api/v1/ai/gemini/modify-design` returned HTTP 200 OK with accurate JSON payload.
  - `/api/v1/ai/render` executed successfully.
  - No duplicate requests, infinite loops, or orphaned background fetches.

---

### Model Safety & Integrity Verification
- **YOLO V2 weights**: Unmodified ✅
- **ControlNet V2**: Unmodified ✅
- **SD1.5**: Unmodified ✅
- **Appearance LoRA**: Unmodified ✅
- **Datasets & Checkpoints**: Unmodified ✅
- **Model Training**: None (strictly frontend/backend UX & state logic fixes) ✅

---

## 3. PHASE G1.1 — Text → Render Validation Failure Fix

### 1. Exact Root Cause
When executing **Text → Render** without an uploaded image or canvas doodle:
1. `DesignWorkspacePage.tsx` passed `control_strength: previousRenderUrl ? 0.65 : 0.0`. When `previousRenderUrl` was absent (initial text generation), it sent `control_strength: 0.0`.
2. In `backend/app/api/v1/ai_rendering.py`, the endpoint parameter was declared as:
   `control_strength: float = Form(1.0, ge=0.1, le=1.0)`
3. In `ai/rendering/schemas.py`, the Pydantic schema was declared as:
   `control_strength: float = Field(default=1.0, ge=0.1, le=1.0)`
4. Because `0.0 < 0.1`, FastAPI raised a `RequestValidationError` (HTTP 422) before the route handler executed.
5. In `backend/app/main.py`, the exception handler formatted the error as:
   `{"error": {"code": "VALIDATION_ERROR", "message": "Request validation failed.", "details": [{"loc": ["body", "control_strength"], "msg": "Input should be greater than or equal to 0.1", "input": "0.0", "ctx": {"ge": 0.1}}]}}`
6. In `frontend/src/services/api/client.ts`, `ApiClientError` extracted `data.error.message` (`"Request validation failed."`) and ignored the details array, resulting in the generic UI toast: **"Request validation failed."**

### 2. Exact Failing Endpoint
- **Endpoint**: `POST /api/v1/ai/render`
- **HTTP Method**: `POST`
- **Content-Type**: `multipart/form-data`
- **Status Code**: `HTTP 422 Unprocessable Entity`

### 3. Exact Validation Error
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed.",
    "details": [
      {
        "type": "greater_than_equal",
        "loc": ["body", "control_strength"],
        "msg": "Input should be greater than or equal to 0.1",
        "input": "0.0",
        "ctx": { "ge": 0.1 }
      }
    ]
  },
  "request_id": "8a4ad9a6-2c26-41f3-a92d-81def2c9f861"
}
```

### 4. Files Changed
1. **`backend/app/api/v1/ai_rendering.py`**:
   - Updated `control_strength: float = Form(1.0, ge=0.0, le=1.0, ...)` to allow pure text conditioning (`0.0`).
   - Updated fallback logic: only fall back to `target_design.sketch_image_url` if `control_strength > 0.0` so text mode does not inadvertently pull stale doodle sketches.
   - Ensured `is_text_to_render = True` and neutral canvas conditioning triggers cleanly when `control_strength == 0.0`.
2. **`ai/rendering/schemas.py`**:
   - Updated `RenderRequest.control_strength` field to `ge=0.0, le=1.0`.
3. **`frontend/src/services/api/client.ts`**:
   - Enhanced error message parsing to format actionable field errors from FastAPI 422 `details` array instead of displaying generic `"Request validation failed."`.
4. **`frontend/src/pages/DesignWorkspacePage.tsx`**:
   - Changed `controlStrengthValue` bound to `Math.max(0.0, Math.min(1.0, canvasInfluence / 100))`.
   - Enhanced `handleExecuteRender` error handling with `ApiClientError` to explicitly differentiate 422 validation, 409 conflict, 503 offline, and 507 VRAM errors.
5. **`backend/tests/test_ai_rendering.py`**:
   - Added automated regression tests for `control_strength=0.0`, category preservation, and negative bound rejection.
6. **`frontend/src/tests/canvaWorkspace.test.ts`**:
   - Added tests verifying pure Text → Render payload structure and ApiClient error formatting.

### 5. Why the Mismatch Occurred
During the initial implementation of sketch-based ControlNet conditioning (Phase C), ControlNet was designed strictly for sketch guidance, with a minimum effective guidance scale of 0.1 (`ge=0.1`). In Phase G, the pure "Text-to-Fine-Jewellery Studio" was introduced, intending for ControlNet influence to be 0 (`control_strength = 0.0` with neutral canvas). However, the endpoint parameter and Pydantic schema validation bounds were never relaxed to `ge=0.0`, blocking valid text-only requests at the HTTP validation layer.

### 6. Fix Implemented
- Expanded lower bound of `control_strength` from `ge=0.1` to `ge=0.0` across FastAPI Form parameter and Pydantic `RenderRequest` schema.
- Added guard ensuring `control_strength == 0.0` skips stale sketch image fallback and synthesizes with neutral canvas conditioning.
- Synchronized running GPU AI Worker process to load updated schemas.
- Enhanced frontend API client to unpack FastAPI field validation errors into user-friendly error messages.

### 7. Text → Render Browser Result
- **Design Tested**: `Royal South Indian Bridal Necklace` (Category: `NECKLACE`)
- **Action**: Clicked "Generate Visuals from Text"
- **Result**: **PASS** ✅
  - Zero validation errors or toasts.
  - Render dispatched cleanly to NVIDIA GeForce RTX 4060 GPU worker.
  - Photorealistic antique gold South Indian bridal choker with emeralds and kundan polki diamonds synthesized in 19.1s.
  - Image smoothly transitioned into split comparison slider view.

### 8. Copilot Render Result
- **Prompt**: `"Change the necklace metal to platinum with sapphires and diamonds."`
- **Action**: Clicked "Render Visuals Now"
- **Result**: **PASS** ✅
  - Successfully compiled design state.
  - Dispatched iterative render with `previous_render_url` conditioning.
  - Output rendered and updated comparison view (`Previous Iteration ⇆ Generative AI Output`).

### 9. Doodle Regression Result
- **Action**: Switched to Sketch Canvas (Doodle) tab and drew on the canvas.
- **Result**: **PASS** ✅
  - Interactive canvas responded smoothly with drawing tools, zoom, pan, and history.

### 10. Image Regression Result
- **Action**: Switched to Image Blueprint tab.
- **Result**: **PASS** ✅
  - Blueprint photo dropzone active, supporting PNG, JPG, and WEBP formats.

### 11. Stale-State Result
- **Action**: Rapid switching across Text → Doodle → Image tabs and between Necklace and other designs.
- **Result**: **PASS** ✅
  - Category strictly preserved as `NECKLACE`.
  - No fallback to `RING`. No phantom gold/diamond defaults injected.
  - State remained isolated and consistent.

### 12. Tests Passed
- **Backend**: **184 of 184 tests passed** (`pytest backend/tests/`).
- **Frontend**: **45 of 45 tests passed** (`npx vitest run`).
- **TypeScript**: **0 compiler errors** (`npx tsc --noEmit`).

### 13. Real RTX 4060 Render Result
- **Device Used**: `cuda:0` (`NVIDIA GeForce RTX 4060 Laptop GPU`)
- **Inference Time**: `19,155.4 ms` (19.15 seconds)
- **Base Model**: `runwayml/stable-diffusion-v1-5`
- **ControlNet Model**: `outputs/rendering_v2_controlnet/controlnet_rendering_v2_final`
- **Control Strength**: `0.0`
- **Output URL**: Supabase-persisted asset URL generated and rendered cleanly.

### 14. Model Integrity Confirmation
- **YOLO V2 weights**: Unmodified ✅
- **ControlNet V2 weights**: Unmodified ✅
- **SD1.5 base model**: Unmodified ✅
- **Appearance LoRA**: Unmodified ✅
- **Training datasets**: Unmodified ✅
- **Architecture**: Preserved existing renderer and pipeline architecture ✅

---

## 15. Phase G1.2 — Final Verification (Read-Only Acceptance)

**Date:** 2026-09-19  
**Branch:** `phase-g-canva-ai-workspace` (NO commit, push, or merge performed)  
**GPU Hardware:** NVIDIA GeForce RTX 4060 Laptop GPU (CUDA 12.8, 8GB VRAM)  
**Worker Processes:**
- Frontend: Vite dev server on `http://localhost:5173` (PID 16352)
- Backend: FastAPI Uvicorn on `http://127.0.0.1:8000` (PID 31964)
- AI GPU Worker: Local FastAPI CUDA service on `http://127.0.0.1:8001` (PID 36816)

### Automated Test Suite Execution
| Test Suite | Command | Result | Summary |
|---|---|---|---|
| Backend Pytest Suite | `pytest backend/tests/` | **PASS (184/184)** | Full API, Gemini LLM, and AI Rendering test coverage |
| Frontend Vitest Suite | `npx vitest run` | **PASS (45/45)** | Full UI component, client parsing, and workspace test coverage |
| Production Build | `npm run build` (`tsc && vite build`) | **PASS (Code 0)** | Zero TypeScript errors, production bundles emitted in `frontend/dist/` (529 kB JS, 105 kB CSS) |

### Mandatory Real Chromium Browser Acceptance Tests

#### A. Text → Render Studio
- **Design Opened:** `Royal South Indian Bridal Necklace` (`911c4fb5-5be1-4a13-a90b-452759d4fee8`), Category: `NECKLACE`.
- **Input Prompt:** `"18k yellow gold necklace with emeralds and intricate traditional filigree"`
- **Action:** Clicked "Generate Visuals from Text" in Text Studio mode.
- **Observed Behavior:**
  - Zero validation errors (`control_strength = 0.0` successfully accepted by backend).
  - Neural Core indicator remained active on GPU worker.
  - Generative visual synthesized cleanly on RTX 4060 GPU and rendered in split comparison slider view.
  - Active state chips automatically updated to: `NECKLACE` · `18K YELLOW GOLD` · `EMERALD`.
- **Result:** **PASS** ✅ (Artifact: `test1_text_render_result_1789827876959.png`)

#### B. Copilot Conversational Render (Material Modification)
- **User Instruction:** `"Change the necklace metal to platinum while preserving the emeralds and filigree."`
- **Observed Behavior:**
  - Copilot analyzed conversational modification request against existing necklace state.
  - Proposed state chips updated to: `NECKLACE` · `PLATINUM` · `EMERALD`.
  - **Zero "Conflict" badge appeared** — category preservation logic correctly retained `NECKLACE`, metal transitioned cleanly to `platinum`, and gemstones were locked to `emeralds`.
  - Clicked "Render Visuals Now".
  - Real renderer synthesized the modified piece in silvery-white platinum with vibrant emeralds and intricate filigree preserved.
- **Result:** **PASS** ✅ (Artifact: `test2_copilot_platinum_result_1789827979531.png`)

#### C. Doodle → Render (Sketch-Guided Synthesis)
- **Action:** Switched to "Sketch Canvas" mode.
- **Interaction:** Sketched a geometric triangular jewellery silhouette on the drawing canvas.
- **Action:** Clicked "Render Visuals Now" with prompt conditioning.
- **Observed Behavior:**
  - ControlNet V2 conditioning successfully captured drawn vector geometry (`control_strength > 0.0`).
  - Output produced a high-end necklace featuring an emerald centerpiece sculpted precisely inside the drawn triangular silhouette with platinum filigree accents.
- **Result:** **PASS** ✅ (Artifact: `test3_doodle_render_result_1789828092138.png`)

#### D. Image → Render (Blueprint / Photo Guidance)
- **Action:** Switched to "Image Blueprint" tab.
- **Input File:** Uploaded real archival jewellery photograph `met_pendant_0016784.jpg` from the Metropolitan Museum dataset.
- **Prompt:** `"Vintage fine jewellery pendant with royal blue sapphire and diamond accents, studio lighting"`.
- **Action:** Clicked "Render Visuals Now".
- **Observed Behavior:**
  - Blueprint uploaded and conditioned cleanly.
  - Generative AI synthesis executed on RTX 4060 and populated the Interactive Comparison view without error.
- **Result:** **PASS** ✅ (Artifact: `test4_image_render_result_1789828938252.png`)

#### E. Stale State & Leakage Prevention
- **Test Sequence:**
  1. Opened Necklace design (`911c4fb5-5be1-4a13-a90b-452759d4fee8`) → Category badge: `NECKLACE`.
  2. Navigated to Earring design (`a3cc687d-c58e-4098-9209-98612bfff0c2`) → Category badge: `EARRINGS`.
  3. Rapidly toggled: Necklace → Earring → Necklace → Earring.
- **Observed Behavior:**
  - `fetchDesign` cleanly reinitialized state on route change without keeping stale memory.
  - Necklace attributes never leaked into Earring design. Earring attributes never leaked into Necklace design.
  - Zero phantom "Ring / Gold / Diamond / Prong" defaults.
- **Result:** **PASS** ✅ (Artifacts: `test4_earring_page_1789828173863.png`, `test4_necklace_page_restored_1789828269478.png`)

#### F. Iterative Redesign (Reference Retention)
- **Action:** Rendered Initial Design A (18K yellow gold necklace with emeralds and filigree).
- **Subsequent Request:** `"Change gold to platinum while preserving the design."`
- **Observed Behavior:**
  - The previous render URL was forwarded as reference image conditioning.
  - New synthesis maintained the identical structural form, filigree motif, and gemstone placement while shifting metal reflectance to high-polish platinum.
  - Avoided generating an unrelated jewellery silhouette.
- **Result:** **PASS** ✅

#### G. Error Handling & Workspace Stability
- **Test:** Cleared prompt completely (empty string) in Text mode and triggered generation.
- **Observed Behavior:**
  - Graceful validation handled on client/API boundary.
  - User is guided with clear feedback.
  - Workspace remained fully responsive; no unhandled exceptions, blank screens, or crashes.
- **Result:** **PASS** ✅ (Artifact: `test5_empty_prompt_handled_1789828488257.png`)

### Integrity Checklist
- [x] YOLO V2 weights & checkpoints untouched
- [x] ControlNet V2 weights & checkpoints untouched
- [x] SD1.5 base model untouched
- [x] Appearance LoRA untouched
- [x] Dataset files untouched
- [x] No training executed
- [x] On branch `phase-g-canva-ai-workspace`
- [x] No commits, pushes, or merges performed



