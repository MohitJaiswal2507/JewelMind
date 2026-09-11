JEWELMIND — PRE-PHASE-19 RUNTIME STABILIZATION & FULL E2E FEATURE AUDIT

IMPORTANT:

DO NOT START THE UI/UX REDESIGN YET.

Before Phase 19 UI/UX redesign begins, we need to make sure the existing JewelMind application actually works end-to-end.

I manually tested the application and found TWO CRITICAL RUNTIME PROBLEMS:

1. YOLO component detection is still behaving like the OLD V1 ring-component detector.
2. AI rendering returns HTTP 500 because the backend receives no UploadFile and accesses file.filename on None.

We need to fix these issues first and then perform a COMPLETE END-TO-END application test using ALL existing JewelMind features and ALL jewellery categories.

==================================================
PHASE / BRANCH
==================================================

Create a stabilization branch from current main:

phase-19-pre-ui-runtime-stabilization

IMPORTANT:

This is a stabilization phase before the actual Phase 19 UI redesign.

DO NOT redesign the UI.

DO NOT change the visual design system.

DO NOT change colors/theme/layout except where absolutely necessary to expose or verify functionality.

DO NOT retrain any AI model.

DO NOT modify production model weights.

DO NOT delete datasets/models.

DO NOT perform destructive cleanup.

DO NOT commit or push until the complete audit is finished and reviewed.

==================================================
CRITICAL ISSUE #1 — YOLO IS STILL USING OLD RING COMPONENT DETECTION
==================================================

CURRENT OBSERVED BEHAVIOR:

The UI currently shows results such as:

- gemstone
- ring_shank

and the detector header indicates YOLO jewellery component detection.

This strongly suggests the runtime is still loading the old V1 ring/component detector or an incorrect fallback/mock model.

THIS MUST BE INVESTIGATED, NOT PAPERED OVER.

==================================================
YOLO V2 PRODUCTION MODEL
==================================================

The production YOLO V2 model is:

runs/segment/runs/segment/runs/jewellery/yolo11m-seg-jewelmind-v2-continued/weights/best.pt

YOLO V2 taxonomy:

0 = ring
1 = earring
2 = pendant
3 = necklace
4 = bracelet
5 = bangle
6 = brooch
7 = other_jewellery

The production detector MUST use this V2 model.

==================================================
YOLO V1 MODEL
==================================================

The old V1 model must NOT be used as the default production detector.

The old V1 taxonomy includes ring-specific component classes such as:

- gemstone
- ring_shank
- ring_head
- prong
- bezel
- setting
- shoulder

Those are NOT the production V2 category outputs.

Do not silently map V1 component predictions into V2 categories.

Do not rename V1 outputs to pretend they are V2.

Do not use V1 as a fallback when V2 is available.

==================================================
YOLO RUNTIME INVESTIGATION
==================================================

Trace the ENTIRE runtime path:

Frontend
→ API request
→ FastAPI route
→ detector service
→ model resolver
→ YOLO model loading
→ inference
→ response schema
→ frontend rendering

Determine EXACTLY which .pt file is loaded at runtime.

Print/log during development:

- resolved model path
- model filename
- model SHA256
- model class names
- model task
- inference device
- requested model preference
- whether fallback occurred

Do NOT expose sensitive filesystem paths to normal end users.

Development diagnostics are acceptable.

==================================================
YOLO MODEL VALIDATION
==================================================

Add or improve a production model verification test.

The test MUST verify:

1. V2 model path resolves correctly.
2. File exists.
3. Model loads successfully.
4. Model class names are exactly the expected V2 taxonomy.
5. The model does NOT expose the old V1 component taxonomy.
6. Inference returns V2 jewellery categories.
7. Production detector does not silently fall back to V1.
8. CPU/mock fallback, if present, is clearly distinguishable and MUST NOT masquerade as production YOLO V2.

Expected production class names:

ring
earring
pendant
necklace
bracelet
bangle
brooch
other_jewellery

==================================================
YOLO FRONTEND VERIFICATION
==================================================

Inspect the frontend detector component.

Determine whether the frontend:

- is displaying stale V1 labels
- contains hardcoded V1 categories
- transforms V2 responses incorrectly
- uses mock fallback data
- caches old results
- calls the wrong endpoint
- sends the wrong model preference
- displays old component terminology

