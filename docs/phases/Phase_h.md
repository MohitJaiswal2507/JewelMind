PHASE H — STUDIO & RENDER HISTORY
READ-ONLY AUDIT ONLY

IMPORTANT:
- Current branch: phase-h-studio-render-history
- Base branch: main
- Phase G Canva AI Workspace has already been merged into main.
- DO NOT modify any source code.
- DO NOT create new implementation files.
- DO NOT delete anything.
- DO NOT commit.
- DO NOT push.
- DO NOT merge.
- DO NOT retrain any AI model.
- DO NOT modify model weights or datasets.
- This phase is ONLY an architecture/functionality audit.
- STOP after producing the report.

==================================================
OBJECTIVE
==================================================

We are preparing Phase H of JewelMind:

"Studio & Render History"

Before implementing anything, perform a complete READ-ONLY audit of the existing Studio, render-history, design-version, comparison, storage, and production handoff functionality.

Do NOT assume anything exists or does not exist.

Inspect the ACTUAL current repository and report what is already implemented.

The goal is to avoid rebuilding functionality that already exists.

==================================================
1. CURRENT JEWELMIND FLOW
==================================================

Audit the current flow:

Design
  ↓
Canva Workspace
  ↓
Text / Doodle / Image
  ↓
Gemini / Design State
  ↓
Renderer
  ↓
Generated Render
  ↓
Studio
  ↓
Future Production

Verify exactly how data moves through this pipeline.

==================================================
2. STUDIO AUDIT
==================================================

Inspect the existing Studio implementation.

Find and inspect:

- Studio pages
- Studio components
- media grids
- media detail/inspector components
- render cards
- source-image cards
- comparison UI
- download functionality
- delete functionality
- open/edit functionality
- design metadata
- version-related UI
- API services
- backend endpoints
- database models/tables
- Supabase storage interactions

Determine what Studio can currently do.

Create a capability matrix:

| Capability | Exists | Partially Exists | Missing | Evidence |
|------------|--------|------------------|---------|----------|

Include:

- view generated renders
- view source images
- view doodles
- open render
- download render
- delete render
- compare images
- source → render relationship
- previous render → new render
- render history
- version numbering
- prompt history
- design state history
- category metadata
- material metadata
- gemstone metadata
- timestamps
- ownership/authentication
- continue editing
- return to Canva workspace
- send to Production

==================================================
3. DATABASE AUDIT
==================================================

Inspect the actual Supabase/Postgres schema.

Identify tables related to:

- designs
- sketches
- renders
- studio media
- AI outputs
- production
- users
- design versions
- source assets

For every relevant table report:

- table name
- primary key
- foreign keys
- ownership/user relationship
- design relationship
- storage URL/path
- created_at
- updated_at
- version fields
- parent/previous render relationship
- source relationship
- category
- prompt
- structured design state

Do NOT change the database.

==================================================
4. RENDER DATA FLOW
==================================================

Trace the actual render flow.

Start from:

DesignWorkspacePage

Follow the code into:

frontend rendering service
→ API request
→ backend ai rendering endpoint
→ renderer
→ storage
→ database
→ Studio

Document:

- where the render image is created
- where it is stored
- what database record is created
- how the record is associated with a design
- how the frontend retrieves it
- how Studio knows which design it belongs to

==================================================
5. TEXT → RENDER
==================================================

Audit whether Text → Render creates a persistent Studio/history record.

Test/read the actual implementation.

Determine:

- Is the original prompt stored?
- Is the enhanced Gemini prompt stored?
- Is the final user-approved prompt stored?
- Is the design state stored?
- Is the generated image stored?
- Is category stored?
- Is material stored?
- Is gemstone stored?
- Is render version stored?
- Is previous render relationship stored?

Do not assume.

==================================================
6. DOODLE → RENDER
==================================================

Audit:

Doodle
→ canvas image
→ render
→ Studio

Determine whether the original doodle is preserved and linked to the resulting render.

Determine whether:

Doodle A
→ Render A

can be distinguished from:

Doodle B
→ Render B

without relying on filenames or timestamps alone.

==================================================
7. IMAGE → RENDER
==================================================

Audit:

Uploaded jewellery photo
→ Gemini/design understanding
→ render
→ Studio

Determine whether the original uploaded image is preserved and linked to its generated render.

The relationship should ideally support:

Source Image
     ↓
Render V1
     ↓
Render V2
     ↓
Render V3

But DO NOT assume this exists.

Report actual implementation.

==================================================
8. ITERATIVE REDESIGN
==================================================

Audit the current implementation for:

Render A
→ user says "Change gold to platinum"
→ Render B

Determine:

- Does Render B know Render A?
- Is previous_render_url stored?
- Is there a database relationship?
- Can Studio display A and B as versions?
- Can the user return to A?
- Can the user continue from B?
- Is the prompt/change instruction stored?
- Is the design state before/after stored?

==================================================
9. VERSIONING
==================================================

Determine whether JewelMind currently has real render versioning.

Look specifically for:

- version_number
- parent_render_id
- previous_render_id
- source_media_id
- generation_id
- iteration_id
- revision_id

If no proper versioning exists, document what currently exists and what would be needed.

Do NOT implement it yet.

==================================================
10. COMPARISON MODE
==================================================

Audit the current comparison system.

Expected conceptual modes:

A. Source | Render

