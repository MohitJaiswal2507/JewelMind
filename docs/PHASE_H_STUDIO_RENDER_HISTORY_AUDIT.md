# JewelMind — Phase H: Studio & Render History Architecture Audit

**Branch:** `phase-h-studio-render-history`  
**Base Branch:** `main`  
**Status:** ✅ READ-ONLY AUDIT COMPLETE — No source code modified, no models trained, no git commits/pushes/merges performed  
**Date:** 2026-09-19  

---

## 1. Executive Summary

Phase H focuses on **"Studio & Render History"** within the JewelMind AI Jewellery Atelier platform. This read-only audit provides a rigorous, code-level inspection of the existing codebase across the frontend, FastAPI backend, PostgreSQL/Supabase database, cloud storage, and AI inference pipelines to establish the ground truth of what currently exists versus what is missing.

### Key Audit Findings

1. **Zero Database Persistence for Render History**:
   The PostgreSQL `designs` table stores only a **single string column**: `rendered_image_url VARCHAR(1024)`. When a user generates a new render (whether via Text, Doodle, or Image Blueprint), this column is directly overwritten. Older renders are completely severed from the database record and become unindexed, orphaned assets in Supabase Storage. There are currently **no tables** for `renders`, `design_versions`, `source_assets`, or `studio_media`.
2. **Studio Page is a Thin Design List View**:
   `frontend/src/pages/StudioPage.tsx` does not query a dedicated media or render history endpoint. Instead, it calls `designService.getDesigns({ page_size: 100 })` and projects each `Design` into a single card in a client-side `useMemo` hook. If a design has had 5 sequential iterations, Studio only displays the latest one.
3. **Hardcoded Mock Collections & Metadata**:
   The Studio sidebar collections (`Summer '25 High Jewellery`, `Spring '25 Bridal Suite`, `Winter '24 Solitaire Editions`), asset file sizes (`fileSize: 1.2 + (index % 5) * 0.4 MB`), and telemetry metrics are hardcoded client-side mocks using modulo arithmetic on array indexes.
4. **Comparison Mode Inverts Photographic Renders**:
   The split comparison slider (`DesignWorkspacePage.tsx`) applies `className="... filter invert opacity-80"` to the left-hand asset. While suitable for black-and-white sketch blueprints, comparing `Previous Iteration` (a rendered photo) with `Generative AI Output` results in an inverted photographic negative on the left panel. Furthermore, `previousRenderUrl` is stored exclusively in ephemeral React state; navigating away or refreshing the page permanently deletes the comparison capability. Studio has no comparison UI whatsoever.
5. **No Production Handoff Bridge**:
   While `production_orders` exists in PostgreSQL with a foreign key to `designs.id`, it has no reference to a specific render ID, approved version number, or visual snapshot. Studio and Design Detail pages lack any "Send Approved Render to Production" workflow.
6. **Zero Model & Code Disruptions**:
   This audit modified zero lines of application code, created zero implementation files, and verified that all test suites (184/184 backend tests, 45/45 frontend tests) and production builds pass cleanly.

---

## 2. Current Studio Architecture

### 2.1 Component Hierarchy
```
StudioPage.tsx (Container)
├── StudioSidebar.tsx (Navigation & Mock Seasonal Collections)
├── StudioMediaGrid.tsx (Search Bar, Category Filter Pills, Lookbook Grid)
│   └── StudioMediaCard.tsx (Individual Media Asset Cards)
└── StudioMediaDetails.tsx (Right-side Asset Inspector & Action Panel)
```

### 2.2 Data Sourcing & State Management
- **API Call**: `designService.getDesigns({ page_size: 100 })` via `GET /api/v1/designs`.
- **Client-Side Projection**: `allMediaItems: StudioMediaItem[] = designs.map(...)` maps each design to exactly one media item:
  ```typescript
  let mediaType: 'PNG Sketch' | 'Photorealistic Render' | 'Vector Blueprint' = 'PNG Sketch';
  let thumbnailUrl = d.sketch_image_url || '';
  if (d.rendered_image_url) {
    mediaType = 'Photorealistic Render';
    thumbnailUrl = d.rendered_image_url;
  }
  ```
