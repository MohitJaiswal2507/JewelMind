JEWELMIND — PHASE C
GEMINI → EXISTING RENDERER INTEGRATION

==================================================
CURRENT STATE
==================================================

Phase A — Gemini Backend Foundation:
COMPLETED, REVIEWED, APPROVED, MERGED.

Phase B — Gemini Design Understanding UX:
COMPLETED, REVIEWED, APPROVED, MERGED.

We are now starting Phase C.

The current branch is MAIN after the Phase B merge.

==================================================
1. GIT / BRANCH REQUIREMENTS
==================================================

FIRST:

1. Verify the current branch.
2. Verify HEAD.
3. Verify working tree status.
4. Verify local main/origin/main state.
5. Confirm Phase B is present in main.

Do NOT modify main directly.

Create exactly ONE branch:

    phase-c-gemini-renderer-integration

All Phase C work must happen on this branch.

DO NOT create another branch.

DO NOT commit.

DO NOT push.

DO NOT merge.

Wait for my review after implementation and report generation.

==================================================
2. PHASE C OBJECTIVE
==================================================

Phase C connects the approved Gemini design-understanding workflow from
Phase B to JewelMind's EXISTING jewellery rendering pipeline.

Target:

    Sketch / Upload
          ↓
    YOLO V2 category/context
          ↓
    Gemini Design Understanding
          ↓
    User reviews/edits
          ↓
    FINAL USER-APPROVED PROMPT
          ↓
    Existing ControlNet
          +
    Existing SD1.5
          +
    Existing LoRA
          ↓
    Jewellery Render

The key principle is:

    Gemini improves UNDERSTANDING and PROMPT QUALITY.

    Gemini does NOT replace or retrain the renderer.

==================================================
3. CRITICAL SAFETY BOUNDARY
==================================================

DO NOT:

- retrain ControlNet
- retrain SD1.5
- retrain LoRA
- retrain YOLO V2
- modify model weights
- modify checkpoints
- modify datasets
- generate training datasets
- change the 1000-step ControlNet model
- replace SD1.5
- replace the LoRA
- dynamically invent ControlNet weights
- dynamically alter ControlNet strength based on Gemini
- introduce new AI models
- introduce paid APIs
- introduce paid GPU services

ZERO GPU TRAINING.

ZERO MODEL RETRAINING.

==================================================
4. EXISTING PRODUCTION RENDERER
==================================================

Before making any changes, carefully inspect the existing rendering
implementation.

Find and audit:

    backend/app/services/ai_rendering_service.py
    backend/app/api/v1/ai_rendering.py
    frontend/src/services/api/aiRenderingService.ts
    frontend/src/components/studio/AiRenderModal.tsx

Also locate the actual production renderer/model loading code.

Verify the currently approved rendering assets and configuration.

The production ControlNet model is:

    outputs/rendering_v2_controlnet/controlnet_rendering_v2_final

with final checkpoint:

    outputs/rendering_v2_controlnet/checkpoints/checkpoint-1000

The production rendering pipeline uses:

    SD1.5
    +
ControlNet
    +
LoRA

DO NOT assume file locations.

Trace the actual current implementation before modifying anything.

==================================================
5. UNDERSTAND PHASE B CONTRACT
==================================================

Read the Phase B implementation.

Inspect:

    frontend/src/types/ai.ts
    frontend/src/services/api/geminiDesignService.ts
    frontend/src/components/studio/GeminiDesignUnderstandingCard.tsx
    frontend/src/components/studio/AiRenderModal.tsx

Also inspect the backend Phase A schemas:

    backend/app/schemas/ai.py

Understand exactly how Phase B represents:

    finalEditablePrompt
    negativePrompt
    designUnderstanding
    renderer_prompt
    fallback_applied
    yolo_category
    gemini_category
    resolved_category
    category_conflict
    warnings

Do not duplicate or reinvent these contracts unnecessarily.

==================================================
6. MOST IMPORTANT RULE:
FINAL USER PROMPT HAS AUTHORITY
==================================================

The final editable prompt from Phase B is the user's approved prompt.

If Gemini generated:

    "A platinum ring with a round brilliant diamond and a thin shank..."

and the user edits it to:

    "A platinum ring with a round brilliant diamond and an ultra-thin
     shank with minimal shoulder decoration..."

the renderer MUST use the user's final edited version.

Never silently regenerate or replace it.

Never call Gemini again immediately before rendering in a way that
overwrites user edits.

The rendering request should consume the final state that the user
actually approved.

==================================================
7. PROMPT FLOW
==================================================

