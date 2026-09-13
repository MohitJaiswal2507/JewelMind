JEWELMIND — PHASE B
GEMINI DESIGN UNDERSTANDING UX INTEGRATION

CURRENT STATE
Phase A — Gemini Backend Service + Structured Schemas — has been completed,
reviewed, approved, committed, pushed, and merged into main.

You are now starting Phase B.

IMPORTANT:
We are currently on main after Phase A was merged.

==================================================
1. GIT / BRANCH REQUIREMENTS
==================================================

FIRST:

1. Verify current branch.
2. Verify HEAD.
3. Verify working tree status.
4. Verify local main matches origin/main as much as possible.
5. Do NOT modify main directly.

Create exactly ONE new branch:

    phase-b-gemini-ux

All Phase B work must happen only on this branch.

DO NOT create another branch.

DO NOT commit or push anything until I explicitly approve your Phase B
implementation/report.

==================================================
2. OBJECTIVE
==================================================

Integrate the Phase A Gemini backend capability into the JewelMind frontend
UX.

The user experience we want is:

    User
      ↓
    Sketch / Upload
      ↓
    YOLO V2 = jewellery category
      ↓
    Gemini Vision
      +
    Optional user prompt
      ↓
    JewelMind Design Understanding
      ↓
    User reviews/edits
      ↓
    Ready for future rendering integration

Phase B is primarily a FRONTEND UX integration phase.

Do NOT yet redesign or modify the actual ControlNet / SD1.5 / LoRA renderer
pipeline.

==================================================
3. IMPORTANT PRODUCT BEHAVIOR
==================================================

JewelMind must support these two major flows.

------------------------------------------
FLOW A — USER PROVIDES A PROMPT
------------------------------------------

Example:

User enters:

    platinum round brilliant diamond thin shank

User clicks:

    "Enhance with AI"

Gemini should enhance the wording while preserving explicit user intent.

The final result MUST NOT silently change:

    platinum → gold
    diamond → emerald
    round brilliant → another stone/cut
    thin shank → thick shank

Explicit user requirements always have highest priority.

The enhanced prompt should be returned into an EDITABLE UI field.

The user must be able to inspect and modify it before continuing.

------------------------------------------
FLOW B — USER PROVIDES IMAGE/SKETCH BUT NO PROMPT
------------------------------------------

User uploads or creates a jewellery sketch.

Prompt field is empty.

JewelMind should allow Gemini to analyze the image/sketch and generate
structured design understanding plus a renderer-ready prompt.

The UI should make it clear that this is AI-generated interpretation.

Do NOT claim visual understanding if Gemini was unavailable.

==================================================
4. EXISTING BACKEND
==================================================

Phase A already created Gemini backend infrastructure.

Before implementing anything:

READ AND UNDERSTAND the existing Phase A implementation.

Inspect:

    backend/app/core/config.py
    backend/app/schemas/ai.py
    backend/app/services/gemini_design_service.py
    backend/app/services/jewellery_prompt_compiler.py
    backend/app/api/v1/ai_gemini.py
    backend/app/api/v1/router.py

DO NOT duplicate Gemini service logic in the frontend.

The frontend must communicate with the backend API.

The Gemini API key must NEVER be exposed to the browser.

==================================================
5. FRONTEND AUDIT
==================================================

Before changing code, inspect the existing frontend architecture.

Pay particular attention to:

    frontend/src/components/
    frontend/src/services/
    frontend/src/api/
    frontend/src/pages/
    frontend/src/components/dashboard/
    AiRenderModal.tsx
    aiRenderingService.ts

Also inspect the existing:

- sketch/upload flow
- AI rendering modal
- prompt input
- category selection
- YOLO detection display
- render workflow
- loading/error states
- existing shadcn/ui components
- existing Tailwind conventions

Reuse existing architecture where appropriate.

Do not create redundant API clients or duplicate UI systems.

==================================================
6. UI REQUIREMENTS
==================================================

Integrate Gemini into the existing JewelMind AI rendering/design workflow.

The UI should include an optional prompt field with wording similar to:

    Describe your design (optional)

Provide an AI action:

    ✨ Enhance with AI

The exact visual wording can be refined to fit the existing design system.

Use:

    React
    TypeScript
    Tailwind CSS
    shadcn/ui

Do not introduce another styling framework.

==================================================
7. ENHANCE PROMPT UX
==================================================

When the user enters a prompt and clicks:

    Enhance with AI

The frontend should:

1. Validate that a prompt exists.
2. Send the request to the Phase A backend endpoint.
3. Show an appropriate loading state.
4. Receive the structured response.
5. Display the enhanced result.
6. Put the compiled/renderer-ready prompt into an editable field.
7. Allow the user to modify it.
8. Clearly indicate that it was AI enhanced.

Do not automatically trigger rendering.