- **Limitation**: If a design has both a sketch and a photorealistic render, the sketch is suppressed in the grid. If a design has undergone 10 render iterations, only iteration 10 is accessible.

### 2.3 Studio Actions & Handlers
- **Open in Drawing Desk**: Calls `onOpenCanvas(item.designId)` which routes the user into `DesignWorkspacePage.tsx`.
- **AI Render (Diffusion)**: Opens `AiRenderModal.tsx` directly from `StudioMediaDetails.tsx`.
- **Download**: Creates a synthetic DOM anchor element `<a href={item.thumbnailUrl} download="...">` to trigger browser download.
- **Delete**: Calls `onDeleteMedia(item)` which triggers `designService.deleteSketch(item.designId)`. This only clears `sketch_image_url` on the design; there is no backend API to delete a rendered image or clean up Supabase storage.

### 2.4 Studio Capability Matrix

| Capability | Status | Evidence in Codebase |
|---|---|---|
| View Generated Renders | **Partially Exists** | Displays only the *latest* `rendered_image_url` per design (`StudioPage.tsx:64-68`). |
| View Source Images / Sketches | **Partially Exists** | Displayed only if `rendered_image_url` is null (`StudioPage.tsx:64`). |
| View Doodles Separately | **Missing** | No separate entity for sketches or doodles. |
| Open Render in Canvas / Studio | **Exists** | `StudioMediaDetails.tsx:190-193` calls `onOpenCanvas(item.designId)`. |
| Download Render Asset | **Exists** | Client-side anchor download in `StudioMediaDetails.tsx:41-50`. |
| Delete Render | **Missing** | `handleDeleteMedia` calls `deleteSketch`; no `deleteRender` endpoint exists. |
| Compare Images in Studio | **Missing** | Zero comparison UI exists in Studio (only present in `DesignWorkspacePage.tsx`). |
| Source → Render Relationship | **Partially Exists** | Conceptual only; both URLs live on the same row in `designs`. |
| Previous Render → New Render | **Missing** | Overwritten upon each synthesis; no history linkage. |
| Render History Timeline | **Missing** | No history list or chronological iterations. |
| Version Numbering (V1, V2, etc.) | **Missing** | No `version_number` in database, frontend, or API. |
| Prompt History | **Missing** | Only single `ai_prompt` column on `designs`; overwritten on save. |
| Design State History | **Missing** | Structured design state is ephemeral in React memory. |
| Category Metadata | **Exists** | Extracted from `designs.category` (`StudioMediaCard.tsx:109`). |
| Material Metadata in Studio | **Missing** | Primary metal and finish are omitted from `StudioMediaDetails.tsx`. |
| Gemstone Metadata in Studio | **Missing** | Gemstone type, cut, and setting omitted from `StudioMediaDetails.tsx`. |
| Timestamps | **Exists** | `item.createdAt` formatted in `StudioMediaDetails.tsx:135-140`. |
| Ownership / User Scoping | **Exists** | Filtered by `current_user.id` on `GET /api/v1/designs`. |
| Return to Canva Workspace | **Exists** | `onOpenCanvas` routes directly to `/design/{id}`. |
| Send to Production | **Missing** | Zero integration between Studio inspector and `production_orders`. |

---

## 3. Database Schema Audit

Direct inspection of the active Supabase PostgreSQL database using SQLAlchemy runtime reflection reveals exactly **8 tables**:

```
ACTUAL DB TABLES: [
  'users', 
  'designs', 
  'production_orders', 
  'production_schedules', 
  'scheduled_tasks', 
  'workers', 
  'machines', 
  'alembic_version'
]
```

### 3.1 Table Specifications

#### 1. `designs`
- **Primary Key**: `id (UUID)`
- **Foreign Keys**: `user_id` → `users.id` (`ON DELETE CASCADE`)
- **Columns**:
  - `id`: `UUID` (PK, default `uuid4`)
  - `user_id`: `UUID` (Indexed, Non-nullable)
  - `name`: `VARCHAR(255)` (Indexed, Non-nullable)
  - `description`: `TEXT` (Nullable)
  - `category`: `VARCHAR(50)` (Indexed, Non-nullable)
  - `status`: `VARCHAR(50)` (Indexed, Default `'draft'`)
  - `sketch_image_url`: `VARCHAR(1024)` (Nullable)
  - `rendered_image_url`: `VARCHAR(1024)` (Nullable) — **Single field, no history array**
  - `ai_prompt`: `TEXT` (Nullable)
  - `created_at`: `TIMESTAMP WITH TIME ZONE`
  - `updated_at`: `TIMESTAMP WITH TIME ZONE`