Implement the following precedence:

CASE A — User never used Gemini:

    Existing manual prompt
          ↓
    Existing renderer

The existing workflow must continue working.

CASE B — User enhanced prompt:

    Original prompt
          ↓
    Gemini enhancement
          ↓
    User review/edit
          ↓
    finalEditablePrompt
          ↓
    Renderer

CASE C — User analyzed sketch:

    Sketch
      ↓
    Gemini analysis
      ↓
    Structured understanding
      ↓
    Generated renderer prompt
      ↓
    User review/edit
      ↓
    finalEditablePrompt
      ↓
    Renderer

CASE D — Gemini unavailable:

    Existing manual rendering workflow

No Gemini requirement should make rendering unusable.

==================================================
8. POSITIVE PROMPT
==================================================

The renderer must receive the FINAL USER-APPROVED positive prompt.

Do not automatically prefer:

    Gemini's original renderer_prompt

over:

    finalEditablePrompt

The user's final editable value is authoritative.

If the user has not edited the Gemini result, the Gemini compiled prompt
may be used.

If the user edited it, use their edited value.

==================================================
9. NEGATIVE PROMPT
==================================================

Phase B provides an editable negative prompt.

Trace how the existing renderer currently handles negative prompts.

Integrate the Phase B negative prompt into the render request only if the
existing renderer supports a negative prompt.

If the existing renderer already has a negative prompt field, preserve
its behavior.

Do not break existing negative-prompt functionality.

The user's final negative prompt should have precedence over an AI-generated
negative prompt.

Do not silently overwrite it.

==================================================
10. DO NOT CHANGE CONTROLNET STRENGTH
==================================================

THIS IS A HARD REQUIREMENT.

Do NOT implement:

    Gemini → ControlNet strength

Do NOT implement:

    Gemini → dynamic conditioning weight

Do NOT implement:

    material → arbitrary ControlNet weight

Do NOT implement:

    gemstone → arbitrary ControlNet weight

Do NOT implement any heuristic that changes the trained ControlNet
conditioning behavior.

The existing ControlNet strength and inference parameters must remain
unchanged unless the current renderer already exposes them as user
controls.

Gemini should improve the textual conditioning, not invent new model
control logic.

==================================================
11. STRUCTURED DESIGN UNDERSTANDING
==================================================

Phase B produces structured design understanding.

Use this primarily as contextual information.

Do not automatically translate every field into a numerical renderer
parameter.

For example:

    material = platinum
    gemstone = round brilliant diamond
    geometry = thin shank

should primarily contribute to the final prompt/context.

Do NOT turn these into arbitrary ControlNet weights.

The existing renderer should remain stable.

==================================================
12. CATEGORY HANDLING
==================================================

JewelMind has verified YOLO V2 categories:

    ring
    earring
    pendant
    necklace
    bracelet
    bangle
    brooch
    other_jewellery

Preserve existing category-aware rendering behavior.

Do not replace YOLO V2.

Do not retrain YOLO V2.

Do not create a new component detector.

If Phase B has:

    resolved_category

use it only where the existing renderer already expects a jewellery
category.

Do not allow Gemini to silently turn:

    ring → necklace

or another explicit user category into something else.

Follow the established Phase A precedence rules.

==================================================
13. RENDER API DESIGN
==================================================

Inspect the existing render endpoint and request contract first.

Do not create a second rendering system.

Extend the existing rendering API minimally if necessary.

A suitable conceptual contract is:

    renderSketch(
        image/sketch,
        final_prompt,
        negative_prompt,
        existing_render_options
    )

If structured design context is useful for logging or future extension,
it may be passed as optional context.

However:

    structured_design

must NOT be required for normal rendering.

The existing renderer must remain backwards compatible.

==================================================
14. BACKWARD COMPATIBILITY
==================================================

These must all continue working:

1. Existing manual prompt rendering.
2. Rendering without Gemini.
3. Rendering when Gemini API key is unavailable.
4. Existing category/material/gemstone controls.
5. Existing ControlNet inference.
6. Existing LoRA behavior.
7. Existing saved sketch workflow.
8. Existing render history/studio workflow.

Gemini integration must be additive.

==================================================
15. FRONTEND RENDER SUBMISSION
==================================================

Modify:

    frontend/src/components/studio/AiRenderModal.tsx

only as necessary.

When the user clicks the existing render button:

1. Determine the current final prompt.
2. Determine the current final negative prompt.
3. Preserve all existing rendering options.
4. Submit them through the existing rendering service.
5. Do NOT invoke Gemini again automatically.
6. Do NOT overwrite user edits.
7. Do NOT create a hidden second prompt.