The user must remain in control.

==================================================
8. IMAGE/SKETCH ANALYSIS UX
==================================================

When a sketch/image exists and the prompt is empty, provide a clear path
for design analysis.

The UI should be able to call the Phase A analyze-design endpoint.

The result should be presented as:

    JewelMind understood your design

or an equivalent polished UX.

Display useful structured fields where available:

    Jewellery Type
    Material
    Gemstone
    Stone Shape/Cut
    Geometry
    Setting
    Design Characteristics
    Rendering Prompt
    Negative Prompt

Do not overwhelm the user with raw JSON.

Create a clean human-readable representation.

==================================================
9. EDITABILITY
==================================================

Gemini output is NOT final authority.

The user must be able to edit the generated prompt.

The UX should communicate:

    AI suggestion → user review → user-controlled final prompt

Do not lock the generated prompt.

Do not automatically overwrite user edits.

If the user manually edits the enhanced prompt, preserve those edits.

==================================================
10. YOLO V2 CONTEXT
==================================================

Phase A already supports YOLO context.

Do NOT modify YOLO V2.

Do NOT retrain YOLO.

Do NOT replace YOLO.

Do NOT create a component detector.

Use the existing detected jewellery category where the current architecture
already provides it.

Remember the approved YOLO V2 categories:

    ring
    earring
    pendant
    necklace
    bracelet
    bangle
    brooch
    other_jewellery

The category should be treated as grounding/context, not as an excuse to
override explicit user requirements.

==================================================
11. GEMINI FAILURE / FALLBACK
==================================================

Gemini is OPTIONAL.

The application MUST remain usable if:

    GEMINI_API_KEY is missing
    Gemini request fails
    Gemini times out
    backend returns an error
    network request fails

The UI should show a friendly error/warning.

Do NOT fabricate:

    "Gemini analyzed your sketch"

when Gemini did not actually analyze it.

For prompt-only enhancement failure, the user should still be able to
continue using their original prompt.

For image/sketch analysis failure, preserve the existing non-Gemini
workflow and clearly indicate that AI analysis was unavailable.

==================================================
12. DO NOT MODIFY RENDERING YET
==================================================

STRICT SCOPE BOUNDARY.

Do NOT:

- modify ControlNet
- modify SD1.5
- modify LoRA
- retrain models
- change model weights
- change rendering checkpoints
- change rendering inference parameters
- replace the existing renderer
- redesign production workflow
- change YOLO V2 model
- change YOLO V2 training
- change datasets

Phase B only prepares the UX and state needed for the future rendering
integration.

If the existing renderer consumes a prompt field, DO NOT alter its
semantics unless absolutely necessary for the frontend UX.

Do not automatically wire Gemini output into the renderer yet.

==================================================
13. STATE MANAGEMENT
==================================================

Use the existing frontend state architecture.

Maintain clear separation between:

    originalUserPrompt
    enhancedPrompt
    finalEditablePrompt
    designUnderstanding
    geminiStatus
    geminiError

Do not create unnecessary global state.

The final user-edited prompt should remain the source of truth for the
future rendering phase.

==================================================
14. TYPESCRIPT TYPES
==================================================

Create/reuse strongly typed TypeScript interfaces corresponding to the
Phase A backend schemas.

Do NOT use:

    any

for Gemini response objects unless there is a genuinely unavoidable
boundary.

Types should represent:

- design understanding
- Gemini analysis response
- prompt enhancement response
- fallback state
- error state

Keep frontend/backend contracts explicit.

==================================================
15. API CLIENT
==================================================

Implement or extend the existing frontend API/service layer.

Prefer something conceptually like:

    aiRenderingService.ts

or the existing appropriate service.

Do NOT place Gemini HTTP calls directly throughout React components.

Centralize API interaction.

The frontend must NEVER contain:

    GEMINI_API_KEY

or any Gemini credential.

==================================================
16. LOADING STATES
==================================================

Provide polished loading states.

Examples:

    Analyzing your jewellery...
    Understanding your design...
    Enhancing your prompt...

Use existing JewelMind/shadcn loading components where available.

Prevent accidental duplicate requests while a request is running.

==================================================
17. ERROR STATES
==================================================

Handle:

- 400
- 422
- 500
- 503
- network failure
- timeout
- malformed response

Gracefully.

Do not expose internal stack traces to users.

Provide actionable UI messages.

==================================================
18. UX DESIGN
==================================================

Follow the existing JewelMind visual language.

Use:

    Tailwind CSS
    shadcn/ui

The Gemini UI should feel like part of JewelMind, not a separate plugin.

The interaction should be simple:

    [ Describe your design (optional)             ]

    [ ✨ Enhance with AI ]