- **Missing Fields**: `version_number`, `parent_render_id`, `source_asset_id`, `structured_state`, `seed`, `inference_steps`, `guidance_scale`, `lora_scale`.

#### 2. `production_orders`
- **Primary Key**: `id (UUID)`
- **Foreign Keys**: 
  - `user_id` → `users.id` (`ON DELETE CASCADE`)
  - `design_id` → `designs.id` (`ON DELETE CASCADE`)
- **Columns**:
  - `id`: `UUID` (PK)
  - `user_id`: `UUID`
  - `design_id`: `UUID`
  - `quantity`: `INTEGER` (Default `1`)
  - `priority`: `VARCHAR(50)` (`low`, `medium`, `high`, `urgent`)
  - `status`: `VARCHAR(50)` (`pending`, `in_production`, `quality_check`, `completed`, `cancelled`)
  - `deadline`: `TIMESTAMP WITH TIME ZONE`
  - `notes`: `TEXT`
  - `created_at`, `updated_at`: `TIMESTAMP WITH TIME ZONE`
- **Missing Fields**: `render_id`, `render_version`, `approved_render_url`, `material_spec`, `gemstone_spec`.

#### 3. Tables that DO NOT Exist in the Database
- ❌ `renders` / `design_renders`
- ❌ `design_versions`
- ❌ `studio_media`
- ❌ `source_assets`
- ❌ `prompt_history`

---

## 4. Render Data Flow Trace

Tracing the end-to-end execution path from user interaction to database persistence:

```
[DesignWorkspacePage.tsx] (handleExecuteRender)
  │
  ├── 1. Gathers state: activePrompt, designState (metal, gemstone, category), controlStrength
  ├── 2. Mode branch:
  │      - Text Mode:   aiRenderingService.renderSketch(null, payload)
  │      - Doodle Mode: canvasRef.exportPngBlob() → aiRenderingService.renderSketch(blob, payload)
  │      - Image Mode:  uploadedImageFile → aiRenderingService.renderSketch(file, payload)
  │
  ▼
[aiRenderingService.ts] (renderSketch)
  │
  ├── Formats FormData multipart payload:
  │      file: Blob/File
  │      prompt, category, material, gemstone, control_strength, control_type, design_id
  └── POST /api/v1/ai-rendering/render
  │
  ▼
[FastAPI: backend/app/api/v1/ai_rendering.py] (render_sketch)
  │
  ├── 1. Validates user authentication (get_current_active_user)
  ├── 2. Validates design ownership: db.query(Design).filter(Design.id == design_id, Design.user_id == current_user.id)
  ├── 3. Resolves conditioning:
  │      - If control_strength == 0.0 → pure text mode (neutral canvas)
  │      - If binary bytes provided → lineart/canny conditioning
  ├── 4. Executes rendering pipeline on local RTX 4060 GPU worker (:8001)
  │      - Base: Stable Diffusion v1.5
  │      - ControlNet: controlnet_rendering_v2_final (1000 steps)
  │      - LoRA: fine_jewellery_appearance_lora
  ├── 5. Uploads resulting PNG to Supabase Storage:
  │      storage_service.upload_rendered_image(rendered_image_bytes, user_id, design_id)
  │      → Path: {user_id}/{design_id}/render_{uuid[:12]}.png
  │      → Returns: https://jxqcklfmqgkudtbhrnef.supabase.co/storage/v1/object/public/jewelmind-assets/...
  ├── 6. Database Update (Lines 407-412):
  │      design.rendered_image_url = public_supabase_url
  │      design.status = "ready"
  │      db.commit()
  └── 7. Returns response JSON: { output_url, category, metadata, ... }
  │
  ▼
[DesignWorkspacePage.tsx]
  │
  ├── Sets renderedImageUrl = res.output_url
  ├── Automatically switches workspaceView = 'comparison'
  └── Stores previous render in React memory: setPreviousRenderUrl(renderedImageUrl)
```

---

