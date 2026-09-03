# PHASE 10 — JEWELLERY CATEGORY PROMPT CONDITIONING FIX REPORT

**Date:** 2026-09-04  
**Status:** Implementation Complete — Awaiting Manual GPU Smoke Test Review  
**Author:** AI Engineering & Architecture  

---

## A. Root Cause Analysis

During Phase 10 validation of the fine-tuned ControlNet model on `ring_train_000.jpg`, the model generated broken geometry (pendant/bracelet/watch loop with loose diamond clusters) rather than an enclosed ring band.

Detailed investigation revealed:
1. **Prompt Inconsistency with Training Captions:**
   - The ControlNet training captions explicitly contained category anchors such as `"photorealistic fine jewellery finger ring crafted in 18k yellow gold..."`.
   - The production prompt builder `build_jewellery_prompt()` completely omitted the jewellery category token, generating generic text: `"photorealistic fine jewellery product photograph, studio lighting, sharp focus, clean background, crafted in polished 18k yellow gold..."`.
2. **CLIP Embedding Semantic Ambiguity:**
   - Without an explicit category token in the positive prompt, the diffusion prior lacked semantic grounding to associate circular lineart with a ring band.
   - Comparative testing proved that adding `"ring"` or `"fine jewellery finger ring"` to the prompt restored correct ring geometry across Pretrained, 100-Step, and 300-Step models without any weight modifications.
3. **Core Architectural Fix:**
   - Fix prompt builder and request schemas to support controlled jewellery categories (`ring`, `earring`, `pendant`, `necklace`, `bracelet`, `bangle`, `brooch`, `other`).
   - No models were retrained, no datasets altered, no weights modified.

---

## B. Prompt-Builder Changes (`ai/rendering/prompts.py`)

- Updated `build_jewellery_prompt()` signature:
  ```python
  def build_jewellery_prompt(
      material: str = "18k yellow gold",
      gemstone: str = "round brilliant diamond",
      category: Optional[str] = None,
      user_prompt: Optional[str] = None,
  ) -> str:
  ```
- **Controlled Category Support:** Validates against `SUPPORTED_CATEGORIES` (`ring`, `earring`, `pendant`, `necklace`, `bracelet`, `bangle`, `brooch`, `other`).
- **Semantic Injection:**
  - `category="ring"` $\rightarrow$ `"photorealistic fine jewellery ring product photograph, studio lighting, sharp focus, clean background, crafted in ..."`
  - `category="earring"` $\rightarrow$ `"photorealistic fine jewellery earring product photograph, studio lighting, sharp focus, clean background, crafted in ..."`
  - `category="pendant"` $\rightarrow$ `"photorealistic fine jewellery pendant product photograph, studio lighting, sharp focus, clean background, crafted in ..."`
  - `category="other"` or `None` $\rightarrow$ Generic style modifier: `"photorealistic fine jewellery product photograph, studio lighting, sharp focus, clean background, crafted in ..."` (no silent ring default).