Fix the complete path.

After the fix, when testing:

RING should produce:
ring

not:

gemstone
ring_shank
prong
etc.

For an earring:

earring

For pendant:

pendant

For necklace:

necklace

For bracelet:

bracelet

For bangle:

bangle

For brooch:

brooch

For other jewellery:

other_jewellery

IMPORTANT:

YOLO V2 is a jewellery-category segmentation model.

Do not expect V2 to output internal ring components.

==================================================
CRITICAL ISSUE #2 — AI RENDER HTTP 500
==================================================

CURRENT ERROR:

POST /api/v1/ai/render

returns:

500 Internal Server Error

with:

AttributeError: 'NoneType' object has no attribute 'filename'

The failure occurs because:

file == None

but the backend executes:

file.filename

This MUST be fixed correctly.

==================================================
INVESTIGATE THE RENDERING API CONTRACT
==================================================

Inspect:

backend/app/api/v1/ai_rendering.py

and the complete frontend rendering service/request code.

Determine exactly how rendering is intended to work.

There appear to be potentially different input sources:

- uploaded sketch file
- saved design/sketch
- Supabase asset
- image URL
- existing design ID
- generated/canvas image

Do NOT simply make file optional and then continue with None.

Implement proper input resolution.

==================================================
RENDERING INPUT RULE
==================================================

The backend should support the input mechanism that the existing JewelMind UI actually uses.

If the frontend is rendering an existing saved sketch/design:

The backend must be able to resolve that source correctly.

If the frontend uploads a file:

The backend must process the UploadFile.

If both mechanisms are supported:

Validate them explicitly.

If neither is supplied:

Return a proper HTTP 400/422 validation error with a useful message.

NEVER allow:

None.filename

or another None dereference.

==================================================
IMPORTANT
==================================================

DO NOT weaken validation just to make the error disappear.

Do NOT catch everything and return fake success.

Do NOT generate a fake image.

Do NOT use mock rendering when production rendering is expected.

The request must reach the real production rendering pipeline.

==================================================
RENDERING PIPELINE VERIFICATION
==================================================

After fixing the request/input contract, trace:

Frontend
→ POST /api/v1/ai/render
→ backend request parsing
→ input resolution
→ LineArt preprocessing
→ production ControlNet
→ LoRA if configured
→ inference
→ output storage
→ database/result record
→ frontend result display

Verify that the production renderer is:

1000-step final ControlNet

and NOT:

- old 300-step model
- old V2 300-step model
- smoke model
- pilot model
- mock renderer

Production final renderer:

outputs/rendering_v2_controlnet/controlnet_rendering_v2_final

Verify its existence and integrity.

DO NOT retrain it.

==================================================
CATEGORY-AWARE RENDERING TEST
==================================================

The renderer must be tested with ALL supported jewellery categories.

Run at least one real rendering for each:

1. Ring
2. Earring
3. Pendant
4. Necklace
5. Bracelet
6. Bangle
7. Brooch
8. Other Jewellery

Use real test inputs.

Do NOT use fake successful responses.

Record:

- category
- input image
- API response
- rendering success/failure
- HTTP status
- render completion time
- output path/result ID
- whether the category was preserved
- whether the output is visually usable

IMPORTANT:

Do not retrain.

Do not modify model weights.

Do not modify datasets.

==================================================
FULL APPLICATION END-TO-END AUDIT
==================================================

After fixing both critical problems, manually run the ACTUAL APPLICATION.

Use the real frontend in the browser.

Use the real backend.

Use the real database/storage.

Do NOT rely only on unit tests.

We need an actual user workflow test.

==================================================
TEST ACCOUNT / AUTH
==================================================

Test:

1. Open application.
2. Login.
3. Verify authenticated session.
4. Verify dashboard loads.
5. Verify logout.
6. Login again.

Do not expose credentials in the report.

==================================================
TEST EVERY JEWELLERY CATEGORY
==================================================

Use at least one real design/input for EACH:

Ring
Earring
Pendant
Necklace
Bracelet
Bangle
Brooch
Other Jewellery

Each category must be exercised through applicable functionality.

Create a test matrix.

==================================================
FEATURE 1 — DASHBOARD
==================================================

Verify:

- dashboard loads
- overview API works
- statistics load
- recent designs load
- navigation works
- no console errors
- no broken images
- no infinite loading