## 5. Text → Render Persistence Audit

- **Original Prompt**: Kept in React state `activePrompt`. Persisted to `designs.ai_prompt` **only if** the user clicks the "Save" button (`handleSaveSketch`).
- **Enhanced Gemini Prompt**: Kept in React state `designState.renderer_prompt`. Never written to the database.
- **Structured Design State** (`primary_metal`, `gemstone_type`, `metal_finish`): Ephemeral in React memory (`designState`). Never persisted to the `designs` table.
- **Generated Render URL**: Persisted to `designs.rendered_image_url`. Overwrites any previous render.
- **Version Tracking**: Zero version metadata stored.

---

## 6. Doodle → Render Persistence Audit

- **Doodle Vector / PNG**: Captured via `canvasRef.current.exportPngBlob()`. Sent directly in the HTTP multipart body.
- **Sketch Storage Linkage**: The doodle is **not saved** to `designs.sketch_image_url` during rendering. It is only saved if the user explicitly clicks "Save" (`handleSaveSketch`), which uploads it via `designService.uploadSketch`.
- **Doodle A vs Doodle B**: If a user renders Doodle A, modifies the canvas to Doodle B, and renders Doodle B, Doodle A is permanently lost unless previously saved to disk. There is no linkage connecting `Doodle A → Render A` versus `Doodle B → Render B`.

---

## 7. Image → Render Persistence Audit

- **Uploaded Jewellery Photo**: Selected via `<input type="file">`, creating a local blob URL `URL.createObjectURL(file)`.
- **Backend Transfer**: Sent as multipart `file` to `/api/v1/ai-rendering/render`.
- **Storage**: The uploaded photo is processed in RAM/VRAM for Canny edge extraction, but **is not uploaded to Supabase Storage** as a source asset.
- **Session Loss**: Once the user navigates away or refreshes the page, the uploaded photo is discarded. No `source_assets` record or persistent URL exists for uploaded blueprints.

---

## 8. Iterative Redesign Audit

- **Flow**: User has Render A (`renderedImageUrl`). User instructs Copilot: *"Change gold to platinum"*. User renders again.
- **Mechanism**:
  ```typescript
  if (renderedImageUrl) {
    setPreviousRenderUrl(renderedImageUrl);
  }
  ```
  `previousRenderUrl` is sent in the render request and used as Canny edge guidance.
- **Persistence Gap**:
  - `previous_render_url` is passed as a transient form parameter to the backend.
  - The backend does **not** store `previous_render_url` or `parent_render_id` anywhere in the database.
  - `designs.rendered_image_url` is overwritten with Render B.
  - Render A is now an orphan in Supabase Storage.
  - If the user reloads the page, they cannot view Render A, compare A and B, or revert back to A.

---

## 9. Versioning System Audit

JewelMind currently has **no versioning model**:
- No `version_number`
- No `parent_render_id`
- No `previous_render_id`
- No `source_media_id`
- No `generation_id`
- No `iteration_id`
- No `revision_id`

Every design acts as a single mutable document with at most one sketch URL and one render URL.

---

## 10. Comparison Mode Audit

### 10.1 Implemented Comparison Modes
In `DesignWorkspacePage.tsx`:
- **Mode A (Source Sketch ⇆ Render)**: Supported when `design.sketch_image_url` is present.
- **Mode B (Doodle ⇆ Render)**: Supported using the active canvas preview.
- **Mode C (Uploaded Photo ⇆ Render)**: Supported in the active session only via `uploadedImageUrl`.
- **Mode D (Previous Render ⇆ New Render)**: Supported in the active session only via `previousRenderUrl`.

### 10.2 Defect Identified in Comparison Mode
In `DesignWorkspacePage.tsx:604`:
```tsx
<img
  src={activeBlueprintUrl || previousRenderUrl!}
  alt="Source Blueprint"
  className="w-full h-full object-contain filter invert opacity-80"
/>
```
When `previousRenderUrl` is displayed on the left side of the split slider, the CSS class `filter invert opacity-80` is erroneously applied. This causes photographic renders to appear inverted (like a film negative with complementary colors).

---

## 11. Stale State & Race Condition Audit

