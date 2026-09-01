# JewelMind — Phase 4: Sketch Upload & Supabase Storage

**Phase:** 4  
**Branch:** `phase-4-sketch-storage`  
**Previous Phase:** Phase 3 — Jewellery Design Management

## Objective

Turn the existing `Design.sketch_image_url` placeholder into a real, secure jewellery-sketch upload system using Supabase Storage.

The user must be able to:
1. Open a design.
2. Upload a jewellery sketch.
3. View the uploaded sketch.
4. Replace the sketch.
5. Delete the sketch.
6. Refresh the page and still see the sketch.

The backend must enforce authentication and design ownership.

## 1. Scope

Before changing anything, inspect and understand the existing JewelMind implementation. Read:
- `PLAN.md`
- `README.md`
- `docs/phases/PHASE_0_REPORT.md`
- `docs/phases/PHASE_1_REPORT.md`
- `docs/phases/PHASE_2_REPORT.md`
- `docs/phases/PHASE_3_REPORT.md`
- existing backend/frontend architecture
- existing Supabase and environment configuration
- Design model, APIs, services, pages and tests

Preserve existing architecture and conventions.

Do NOT implement AI image generation, Stable Diffusion/SDXL, ControlNet, LoRA, Hugging Face inference, GPU workers, AI queues, Redis/Celery, sketch-to-render generation, production planning, manufacturing prediction, or material/gemstone prediction. Those belong to later phases.

## 2. Git

Work only on:
`phase-4-sketch-storage`

Do not merge into `main`.
Do not commit automatically.
Stop after creating the report and wait for my review.

## 3. Supabase Storage

Use the existing JewelMind Supabase project.

Create/use a dedicated bucket:
`jewel-sketches`

If bucket creation or login requires my action, STOP and ask me to do it. Do not guess or expose credentials. Do not delete/reset existing data.

Architecture:

```text
User
  ↓
JewelMind Frontend
  ↓
FastAPI Backend
  ↓
Authentication + Design Ownership Check
  ↓
Supabase Storage
  ↓
Sketch File

Design.sketch_image_url
  ↓
Frontend Sketch Display
```

## 4. Storage Path

Use:
`jewel-sketches/{user_id}/{design_id}/{unique_filename}`

The backend must construct the path from the authenticated user ID, design ID, and generated safe filename. Never trust a complete storage path supplied by the frontend.

## 5. Supported Files

Allow:
- PNG
- JPEG/JPG
- WEBP

Reject unsupported formats such as PDF, SVG, GIF, ZIP, EXE, and arbitrary files.

Validate MIME type on the backend. Do not rely only on the filename extension.

Maximum size:
`10 MB`

Return an appropriate 4xx/413 error using existing JewelMind error conventions.

## 6. Authorization

Every sketch operation must:
1. Authenticate the user.
2. Find the Design.
3. Verify `design.user_id == current_user.id`.
4. Only then access Supabase Storage.

If the design does not belong to the user, preserve the Phase 3 safe `404 DESIGN_NOT_FOUND` behavior.

Do not reveal another user's design existence.

## 7. Upload API

Add:

`POST /api/v1/designs/{design_id}/sketch`

Use multipart/form-data.

Flow:

```text
Authenticate
→ Find Design
→ Verify Ownership
→ Validate MIME
→ Validate Size
→ Generate Safe Filename
→ Upload to Supabase Storage
→ Update Design.sketch_image_url
→ Return updated design/sketch information
```

Follow existing router/service conventions. Do not put all storage logic directly in the route.

## 8. Storage Service

Create a clean storage abstraction following existing architecture, for example:
`backend/app/services/storage_service.py`

The service should handle upload, deletion, and URL/reference handling as appropriate.

Keep storage logic separate from HTTP route logic and testable.

## 9. Replace Sketch

If a design already has a sketch:

```text
Validate New File
→ Upload New File
→ Confirm Upload
→ Update Database Reference
→ Delete Old Storage Object
```

Never delete the old valid sketch before the new upload succeeds.

If replacement fails, the old sketch must remain intact.

Avoid orphaned storage objects.

## 10. Delete Sketch API

Add:

`DELETE /api/v1/designs/{design_id}/sketch`

Requirements:
- authentication required
- ownership required
- delete storage object
- clear `Design.sketch_image_url`
- do not delete the Design
- handle missing sketch safely

## 11. Database