If AI understanding exists:

    ┌─────────────────────────────────────┐
    │ ✨ JewelMind understood your design │
    │                                     │
    │ Type       Ring                     │
    │ Material   Platinum                 │
    │ Gemstone   Round Brilliant Diamond  │
    │ Geometry   Thin shank               │
    │                                     │
    │ Rendering Prompt                     │
    │ [ editable prompt................ ] │
    │                                     │
    │ Negative Prompt                      │
    │ [ editable / reviewable .......... ] │
    └─────────────────────────────────────┘

The exact layout should match the existing application.

Do not blindly reproduce this ASCII layout if another existing component
structure is more appropriate.

==================================================
19. ACCESSIBILITY
==================================================

Ensure:

- buttons have accessible labels
- form fields have labels
- keyboard navigation works
- loading states are understandable
- errors are announced appropriately where practical
- color is not the only indication of state

==================================================
20. SECURITY
==================================================

Never expose Gemini credentials.

Never log:

    GEMINI_API_KEY

Do not put secrets in frontend environment variables.

Only the backend communicates with Gemini.

Do not introduce unsafe HTML rendering.

==================================================
21. TESTING
==================================================

Add/update frontend tests where the project already has a testing
framework.

At minimum cover:

TEST 1:
Prompt entered → Enhance with AI → enhanced prompt displayed.

TEST 2:
Prompt contains explicit:

    platinum
    round brilliant diamond
    thin shank

Verify the frontend preserves the returned constraints and does not
overwrite them.

TEST 3:
Image/sketch + empty prompt → Analyze Design → structured understanding
displayed.

TEST 4:
Gemini backend returns failure → friendly error displayed.

TEST 5:
Prompt enhancement fails → original prompt remains usable.

TEST 6:
User edits enhanced prompt → manual edits remain intact.

TEST 7:
Gemini loading state prevents duplicate submissions.

TEST 8:
No Gemini credentials/backend availability → existing workflow remains
usable.

Use mocks for backend calls.

DO NOT make real Gemini API calls during tests.

==================================================
22. REGRESSION TESTING
==================================================

Run the existing relevant frontend tests.

Run backend tests relevant to the unchanged Phase A API contract.

Run production frontend build.

Verify that existing JewelMind functionality still works.

Do not modify unrelated failing tests just to make the test suite green.

Clearly distinguish:

- Phase B failures
- pre-existing failures
- environment failures

==================================================
23. NO TRAINING
==================================================

Absolutely NO:

- GPU training
- model training
- dataset generation
- checkpoint modification
- LoRA training
- ControlNet training
- YOLO training

This phase requires ZERO GPU training.

==================================================
24. NO DATABASE CHANGES
==================================================

Do not modify:

- Supabase schema
- database migrations
- storage schema

unless the existing frontend architecture absolutely requires an existing
field to be consumed.

Phase B should not introduce persistent Gemini data.

==================================================
25. DOCUMENTATION
==================================================

Create:

    docs/PHASE_B_GEMINI_UX_REPORT.md

The report must contain:

1. Branch name
2. Starting commit
3. Files changed
4. Files created
5. Existing frontend flow audited
6. Gemini UX architecture
7. API integration details
8. State management
9. User intent preservation behavior
10. Gemini fallback behavior
11. YOLO context handling
12. Screens/components modified
13. Tests executed
14. Test results
15. Build result
16. Any warnings
17. Any known limitations
18. Exact files/functions that Phase C should modify
19. Confirmation that ControlNet/SD1.5/LoRA/YOLO/model weights were not
    changed
20. Confirmation that no Gemini API key was exposed
21. Confirmation that no real Gemini API calls were made during testing

==================================================
26. STRICT GIT RULE
==================================================

DO NOT:

    git commit
    git push
    merge
    modify main

until I review the implementation and explicitly tell you to commit.

==================================================
27. FINAL REPORT REQUIREMENT
==================================================

When implementation is complete:

STOP.

Do not commit.

Do not push.

Do not merge.

Provide:

    docs/PHASE_B_GEMINI_UX_REPORT.md

and report back with:

    Branch:
    Starting HEAD:
    Working tree:
    Files changed:
    Files created:
    Tests:
    Build:
    Gemini API calls:
    Model/training changes:
    YOLO changes:
    Renderer changes:
    Database changes:
    Known limitations:

Then wait for my review.

==================================================
FINAL PRINCIPLE
==================================================

Phase B should make JewelMind feel like it can understand a jewellery
design through Gemini, while keeping the user in control.

The target UX is:

    Sketch / Upload
          ↓
    Understand design
          ↓
    Show what JewelMind understood
          ↓
    Generate / enhance prompt
          ↓
    User reviews and edits
          ↓
    Ready for the future rendering integration

Do NOT jump ahead into renderer integration.

Do NOT retrain any model.

Do NOT expose Gemini credentials.

Do NOT commit or push.

Implement only Phase B.