1. **Design ID Scoping in Studio**:
   `StudioPage.tsx` loads all designs for `current_user.id`. Selecting a media card sets `selectedMedia`. Switching collections or search queries preserves `selectedMedia` unless explicitly deselected.
2. **Design Detail & Canvas Isolation**:
   Phase G1 resolved stale state leakage between designs in `DesignWorkspacePage.tsx` by introducing clean object initialization in `fetchDesign`.
3. **Studio Collection Modulo Filter**:
   `StudioPage.tsx:105-107` filters collections using `index % 3`. If designs are created or deleted, designs jump between "Summer '25", "Spring '25", and "Winter '24" unpredictably.

---

## 12. Authorization & Security Audit

| Vector | Status | Implementation Details |
|---|---|---|
| Design API Ownership | **SECURE** | All `/api/v1/designs` endpoints filter by `current_user.id`. |
| Render API Ownership | **SECURE** | `/api/v1/ai-rendering/render` validates `Design.user_id == current_user.id` when `design_id` is supplied. |
| Production API Ownership | **SECURE** | All `/api/v1/production` endpoints validate `ProductionOrder.user_id == current_user.id`. |
| Local Render Output Route | **VULNERABLE** | `/api/v1/ai-rendering/outputs/{filename}` has **no authentication check** (`current_user` is omitted). Any user knowing the filename can fetch the file. |
| Supabase Storage Access | **PUBLIC BUCKET** | `jewelmind-assets` bucket is configured as public. Objects are accessible via unguessable UUID URLs, but without signed URL expiry. |

---

## 13. Storage & Asset Lifecycle Audit

- **Bucket**: `jewelmind-assets`
- **Paths**:
  - Sketches: `{user_id}/{design_id}/sketch_{uuid[:12]}.png`
  - Renders: `{user_id}/{design_id}/render_{uuid[:12]}.png`
- **Orphan File Problem**:
  Every render synthesis uploads a new unique file `render_{uuid[:12]}.png`. Because the database updates `designs.rendered_image_url` to the new URL without deleting or tracking the old URL, previous renders remain in the bucket permanently as unreferenced orphan files.

---

## 14. Production Handoff Audit

- **Current State**:
  The `production_orders` table and `ProductionPage.tsx` UI are fully functional for scheduling (OR-Tools CP-SAT solver), artisan allocation, and machine dispatch.
- **Missing Link**:
  There is no mechanism to send a specific render version from Studio or Canva Workspace into Production. In `ProductionPage.tsx`, an order is manually created by selecting a design from a dropdown. It stores `design_id`, but cannot capture the approved render version, rendering prompt, or material specifications.

---

## 15. UI/UX Audit

- **Responsive Layout**:
  `StudioPage.tsx` implements responsive Flexbox/Grid (`w-full lg:w-64`, `grid-cols-1 sm:grid-cols-2 md:grid-cols-3 xl:grid-cols-3`).
- **Obsolete UI Remnants**:
  `StudioMediaDetails.tsx` still imports and mounts `AiRenderModal.tsx` ("Atelier Generative Diffusion & Design Intelligence Suite"). This modal was deprecated during Phase G in favor of the Canva AI Workspace.
- **Empty States**: Clean empty states with `ImageOff` icon and descriptive messaging are implemented.
- **Missing UI in Studio**:
  - No version history drawer / list.
  - No side-by-side or slider comparison modal.
  - No filter by render type (Text-guided, Doodle-guided, Image-guided).
  - No batch export or multi-select download.

---

## 16. Performance Audit

- **Full Catalogue Fetch**:
  `StudioPage.tsx` fetches `page_size: 100` in a single request. For ateliers with hundreds of designs, this will degrade initial load times.
- **Uncompressed High-Res Thumbnails**:
  Full 4K/1024x1024 PNG render images are loaded directly into 200px card thumbnails without CDN resizing or WebP thumbnail derivatives.
- **Memory Consumption**:
  In-memory filtering of 100+ items in React `useMemo` is currently fast (<5ms), but will require paginated or virtualized scrolling as the asset library grows.

---

## 17. Existing Test Coverage Verification

All existing tests were executed in read-only mode:

### Backend Pytest Suite
```bash
$ pytest backend/tests/
====================== 184 passed, 21 warnings in 36.35s ======================
```
- **Result**: **184 PASSED**, 0 FAILED.