Inspect the Phase 3 Design model first.

Use the existing:
`Design.sketch_image_url`

Do not create duplicate columns.

Only create an Alembic migration if genuinely required. Never drop/reset existing users/designs.

If a migration is required, run and verify:
`alembic upgrade head`
`alembic current`

## 12. URL / Storage Reference

Keep compatibility with `sketch_image_url`.

Prefer a stable storage reference/path where appropriate instead of permanently storing a short-lived signed URL. If the current architecture requires public or signed URLs, document the decision and security implications.

Do not make private storage public merely to simplify development without a documented reason.

## 13. Environment Variables

Inspect existing `.env` and `.env.example` files first.

Add only variables actually required by the implementation.

Never hardcode:
- Supabase service-role key
- Supabase secret
- database password
- JWT secret
- access tokens
- API keys

Real secrets must remain in ignored `.env` files. Templates contain placeholders only.

Never print secret values in terminal output or reports.

## 14. Frontend Design Detail

Update the existing Design Detail page.

If no sketch:

```text
Sketch

[ Upload Sketch ]

PNG, JPG or WEBP
Maximum 10 MB
```

If a sketch exists:

```text
┌──────────────────────────┐
│       SKETCH IMAGE       │
└──────────────────────────┘

[ Replace Sketch ] [ Delete ]
```

Use the existing JewelMind visual language. Do not redesign the whole application.

## 15. Upload UX

Provide:
- file picker
- optional drag-and-drop if it fits cleanly
- selected file state
- uploading state
- success state
- error state
- prevention of duplicate submissions

Handle invalid file, oversized file, network failure, unauthorized request, server error and successful upload.

Use existing shadcn/ui notification/error patterns.

## 16. Frontend Validation

Validate file type and maximum 10 MB before upload.

Remember that frontend validation is not a security boundary; backend validation is mandatory.

## 17. Replace UX

The Replace action should use the upload interface.

After successful replacement:
- update displayed sketch
- update local state
- no forced full page reload

If replacement fails:
- preserve current sketch
- show useful error

## 18. Delete UX

Use an existing shadcn/ui confirmation pattern such as AlertDialog.

Message:

`Delete this sketch?`
`This action cannot be undone.`

After successful deletion:
- remove image from UI
- clear sketch state
- show upload/empty state

## 19. Tailwind CSS

Tailwind CSS is mandatory for layout, spacing, responsiveness, image sizing, upload area and states.

Do not introduce a large custom CSS layout system.

## 20. shadcn/ui

Continue using shadcn/ui and existing components where possible:
- Button
- Card
- Dialog
- AlertDialog
- Input
- Badge
- Progress
- Separator
- existing Toast/Sonner

Do not introduce Bootstrap, Material UI, Chakra UI, Ant Design, or another UI framework.

## 21. Responsiveness

Verify at:
- 375px
- 768px
- 1280px
- 1440px+

Ensure no horizontal overflow, usable controls, mobile-friendly dialogs, and safe handling of long filenames.

## 22. Frontend API Service

Follow the existing API service architecture. Do not scatter raw fetch calls through components.

Add typed service functions such as:
- `uploadSketch()`
- `deleteSketch()`

Use existing authentication handling and avoid `any`.

## 23. Backend Tests

Add tests for:

Authentication:
- unauthenticated upload → 401
- unauthenticated delete → 401

Ownership:
- own design upload → PASS
- another user's design upload → 404
- another user's design delete → 404

Valid files:
- PNG
- JPG/JPEG
- WEBP

Invalid files:
- unsupported MIME → 4xx
- >10MB → 413/4xx

Replacement:
- first upload
- second upload
- old object handled
- failed replacement preserves old sketch

Deletion:
- existing sketch deleted
- missing sketch handled safely
- Design remains after sketch deletion

Mock Supabase Storage in normal automated tests where appropriate. Do not require live Supabase network access for every unit test.

## 24. Frontend Tests

Verify:
- no-sketch state
- upload UI
- uploading state
- success state
- failure state
- existing sketch display
- replace flow
- delete confirmation
- delete success
- responsive layout

Maintain TypeScript strictness.

## 25. Manual End-to-End Test

After implementation verify:

```text
[ ] Login
[ ] Open Designs
[ ] Open an existing design
[ ] Upload PNG
[ ] Verify sketch appears
[ ] Refresh page
[ ] Verify sketch persists
[ ] Replace sketch
[ ] Verify new sketch appears
[ ] Delete sketch
[ ] Verify sketch disappears
[ ] Upload invalid file
[ ] Upload file over 10MB
```

If Supabase dashboard configuration is required, stop and ask me before proceeding.

## 26. UML

Update the existing UML documentation.

Add/update Sketch Upload sequence:

```text
User
  ↓
Frontend
  ↓
FastAPI
  ↓
Authentication
  ↓
Design Ownership Check
  ↓
Storage Service
  ↓
Supabase Storage
  ↓
Database
  ↓
Frontend
```

Keep diagrams consistent with actual implementation.

## 27. Documentation

Create:
`docs/phases/PHASE_4_REPORT.md`

Include:
1. Executive Summary
2. Objective
3. Existing Architecture Used
4. Supabase Storage Architecture
5. Bucket Configuration
6. Storage Path Convention
7. Backend Changes
8. API Endpoints
9. Authentication/Authorization
10. File Validation
11. Replacement Logic
12. Delete Logic
13. Frontend Changes
14. Tailwind Responsiveness
15. shadcn/ui Components
16. Testing
17. Manual Verification
18. UML Updates
19. Environment Variables
20. Files Created
21. Files Modified
22. Known Limitations
23. Future AI Integration
24. Commands Used
25. Final Validation Results

Clearly state:
`AI rendering is NOT implemented in Phase 4.`

## 28. Git Security

Verify:
- `.env`
- `backend/.env`
- `frontend/.env`

are ignored.

Verify no real credentials are in tracked files.

Search tracked files for credential patterns. There must be no real secrets committed.

## 29. Validation

Run the existing backend test suite.

Run frontend TypeScript/build validation.

If migration was changed:
`alembic upgrade head`
`alembic current`

Verify Phase 2 and Phase 3 functionality still works.

Do not modify tests simply to hide failures.

## 30. Completion Criteria

Phase 4 is complete only when:

```text
✓ Supabase Storage integrated
✓ jewel-sketches bucket configured
✓ Secure user/design storage path implemented
✓ Authentication enforced
✓ Design ownership enforced
✓ MIME validation implemented
✓ 10MB size validation implemented
✓ Sketch upload implemented
✓ Sketch replacement implemented
✓ Sketch deletion implemented
✓ Existing Design remains intact after sketch deletion
✓ Responsive frontend implemented
✓ Tailwind used
✓ shadcn/ui used
✓ Backend tests pass
✓ Frontend TypeScript/build passes
✓ Security checks pass
✓ UML updated
✓ Documentation created
✓ No secrets committed
✓ Phase 4 report created
```

Do not claim PASS unless actually tested. If something requires my manual action, mark it:
`MANUAL VERIFICATION REQUIRED`

## 31. Phase Boundary

Do NOT start Phase 5.
Do NOT implement AI.
Do NOT implement rendering.
Do NOT implement production planning.
Do NOT implement GPU workers.
Do NOT implement Hugging Face inference.
Do NOT implement ControlNet.
Do NOT redesign the UI.

Stop after Phase 4.

## 32. Final Response

When finished, respond with:

```text
PHASE 4 COMPLETE

Branch:
phase-4-sketch-storage

Implemented:
- ...

Supabase Storage:
PASS / FAIL / MANUAL VERIFICATION REQUIRED

Upload:
PASS / FAIL

Replace:
PASS / FAIL

Delete:
PASS / FAIL

Backend Tests:
X/X

Frontend Build:
PASS / FAIL

Security:
PASS / FAIL

UML:
UPDATED / NOT UPDATED

Files Created:
- ...

Files Modified:
- ...

Known Issues:
- ...

Manual Verification:
- ...

Report:
docs/phases/PHASE_4_REPORT.md
```

Then STOP.

Do not commit or merge. I will review the Phase 4 report first, test the application, and decide whether the branch is ready to merge into `main`.

## Phase 4 End State

```text
                 JEWELMIND
                     |
                   User
                     |
                  Design
                     |
              ┌──────┴──────┐
              |             |
           Metadata       Sketch
                            |
                            v
                     Supabase Storage
                            |
                            v
                  sketch_image_url
                            |
                            v
                       UI Display
                            |
                            v
                 [Future AI Rendering]
```

The AI rendering system is intentionally NOT part of this phase.
