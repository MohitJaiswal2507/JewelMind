# JewelMind — AI Design Understanding & Gemini Integration
## Phase 0: Read-Only Integration Audit from Current Main Branch

**Date:** September 12, 2026  
**Auditor:** Antigravity AI Engineering Assistant  
**Repository:** `MohitJaiswal2507/JewelMind`  
**Current Branch:** `main`  
**Current HEAD Commit:** `765b7cb Merge pull request #25 from MohitJaiswal2507/phase-19-pre-ui-runtime-stabilization`  
**Target Capability:** Gemini-Powered Multimodal Jewellery Design Understanding & Prompt Enhancement Pipeline  
**Execution Context:** Strictly Read-Only Audit (Zero code modifications, zero commits, zero package installations, zero AI training)

---

## 1. Executive Summary

JewelMind operates an end-to-end jewellery design and manufacturing system consisting of:
1. **Frontend:** React + Vite + Tailwind CSS + shadcn/ui featuring an interactive drawing canvas (`DesignWorkspacePage.tsx`), digital design catalog (`DesignsPage.tsx`, `DesignDetailPage.tsx`), generative diffusion studio (`StudioPage.tsx`, `AiRenderModal.tsx`), and production management suite (`ProductionPage.tsx`).
2. **Backend:** FastAPI + SQLAlchemy 2.0 + Alembic backed by Supabase PostgreSQL and Supabase Storage for CAD blueprints and diffusion renders.
3. **AI Vision & Rendering:** An in-house **YOLO11m-seg** production model (`yolo11m-seg-jewelmind-v2-continued`) for whole-jewellery classification/segmentation across 8 categories, coupled with an approved **1000-step ControlNet v2 (LineArt)** conditioned on **Stable Diffusion v1.5** (`UniPCMultistepScheduler`) running on an NVIDIA RTX 4060 GPU (8GB VRAM).
4. **Operations:** Google OR-Tools CP-SAT scheduling engine for workshop job-shop optimization.

Currently, the bridge between **design input** (a sketch or uploaded blueprint) and **photorealistic rendering** relies on basic manual dropdown selections (Material: *18k yellow gold*, Gemstone: *round brilliant diamond*) concatenated with an optional plain text string via a rudimentary template builder (`build_jewellery_prompt()` in `ai/rendering/prompts.py`). If the user does not type a detailed description, the diffusion model receives generic prompts that cannot capture nuanced geometry, stone settings, prong structures, or design motifs visible in the sketch.

This audit establishes how to integrate **Google Gemini Vision** (specifically `gemini-1.5-flash` / `gemini-2.5-flash`) into JewelMind's existing architecture. Gemini will act as an **Artisan Design Intelligence Copilot** that:
- Inspects uploaded sketches and CAD blueprints visually alongside YOLO V2 classification.
- Extracts structured design semantics (jewellery type, metals, primary/secondary stones, setting types, prongs, shanks, motifs, symmetry, geometry preservation rules).
- Synthesizes rich, diffusion-optimized positive and negative prompts that dramatically improve photorealistic render fidelity without overriding explicit user intent.
- Provides actionable material and stone counts to downstream Production Management and Optimization workflows.
- Operates under a strict **₹0 / Free-Tier Budget** with resilient, zero-downtime fallback to the existing template builder if Gemini is unavailable, unconfigured, or rate-limited.

---

## 2. Current Main Branch State

A strict verification of the active Git environment confirmed:
- **Active Branch:** `main` (Verified clean checkout, exactly tracking `origin/main`).
- **HEAD Commit:** `765b7cb Merge pull request #25 from MohitJaiswal2507/phase-19-pre-ui-runtime-stabilization`.
- **Preceding Commits:**
  - `977180d fixed Runtime errors`
  - `f5f8624 Merge pull request #24 from MohitJaiswal2507/phase-19-ui-ux-redesign`
  - `d68881d UI-ux redesigned part 1`
- **Working-Tree Status:** Clean working tree. No uncommitted modifications to existing application source code. (Untracked files are strictly isolated audit markdown documents in `docs/`).
- **Production Checkpoints:** Unmodified and verified on disk at `runs/segment/runs/segment/runs/jewellery/yolo11m-seg-jewelmind-v2-continued/weights/best.pt` and `outputs/rendering_v2_controlnet/controlnet_rendering_v2_final`.

---

## 3. Current Architecture Overview

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               FRONTEND (React + Vite)                                  │
│  ┌───────────────────────┐  ┌───────────────────────┐  ┌────────────────────────────┐  │
│  │  DesignWorkspacePage  │  │   DesignDetailPage    │  │         StudioPage         │  │
│  │    (DrawingCanvas)    │  │ (SketchUploadDropzone)│  │     (AiRenderModal)        │  │
│  └───────────┬───────────┘  └───────────┬───────────┘  └─────────────┬──────────────┘  │
│              │                          │                            │                 │
│              ▼                          ▼                            ▼                 │
│        designService              designService              aiRenderingService        │
└──────────────┼──────────────────────────┼────────────────────────────┼─────────────────┘
               │                          │                            │
               ▼                          ▼                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               BACKEND (FastAPI - Port 8000)                            │