==================================================
FEATURE 2 — DESIGN MANAGEMENT
==================================================

Test:

- create design
- select category
- upload/use sketch
- save design
- list designs
- search/filter if available
- open design
- edit/update
- delete test design if appropriate

Verify all 8 categories can be represented.

==================================================
FEATURE 3 — SKETCH CANVAS
==================================================

Actually open the canvas.

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
- save
- upload/reference where supported

Create at least one usable test sketch.

Verify it saves correctly.

==================================================
FEATURE 4 — YOLO V2 DETECTION
==================================================

Run actual detection using real jewellery images.

Test ALL 8 categories:

Ring
Earring
Pendant
Necklace
Bracelet
Bangle
Brooch
Other Jewellery

For every category record:

- model loaded
- category prediction
- confidence
- segmentation mask
- bounding box if supported
- API response
- UI rendering

CRITICAL:

Confirm the result uses V2 taxonomy.

No:

gemstone
ring_shank
ring_head
prong
bezel
setting
shoulder

unless those are coming from an explicitly separate legacy V1 feature.

Production V2 detection must show the 8 jewellery categories.

==================================================
FEATURE 5 — AI RENDERING
==================================================

Run actual rendering for ALL 8 categories.

For each:

- select category
- provide blueprint/sketch
- select currently supported options
- start generation
- wait for real result
- verify backend response
- verify output is saved
- verify frontend displays result
- verify no 500
- verify no broken state
- verify output can be opened/downloaded if supported

Do not fake completion.

==================================================
FEATURE 6 — STUDIO
==================================================

Verify:

- Studio loads
- generated renders appear
- images load
- filters work if available
- open image
- inspector/details
- download
- delete
- navigation back to design

==================================================
FEATURE 7 — DESIGN DETAIL
==================================================

Verify:

- sketch preview
- rendered preview
- metadata
- category
- actions
- navigation to canvas
- rendering launch
- component detection launch where available

==================================================
FEATURE 8 — PRODUCTION MANAGEMENT
==================================================

Verify actual existing functionality.

Test:

- create/view production order if supported
- category
- quantity
- status
- production data
- update actions
- list/detail
- error handling

DO NOT invent new production functionality.

==================================================
FEATURE 9 — PRODUCTION OPTIMIZATION
==================================================

Actually run the existing optimization functionality.

Verify:

- optimization request
- solver execution
- result
- schedule/timeline if present
- bottleneck/recommendation data
- UI rendering
- failure handling

Do not create fake optimization results.

==================================================
FEATURE 10 — AUTHORIZATION / ERROR STATES
==================================================

Verify:

- unauthenticated access
- expired/invalid auth behavior
- invalid design ID
- missing image
- unsupported category
- invalid rendering request
- invalid detection request
- backend unavailable behavior

Errors should be useful and should NOT produce raw Python tracebacks in normal UI.

==================================================
BROWSER CONSOLE AUDIT
==================================================

During the full application test:

Monitor browser console.

Record:

- errors
- warnings
- failed network requests
- CORS errors
- 404s
- 500s
- React warnings
- broken asset URLs

Fix any errors caused by this stabilization work.

Do not ignore errors simply because the UI still appears usable.

==================================================
NETWORK AUDIT
==================================================

Inspect browser Network requests.

For every major feature verify:

- request method
- endpoint
- status
- request payload
- response payload
- latency
- failed requests

Especially inspect:

/api/v1/ai/components/detect

/api/v1/ai/render

and all design/studio/production endpoints.

==================================================
BACKEND LOG AUDIT
==================================================

During the E2E test:

Monitor backend logs.

There must be:

NO:

- unhandled exceptions
- AttributeError
- NoneType dereferences
- 500 responses
- unexpected model fallback
- missing model errors
- storage failures
- database rollback caused by test operations

Expected validation errors are acceptable when intentionally testing invalid inputs.

==================================================
TEST MATRIX
==================================================

Create:

docs/phases/PHASE_19_PRE_UI_RUNTIME_STABILIZATION_REPORT.md

Include a table:

| Feature | Test | Result | Status | Evidence |
|---------|------|--------|--------|----------|

Also create a jewellery coverage table:

| Category | YOLO V2 | Rendering | Design | Studio | Production | Result |
|----------|---------|-----------|--------|--------|------------|--------|
| Ring | | | | | | |
| Earring | | | | | | |
| Pendant | | | | | | |
| Necklace | | | | | | |
| Bracelet | | | | | | |
| Bangle | | | | | | |
| Brooch | | | | | | |
| Other Jewellery | | | | | | |

Use:

PASS
FAIL
BLOCKED
NOT APPLICABLE

Do not claim PASS unless actually tested.

==================================================
PER-CATEGORY EVIDENCE
==================================================

For every jewellery category, record:

- test image used
- detector result
- render result
- relevant API result
- visual result

If screenshots are generated during testing, store them in a clearly identified test/evidence directory that is gitignored if appropriate.

Do not commit large generated render datasets.

A small number of representative evidence images may be retained if useful.

==================================================
AUTOMATED TESTS
==================================================

Run:

pytest tests/ai/ -v

and all relevant backend tests.

Run frontend:

npm run build

and any existing frontend test/typecheck commands.

Also run targeted tests for:

- YOLO V2 model resolution
- YOLO V2 class taxonomy
- rendering input validation
- rendering endpoint
- category normalization
- production model resolution

Record exact results.

==================================================
NO MODEL TRAINING
==================================================

ABSOLUTELY DO NOT:

- train YOLO
- train ControlNet
- train LoRA
- regenerate datasets
- alter production model weights
- download replacement models
- run GPU training

This is an application runtime/integration audit only.

==================================================
NO UI REDESIGN
==================================================

Do NOT begin Phase 19 visual redesign.

Do NOT:

- change global theme
- redesign dashboard
- redesign sidebar
- redesign cards
- change typography
- redesign canvas
- change color palette
- implement BLNG-inspired styling

Those changes come AFTER this stabilization branch is merged.

==================================================
SECURITY
==================================================

Verify:

- .env is not committed
- secrets are not logged
- auth tokens are not logged
- model paths are not exposed unnecessarily
- uploaded files are validated
- invalid categories are rejected
- path traversal is prevented
- unsupported files are rejected
- error responses do not leak stack traces to frontend users

==================================================
SUCCESS CRITERIA
==================================================

This stabilization phase is successful only when:

[ ] YOLO production path uses V2 model
[ ] YOLO V2 classes are exactly correct
[ ] Old V1 component predictions are no longer used as production V2 output
[ ] AI render no longer crashes when using the actual frontend workflow
[ ] Missing rendering input produces proper validation error
[ ] Real rendering succeeds
[ ] Ring rendering tested
[ ] Earring rendering tested
[ ] Pendant rendering tested
[ ] Necklace rendering tested
[ ] Bracelet rendering tested
[ ] Bangle rendering tested
[ ] Brooch rendering tested
[ ] Other jewellery rendering tested
[ ] Design management tested
[ ] Canvas tested
[ ] YOLO tested
[ ] Rendering tested
[ ] Studio tested
[ ] Production tested
[ ] Optimization tested
[ ] Authentication tested
[ ] Browser console audited
[ ] Network requests audited
[ ] Backend logs audited
[ ] Automated tests pass
[ ] Frontend build passes
[ ] No unresolved critical runtime errors
[ ] Production AI assets remain untouched
[ ] No secrets committed

==================================================
FINAL REPORT
==================================================

Create:

docs/phases/PHASE_19_PRE_UI_RUNTIME_STABILIZATION_REPORT.md

Include:

1. Executive summary
2. Initial YOLO V1/V2 issue
3. Root cause
4. YOLO fix
5. Rendering 500 root cause
6. Rendering fix
7. Full application test results
8. All 8 jewellery category results
9. Feature-by-feature test results
10. Browser console results
11. Network results
12. Backend log results
13. Automated test results
14. Frontend build result
15. Production model verification
16. Security checks
17. Files modified
18. Files intentionally untouched
19. Known limitations
20. Final PASS/FAIL verdict

==================================================
GIT WORKFLOW
==================================================

DO NOT commit yet.

DO NOT push yet.

DO NOT merge yet.

At the end show:

1. Current branch
2. git status
3. Files modified
4. Files added
5. Files deleted
6. Tests run
7. Full E2E results
8. All 8 category results
9. Remaining issues
10. Production model verification

STOP and wait for my review.

Do not commit or push until I approve the report.