The render button should use the state the user sees.

==================================================
16. FRONTEND RENDER SERVICE
==================================================

Inspect:

    frontend/src/services/api/aiRenderingService.ts

Extend the existing request contract only when necessary.

Do not duplicate render API logic.

Do not introduce a second HTTP client.

Maintain existing authentication behavior.

==================================================
17. BACKEND RENDER SERVICE
==================================================

Inspect:

    backend/app/services/ai_rendering_service.py

Integrate the final prompt at the narrowest safe point.

The service should continue to:

- load the existing renderer
- use the existing ControlNet
- use the existing SD1.5
- use the existing LoRA
- preserve existing inference configuration

Only the prompt/context input should be enhanced.

Do not rewrite the rendering engine.

==================================================
18. FALLBACK LOGIC
==================================================

Rendering must never depend on Gemini availability.

Example:

    Gemini succeeds
       ↓
    User reviews
       ↓
    Render

OR:

    Gemini fails
       ↓
    User continues with original prompt
       ↓
    Render

OR:

    No Gemini used
       ↓
    Existing prompt
       ↓
    Render

All three must work.

==================================================
19. GEMINI FALLBACK WARNING
==================================================

If Gemini failed during Phase B:

    do not call Gemini again automatically during rendering.

Use the user's current prompt.

If there is no AI-generated prompt, use the existing renderer's current
prompt behavior.

Do not fabricate AI understanding.

==================================================
20. SECURITY
==================================================

Gemini API key remains backend-only.

Do not:

- expose GEMINI_API_KEY
- send GEMINI_API_KEY to frontend
- store Gemini key in localStorage
- store Gemini key in browser state
- log Gemini credentials

Do not add secrets to Git.

==================================================
21. PERFORMANCE
==================================================

Do not add unnecessary Gemini calls.

The normal sequence should be:

    Analyze/enhance ONCE
          ↓
    User reviews
          ↓
    Render

Rendering itself should NOT automatically trigger another Gemini request.

This avoids unnecessary latency and API usage.

==================================================
22. ERROR HANDLING
==================================================

Handle:

- missing Gemini data
- malformed Gemini response
- Gemini fallback state
- missing optional structured context
- render API errors
- backend errors
- invalid prompt
- network errors

A rendering failure must remain distinguishable from a Gemini failure.

Do not show misleading messages such as:

    "Gemini failed"

when the actual renderer failed.

==================================================
23. TESTING REQUIREMENTS
==================================================

Create/update tests for at least:

TEST 1:
Existing manual prompt → renderer.

Expected:
Rendering works exactly as before.

TEST 2:
Gemini enhanced prompt → user accepts → renderer receives enhanced
final prompt.

TEST 3:
Gemini enhanced prompt → user edits it → renderer receives the edited
prompt, NOT the original Gemini prompt.

TEST 4:
Sketch analyzed by Gemini → generated prompt → user edits → renderer
receives edited prompt.

TEST 5:
Gemini unavailable → original/manual prompt still renders.

TEST 6:
Gemini fails → renderer does not make another Gemini request.

TEST 7:
Negative prompt from Gemini is passed correctly when applicable.

TEST 8:
User-edited negative prompt is preserved.

TEST 9:
Verified YOLO V2 category remains correctly propagated.

TEST 10:
No Gemini/structured data → existing renderer contract remains valid.

TEST 11:
All existing rendering options remain intact.

TEST 12:
No ControlNet strength or inference parameter is altered by Gemini.

TEST 13:
Renderer does not automatically invoke Gemini.

TEST 14:
Frontend build succeeds.

Use mocks where appropriate.

DO NOT make real Gemini API calls during automated tests.

DO NOT perform GPU training.

==================================================
24. REGRESSION TESTING
==================================================

Run:

- Phase B frontend Gemini tests
- Phase A backend Gemini tests
- relevant rendering tests
- relevant AI tests
- frontend production build
- backend test suite relevant to changed files

Clearly distinguish:

    Phase C failures
    pre-existing failures
    environment failures

Do not hide pre-existing failures.

==================================================
25. MANUAL SMOKE TEST
==================================================

If the local environment allows it, perform a lightweight manual smoke
test of the integration.

Use an existing test sketch/image.

Verify:

    Sketch
      ↓
    Gemini understanding
      ↓
    Final editable prompt
      ↓
    Render request
      ↓
    Existing renderer

For manual rendering, DO NOT retrain anything.

Use existing trained models/checkpoints.