B. Doodle | Render

C. Uploaded Image | Render

D. Previous Render | New Render

Determine which are already implemented.

Verify:

- comparison slider
- side-by-side mode
- render-only mode
- source-only mode
- correct asset pairing
- no stale asset pairing

==================================================
11. STALE STATE / OWNERSHIP
==================================================

This is extremely important because Phase G fixed several stale-state bugs.

Audit whether Studio can accidentally display:

Design A render
under Design B.

Test/read the code for:

- design ID filtering
- user ID filtering
- stale React state
- cached media
- race conditions
- rapid navigation
- async fetch cancellation
- incorrect query keys

Conceptually test:

Design A
→ Studio

then quickly:

Design B
→ Studio

Verify whether the final Studio state strictly belongs to Design B.

Do not modify anything.

==================================================
12. AUTHORIZATION / SECURITY
==================================================

Audit Studio access control.

Verify that a user cannot access another user's:

- designs
- renders
- source images
- Studio media
- production records

Inspect:

- backend authorization
- Supabase RLS
- API ownership checks
- storage access rules
- signed URLs if applicable

Do not change security rules during this audit.

==================================================
13. STORAGE AUDIT
==================================================

Inspect Supabase Storage usage.

Determine:

- bucket names
- folder/path structure
- source image storage
- sketch storage
- render storage
- deletion behavior
- orphan files
- duplicate files
- public vs signed URLs
- ownership/path isolation

Report potential orphan-storage problems.

Do NOT delete anything.

==================================================
14. PRODUCTION HANDOFF
==================================================

Inspect whether Studio already supports:

Approved Render
    ↓
Production

Determine exactly what exists.

Check:

- production creation
- source render reference
- design ID
- production ID
- approval state
- material information
- jewellery category
- production status

Do not implement Production changes yet.

==================================================
15. UI/UX AUDIT
==================================================

Inspect the current Studio visually and structurally.

Check:

- desktop
- tablet
- mobile
- responsive grid
- empty states
- loading states
- error states
- skeleton states
- image aspect ratios
- overflow
- large image handling
- metadata presentation
- action buttons
- navigation back to Canva
- comparison UX

Identify obsolete UI left over from older JewelMind versions.

Especially verify that the old:

"Atelier Generative Diffusion & Design Intelligence Suite"

does NOT reappear in Studio/Card flows.

==================================================
16. PERFORMANCE AUDIT
==================================================

Read-only inspection of:

- image loading
- thumbnails
- lazy loading
- pagination
- infinite scroll
- API query sizes
- unnecessary duplicate requests
- Supabase queries
- render history size handling

Do not optimize yet.

Report likely bottlenecks.

==================================================
17. EXISTING TEST COVERAGE
==================================================

Find all tests related to:

- Studio
- renders
- designs
- media
- comparisons
- storage
- production
- Canva workspace

Run existing relevant tests if they are safe and do not modify files.

Report:

Backend:
X passed / X failed

Frontend:
X passed / X failed

Build:
PASS / FAIL

Do not create or modify tests during this audit.

==================================================
18. MODEL INTEGRITY
==================================================

Confirm that this audit does NOT modify:

- YOLO V2
- ControlNet V2 1000-step
- SD1.5
- Appearance LoRA
- datasets
- checkpoints

No GPU training.

==================================================
19. PHASE H GAP ANALYSIS
==================================================

Based ONLY on the actual repository, classify every Studio capability into:

A. Already complete
B. Partially complete
C. Missing
D. Buggy
E. Needs UX improvement

Then propose the minimum implementation scope for Phase H.

Do NOT propose unnecessary rewrites.

==================================================
20. RECOMMENDED PHASE H ARCHITECTURE
==================================================

Only after auditing the current implementation, propose a target architecture.

The desired conceptual model is:

Design
 ├── Source Assets
 │    ├── Doodle
 │    └── Uploaded Image
 │
 └── Render Versions
      ├── V1
      ├── V2
      ├── V3
      └── Final

Each render should ideally know:

- design_id
- source_asset_id
- previous_render_id
- version_number
- prompt
- negative_prompt
- structured_design
- category
- material
- gemstone
- renderer metadata
- created_at
- storage location

BUT:

Do not implement this architecture during the audit.

First compare it against what actually exists.

==================================================
21. FINAL REPORT
==================================================

Create:

docs/PHASE_H_STUDIO_RENDER_HISTORY_AUDIT.md

The report MUST contain:

1. Executive summary
2. Current Studio architecture
3. Current render architecture
4. Database schema findings
5. Storage findings
6. Text → Render persistence
7. Doodle → Render persistence
8. Image → Render persistence
9. Iterative redesign persistence
10. Versioning findings
11. Comparison findings
12. Stale-state findings
13. Security findings
14. Production handoff findings
15. UI/UX findings
16. Performance findings
17. Existing test results
18. Model integrity
19. Complete gap matrix
20. Recommended Phase H implementation scope
21. Files likely to change in Phase H
22. Risks and migration concerns

IMPORTANT:
Every claim must be based on the actual repository.

Do not fabricate functionality.
Do not claim a feature works unless you verified it.
Do not silently redesign existing architecture.
Do not modify source code.

STOP after generating the report.

FINAL GIT STATE:
- No commit
- No push
- No merge
- No source-code changes
- Only the audit report may be created