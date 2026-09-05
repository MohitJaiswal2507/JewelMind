# JEWELMIND — PRE-DEPLOYMENT FULL APPLICATION QA / EXPLORATORY TEST

## OBJECTIVE

Before JewelMind is deployed, perform a complete end-to-end manual QA and exploratory testing pass of the ENTIRE application.

You must actually RUN the application and USE IT THROUGH THE UI like a real user.

Do NOT simply inspect source code and say that features appear correct.

Your job is to:

1. Start all required JewelMind services.
2. Open the application in a browser.
3. Log in/register as necessary.
4. Navigate through every major section.
5. Actually execute every major user-facing function.
6. Use real jewellery images from:

C:\Users\usern\Downloads\Images

7. Test normal workflows.
8. Test edge cases.
9. Test invalid inputs where appropriate.
10. Test persistence by refreshing pages and restarting services where practical.
11. Test AI rendering using the actual trained AI pipeline.
12. Test YOLO jewellery component detection.
13. Test production management.
14. Test OR-Tools production optimization.
15. Test dashboard aggregation.
16. Look for UI bugs, backend bugs, API errors, broken workflows, incorrect states, data inconsistencies, crashes, and security/authorization issues.
17. DO NOT fix bugs during this phase unless a fix is absolutely necessary merely to continue testing.
18. Document every discovered issue in a detailed final report.
19. Do NOT commit, push, or merge anything.

This is a QA DISCOVERY phase, not an implementation phase.

==================================================
## IMPORTANT PROJECT RULES
==================================================

Project:
JewelMind

Current architecture:

Frontend:
React + TypeScript + Vite
Tailwind CSS
shadcn/ui

Backend:
Python + FastAPI

Database:
Supabase/PostgreSQL

Storage:
Supabase Storage

AI:
Local RTX 4060 AI Worker

Optimization:
OR-Tools CP-SAT

Known AI architecture:

Frontend
    ↓
FastAPI
    ↓
AI Worker :8001
    ↓
RTX 4060 CUDA
    ↓
YOLO / Stable Diffusion / ControlNet / LoRA
    ↓
Supabase Storage
    ↓
Frontend

The AI worker is intentionally separate from the backend Python environment.

DO NOT:
- retrain any model
- modify model weights
- delete model files
- delete datasets
- change the trained ControlNet
- change YOLO weights
- change the Appearance LoRA
- change Supabase data unnecessarily
- reset the database
- run destructive database commands
- commit changes
- push changes
- merge branches
- start Phase 15 deployment

This is strictly PRE-DEPLOYMENT QA.

==================================================
## SERVICES
==================================================

First inspect the project and determine the correct startup commands.

Known local architecture:

Backend:
http://127.0.0.1:8000

AI Worker:
http://127.0.0.1:8001

Frontend:
http://localhost:5173

Known backend startup from project root:

.\backend\.venv\Scripts\python.exe -m uvicorn --app-dir backend app.main:app --host 127.0.0.1 --port 8000 --reload

Known frontend:

cd frontend
npm run dev

Known AI worker:

C:\Users\usern\miniconda3\envs\tgpu\python.exe -m ai.workers.local_worker

IMPORTANT:

Use the existing tgpu environment for AI functionality.

Do not install a second GPU environment unless absolutely necessary.

Verify that the RTX 4060 is actually being used when AI inference is executed.

==================================================
## TEST DATA
==================================================

Use the jewellery images located at:

C:\Users\usern\Downloads\Images

First inspect the directory.

Determine:
- how many images exist
- image formats
- dimensions
- whether they are jewellery-related
- whether there are different jewellery categories

DO NOT modify the original images.

Use copies if necessary.

Try different images where appropriate, including different jewellery types.

Prefer realistic examples such as:
- rings
- earrings
- pendants
- necklaces
- bracelets
- bangles
- brooches
- other jewellery

Do not assume all files are valid.

Test appropriate images against appropriate features.

==================================================
## TEST PHILOSOPHY
==================================================

Act like a real user.

Do not only click buttons once.

For every major feature ask:

- Does the UI open?
- Does the UI display correctly?
- Does the action actually execute?
- Is loading state shown?
- Is success state shown?
- Is error state handled?
- Does the backend receive the request?
- Does the database change correctly?
- Does Supabase storage contain the expected asset?
- Does the result remain after refresh?
- Does the result remain after restarting the backend?
- Does the UI display the correct data?
- Are there console errors?
- Are there failed network requests?
- Are there unexpected 4xx/5xx responses?
- Does the feature work with realistic data?
- Does it fail gracefully with invalid data?