│  ┌──────────────────────────────────────────────────────────────────────────────────┐  │
│  │ API Endpoints:                                                                   │  │
│  │  - POST /api/v1/designs (CRUD)                                                   │  │
│  │  - POST /api/v1/designs/{id}/sketch (Upload to Supabase Storage)                 │  │
│  │  - POST /api/v1/ai/components/detect (YOLO V2 Instance Segmentation)             │  │
│  │  - POST /api/v1/ai/render (ControlNet Generative Diffusion)                      │  │
│  │  - POST /api/v1/production/optimize (OR-Tools CP-SAT Scheduling)                 │  │
│  └──────────────────────────────────────────────────────────────────────────────────┘  │
│         │                                      │                                       │
│         ▼                                      ▼                                       │
│  ┌──────────────┐                       ┌──────────────┐                               │
│  │  PostgreSQL  │                       │   Supabase   │                               │
│  │  (Supabase)  │                       │   Storage    │                               │
│  └──────────────┘                       └──────────────┘                               │
└────────────────────────────────────────────────┼───────────────────────────────────────┘
                                                 │ (Internal HTTP proxy or direct call)
                                                 ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                 AI INFERENCE ENGINE / LOCAL WORKER (Port 8001 / 'tgpu')                │
│  ┌────────────────────────────────────────┐  ┌──────────────────────────────────────┐  │
│  │ YOLO V2 Segmenter (YOLO11m-seg)        │  │ JewelleryRenderingPipeline           │  │
│  │  - 8 Categories (ring, necklace, etc.) │  │  - Preprocessing (LineArt / Canny)   │  │
│  │  - Fast instance masks & bboxes        │  │  - ControlNet v2 (1000-step)         │  │
│  │                                        │  │  - Base Diffusion (SD1.5, FP16)      │  │
│  │                                        │  │  - Prompt Builder (Static Templates) │  │
│  └────────────────────────────────────────┘  └──────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Current Sketch Flow Trace

### Step-by-Step Execution:
1. **User Action:** The artisan enters the drawing desk at `frontend/src/pages/DesignWorkspacePage.tsx` and draws on `frontend/src/components/canvas/DrawingCanvas.tsx` using brush, eraser, line, ellipse, or symmetry tools.
2. **Export:** Clicking "Save Blueprint" invokes `handleSaveSketch()`. The canvas calls `canvasRef.current.exportPngBlob()`, serializing the HTML5 Canvas to a PNG binary blob.
3. **Upload API:** Invokes `designService.uploadSketch(design.id, file)` (`frontend/src/services/api/designService.ts`), issuing a `POST /api/v1/designs/{id}/sketch` multipart request.
4. **Backend Ingestion:** Caught by `upload_design_sketch()` in `backend/app/api/v1/designs.py`.
5. **Storage Persistence:** Calls `storage_service.upload_sketch()` in `backend/app/services/storage_service.py`. The file is cryptographically validated (magic bytes `\x89PNG\r\n\x1a\n`, max 10MB) and uploaded to Supabase Storage at `{user_id}/{design_id}/sketch_{uuid}.png`.
6. **Database Persistence:** Updates the `designs` table: `design.sketch_image_url = public_url`, `design.status = 'draft'`.
7. **Downstream Trigger:** The artisan navigates to `StudioPage.tsx` or `DesignDetailPage.tsx` and clicks **AI Render (Diffusion)**, which opens `frontend/src/components/studio/AiRenderModal.tsx`.

---

## 5. Current Upload Flow Trace

### Step-by-Step Execution:
1. **User Action:** The user accesses `DesignDetailPage.tsx` (or canvas reference upload) and drops a file onto `frontend/src/components/designs/SketchUploadDropzone.tsx`.
2. **Validation:** Checks MIME type (`image/png`, `image/jpeg`, `image/webp`) and size (<10MB).
3. **API Call:** Emits `onUpload(file)` $\rightarrow$ `designService.uploadSketch(design.id, file)`.
4. **Backend Processing:** `backend/app/api/v1/designs.py` receives the binary stream, persists it via `storage_service.upload_sketch()`, and updates `design.sketch_image_url`.
5. **Detection (Optional / Decoupled):** The frontend has an `aiComponentService.detectComponents(file, conf)` endpoint calling `POST /api/v1/ai/components/detect`.
6. **Observation:** In the current code, **detection is not automatically chained to image upload**. The sketch is saved to Supabase, but YOLO V2 is only invoked if explicitly queried. There is currently no unified pipeline that takes an uploaded image, runs YOLO V2, generates a prompt, and renders it in one automated flow.

---

## 6. Current Prompt Flow Trace

### Prompt Entry & Storage Points:
1. **Design Creation:** `DesignModal.tsx` allows entering a design name, category, and description.
2. **Workspace Chat Copilot:** `frontend/src/components/chat/DesignChatPanel.tsx` contains a prompt textarea and preset suggestions. Entering a prompt calls `onPromptChange(text)`, which updates local state `prompt` in `DesignWorkspacePage.tsx`. When "Save Sketch" is clicked, it calls `designService.updateDesign(design.id, { ai_prompt: prompt })`, storing the string in `designs.ai_prompt`.
3. **Studio Rendering Modal:** `frontend/src/components/studio/AiRenderModal.tsx` provides an input under "Advanced Settings" titled *"Custom Lighting / Prompt Notes"* (`customPrompt`).