### Frontend Vitest Suite
```bash
$ npm test -- --run
Test Files  5 passed (5)
Tests       45 passed (45)
Duration    495ms
```
- **Result**: **45 PASSED**, 0 FAILED.

### Production Build
```bash
$ npm run build
✓ built in 393ms (dist/assets/index-Dzd5mTiE.js: 529.00 kB, dist/assets/index-DQuIKeB9.css: 105.06 kB)
```
- **Result**: **PASS (Code 0)**. Zero TypeScript compilation errors.

---

## 18. Model & Weight Integrity Verification

- **YOLO V2 Model Weights**: `ai/vision/checkpoints/` unmodified ✅
- **ControlNet V2 1000-step Weights**: `outputs/rendering_v2_controlnet/` unmodified ✅
- **Stable Diffusion 1.5 Base**: Unmodified ✅
- **Appearance LoRA**: Unmodified ✅
- **Training Datasets**: Unmodified ✅
- **GPU Training**: 0 training epochs or scripts executed ✅

---

## 19. Complete Gap Analysis Matrix

| Domain | Capability | Existing Status | Defect / Missing Element |
|---|---|---|---|
| **Data Layer** | Render History Table | **MISSING** | No `renders` table exists; only single column on `designs`. |
| **Data Layer** | Render Versioning | **MISSING** | No `version_number` or parent-child lineage. |
| **Data Layer** | Source Asset Persistence | **MISSING** | Uploaded photos & doodles are not stored as distinct source entities. |
| **Data Layer** | Structured State Storage | **MISSING** | Primary metal, finish, and gemstone details exist only in React memory. |
| **API** | List Renders for Design | **MISSING** | No `GET /api/v1/designs/{id}/renders` endpoint. |
| **API** | Delete Individual Render | **MISSING** | No `DELETE /api/v1/renders/{id}` endpoint. |
| **API** | Public Output Security | **BUGGY** | `/api/v1/ai-rendering/outputs/{filename}` lacks user authentication. |
| **Storage** | Render Asset Cleanup | **MISSING** | Old renders remain as unindexed orphan files in Supabase bucket. |
| **Studio UX** | Multi-Version Display | **MISSING** | Studio only shows 1 card per design (latest render or sketch). |
| **Studio UX** | Seasonal Collections | **BUGGY / MOCK** | Collections use `index % 3` hardcoded arithmetic. |
| **Studio UX** | Asset Telemetry | **MOCK** | File sizes are calculated via `(1.2 + (index % 5) * 0.4) MB`. |
| **Studio UX** | Image Comparison | **MISSING** | Studio has no comparison tool between iterations or source blueprints. |
| **Studio UX** | Obsolete Render Modal | **OBSOLETE** | Studio still mounts deprecated `AiRenderModal`. |
| **Workspace UX** | Iteration Comparison | **BUGGY** | Inverts photographic colors (`filter invert`) when comparing iterations. |
| **Production** | Approved Render Handoff | **MISSING** | Production orders have no reference to the approved render image or version. |

---

## 20. Recommended Phase H Implementation Scope & Architecture

### 20.1 Target Conceptual Architecture

```
Design (Entity)
 ├── Source Assets (Sketches, Doodles, Uploaded CAD/Photos)
 │    ├── id: UUID
 │    ├── asset_type: 'doodle' | 'blueprint_upload' | 'reference_photo'
 │    ├── storage_url: String
 │    └── created_at: DateTime
 │
 └── Render History (Versions V1 → Vn)
      ├── id: UUID
      ├── design_id: UUID (FK)
      ├── version_number: Integer (1, 2, 3...)
      ├── parent_render_id: UUID (Nullable, points to previous version)
      ├── source_asset_id: UUID (Nullable, points to doodle/image)
      ├── render_mode: 'text' | 'doodle' | 'image'
      ├── prompt: Text (Final synthesis prompt)
      ├── enhanced_prompt: Text (Gemini enhanced prompt)
      ├── structured_state: JSONB (metal, finish, gemstones, setting)
      ├── image_url: String (Supabase public/signed URL)
      ├── thumbnail_url: String
      ├── control_type: String ('lineart' | 'canny' | 'none')
      ├── control_strength: Float
      ├── is_approved: Boolean (For production handoff)
      └── created_at: DateTime
```