- **Validation:** Raises `ValueError` with clear message if an invalid category string is provided (e.g., `"automobile"`).
- **Token Efficiency:** Preserves prompt token length between 30–40 tokens (well below CLIP's 77-token ceiling).

---

## C. RenderRequest Changes (`ai/rendering/schemas.py`)

- Added `JewelleryCategory` literal type:
  ```python
  JewelleryCategory = Literal[
      "ring",
      "earring",
      "pendant",
      "necklace",
      "bracelet",
      "bangle",
      "brooch",
      "other",
  ]
  ```
- Added `category` field to `RenderRequest`:
  ```python
  category: Optional[JewelleryCategory] = Field(
      default=None,
      description="Controlled jewellery category ('ring', 'earring', 'pendant', 'necklace', 'bracelet', 'bangle', 'brooch', 'other')",
  )
  ```
- Added field validator `normalize_category` to trim whitespace and lowercase input before validation.
- Kept `default=None` so omitting the field does not silently force all requests to be rings.

---

## D. Category Validation Design

| Category | Prompt Modifier Output |
| :--- | :--- |
| `ring` | `photorealistic fine jewellery ring product photograph...` |
| `earring` | `photorealistic fine jewellery earring product photograph...` |
| `pendant` | `photorealistic fine jewellery pendant product photograph...` |
| `necklace` | `photorealistic fine jewellery necklace product photograph...` |
| `bracelet` | `photorealistic fine jewellery bracelet product photograph...` |
| `bangle` | `photorealistic fine jewellery bangle product photograph...` |
| `brooch` | `photorealistic fine jewellery brooch product photograph...` |
| `other` | `photorealistic fine jewellery product photograph...` |
| `None` (omitted) | `photorealistic fine jewellery product photograph...` |
| *Invalid* (e.g. `car`) | **Rejected with Validation Error / HTTP 422** |

---

## E. Smoke-Test Changes (`scripts/smoke_test_rendering.py`)

- Updated `smoke_test_rendering.py` to explicitly specify `category="ring"` in `RenderRequest`:
  ```python
  request = RenderRequest(
      category="ring",
      material="18k yellow gold",
      gemstone="round brilliant diamond",
      control_type="lineart",
      control_strength=0.8,
      steps=20,
      guidance_scale=7.5,
      seed=42,
      width=512,
      height=512,
  )
  ```
- **Unchanged Parameters:**
  - Seed: `42`
  - Resolution: `512x512`
  - Denoising steps: `20`
  - Guidance scale: `7.5`
  - ControlNet scale: `0.8`
  - Scheduler: `UniPCMultistepScheduler`
  - Preprocessing: `LineArtProcessor`

---

## F. Tests Run & Results

### 1. AI & Rendering Tests (`pytest tests/`)
```
====================== 95 passed, 10 warnings in 12.56s =======================
```
- Verified `build_jewellery_prompt()` for all controlled categories (`ring`, `earring`, `pendant`, `necklace`, `bracelet`, `bangle`, `brooch`).
- Verified `other` and `None` fallbacks do not inject unwanted category tokens.
- Verified whitespace trimming and case normalization (`"  RING  "` $\rightarrow$ `"ring"`).
- Verified invalid category rejection in `build_jewellery_prompt` and `RenderRequest`.

### 2. Backend API Tests (`pytest backend/tests/`)
```
======================= 59 passed, 10 warnings in 7.22s ========================
```
- Verified POST `/api/v1/ai/render` handles `category="ring"` successfully.
- Verified POST `/api/v1/ai/render` rejects unsupported categories with HTTP 422.

### 3. Frontend TypeScript Compilation (`npm run build`)
```
✓ 1864 modules transformed.
✓ built in 238ms
```
- Verified `RenderOptions` and `aiRenderingService.renderSketch` compile cleanly with full type safety.

---

## G. Files Changed

| File | Nature of Change |
| :--- | :--- |
| `ai/rendering/prompts.py` | Added `SUPPORTED_CATEGORIES`, category parameter in `build_jewellery_prompt()`, category validation, and semantic modifier injection. |
| `ai/rendering/schemas.py` | Added `JewelleryCategory` literal, `category` field in `RenderRequest`, and normalization validator. |
| `ai/rendering/pipeline.py` | Passed `category=req.category` into `build_jewellery_prompt()`. |
| `backend/app/api/v1/ai_rendering.py` | Added `category: Optional[str] = Form(None)` and validation error handling. |
| `frontend/src/services/api/aiRenderingService.ts` | Added `category` to `RenderOptions` interface and form data payload. |
| `scripts/smoke_test_rendering.py` | Explicitly configured `category="ring"` in `RenderRequest`. |
| `scripts/benchmark_rendering.py` | Added `category="ring"` in `RenderRequest`. |
| `scripts/validate_quality.py` | Updated validation suite items with explicit lowercase category values. |
| `tests/ai/test_rendering.py` | Added unit tests covering all category permutations, normalization, and validation rules. |
| `backend/tests/test_ai_rendering.py` | Added backend API tests for valid and invalid category parameters. |

---

## H. Manual GPU Smoke-Test Command

To execute the GPU smoke test with the category fix on the local NVIDIA RTX 4060:

```powershell
& "C:\Users\usern\miniconda3\envs\tgpu\python.exe" scripts/smoke_test_rendering.py
```

---

## I. Expected Result

1. Pipeline loads the fine-tuned ControlNet model on CUDA.
2. The prompt builder incorporates `fine jewellery ring` into the positive prompt.
3. Stable Diffusion denoises with full geometric conditioning for a ring band, producing a clean, photorealistic ring with correct closure and prong geometry.
4. Output image is saved to `outputs/rendering/` without leaking filesystem paths.
5. VRAM peak remains safely under $\sim 3.2$ GiB (well within 8GB VRAM envelope).

---

## J. Backwards-Compatibility Considerations

1. **Optional Category:** `RenderRequest.category` is optional (`default=None`). Existing API clients that do not pass a category parameter will not break; they receive generic jewellery prompts rather than failing.
2. **Explicit Smoke Test:** The smoke test explicitly passes `category="ring"` instead of relying on an implicit global default.
3. **Multi-Category Extensibility:** As dataset coverage expands to pendants, necklaces, earrings, and bracelets, frontend callers can immediately request those categories without backend schema modifications.