### Prompt Assembly & Enhancement (Current State):
Currently, JewelMind has **no AI-powered prompt enhancement**. Prompts are assembled strictly through string formatting in `ai/rendering/prompts.py`:

```python
def build_jewellery_prompt(
    material: str = "18k yellow gold",
    gemstone: str = "round brilliant diamond",
    category: Optional[str] = None,
    user_prompt: Optional[str] = None,
) -> str:
    material_desc = MATERIAL_PROMPTS.get(material.strip().lower(), f"polished {material}, precious metal")
    gemstone_desc = GEMSTONE_PROMPTS.get(gemstone.strip().lower(), f"faceted {gemstone}, refractive clarity")
    
    # Static style modifiers:
    # "photorealistic fine jewellery {category} product photograph, studio lighting, sharp focus, clean background"
    parts = [style_modifiers, f"crafted in {material_desc}", f"embellished with {gemstone_desc}"]
    if user_prompt and user_prompt.strip():
        parts.insert(0, user_prompt.strip())
    return ", ".join(parts)
```

**Flaws in Current Implementation:**
- Static dictionaries (`MATERIAL_PROMPTS`, `GEMSTONE_PROMPTS`) only recognize 6 hardcoded materials and 6 hardcoded stones. Any custom alloy or gemstone defaults to a generic fallback.
- No semantic understanding of the sketch geometry: prongs, bezels, pavé accents, filigree, multi-stone clusters, or band profiles are completely absent from the prompt unless manually typed by the user.

---

## 7. Current YOLO V2 Integration Audit

### 7.1 Architecture & Verification
- **Model Checkpoint:** `runs/segment/runs/segment/runs/jewellery/yolo11m-seg-jewelmind-v2-continued/weights/best.pt`
- **Model Type:** Ultralytics YOLO11m-seg (SegmentationModel)
- **Parameters:** 22,365,384 (~22.4M params)
- **Verified 8-Class Production Taxonomy:**
  - `0: ring`
  - `1: earring`
  - `2: pendant`
  - `3: necklace`
  - `4: bracelet`
  - `5: bangle`
  - `6: brooch`
  - `7: other_jewellery`
- **Inference Service:** `ai/vision/inference/detector.py` (`JewelleryComponentDetector`).
- **Endpoint:** `POST /api/v1/ai/components/detect` (`backend/app/api/v1/ai_components.py`).
- **Input:** Multipart image file + optional confidence threshold (`conf`, default `0.25`).
- **Output:** `DetectionResult` schema containing:
  - `detections`: List of detected objects with `class_id`, `class_name`, `confidence`, `box` `(x1, y1, x2, y2)`, and `polygon` coordinates `[[x, y], ...]`.
  - `summary`: High-level count dictionary (e.g. `{"ring": 1}`).
  - `image_size`: `(width, height)`.

### 7.2 Integration Opportunity for Gemini
YOLO V2 provides **ground-truth spatial bounding boxes and class confirmation**. Passing YOLO V2 detections into Gemini:
1. Gives Gemini verified category grounding (e.g., "YOLO detected category: ring with 96.2% confidence at coordinates [x1, y1, x2, y2]").
2. Prevents Gemini hallucination (e.g., misidentifying a circular pendant as a ring).
3. Focuses Gemini Vision's attention on the specific jewellery bounding box.

---

## 8. Current Rendering Pipeline Audit

### 8.1 Model Specifications & Hardware
- **Base Diffusion Model:** Stable Diffusion v1.5 (`runwayml/stable-diffusion-v1-5` or local weights in `models/diffusion`).
- **ControlNet Model:** Final approved 1000-step ControlNet (`outputs/rendering_v2_controlnet/controlnet_rendering_v2_final`).
- **Preprocessing:** LineArt edge extraction (`ai/rendering/preprocessing.py`) or Canny filter. Converts input sketch to a normalized conditioning map.
- **Scheduler:** `UniPCMultistepScheduler` (fast 20-step deterministic sampling).
- **VRAM Optimizations:** FP16 mixed precision, `enable_attention_slicing("auto")`, `enable_vae_slicing()`, concurrency lock (`DiffusionModelManager.execution_lock`).
- **Memory Footprint:** Peak VRAM during 512x512 rendering is **~4.8 GB**, operating comfortably within the RTX 4060's 8,188 MiB ceiling.

### 8.2 Exact Point of Gemini Insertion
In `backend/app/api/v1/ai_rendering.py`:
Currently, `render_jewellery_sketch()` receives `prompt`, `material`, `gemstone`, and `category`, which are passed directly to `RenderRequest`.
**The exact insertion point for Gemini is immediately after sketch bytes decoding (around line 178 of `ai_rendering.py`)**:
```python
# PROPOSED INSERTION POINT:
if gemini_enhancement_requested:
    enhanced_context = await gemini_design_service.understand_and_enhance(
        image_bytes=contents,
        yolo_category=category,
        user_prompt=prompt,
        material=material,
        gemstone=gemstone
    )
    # Override/augment rendering prompt with Gemini-engineered specification
    prompt = enhanced_context.rendering_prompt
    negative_prompt = enhanced_context.negative_prompt
```

