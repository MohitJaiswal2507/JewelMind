JewelMind — AI Design Understanding & Gemini Integration
PHASE 0: READ-ONLY INTEGRATION AUDIT FROM CURRENT MAIN

IMPORTANT:
This is an AUDIT ONLY.

DO NOT modify any source code.
DO NOT create or switch branches.
DO NOT commit.
DO NOT push.
DO NOT merge.
DO NOT delete files.
DO NOT install packages.
DO NOT retrain any AI model.
DO NOT download model weights.
DO NOT change datasets.
DO NOT change database schema.
DO NOT change environment files.
DO NOT expose or print API keys/secrets.

The goal is to deeply inspect the CURRENT `main` branch and determine exactly how we can introduce Gemini-based jewellery design understanding and prompt enhancement into the existing JewelMind pipeline.

==================================================
1. START FROM CURRENT MAIN
==================================================

First verify:

- current branch
- HEAD commit
- working-tree status
- whether local main matches origin/main
- whether there are uncommitted changes
- recent relevant commits

If the current checkout is not `main`, STOP and report it.

Do NOT switch branches yourself.

The audit must represent the actual CURRENT `main` implementation, not an assumed architecture.

==================================================
2. UNDERSTAND THE EXISTING JEWELMIND ARCHITECTURE
==================================================

Inspect the complete relevant implementation across:

FRONTEND:
- frontend/src/
- routing
- dashboard
- design creation
- sketch canvas
- image upload
- prompt input
- AI chat
- rendering UI
- Studio
- production management
- production optimization
- API clients/services
- state management
- hooks
- relevant shadcn components

BACKEND:
- backend/app/
- API routes
- services
- AI services
- rendering services
- design services
- production services
- database models/schemas
- authentication dependencies where relevant
- configuration
- environment handling

AI:
- ai/
- vision/
- rendering/
- training/configuration references
- inference services
- model loading
- rendering pipeline
- prompt construction
- ControlNet integration
- LoRA integration
- YOLO V2 integration

TESTS:
- tests/
- AI tests
- backend tests
- relevant frontend tests

DO NOT modify anything.

==================================================
3. TRACE THE CURRENT DESIGN-TO-RENDER FLOW
==================================================

Determine the ACTUAL current flow for:

A. User draws a jewellery sketch.

Trace:

Canvas
→ save/export
→ API
→ database/storage
→ detection
→ rendering
→ result
→ Studio/design record

B. User uploads an existing jewellery image.

Trace:

Upload
→ storage
→ API
→ YOLO V2
→ rendering
→ result
→ Studio/design record

C. User manually enters a text prompt.

Trace:

Prompt input
→ frontend state
→ API
→ backend
→ prompt construction
→ ControlNet/diffusion
→ result

For every flow, identify:

- exact frontend file
- exact component/function
- exact API endpoint
- exact backend function/service
- exact request schema
- exact response schema
- exact database/storage interaction
- exact AI inference function
- exact model/config used
- where the prompt is created
- where the image/sketch is passed
- where the final render is generated

Include file paths and function/class names.

==================================================
4. AUDIT YOLO V2 INTEGRATION
==================================================

Inspect the CURRENT production YOLO V2 integration.

Verify:

- model path
- model loading
- class mapping
- inference endpoint
- request format
- response format
- confidence handling
- segmentation handling
- CPU/GPU device handling
- error handling
- frontend display
- persistence of detection results

Confirm the current 8-class taxonomy:

0 ring
1 earring
2 pendant
3 necklace
4 bracelet
5 bangle
6 brooch
7 other_jewellery

Do not assume this mapping is correct merely because it is documented elsewhere.

Verify it from the actual current code/model configuration.

Explain exactly where YOLO V2 results could be passed into a future Gemini prompt-generation service.

==================================================
5. AUDIT CURRENT RENDERING PIPELINE
==================================================

Inspect the actual rendering implementation.

Identify:

- diffusion model
- ControlNet model
- ControlNet input preparation
- LoRA
- scheduler
- image preprocessing
- sketch/conditioning preprocessing
- prompt construction
- negative prompt construction
- inference parameters
- seed handling
- resolution
- inference steps
- guidance scale
- ControlNet strength
- category handling
- model loading
- output storage
- rendering API
- frontend rendering flow

Verify the currently intended production models from code/configuration.

Do not change anything.

Most importantly determine:

WHERE should a Gemini-generated prompt enter the current rendering pipeline?

Identify the exact function/file where it should be inserted.

==================================================
6. AUDIT CURRENT PROMPT SYSTEM
==================================================

Find every place where prompts are:

- entered
- stored
- modified
- constructed
- enhanced
- sent to AI
- displayed
- persisted

Determine whether the current system already has:

- prompt enhancement
- AI-generated prompts
- prompt templates
- category-specific prompts
- negative prompts
- system prompts
- rendering prompt builders

Document the actual implementation.

==================================================
7. DESIGN THE PROPOSED GEMINI ROLE
==================================================

DO NOT IMPLEMENT IT.

Instead, determine how Gemini SHOULD fit into the architecture.

The desired behavior is:

-----------------------------------------------
CASE 1 — IMAGE/SKETCH + NO USER PROMPT
-----------------------------------------------

User draws or uploads jewellery.

JewelMind:

Image
→ YOLO V2
→ Gemini Vision
→ Gemini understands the jewellery/design
→ structured design understanding
→ rendering prompt
→ existing ControlNet + diffusion + LoRA
→ final render

Gemini should analyze the actual image/sketch.

The user should NOT be required to type a prompt.

-----------------------------------------------
CASE 2 — IMAGE/SKETCH + USER PROMPT
-----------------------------------------------

User provides:

Image/sketch
+
"a ring with platinum round brilliant diamond..."

Then:

Image
+
YOLO V2 result
+
user prompt
→ Gemini
→ enhanced structured design specification
→ rendering prompt
→ existing renderer

The user's explicit design intent must have priority.

Gemini must improve wording/precision WITHOUT replacing the user's design.

-----------------------------------------------
CASE 3 — USER PROMPT ONLY
-----------------------------------------------

If the current application allows text-only rendering:

User prompt
→ Gemini enhancement
→ rendering prompt
→ existing renderer

Determine whether this flow currently exists.

-----------------------------------------------
CASE 4 — USER DOES NOT WANT ENHANCEMENT
-----------------------------------------------

The user should be able to use their original prompt without Gemini enhancement.

Do not design the system so Gemini is mandatory for every request.

==================================================
8. PROPOSE THE GEMINI DATA CONTRACT
==================================================

DO NOT implement it.

Design a proposed structured output contract.

For example, investigate whether something conceptually similar to this fits the existing application:

{
  "jewellery_type": "ring",
  "material": "platinum",
  "primary_stone": "round brilliant diamond",
  "secondary_stones": [],
  "structure": "...",
  "geometry": "...",
  "symmetry": "...",
  "visible_components": [],
  "design_characteristics": [],
  "user_intent": "...",
  "geometry_preservation": [],
  "rendering_prompt": "...",
  "negative_prompt": "..."
}

IMPORTANT:

Do NOT blindly use this example.

Inspect the current JewelMind architecture first and recommend the smallest clean contract that fits it.

Explain:

- which fields are required
- which are optional
- which should be persisted
- which should only exist during rendering
- which should come from YOLO
- which should come from Gemini
- which should come directly from the user

==================================================
9. USER INTENT VS GEMINI INFERENCE
==================================================

This is a critical design requirement.

Determine how the system should distinguish:

USER EXPLICIT INTENT

from

GEMINI VISUAL OBSERVATION

from

GEMINI ENHANCEMENT

Example:

User:
"platinum ring with round diamond"

Gemini must NOT silently change:

platinum → gold
round diamond → emerald
thin shank → thick shank

Design a proposed precedence model such as:

1. Explicit user requirements
2. Observable geometry/design from image
3. YOLO jewellery category
4. Gemini inferred attributes
5. Safe rendering defaults

But do not assume this exact hierarchy is correct. Analyze and recommend.

==================================================
10. SKETCH UNDERSTANDING
==================================================

Audit how the current application represents sketches.

Determine:

- canvas output format
- resolution
- transparency/background
- line color
- saved PNG/JPEG behavior
- crop/resize
- preprocessing
- whether the original sketch remains available
- whether the renderer receives the original sketch
- whether Gemini could receive the same image
- whether there are any current transformations that could damage Gemini's visual understanding

Recommend the best point to send the image to Gemini.

Do not modify it.

==================================================
11. UPLOADED IMAGE UNDERSTANDING
==================================================

Determine:

- where uploaded images are stored
- whether original images are preserved
- whether they are resized
- whether URLs or storage paths are available
- whether backend can access them
- whether Gemini could receive them
- whether external API calls can safely access the image
- what privacy/security implications exist

Do NOT upload any real user data anywhere.

Do not make external Gemini API calls.

==================================================
12. GEMINI API ARCHITECTURE
==================================================

Research the current codebase configuration and determine the cleanest architecture for Gemini.

Potential conceptual options:

A.
Frontend → Gemini directly

B.
Frontend → FastAPI → Gemini

C.
Frontend → FastAPI → AI service → Gemini

Evaluate them against:

- API key security
- privacy
- error handling
- rate limits
- logging
- cost
- maintainability
- future model replacement
- ability to disable Gemini
- testing

Do NOT add the Gemini dependency yet.

Do NOT create API keys.

Do NOT call Gemini.

Recommend one architecture.

The API key MUST NOT ever be exposed to the frontend if the recommendation requires an API key.

==================================================
13. ₹0 / FREE-TIER REQUIREMENT
==================================================

JewelMind currently has a strict ₹0 budget.

Therefore audit the proposed Gemini integration with:

- free-tier feasibility
- rate limits
- failure behavior
- request frequency
- caching opportunities
- optional enhancement
- fallback behavior

Do NOT assume free-tier limits.

If external current information is required, clearly mark it as external research and verify it separately.

The application must continue functioning if Gemini is unavailable.

Propose:

Gemini available
→ Gemini enhancement

Gemini unavailable
→ graceful fallback

No Gemini key
→ graceful fallback

Rate limit
→ graceful fallback

API failure
→ graceful fallback

Do not implement any of this yet.

==================================================
14. PROPOSE UX FLOW
==================================================

Audit the existing UI and determine where these controls should fit.

Desired conceptual UX:

PROMPT BOX

"Describe your jewellery (optional)"