Record evidence for every failure.

==================================================
# TEST 1 — APPLICATION STARTUP
==================================================

Start:

1. Backend
2. AI Worker
3. Frontend

Verify:

- all processes start successfully
- no startup exceptions
- frontend loads
- backend health endpoint works
- AI worker starts successfully
- CUDA is available
- RTX 4060 is detected
- no missing dependency errors

Record:
- startup time
- warnings
- exceptions
- console errors

==================================================
# TEST 2 — AUTHENTICATION
==================================================

Test:

### Registration

Create a test user.

Verify:
- valid registration works
- duplicate email is rejected correctly
- invalid email rejected
- weak/invalid password behavior
- empty fields
- loading state
- success state
- error state

### Login

Test:
- valid credentials
- wrong password
- unknown account
- empty credentials

Verify:
- correct redirect
- token handling
- authenticated state
- logout

### Session

After login:
- refresh browser
- navigate between pages
- verify session remains valid

Logout:
- verify private pages cannot be accessed

Record any authentication bugs.

==================================================
# TEST 3 — DASHBOARD
==================================================

Open Dashboard.

Verify all dashboard sections.

Test:

- KPI cards
- active designs
- AI rendering counts
- production order counts
- artisan capacity
- workshop utilization
- on-time delivery
- quick actions
- recent AI renders
- component detection widget
- production overview
- deadline tracker
- analytics
- latest optimization schedule

Verify:

- numbers are realistic
- no NaN
- no undefined
- no negative impossible values
- no broken charts
- no stale data after creating records

Create data in later tests and return to Dashboard.

Verify dashboard updates correctly.

==================================================
# TEST 4 — DESIGN MANAGEMENT
==================================================

Create multiple designs.

Test:

- create design
- title
- category
- description
- material
- gemstone if available
- save
- open
- edit
- delete
- cancel delete
- search
- filters if available

Test multiple categories:

- ring
- earring
- pendant
- necklace
- bracelet
- bangle
- other

Verify:

- data persists after refresh
- correct design opens
- deleted design disappears
- unrelated designs are not affected

==================================================
# TEST 5 — CANVAS / SKETCH STUDIO
==================================================

Open a design canvas.

Actually use the canvas.

Test:

- brush
- eraser
- line
- rectangle
- ellipse
- symmetry
- grid
- undo
- redo
- clear
- zoom
- drawing
- saving

Create a meaningful jewellery sketch.

Use different tools together.

Test:

1. draw
2. undo
3. redo
4. zoom
5. save
6. refresh
7. reopen

Verify sketch remains available.

Test Save Sketch.

Verify:
- PNG is generated
- upload succeeds
- Supabase asset exists
- correct design association
- correct user association
- UI displays saved asset

==================================================
# TEST 6 — REAL JEWELLERY IMAGE DATA
==================================================

Use images from:

C:\Users\usern\Downloads\Images

For appropriate features:

- upload images
- inspect images
- use them in the relevant workflow
- verify accepted formats
- verify unsupported files are rejected
- test reasonably large images if present

DO NOT modify originals.

Document:
- filename
- dimensions
- format
- feature tested
- result

==================================================
# TEST 7 — AI PHOTOREALISTIC RENDERING
==================================================

THIS IS A CRITICAL TEST.

Actually perform a real AI rendering request from the UI.

Do NOT mock it.

Use a saved jewellery sketch.

Test at least several categories where possible:

- ring
- earring
- pendant
- necklace
- bracelet/bangle

Use realistic material/gemstone combinations.

Verify the complete pipeline:

UI
↓
Frontend API
↓
FastAPI
↓
AI Worker :8001
↓
RTX 4060 CUDA
↓
Stable Diffusion
↓
JewelMind ControlNet
↓
Appearance LoRA
↓
Generated image
↓
Supabase Storage
↓
Frontend

Verify:

- request starts
- loading UI works
- GPU inference occurs
- no timeout/crash
- generated image exists
- output is valid
- output is displayed
- output is persisted
- output URL is valid
- refreshing page still shows output
- backend restart still preserves output
- Dashboard sees render
- Studio sees render

Test:
- normal generation
- different category
- different material
- different gemstone
- different control strength if exposed
- different steps if exposed
- seed behavior if exposed

DO NOT change model weights.

Record:
- inference time
- device
- resolution
- model used if visible
- any warnings
- any CUDA errors
- generated output path/URL
- whether output survives refresh/restart

==================================================
# TEST 8 — YOLO COMPONENT DETECTION
==================================================

Actually run component detection.