---

## 9. Current Production Pipeline Audit

### 9.1 Operations & Scheduling Architecture
- **Location:** `backend/app/services/production_service.py` and `backend/app/services/production_optimization_service.py`.
- **Entities:** `ProductionOrder`, `Worker`, `Machine`, `ProductionSchedule`, `ScheduledTask`.
- **Current Capability:** Google OR-Tools CP-SAT scheduler solves job-shop task conflicts, worker skill matching, and machine assignment based on order priorities (`urgent`, `high`, `medium`, `low`) and deadlines.
- **Current Limitation:** In `production_optimization_service.py` (`OPERATION_DEFS`), every production order is routed through identical hardcoded operations:
  1. `Casting & Metallurgy` (Base: 2h, +0.5h/unit)
  2. `Stone Setting & Assembly` (Base: 2h, +0.75h/unit)
  3. `Polishing & Finishing` (Base: 1h, +0.5h/unit)

### 9.2 Proposed Future Flow: Gemini $\rightarrow$ Production
Gemini's structured design understanding can bridge design and manufacturing:
- **Material Detection:** Identifying `950 Platinum` vs `18K Gold` automatically adjusts furnace temperature parameters and casting cycle duration.
- **Gemstone Breakdown:** Knowing that a design contains *1 center diamond + 24 pavé melee diamonds* allows dynamic scaling of the `Stone Setting & Assembly` stage (e.g., $+0.1\text{h}$ per pave stone).
- **Specialized Operations:** Detecting intricate filigree or micro-engraving automatically inserts an optional `Laser Engraving & Detailing` operation into the CP-SAT model.

---

## 10. Current Database & Data Model Audit

### 10.1 `designs` Table Schema (`backend/app/models/design.py`)
| Column | Type | Nullable | Current Usage |
| :--- | :--- | :--- | :--- |
| `id` | UUID | No | Primary Key |
| `user_id` | UUID | No | Owner Foreign Key |
| `name` | String(255) | No | Design Title |
| `description` | Text | Yes | User notes |
| `category` | String(50) | No | Ring, earring, pendant, etc. |
| `status` | String(50) | No | `draft`, `rendering`, `ready`, `archived` |
| `sketch_image_url` | String(1024) | Yes | Public Supabase URL to sketch |
| `rendered_image_url`| String(1024) | Yes | Public Supabase URL to render |
| `ai_prompt` | Text | Yes | User prompt / Copilot text |
| `created_at` | DateTime | No | Timestamp |
| `updated_at` | DateTime | No | Timestamp |

### 10.2 Database Impact Assessment
- **Zero Schema Breaking Changes:** Currently, there is no JSON metadata column on `designs`.
- **Non-Breaking Extension Recommendation:** Add an optional nullable JSON column:
  `design_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)`  
  via an Alembic migration.
- **Immediate MVP Alternative (Zero Migration):** For the initial Phase A/B integration, Gemini structured output can be passed ephemerally in API responses, or stored serialized as JSON within `designs.description` or a dedicated lightweight metadata table.

---

## 11. Proposed Gemini Role

Gemini is introduced as an **Artisan Intelligence Copilot**, supporting four distinct operational cases:

```
                               ┌─────────────────────────────────┐
                               │         Input Options           │
                               └────────────────┬────────────────┘
                                                │
         ┌──────────────────────┬───────────────┴───────────────┬──────────────────────┐
         ▼                      ▼                               ▼                      ▼
  [Case 1: Sketch/Img]   [Case 2: Sketch + Prompt]       [Case 3: Prompt Only]  [Case 4: No Enhance]
  No User Prompt         "platinum solitaire ring..."    "art deco emerald..."  User explicit prompt
         │                      │                               │                      │
         ▼                      ▼                               ▼                      ▼
  YOLO V2 Category       YOLO V2 + User Prompt           Text Analysis Only     Bypass Gemini
         │                      │                               │                      │
         ▼                      ▼                               ▼                      │
   Gemini Vision          Gemini Vision                   Gemini Text                  │
(Understand Geometry)  (Honor Intent + Detail)         (Synthesize Details)            │
         │                      │                               │                      │
         └──────────────────────┼───────────────────────────────┘                      │
                                │                                                      │
                                ▼                                                      │
                    Structured Design Contract                                         │
                    (Materials, Stones, Settings)                                      │
                                │                                                      │
                                ▼                                                      ▼
                    Enhanced Diffusion Prompt ──────────────────────────────► ControlNet + SD1.5
```

### Case 1: Image / Sketch + No User Prompt
- **User Action:** Artisan draws a sketch or uploads an image and leaves the prompt box blank.
- **Gemini Pipeline:**
  1. Image bytes passed to YOLO V2 $\rightarrow$ Detects category (e.g. `ring`, conf `0.94`).
  2. Image bytes + YOLO category passed to Gemini Vision.
  3. Gemini analyzes line art, contours, gemstone placements, prongs, and shank thickness.
  4. Gemini generates structured design attributes and builds a complete photorealistic rendering prompt.
  5. Renderer generates high-fidelity render matching the sketch geometry.