If the local environment does not have the required renderer dependencies,
do not install large GPU packages just for this phase.

Report the limitation clearly.

==================================================
26. MODEL INTEGRITY CHECK
==================================================

Before and after implementation verify that these have not changed:

    YOLO V2 production weights
    ControlNet 1000-step weights
    SD1.5 model
    LoRA weights
    datasets

Do not regenerate them.

Do not modify them.

If practical, report file timestamps/hash/status evidence.

==================================================
27. DATABASE
==================================================

Do not change database schemas.

Do not add migrations.

Do not introduce persistent Gemini tables.

Phase C does not require storing Gemini understanding permanently.

==================================================
28. UI BEHAVIOR
==================================================

The existing Phase B UX should remain intact.

The user should be able to see:

    AI understanding
    ↓
    editable prompt
    ↓
    Render

Do not remove the review/edit step.

Do not auto-render immediately after Gemini.

The user explicitly controls when rendering happens.

==================================================
29. DO NOT OVER-ENGINEER
==================================================

Keep this phase narrow.

Do NOT build:

- render feedback loops
- automatic image comparison
- AI quality scoring
- automatic prompt regeneration
- autonomous iterative rendering
- production optimization
- production planning intelligence
- new model architecture
- component detection
- automatic material recognition outside Gemini
- dynamic ControlNet parameter selection

Those are future possibilities, not Phase C.

==================================================
30. DOCUMENTATION
==================================================

Create:

    docs/PHASE_C_GEMINI_RENDERER_INTEGRATION_REPORT.md

The report MUST include:

1. Branch name
2. Starting HEAD
3. Working tree status
4. Phase B integration audit
5. Existing renderer architecture
6. Files changed
7. Files created
8. Exact API contract changes
9. Prompt flow
10. Negative prompt flow
11. User intent precedence
12. YOLO V2 integration
13. Gemini fallback behavior
14. Renderer integration details
15. Confirmation of unchanged ControlNet
16. Confirmation of unchanged SD1.5
17. Confirmation of unchanged LoRA
18. Confirmation of unchanged YOLO V2
19. Confirmation of unchanged model weights
20. Confirmation of unchanged datasets
21. Confirmation of zero GPU training
22. Security review
23. Tests performed
24. Test results
25. Build results
26. Manual smoke-test result
27. Known limitations
28. Phase D recommendations

==================================================
31. PHASE D HANDOFF
==================================================

Do NOT assume Phase D yet.

At the end of the report, clearly state what remains for future phases.

Potential future work may include:

- render quality evaluation
- automated prompt/image QA
- production workflow intelligence
- advanced design analysis
- iterative render refinement

But do not implement these now.

==================================================
32. STRICT GIT RULE
==================================================

DO NOT:

    git commit
    git push
    git merge

until I explicitly review and approve the Phase C report.

==================================================
33. FINAL REPORT RESPONSE
==================================================

When implementation is complete:

STOP.

Do not commit.

Do not push.

Do not merge.

Provide:

    Branch:
    Starting HEAD:
    Working tree:
    Files changed:
    Files created:
    Renderer files modified:
    API changes:
    Positive prompt flow:
    Negative prompt flow:
    YOLO V2 handling:
    Gemini fallback:
    ControlNet changes:
    SD1.5 changes:
    LoRA changes:
    Model/weights changes:
    Dataset changes:
    GPU training:
    Database changes:
    Tests:
    Build:
    Manual smoke test:
    Known limitations:

Also create:

    docs/PHASE_C_GEMINI_RENDERER_INTEGRATION_REPORT.md

Then WAIT for my review.

==================================================
FINAL ARCHITECTURAL PRINCIPLE
==================================================

JewelMind should now behave like:

    USER
      ↓
    SKETCH / IMAGE
      ↓
    YOLO V2
      ↓
    GEMINI UNDERSTANDING
      ↓
    USER REVIEW
      ↓
    USER-APPROVED FINAL PROMPT
      ↓
    EXISTING CONTROLNET
      +
    EXISTING SD1.5
      +
    EXISTING LoRA
      ↓
    JEWELLERY RENDER

Gemini is the intelligence layer.

ControlNet + SD1.5 + LoRA remain the rendering engine.

The user remains the final authority.

DO NOT RETRAIN.

DO NOT CHANGE MODEL WEIGHTS.

DO NOT CHANGE CONTROLNET STRENGTH.

DO NOT INVENT DYNAMIC CONDITIONING.

DO NOT COMMIT.

DO NOT PUSH.

IMPLEMENT ONLY PHASE C.