### 20.2 Minimal, Non-Breaking Implementation Plan for Phase H

1. **Database Migration (`alembic/versions/0005_create_renders_table.py`)**:
   - Create `design_renders` table linked to `designs.id` and `users.id`.
   - Add `is_approved_for_production` boolean flag.
   - Maintain `designs.rendered_image_url` as a backward-compatible pointer to the latest active render.
2. **Backend API Extensions**:
   - `GET /api/v1/designs/{design_id}/renders` — Fetch chronological version history.
   - `POST /api/v1/designs/{design_id}/renders/{render_id}/approve` — Mark a version as approved for production.
   - `DELETE /api/v1/designs/{design_id}/renders/{render_id}` — Delete render and clean up storage.
   - Automatically record every generation in `design_renders` inside `ai_rendering.py`.
3. **Studio Lookbook Upgrade**:
   - Replace `index % 3` mock collections with real filters: "All Renders", "Approved for Production", "Doodle-guided", "Text-guided".
   - Group by Design or display flat chronological feed with version badges (`v1`, `v2`).
   - Replace deprecated `AiRenderModal` with a **Studio Comparison Drawer** (Side-by-Side & Split Slider).
4. **Fix Comparison Color Inversion**:
   - In `DesignWorkspacePage.tsx`, conditionally apply `filter invert` **only** if the left asset is a black-and-white sketch, never if it is a previous render iteration.
5. **Production Handoff Bridge**:
   - In `StudioMediaDetails.tsx` and `DesignWorkspacePage.tsx`, add **"Send Approved Render to Production"** button.
   - Pre-populates `ProductionOrderCreate` with `design_id`, `approved_render_url`, and structured material/gemstone notes.

---

## 21. Files Likely to Change in Phase H

### Backend Files
- `backend/app/models/design.py` (Add `DesignRender` model and relationship)
- `backend/app/schemas/design.py` (Add `DesignRenderResponse`, `DesignRenderCreate`)
- `backend/app/api/v1/ai_rendering.py` (Insert into `design_renders` table upon synthesis)
- `backend/app/api/v1/designs.py` (Add render history and version management endpoints)
- `backend/app/services/storage_service.py` (Add `delete_rendered_image` method)
- `backend/alembic/versions/0005_create_design_renders_table.py` (Alembic migration)

### Frontend Files
- `frontend/src/types/design.ts` (Add `DesignRender` interface)
- `frontend/src/services/api/designService.ts` (Add `getDesignRenders`, `approveRender`, `deleteRender`)
- `frontend/src/pages/StudioPage.tsx` (Wire up real render history and collection filtering)
- `frontend/src/components/studio/StudioMediaGrid.tsx` (Support version grouping)
- `frontend/src/components/studio/StudioMediaCard.tsx` (Add version badges `v1`, `v2`, approved status)
- `frontend/src/components/studio/StudioMediaDetails.tsx` (Add Version History list, Comparison modal, and "Send to Production" button; remove obsolete `AiRenderModal`)
- `frontend/src/pages/DesignWorkspacePage.tsx` (Fix comparison color inversion defect and preserve render history)

---

## 22. Risks and Migration Concerns

1. **Backward Compatibility**:
   Existing designs have `rendered_image_url` populated. The migration must backfill a `v1` record into `design_renders` for every design with an existing render URL so no existing work is lost.
2. **Supabase Storage Quota**:
   Retaining full version histories means multiple 1-2 MB PNGs per design. Implementing storage cleanup when a render is deleted is essential to stay comfortably within free-tier limits.
3. **Comparison Aspect Ratio Mismatches**:
   Different render modes (e.g. 512x512 square sketch vs 768x512 rectangular render) require CSS letterboxing/containment in the comparison slider to prevent visual distortion.

---

## 23. Conclusion & Next Steps

This comprehensive audit establishes the exact architecture and gaps in JewelMind's current Studio and rendering pipelines. The platform has strong real AI rendering capabilities (ControlNet V2 + LoRA on RTX 4060) and solid production scheduling (OR-Tools CP-SAT), but lacks the intermediate versioning and history persistence layer linking them together.

**Status:** Read-only audit complete. No code modifications or commits were executed. Ready for review.