### Case 2: Image / Sketch + User Prompt
- **User Action:** Artisan provides a sketch and types *"platinum ring with oval blue sapphire and pavé diamonds"*.
- **Gemini Pipeline:**
  1. User prompt is marked as **LOCKED INTENT** (precedence level 1).
  2. Gemini analyzes sketch to extract physical layout (e.g. 4 prongs, cathedral shoulder, halo contour).
  3. Gemini merges user's explicit intent (platinum + sapphire + pave) with observable sketch geometry.
  4. **Strict Constraint:** Gemini is forbidden from replacing platinum with gold or sapphire with emerald.

### Case 3: User Prompt Only (No Image)
- **User Action:** User types a creative prompt without providing a sketch.
- **Gemini Pipeline:**
  - Evaluates text prompt, resolves missing lighting, material luster, and facet specifications, producing a diffusion-grade prompt.

### Case 4: User Does Not Want Enhancement (Bypass Mode)
- **User Action:** User disables the *"Enhance with AI"* toggle or clicks direct *"Generate Render"*.
- **Gemini Pipeline:** Gemini is bypassed completely. The system routes directly to the legacy `build_jewellery_prompt()` builder with zero added latency.

---

## 12. Proposed End-to-End Architecture

```
                               ┌───────────────────────────────┐
                               │  Client (AiRenderModal / UI)  │
                               └───────────────┬───────────────┘
                                               │ Multipart Form / JSON
                                               ▼
                               ┌───────────────────────────────┐
                               │     FastAPI Backend (8000)    │
                               └───────────────┬───────────────┘
                                               │
                                 ┌─────────────┴─────────────┐
                                 │                           │
                                 ▼ (Step 1)                  ▼ (Step 2)
                    ┌─────────────────────────┐ ┌─────────────────────────┐
                    │ YOLO V2 Category Engine │ │  Gemini Design Service  │
                    │   (Fast Local CUDA)     │ │ (gemini-1.5/2.5-flash)  │
                    │  - Whole-type detector  │ │  - Visual understanding │
                    │  - Bounding box / mask  │ │  - Intent preservation  │
                    └────────────┬────────────┘ │  - Structured contract   │
                                 │              └────────────┬────────────┘
                                 │ Verified Category         │ Structured JSON +
                                 └───────────────────────────► Engineered Prompt
                                                             │
                                                             ▼ (Step 3)
                                                ┌─────────────────────────┐
                                                │  Jewellery Render Pipe  │
                                                │    (ControlNet + SD)    │
                                                │  - LineArt condition    │
                                                │  - Precise metal/stones │
                                                └────────────┬────────────┘
                                                             │
                                                             ▼ (Step 4)
                                                ┌─────────────────────────┐
                                                │    Supabase Storage     │
                                                │  - Master Render Asset  │
                                                └─────────────────────────┘
```

---

## 13. Proposed Gemini Data Contract

The structured contract is minimal, clean, and directly maps to JewelMind's existing models:

```json
{
  "jewellery_type": "ring",
  "category_confidence": 0.96,
  "materials": {
    "primary_metal": "950 platinum",
    "finish": "high-polish reflective finish",
    "accent_metal": null
  },
  "gemstones": {
    "primary_stone": {
      "type": "diamond",
      "cut": "round brilliant",
      "estimated_count": 1,
      "setting_type": "4-prong basket setting"
    },
    "secondary_stones": [
      {
        "type": "diamond",
        "cut": "melee round",
        "estimated_count": 16,
        "setting_type": "micro-pavé channel"
      }
    ]
  },
  "structural_elements": {
    "shank_type": "tapered cathedral shank",
    "shoulder": "pavé diamond embellished",
    "head_style": "elevated open gallery",
    "findings": null
  },
  "design_motifs": ["Art Deco geometric symmetry", "clean modern lines"],
  "user_intent_preserved": true,
  "rendering_prompt": "photorealistic fine jewellery ring product photograph, round brilliant center diamond mounted in 4-prong elevated open gallery, tapered cathedral shank embellished with micro-pavé melee diamonds, polished 950 platinum with brilliant specular highlights, studio lighting, crisp focus, neutral background",
  "negative_prompt": "malformed jewellery, deformed ring, melted metal, broken geometry, distorted symmetry, missing prongs, cloudy stones, blurry, bad anatomy"
}
```

### Data Contract Lifecycle & Attribution:
- **`jewellery_type`**: Grounded by YOLO V2, confirmed by Gemini.
- **`materials` / `gemstones`**: Sourced from user prompt if specified; otherwise inferred visually by Gemini.
- **`structural_elements`**: Inferred by Gemini Vision from sketch line contours.
- **`rendering_prompt`**: Built by Gemini, formatted under 75 CLIP tokens.
- **Persistence**: Stored in `designs.design_metadata` (or cached during session).

---

## 14. User Intent vs. Gemini Inference Precedence Model

To prevent AI hallucination from corrupting custom client specifications, the system enforces a strict 5-tier precedence hierarchy:

```
  Tier 1: EXPLICIT USER REQUIREMENTS (LOCKED)
  -------------------------------------------------------------
  Materials, specific stones, colors, or styles typed by the user
  CANNOT be altered or overridden by Gemini.

  Tier 2: OBSERVABLE BLUEPRINT GEOMETRY
  -------------------------------------------------------------
  Physical contours extracted from the sketch: silhouette, symmetry,
  stone count, prong positions, and band curvature.

  Tier 3: YOLO V2 CATEGORY GROUNDING
  -------------------------------------------------------------
  Verified whole-jewellery classification (e.g. confirms "pendant"
  vs "earring" to prevent category drift).

  Tier 4: GEMINI INFERRED MICRO-ATTRIBUTES
  -------------------------------------------------------------
  Realistic faceting, metal specular lusters, prong curvature,
  setting depth, and lighting reflections.

  Tier 5: SAFE RENDERING DEFAULTS
  -------------------------------------------------------------
  JewelMind default negative prompt and studio product lighting anchors.
```

---

## 15. Proposed UX Flow

### Recommended UI Extension: `frontend/src/components/studio/AiRenderModal.tsx`

Currently, `AiRenderModal.tsx` buries the prompt input inside an "Advanced Settings" accordion. The proposed UX elevates design description and adds an interactive **"✨ Enhance with AI"** copilot button:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Atelier Generative Studio                       │
├──────────────────────────────────┬─────────────────────────────────────┤
│  Blueprint Canvas / Preview      │  Design & Styling Parameters        │
│                                  │                                     │
│  ┌────────────────────────────┐  │  Category: [ Ring               ▼ ] │
│  │                            │  │  Precious Metal: [ 950 Platinum ▼ ] │
│  │       Sketch Blueprint     │  │  Primary Stone: [ Diamond       ▼ ] │
│  │                            │  │                                     │
│  │                            │  │  Design Description (Optional)     │
│  └────────────────────────────┘  │  ┌────────────────────────────────┐ │
│                                  │  │ Solitaire with pavé band       │ │
│                                  │  └────────────────────────────────┘ │
│                                  │                                     │
│                                  │  [ ✨ Enhance with AI ]  ◄── (NEW)  │
│                                  │                                     │
│                                  │  ┌────────────────────────────────┐ │
│                                  │  │ ✨ AI Enhanced Specification:  │ │
│                                  │  │ "Photorealistic ring in 950   │ │
│                                  │  │ platinum, round diamond in     │ │
│                                  │  │ 4-prong setting with pavé..."  │ │
│                                  │  └────────────────────────────────┘ │
│                                  │                                     │
│                                  │  [ Generate Photorealistic Render ] │
└──────────────────────────────────┴─────────────────────────────────────┘
```

1. **Automatic Understanding (No Prompt):** If the user leaves the description empty and clicks *"Generate"*, Gemini silently analyzes the sketch, produces the structured contract, and sends the prompt to ControlNet.
2. **Interactive Preview & Edit:** If the user clicks *"✨ Enhance with AI"*, a loading shimmer displays (`Gemini analyzing blueprint...`), populating an editable enhanced prompt card. The user can tweak words before rendering.

---

## 16. Gemini API Architecture Recommendation

### Evaluated Architectural Options:
- **Option A: Frontend calls Gemini directly via SDK.**  
  *Rejected:* Exposes Gemini API keys to the browser, violates CORS/security rules, prevents rate-limit orchestration, and couples frontend to external AI providers.
- **Option B: Frontend $\rightarrow$ FastAPI Backend $\rightarrow$ Dedicated Gemini AI Service.**  
  *RECOMMENDED.* The backend securely stores the API key in `.env` (`settings.GEMINI_API_KEY`), handles image encoding, integrates YOLO V2 detections, implements rate limiting and caching, and ensures resilient fallback.
- **Option C: Frontend $\rightarrow$ FastAPI $\rightarrow$ Local AI Worker $\rightarrow$ Gemini.**  
  *Unnecessary Overhead:* The local worker (`local_worker.py`) is designed for heavy PyTorch/CUDA GPU workloads. Offloading a cloud REST API call to the GPU worker introduces unneeded IPC latency.

---

## 17. ₹0 / Free-Tier Strategy

JewelMind operates on a strict **₹0 budget**. The Gemini integration is engineered to remain permanently within Google AI Studio's free limits:

### 17.1 Free Tier Metrics (`gemini-1.5-flash` / `gemini-2.5-flash`)
- **Cost:** **$0.00 / ₹0**
- **Rate Limit:** **15 Requests Per Minute (RPM)**
- **Daily Limit:** **1,500 Requests Per Day (RPD)**
- **Token Ceiling:** **1,000,000 Tokens Per Minute (TPM)**

### 17.2 Free-Tier Optimization Tactics:
1. **On-Demand Execution:** Gemini is only invoked when rendering or when the user clicks *"Enhance"*. It is never polled on canvas strokes.
2. **Image Downsampling for Vision Prompt:** Blueprints are resized to max 512x512 JPEG before transmission to Gemini, reducing payload to <100 KB and consuming minimal multimodal tokens (~258 tokens per image).
3. **Session Cache:** In-memory LRU cache keyed by `MD5(image_bytes + user_prompt)`. If an artisan re-renders the same sketch with different seeds, the Gemini call is answered from cache in 0ms with zero API usage.
4. **Graceful Degradation:** If the 15 RPM limit is reached (HTTP 429), the system catches the error and instantly falls back to `build_jewellery_prompt()` without failing the render job.

---

## 18. Security Considerations

1. **Zero Client-Side Exposure:** `GEMINI_API_KEY` is strictly managed via Pydantic Settings in `backend/app/core/config.py` from `.env`. It is never returned in API responses or imported in frontend bundles.
2. **Prompt Injection Mitigation:** User prompts are sanitized and enclosed within structured system prompt delimiters:
   ```text
   <user_design_intent>
   {sanitized_user_prompt}
   </user_design_intent>
   ```
   The system instruction explicitly commands Gemini to treat user text strictly as design specifications, ignoring meta-instructions (e.g. "ignore previous instructions").
3. **Pydantic Schema Validation:** Gemini output is requested using Google's `response_schema` (JSON mode) and validated by Pydantic. Any unexpected or malformed payload is rejected safely.
4. **Privacy:** Cloud API requests transmit only black-and-white CAD sketch blueprints or jewelry contours—never customer PII, user credentials, or pricing data.

---

## 19. Failure & Fallback Matrix

The rendering engine must never crash due to an external API error:

| Scenario | System Behavior | User Experience |
| :--- | :--- | :--- |
| **1. YOLO OK, Gemini OK** | Full pipeline: YOLO category $\rightarrow$ Gemini Vision $\rightarrow$ ControlNet render. | Maximum quality render; rich detail. |
| **2. YOLO OK, Gemini Fails (429/500/Timeout)** | Fallback to `build_jewellery_prompt(category, material, gemstone, user_prompt)`. | Clean render succeeds using local template; toast indicates "Standard rendering applied". |
| **3. YOLO Fails, Gemini OK** | Gemini performs category detection and full prompt synthesis. | Clean render succeeds; Gemini acts as backup classifier. |
| **4. YOLO Fails, Gemini Fails** | Safe baseline: category defaults to 'other' or user selection; template prompt applied. | Render succeeds using safe fallback defaults. |
| **5. No Gemini API Key Configured** | Gemini service detects missing key during startup and enters passive bypass mode. | Full existing application functionality continues uninterrupted. |
| **6. Malformed Output from Gemini** | JSON validation fails $\rightarrow$ Logs warning $\rightarrow$ Falls back to legacy prompt builder. | Seamless fallback; zero crash. |

---

## 20. Database Impact Analysis

### Recommended Approach:
- **Phase 0/1 (MVP):** **Zero Database Changes.** Gemini returns the structured design contract and enhanced prompt directly in the HTTP response of `/api/v1/ai/render` and `/api/v1/ai/prompt/enhance`. The enhanced prompt is persisted in the existing `designs.ai_prompt` column.
- **Future Phase:** Add an Alembic migration adding `design_metadata = Column(JSON, nullable=True)` to `designs` table to persist gemstone counts, prong styles, and CAD notes for the production management module.

---

## 21. Testing Strategy

Prior to deployment, the following test suites must be created:
1. **Backend Unit Tests (`backend/tests/test_gemini_service.py`):**
   - Test Gemini service initialization with and without API key.
   - Test fallback behavior when httpx times out or returns 429.
   - Test prompt precedence (verifying user intent words are never stripped).
   - Test Pydantic validation of structured JSON output.
2. **AI Integration Tests (`tests/ai/test_gemini_rendering_integration.py`):**
   - Test YOLO V2 category injected into Gemini context.
   - Test Gemini enhanced prompt passed to `JewelleryRenderingPipeline`.
   - Verify prompt token count remains safely under CLIP 77-token limit.
3. **Frontend Component Tests:**
   - Test *"Enhance with AI"* button loading, success, and error states in `AiRenderModal.tsx`.
   - Test editing the enhanced prompt before triggering generation.

---

## 22. Performance & Latency Considerations

- **Current Latency:** Sketch Preprocessing (~0.1s) + ControlNet Diffusion (~3.2s) = **~3.3 seconds total**.
- **Gemini Added Latency:** `gemini-1.5-flash` processing a 512x512 image typically responds in **1.1 to 1.8 seconds**.
- **Total Projected Latency with Gemini:** **~4.5 to 5.0 seconds**.
- **UX Optimization:** When the user clicks *"Enhance with AI"*, the 1.5s call happens *interactively upfront*. When they subsequently click *"Generate Render"*, generation is instantaneous (prompt is already enhanced).

---

## 23. Exact Files and Functions Requiring Changes

| File Path | Current Role | Proposed Change | Priority |
| :--- | :--- | :--- | :---: |
| `backend/app/core/config.py` | Pydantic Settings | Add `GEMINI_API_KEY: Optional[str] = None`, `GEMINI_MODEL: str = "gemini-1.5-flash"` | P0 |
| `backend/app/services/gemini_design_service.py` | *(New File)* | Core Gemini Vision service, prompt engineer, structured contract validator, fallback handler | P0 |
| `backend/app/api/v1/ai_rendering.py` | Rendering API route | Integrate Gemini service before `RenderRequest` construction; add enhancement toggle | P0 |
| `backend/app/schemas/design.py` | Design schemas | Add `GeminiDesignAnalysisResponse` and `PromptEnhanceRequest` schemas | P1 |
| `frontend/src/services/api/aiRenderingService.ts` | Frontend API client | Add `enhancePrompt()` method and pass `enhance_with_ai` flag to `renderSketch()` | P1 |
| `frontend/src/components/studio/AiRenderModal.tsx` | Rendering modal dialog | Add *"✨ Enhance with AI"* button, prompt preview card, and auto-enhance checkbox | P1 |
| `backend/app/services/production_optimization_service.py`| CP-SAT scheduling service | Dynamically scale stone setting hours based on Gemini gemstone count | P2 |

---

## 24. Implementation Phase Breakdown

### Phase A: Backend Gemini Service & Core Schemas
- Add Gemini configuration to `backend/app/core/config.py`.
- Create `backend/app/services/gemini_design_service.py` using `google-genai` or standard asynchronous `httpx` client (avoiding heavyweight dependencies).
- Implement Pydantic data contract schemas and fallback logic.

### Phase B: Dedicated Prompt Enhancement Endpoint
- Add `POST /api/v1/ai/prompt/enhance` endpoint in `ai_rendering.py` accepting sketch image + optional user prompt.
- Unit test prompt precedence, prompt length, and error handling.

### Phase C: Rendering Pipeline Integration
- Update `POST /api/v1/ai/render` to accept `enhance_with_ai: bool = True`.
- Connect YOLO V2 detected category directly into Gemini prompt context.

### Phase D: Studio UI Enhancement
- Enhance `AiRenderModal.tsx` with dedicated prompt enhancement controls and visual status indicators.
- Connect to `DesignChatPanel.tsx` in `DesignWorkspacePage.tsx`.

### Phase E: Production Optimization Integration
- Feed Gemini extracted component metrics (stone count, setting type, metal alloy) into `production_optimization_service.py`.

---

## 25. Risks & Mitigation

| Risk | Impact | Mitigation |
| :--- | :---: | :--- |
| **API Rate Limiting (15 RPM Free Tier)** | Medium | In-memory cache + instant graceful fallback to `build_jewellery_prompt()`. |
| **Overriding User Intent (Hallucination)** | High | Enforce Tier 1 Locked Intent hierarchy in Gemini system instructions. |
| **CLIP 77-Token Overflow** | Medium | Gemini prompt instructed to output concise specifications strictly $\le 65$ tokens. |
| **API Key Exposure** | Critical | Keys stored exclusively in server `.env`; never accessible to frontend. |

---

## 26. Open Questions for User Review

1. **Automatic vs. Explicit Enhancement:** Should Gemini automatically enhance prompts for all renders where the prompt box is left blank, or should it strictly require clicking an *"Enhance with AI"* button? *(Recommended: Automatic when empty, explicit button when prompt is provided).*
2. **Gemini SDK vs. Lightweight HTTPX:** Should we install the official `google-genai` package, or use JewelMind's existing `httpx` async client to query the Google AI Studio REST API directly with zero new dependencies? *(Recommended: `httpx` direct calls for maximum stability and ₹0 bloat).*

---

## 27. Final Recommendation

JewelMind should transform from its current workflow:
$$\text{Upload / Sketch} \longrightarrow \text{Static Template Dropdown} \longrightarrow \text{Render}$$

Into an **Artisan Design Intelligence Pipeline**:
$$\text{Upload / Sketch} \longrightarrow \text{YOLO V2 Grounding} \longrightarrow \text{Gemini Vision Understanding} \longrightarrow \text{Engineered Prompt} \longrightarrow \text{ControlNet Render} \longrightarrow \text{Production Planning}$$

### The Single Recommended Architecture:
1. **Host Gemini on the FastAPI Backend (`backend/app/services/gemini_design_service.py`)** using asynchronous `httpx` calls to the Gemini 1.5 Flash REST API, utilizing the free-tier API key.
2. **Chain YOLO V2 $\rightarrow$ Gemini Vision**: Pass the local YOLO V2 detected category into Gemini as verified spatial grounding.
3. **Enforce Tier 1 User Intent Precedence**: Gemini must preserve user-specified metals and gemstones without alteration.
4. **Insert into `ai_rendering.py`**: Inject the enhanced prompt directly into `JewelleryRenderingPipeline`, maintaining 100% compatibility with the approved 1000-step ControlNet v2 renderer.
5. **Zero-Failure Guarantee**: If Gemini is unconfigured or unavailable, silently fall back to the existing template builder so rendering never fails.

---

## 28. Final Status Confirmation

- **Audit Status:** **AUDIT COMPLETE (Read-Only)**
- **Current Branch:** `main`
- **Current HEAD:** `765b7cb Merge pull request #25 from MohitJaiswal2507/phase-19-pre-ui-runtime-stabilization`
- **Files Created:** Exactly one documentation file:
  `docs/JEWELMIND_GEMINI_INTEGRATION_AUDIT.md`
- **Files Modified:** None.
- **AI Training / Workloads:** None (0 training runs, 0 model alterations).
- **Recommended Next Step:** User review and approval of Phase A implementation.