Use:
- saved jewellery sketches
- appropriate jewellery images from Downloads\Images

Test multiple jewellery categories.

Verify:

- request starts
- loading state
- detection completes
- bounding boxes/masks display
- confidence values display
- component names are correct
- visualization is usable
- no crashes

Test:
- valid jewellery image
- simple jewellery image
- complex jewellery image
- image with little/no jewellery if available

Verify graceful behavior for poor inputs.

Confirm YOLO uses the existing trained JewelMind model.

DO NOT retrain.

==================================================
# TEST 9 — AI RENDER + YOLO COMBINED WORKFLOW
==================================================

Perform the actual intended workflow:

1. Create design
2. Draw jewellery sketch
3. Save sketch
4. Generate AI photorealistic rendering
5. View rendering
6. Run component detection
7. View detected components
8. Return to dashboard
9. Confirm render/detection-related data remains available

This is one of the most important capstone workflows.

Record every failure.

==================================================
# TEST 10 — STUDIO / MEDIA
==================================================

Test:

- media grid
- search
- asset selection
- media inspector
- metadata
- download
- delete
- open asset
- rendered images
- sketches

Verify:

- correct assets belong to correct designs
- deleted assets disappear
- UI does not show stale records
- broken image URLs are handled
- refresh maintains state

==================================================
# TEST 11 — PRODUCTION MANAGEMENT
==================================================

Test production section.

### Production Orders

Create multiple orders.

Test:
- create
- edit if available
- status
- priority
- quantity
- due date
- design association
- delete

Create different priorities:

- Urgent
- High
- Medium
- Low

Create multiple orders.

### Workshop Artisans

Test:
- create artisan
- edit
- availability
- skills
- delete
- invalid inputs

Use different skills.

### Workshop Machinery

Test:
- create machine
- type
- availability
- delete
- invalid inputs

Verify relationships and UI updates.

==================================================
# TEST 12 — OR-TOOLS PRODUCTION OPTIMIZATION
==================================================

THIS IS A CRITICAL BUSINESS FEATURE.

Create realistic production data first.

Then run:

AI Optimization & Schedule

Test:

- planning horizon
- solver time limit
- schedule name
- optimize
- saved schedule history
- schedule details
- Gantt chart
- artisan grouping
- machine grouping
- order grouping
- task modal
- KPIs
- makespan
- utilization
- overdue indicators
- infeasibility behavior

Verify hard constraints:

### Precedence

Casting
→ Stone Setting
→ Polishing
→ Finishing

Verify no task starts before its predecessor finishes.

### Worker overlap

Verify an artisan is not assigned overlapping tasks.

### Machine overlap

Verify a machine is not assigned overlapping tasks.

### Skill eligibility

Verify workers without required skills are not assigned inappropriate operations.

### Machine eligibility

Verify operations requiring specific machinery are assigned appropriately.

### Horizon

Verify tasks remain within planning horizon where feasible.

Test:

- feasible schedule
- multiple orders
- multiple artisans
- multiple machines
- constrained resources
- infeasible situation if practical

Verify graceful infeasibility handling.

==================================================
# TEST 13 — SCHEDULE PERSISTENCE
==================================================

After generating an optimization schedule:

1. Refresh page.
2. Navigate away.
3. Return.
4. Open saved schedule.
5. Restart backend.
6. Return to UI.
7. Verify schedule remains.

Test schedule deletion.

Verify only intended schedule is removed.

==================================================
# TEST 14 — MULTI-TENANT SECURITY
==================================================

This must be tested carefully.

Create two users:

User A
User B

Create data under User A:

- designs
- sketches
- renders
- production orders
- workers
- machines
- schedules

Login as User B.

Verify User B cannot:

- view User A's designs
- modify User A's designs
- delete User A's designs
- access User A's production orders
- access User A's workers
- access User A's machinery
- access User A's schedules
- generate AI renders for User A's design
- access User A's protected application data

Do not perform destructive attacks.

Use normal API/UI behavior and safe authorization checks.

Document any IDOR or tenant-isolation issue.

==================================================
# TEST 15 — FILE UPLOAD SECURITY
==================================================

Test allowed formats:

- PNG
- JPG
- JPEG
- WEBP

Test invalid formats if safe:

- TXT
- PDF
- SVG
- EXE
- other available non-image files

Verify:
- invalid files rejected
- MIME validation
- actual image validation
- size limit behavior
- no arbitrary file execution
- safe randomized filenames

Do not upload malicious executables or dangerous payloads.

==================================================
# TEST 16 — ERROR HANDLING
==================================================