[ user's prompt ]

[ ✨ Enhance with AI ]

[ Generate Render ]

If no prompt exists:

Gemini can analyze the image/sketch automatically.

After enhancement, the user should be able to see/edit Gemini's generated prompt before rendering if that fits the existing UX.

Determine the best existing component to extend.

Do NOT redesign or modify the UI.

Give exact file/component recommendations.

==================================================
15. PROPOSE AI UNDERSTANDING FLOW
==================================================

Design the recommended architecture:

IMAGE/SKETCH
      +
USER PROMPT (optional)
      +
YOLO V2
      ↓
GEMINI VISION
      ↓
STRUCTURED DESIGN UNDERSTANDING
      ↓
RENDER PROMPT
      ↓
EXISTING CONTROLNET
      +
DIFFUSION
      +
LORA
      ↓
FINAL RENDER

Determine whether YOLO should run:

- before Gemini
- after Gemini
- in parallel

Explain the recommendation.

==================================================
16. PRODUCTION WORKFLOW INTEGRATION
==================================================

Audit the current Production Management and Production Optimization implementation.

Determine how jewellery category currently influences:

- production plans
- processes
- materials
- optimization
- production templates

Recommend how the new "understood jewellery context" could flow into production.

For example:

YOLO:
Ring

Gemini:
Platinum + round diamond + specific design characteristics

Then:

Production Planner
→ Ring workflow
→ material information
→ relevant manufacturing steps

IMPORTANT:

Do not invent production logic that does not currently exist.

Clearly distinguish:

CURRENT CAPABILITY

from

PROPOSED FUTURE CAPABILITY.

==================================================
17. DATA STORAGE / DATABASE IMPACT
==================================================

Determine whether the proposed Gemini integration requires database changes.

Inspect current Design-related models/tables.

Determine whether we can initially store Gemini analysis as:

- JSON metadata
- design metadata
- rendering metadata
- separate analysis record

Recommend the minimum viable approach.

Do NOT change the database.

Do NOT create migrations.

==================================================
18. SECURITY AUDIT
==================================================

Identify risks involving:

- Gemini API key exposure
- user image transmission
- prompt injection through uploaded images
- malicious text prompts
- sensitive design data
- logging
- external API requests
- rate abuse
- oversized images
- Gemini response validation
- arbitrary model output

Recommend mitigations.

Do NOT implement them.

==================================================
19. FAILURE / FALLBACK DESIGN
==================================================

Design expected behavior for:

1. YOLO succeeds, Gemini succeeds
2. YOLO succeeds, Gemini fails
3. YOLO fails, Gemini succeeds
4. YOLO fails, Gemini fails
5. No prompt, sketch exists
6. No prompt, uploaded image exists
7. Prompt exists, no image
8. Prompt + image
9. Gemini returns malformed structured output
10. Gemini times out
11. Gemini API rate limit
12. Gemini unavailable

The renderer should remain usable wherever reasonably possible.

==================================================
20. TESTING STRATEGY
==================================================

Do NOT write tests yet.

Instead identify exactly what tests should eventually be added.

Include:

BACKEND
- Gemini service tests
- schema validation
- fallback behavior
- prompt precedence
- API error handling

AI
- YOLO → Gemini context
- Gemini → renderer prompt
- structured output validation

FRONTEND
- Enhance button
- no-prompt flow
- prompt-only flow
- enhancement editing
- loading/error states

INTEGRATION
- sketch → YOLO → Gemini → renderer
- upload → YOLO → Gemini → renderer
- prompt + image → Gemini → renderer
- Gemini unavailable → renderer fallback

==================================================
21. PERFORMANCE
==================================================

Estimate the likely latency pipeline:

Current:
Image
→ YOLO
→ Renderer

Proposed:
Image
→ YOLO
→ Gemini
→ Renderer

Identify:

- likely additional network latency
- whether Gemini calls should happen only on demand
- whether analysis can be cached
- whether automatic no-prompt analysis should happen at Generate time
- whether enhancement should be explicit

Do not benchmark external APIs.

==================================================
22. DO NOT TRAIN ANYTHING
==================================================

Absolutely NO:

- YOLO training
- ControlNet training
- LoRA training
- dataset generation
- dataset modification
- model conversion
- model replacement

The existing production models remain untouched.

==================================================
23. REQUIRED FINAL REPORT
==================================================

Create ONLY this documentation file:

docs/JEWELMIND_GEMINI_INTEGRATION_AUDIT.md

Do not modify any other file.

The report MUST contain:

1. Executive Summary
2. Current Main Branch State
3. Current Architecture
4. Current Sketch Flow
5. Current Upload Flow
6. Current Prompt Flow
7. Current YOLO V2 Integration
8. Current Rendering Pipeline
9. Current Production Pipeline
10. Current Database/Data Model
11. Proposed Gemini Role
12. Proposed End-to-End Architecture
13. Proposed Gemini Data Contract
14. User Intent vs Gemini Inference Precedence
15. Proposed UX Flow
16. Gemini API Architecture Recommendation
17. ₹0 / Free-Tier Strategy
18. Security Considerations
19. Failure/Fallback Strategy
20. Database Impact
21. Testing Strategy
22. Performance Considerations
23. Exact Files/Functions That Would Need Changes
24. Implementation Plan
25. Risks
26. Open Questions
27. Final Recommendation

==================================================
24. EXACT FILE CHANGE PLAN
==================================================

At the end include a table:

| File | Current Role | Proposed Change | Priority |
|------|--------------|-----------------|----------|

This is a PLAN ONLY.

Do not modify these files.

==================================================
25. IMPLEMENTATION PHASE BREAKDOWN
==================================================

Propose implementation phases, for example:

Phase A
Gemini backend service + schemas

Phase B
Prompt enhancement UI

Phase C
Automatic image/sketch understanding

Phase D
YOLO + Gemini unified context

Phase E
Renderer integration

Phase F
Production workflow integration

Phase G
Testing/security/performance

But determine the actual best breakdown from the codebase.

==================================================
26. FINAL RECOMMENDATION
==================================================

End the report with a clear answer to:

"How should JewelMind transform from:

Upload/Sketch → Render

into:

Upload/Sketch
→ Understand Jewellery
→ Understand Design
→ Generate/Enhance Prompt
→ Render
→ Prepare Production Workflow

using the existing YOLO V2 + ControlNet + LoRA pipeline and Gemini?"

Give ONE recommended architecture.

Do not provide multiple competing architectures without selecting one.

==================================================
27. FINAL STATUS
==================================================

After creating the report:

- show `git status`
- confirm ONLY the requested documentation file was created
- do NOT commit
- do NOT push
- do NOT merge
- do NOT create a branch

Final output should briefly state:

AUDIT COMPLETE

and provide:

- current branch
- HEAD commit
- report path
- files changed
- whether any AI training occurred
- whether any model files changed
- whether any dataset files changed
- recommended next implementation phase

STOP after the audit.