Intentionally test normal invalid inputs.

Examples:

- missing required fields
- invalid IDs
- invalid category
- invalid dates
- invalid quantity
- missing design
- unauthorized access
- unsupported image format
- empty image
- invalid schedule configuration

Verify:

- user-friendly errors
- no stack traces exposed in UI
- no secrets exposed
- no internal filesystem paths exposed unnecessarily
- backend returns appropriate status codes
- frontend handles errors without crashing

==================================================
# TEST 17 — BROWSER / FRONTEND QA
==================================================

Inspect browser console.

Look for:

- JavaScript exceptions
- React errors
- failed API requests
- CORS errors
- 404s
- 500s
- broken images
- hydration/runtime errors
- warnings that indicate real problems

Test:

- refresh
- back/forward
- opening pages directly
- navigation between sections
- logout
- session expiration behavior if practical

Check responsive behavior at:

- desktop
- smaller desktop/tablet width
- mobile-ish width

Look for:

- overflowing panels
- broken dialogs
- clipped buttons
- unusable canvas
- broken tables
- Gantt overflow
- sidebar issues

==================================================
# TEST 18 — DATABASE / STORAGE CONSISTENCY
==================================================

After performing workflows, verify data consistency.

Check:

Design
→ Sketch
→ Render
→ Production Order
→ Schedule

relationships.

Verify deleting a design behaves according to the intended cascade rules.

Verify unrelated users' data remains untouched.

Verify Supabase Storage assets correspond to actual records.

Do not manually delete database data unless the test explicitly requires it and it is safe.

==================================================
# TEST 19 — PERFORMANCE / STABILITY
==================================================

Do not perform destructive load testing.

Instead perform a reasonable stability test:

- several design creations
- several image uploads
- multiple AI renders sequentially
- several YOLO detections
- multiple production orders
- multiple optimization schedules

Watch for:

- memory leaks
- GPU memory issues
- CUDA OOM
- backend crashes
- worker crashes
- browser freezes
- requests hanging indefinitely

Record approximate AI inference times.

Do not run parallel GPU-heavy requests unless the existing architecture explicitly supports it.

==================================================
# TEST 20 — FINAL END-TO-END CAPSTONE DEMO
==================================================

Perform one clean end-to-end demonstration as if presenting JewelMind to an examiner.

Workflow:

1. Login
2. Dashboard
3. Create jewellery design
4. Open Canvas
5. Draw jewellery sketch
6. Save sketch
7. Generate AI photorealistic rendering
8. Verify generated image
9. Run component detection
10. Verify YOLO result
11. Return to Dashboard
12. Create production order
13. Add artisan
14. Add machinery
15. Run OR-Tools optimization
16. View Gantt schedule
17. Return to Dashboard
18. Verify updated metrics
19. Refresh
20. Verify persistence

This should be treated as the primary acceptance test.

==================================================
# BUG CLASSIFICATION
==================================================

Classify every issue as:

CRITICAL
- application unusable
- data loss
- security breach
- AI pipeline completely broken
- database corruption
- production scheduling fundamentally incorrect

HIGH
- major feature broken
- repeated crashes
- incorrect production schedule constraints
- tenant isolation failure
- AI rendering unavailable
- YOLO detection unavailable

MEDIUM
- feature partially broken
- incorrect UI state
- persistence issue
- important validation problem
- incorrect metrics

LOW
- cosmetic issue
- minor alignment
- minor wording
- non-blocking UI issue

INFO
- warning
- improvement suggestion
- non-blocking observation

==================================================
# BUG REPORT FORMAT
==================================================

For EVERY bug use:

## BUG-001 — Short Title

Severity:
CRITICAL / HIGH / MEDIUM / LOW / INFO

Area:
Authentication / Dashboard / Designs / Canvas / AI Rendering / YOLO / Studio / Production / Optimization / Security / Storage / UI / etc.

Environment:
Frontend:
Backend:
AI Worker:
Browser:
OS:

Preconditions:

Steps to Reproduce:

1.
2.
3.
4.

Expected Result:

Actual Result:

Frequency:
Always / Often / Sometimes / Once

Evidence:

- screenshot if available
- browser console error
- backend log
- AI worker log
- API status code
- relevant URL/endpoint
- relevant filename

Impact:

Suggested Root Cause:
Only if you can confidently determine it.

Suggested Fix:
Do not implement it in this QA phase.

==================================================
# FINAL REPORT
==================================================

Create:

PRE_DEPLOYMENT_QA_REPORT.md

The report MUST contain:

# JewelMind Pre-Deployment QA Report

## 1. Executive Summary

## 2. Environment Tested

## 3. Services Tested

## 4. Test Data

Include:
- image directory
- number of images
- formats
- categories used

## 5. Feature Coverage

Create a table:

| Feature | Tested | Passed | Failed | Notes |
|---|---:|---:|---:|---|

Include:

- Authentication
- Dashboard
- Design Management
- Canvas
- Sketch Storage
- AI Rendering
- YOLO Detection
- Studio
- Production Orders
- Artisans
- Machinery
- OR-Tools Optimization
- Schedule Persistence
- Multi-Tenant Security
- File Upload Security
- Error Handling
- Frontend Navigation
- Responsive UI
- Database/Storage consistency
- End-to-End Workflow

## 6. AI Pipeline Verification

Explicitly document:

Frontend
→ FastAPI
→ AI Worker
→ RTX 4060
→ SD1.5
→ ControlNet
→ Appearance LoRA
→ Supabase
→ UI

State whether this was actually executed.

Include measured inference times.

## 7. YOLO Verification

Document:
- model loaded
- inference executed
- detections
- masks/bboxes
- confidence
- input images

## 8. Production Optimization Verification

Document:

- orders
- workers
- machines
- precedence
- worker constraints
- machine constraints
- skills
- schedule
- Gantt
- persistence

## 9. Security Testing

Document:
- authentication
- authorization
- tenant isolation
- file validation
- AI endpoint authorization
- storage behavior
- CORS
- error handling

## 10. Bugs Found

Separate:

### Critical
### High
### Medium
### Low
### Informational

Each bug must have the full reproduction details.

## 11. Screenshots / Evidence

Include references to screenshots/logs where available.

If screenshots cannot be embedded, list their filenames and locations.

## 12. Regression Results

Run existing tests AFTER the manual QA.

Backend:

.\backend\.venv\Scripts\python.exe -m pytest backend/tests/

AI:

C:\Users\usern\miniconda3\envs\tgpu\python.exe -m pytest tests/

Frontend:

npm --prefix frontend run build

Record exact results.

DO NOT alter tests just to make them pass.

## 13. Final Acceptance Status

Choose exactly one:

### READY FOR DEPLOYMENT

Only if:
- no Critical bugs
- no High bugs
- core end-to-end workflow passes
- AI rendering works
- YOLO works
- production optimization works
- security isolation passes
- existing regression tests pass

OR

### NOT READY FOR DEPLOYMENT

If any critical/high/core blocking issue remains.

## 14. Recommended Fix Priority

List bugs in order:

1.
2.
3.
4.

## 15. Deployment Blockers

Clearly state whether any issue must be fixed before Phase 15.

==================================================
# IMPORTANT FINAL RULES
==================================================

1. ACTUALLY USE THE APPLICATION.
2. DO NOT CLAIM A FEATURE PASSED JUST BECAUSE CODE LOOKS CORRECT.
3. DO NOT FABRICATE test results.
4. Do not fabricate AI inference.
5. Do not fabricate screenshots.
6. Do not fabricate database/storage verification.
7. Clearly distinguish:
   - code inspection
   - automated test
   - manual UI test
   - live AI test
   - live end-to-end test
8. Preserve all trained models and datasets.
9. Do not retrain anything.
10. Do not deploy anything.
11. Do not commit.
12. Do not push.
13. Do not merge.
14. Do not modify production architecture.
15. Do not fix bugs during this phase unless absolutely required to continue testing.
16. If a bug is found, document it instead of silently fixing it.
17. If you encounter a blocker, continue testing other independent features.
18. If the application requires login credentials, STOP and ask me for credentials rather than guessing.
19. If the browser asks for confirmation for an irreversible/destructive action, STOP and ask me.
20. At the end, generate ONLY the QA report and any supporting evidence/log references.

==================================================
# FINAL DELIVERABLE
==================================================

Create:

PRE_DEPLOYMENT_QA_REPORT.md

And, if useful:

qa-evidence/
    screenshots/
    logs/

At the end, report:

- total features tested
- total test scenarios
- passed
- failed
- blocked
- Critical bugs
- High bugs
- Medium bugs
- Low bugs
- whether AI rendering was actually tested
- whether YOLO was actually tested
- whether OR-Tools was actually tested
- whether the complete end-to-end workflow passed
- whether JewelMind is READY FOR DEPLOYMENT

STOP after producing the report.

WAIT FOR MOHIT'S REVIEW.

DO NOT COMMIT.
DO NOT PUSH.
DO NOT MERGE.