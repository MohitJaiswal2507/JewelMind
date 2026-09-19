JEWELMIND — CANVA-LIKE AI JEWELLERY DESIGN WORKSPACE
=====================================================

BRANCH: phase-g-canva-ai-workspace

You are currently on the `main` branch.

FIRST ACTION:
Create and checkout exactly this new branch:

    phase-g-canva-ai-workspace

The branch must be created from the current `main`.

Do not create any other branch.

============================================================
IMPORTANT PROJECT CONTEXT
============================================================

JewelMind is an AI-powered jewellery design platform.

The existing project already contains:

- React + TypeScript + Vite frontend
- Tailwind CSS
- shadcn/ui
- FastAPI backend
- Supabase/Postgres
- Supabase Storage
- YOLO V2 jewellery classification/segmentation
- Gemini design understanding/prompt enhancement
- ControlNet V2 jewellery renderer
- Stable Diffusion 1.5
- Appearance LoRA
- Studio
- Design Management
- Production Management
- Production Optimization
- Authentication
- Existing AI rendering pipeline

DO NOT replace these systems.

DO NOT build a second renderer.

DO NOT train a new model.

DO NOT retrain YOLO.

DO NOT retrain ControlNet.

DO NOT retrain LoRA.

DO NOT replace the existing renderer architecture.

The existing production renderer remains:

    YOLO V2 where applicable
          +
    Gemini design understanding
          +
    Prompt Compiler
          +
    ControlNet V2
          +
    SD1.5
          +
    Appearance LoRA
          ↓
    Photorealistic Render

The existing production models must remain intact.

============================================================
CORE PRODUCT VISION
============================================================

JewelMind must evolve from a modal/form-heavy rendering workflow into a
Canva-like AI jewellery design workspace.

The core JewelMind experience is:

                    JEWELMIND
                        │
          ┌─────────────┼─────────────┐
          │             │             │
          ▼             ▼             ▼
       TEXT          DOODLE         IMAGE
       INPUT         CANVAS        UPLOAD
          │             │             │
          └─────────────┼─────────────┘
                        ▼
                DESIGN UNDERSTANDING
                        │
              ┌─────────┴─────────┐
              │                   │
            YOLO V2            GEMINI
        "WHAT TYPE?"       "WHAT IS IT?"
              │                   │
              └─────────┬─────────┘
                        ▼
                CURRENT DESIGN STATE
                        │
                        ▼
               ┌─────────────────┐
               │  AI SIDE CHAT   │
               │                 │
               │ "Change gold   │
               │  to platinum"  │
               │                 │
               │ "Make stone    │
               │  larger"       │
               │                 │
               │ "Try emerald"  │
               └────────┬────────┘
                        │
                        ▼
                 USER APPROVES
                        │
                        ▼
                PROMPT COMPILER
                        │
                        ▼
             CONTROLNET + SD1.5
                   + LoRA
                        │
                        ▼
                  PHOTOREAL RENDER
                        │
                        ▼
                     STUDIO

This architecture is the target.

============================================================
THE THREE CORE JEWELMIND CAPABILITIES
============================================================

The application MUST support exactly these three fundamental creation
workflows:

1. TEXT → RENDER
2. DOODLE/SKETCH → RENDER
3. IMAGE → RENDER

These are not three unrelated features.

They must all feed into the same JewelMind design-state and rendering
architecture.

============================================================
1. TEXT → RENDER
============================================================

USER EXPERIENCE:

The user creates/selects a jewellery design through the existing
"Create New Jewellery Design" dialog.

The initial metadata dialog should remain focused on metadata only.

For example:

    Design Name
    Category
    Status
    other existing metadata

After creation, the user clicks:

    OPEN IN CANVA

This takes the user into the new Canva-like JewelMind workspace.

For TEXT → RENDER:

There does not need to be a doodle or uploaded image.

The user opens the Gemini side chat and writes something like:

    "Create a minimalist platinum earring with an oval sapphire."

The selected jewellery category from the initial design dialog should
already be available as context.

The user can optionally press the AI button beside the chat input.

If AI enhancement is requested:

    User Prompt
          ↓
       Gemini
          ↓
    Enhanced Prompt
          ↓
    UI animation
          ↓
    Enhanced prompt replaces the original editable prompt

The enhanced prompt must be visible/editable to the user before rendering.

IMPORTANT:

The user remains the final authority.

Gemini must NOT silently change explicit user requirements.

For example:

User:

    "Create a platinum earring with a blue sapphire."

Gemini must not transform it into:

    "gold earring with diamond."

The existing Phase E.1 prompt-fidelity rules must remain active.

The user can press Enter / Send / Render.

Then:

    Final approved prompt
          ↓
    Prompt Compiler
          ↓
    Existing Renderer V2
          ↓
    Render
          ↓
    Canvas / render area

============================================================
2. DOODLE → RENDER
============================================================

The user can draw directly in the JewelMind Canva workspace.

Existing canvas capabilities should be preserved:

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
- existing canvas behavior

Do not unnecessarily rebuild the existing drawing engine.

The doodle becomes the visual design reference.

Flow:

    User doodles
        ↓
    Current canvas image
        ↓
    Gemini multimodal design understanding
        ↓
    Structured design understanding
        ↓
    Prompt Compiler
        ↓
    ControlNet V2
        +
    SD1.5
        +
    Appearance LoRA
        ↓
    Photorealistic render

Gemini must be able to inspect the current doodle/blueprint.

IMPORTANT:

Do not expose the hidden Gemini-generated renderer prompt to the client
for this flow.

The client should see the understanding/result in a user-friendly way
if appropriate, but the internal renderer instruction generated for
the model remains an implementation detail.

The client should simply be able to say:

    "Render this."

or:

    "Make the metal platinum."

or:

    "Use an emerald instead."

and JewelMind should update the current design state and render.

============================================================
3. IMAGE → RENDER
============================================================

The Gemini side chat must have an ADD / PLUS button.

The user can click it and upload an image/photo of jewellery.

Only supported image files should be accepted.

For example:

    PNG
    JPG/JPEG
    WEBP

The uploaded image becomes the current visual reference.

The user can then type:

    "Make this rose gold and replace the center diamond with
     an oval blue sapphire."

The AI button should be available beside the prompt.

When the user presses AI:

    Uploaded Image
          +
    User Prompt
          ↓
       Gemini
          ↓
    Context-aware enhancement
          ↓
    Enhanced editable prompt
          ↓
    User approves
          ↓
    Renderer

Gemini MUST consider both:

1. the uploaded image
2. the user's written instruction

The enhancement should describe the requested transformation while
preserving relevant structure from the reference image.

Example:

IMAGE:
    silver pendant with round diamond

USER:
    "Make it rose gold with emerald."

Gemini should understand:

    Preserve pendant structure
    Preserve overall geometry
    Change metal → rose gold
    Change gemstone → emerald

Do NOT allow Gemini to randomly redesign the entire jewellery piece
unless the user asks for a redesign.

============================================================
CANVA-LIKE WORKSPACE
============================================================

The current rendering experience should evolve into a proper creative
workspace.

The workspace should feel similar in interaction philosophy to Canva
rather than a traditional form.

Do NOT copy Canva branding or proprietary visual assets.

Create a JewelMind-native design.

Suggested structure:

┌─────────────────────────────────────────────────────────────┐
│ JEWELMIND                         Save   Undo   Redo   ...   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│                 MAIN CREATIVE AREA                          │
│                                                             │
│      Blueprint / Canvas          Render                    │
│                                                             │
│                                                             │
│                                                             │
│                                                             │
├───────────────────────────────────────────────┬─────────────┤
│                                               │             │
│                                               │ GEMINI AI   │
│                                               │             │
│                                               │ conversation│
│                                               │             │
│                                               │             │
│                                               │             │
│                                               │             │
│                                               │             │
│                                               │             │
│                                               │             │
│                                               │             │
│                                               │─────────────│
│                                               │ +  Ask AI   │
└───────────────────────────────────────────────┴─────────────┘

The exact layout can be refined after inspecting the current UI.

IMPORTANT:

The AI chat must be collapsible.

The user can:

    OPEN AI CHAT
    CLOSE AI CHAT

The workspace should remain usable when the chat is collapsed.

Do not force the user to keep the chat open.

============================================================
GEMINI SIDE CHAT
============================================================

This is one of the most important parts of the implementation.

The side chat is not merely a prompt box.

It is the conversational control layer for the CURRENT DESIGN.

The chat must understand the current design context.

Example:

Current Design:

    Type: Earring
    Metal: 18K Yellow Gold
    Gemstone: Diamond
    Cut: Pear
    Style: Minimalist
    Geometry: Long curved drop

User:

    "Make the gold rose gold."

Gemini should understand:

    CHANGE:
        metal = rose gold

    PRESERVE:
        earring
        gemstone = diamond
        pear cut
        overall geometry
        design structure
        style

Then:

    "Make the center stone larger."

Gemini should understand that this refers to the current design.

Then:

    "Try an emerald instead."

Gemini should understand that this refers to the gemstone of the
current design.

The chat must maintain CURRENT DESIGN STATE.

============================================================
CURRENT DESIGN STATE
============================================================

Introduce or extend a structured current-design representation.

Conceptually:

    currentDesignState = {
        category,
        material,
        gemstone,
        gemstoneCut,
        geometry,
        style,
        motifs,
        dimensions,
        userRequirements,
        sourceType,
        sourceImage,
        sourceDoodle,
        currentPrompt,
        currentNegativePrompt,
        currentRender,
        previousRender,
        renderHistory
    }

Use the project's existing types/services where possible.

DO NOT create redundant parallel state systems if an existing
design/render state architecture can be extended.

The design state must distinguish:

    ORIGINAL INPUT
    CURRENT DESIGN SPECIFICATION
    CURRENT RENDER
    PREVIOUS RENDER
    USER MODIFICATIONS

============================================================
ITERATIVE REDESIGN
============================================================

This is mandatory.

JewelMind must support:

    Initial generation
          ↓
       Render 1
          ↓
    User asks for change
          ↓
    Gemini understands CURRENT DESIGN
          ↓
    Renderer uses appropriate previous/current visual reference
          ↓
       Render 2
          ↓
    User asks for another change
          ↓
       Render 3
          ↓
         ...

Example:

USER:

    "Create a platinum pendant with an oval sapphire."

Render 1.

USER:

    "Make the sapphire larger."

Render 2.

USER:

    "Change the metal to rose gold."

Render 3.

USER:

    "Make the chain thinner."

Render 4.

Each subsequent request is a modification of the current design.

Do NOT treat every chat message as a completely independent generation
request.

============================================================
PREVIOUS OUTPUT AS REDESIGN REFERENCE
============================================================

When the user asks to modify an existing render, the system should
use the previous/current render as a visual reference where appropriate.

Conceptually:

    Current Design
         +
    Previous Render
         +
    New User Request
         ↓
       Gemini
         ↓
    Updated structured design state
         ↓
    Prompt Compiler
         ↓
    Renderer with appropriate image/control/reference conditioning
         ↓
    New Render

The purpose is to preserve:

- geometry
- proportions
- composition
- overall design identity
- jewellery type
- relevant structure

while applying the requested modification.

DO NOT blindly start every redesign from an unrelated random generation.

IMPORTANT:

Use the existing renderer capabilities.

Do not invent a new diffusion architecture.

Before implementing this, inspect the existing ControlNet/rendering
pipeline and determine the correct existing mechanism for passing a
previous output/reference image.

If the existing renderer cannot safely use a previous render as an
image reference in the current configuration, do not fabricate a
fake implementation.

Document the limitation and implement the safest compatible approach.

============================================================
USER INTENT PRIORITY
============================================================

The existing Phase E.1 prompt-fidelity behavior MUST remain.

Priority:

    EXPLICIT USER REQUIREMENTS
              >
    USER EDITS / CURRENT DESIGN STATE
              >
    GEMINI UNDERSTANDING
              >
    HIGH-CONFIDENCE YOLO V2
              >
    DEFAULTS

Never allow Gemini to override explicit user intent.

Examples:

USER:
    "Platinum ring with emerald."

Gemini:
    "gold ring with diamond."

Final:
    PLATINUM + EMERALD

USER:
    "No gemstone."

Gemini must NOT inject a diamond.

USER:
    "Thin shank."

Do NOT convert this into a thick/wide shank.

USER:
    "Blue sapphire."

Do NOT retain diamond as the primary gemstone.

Preserve the existing deterministic conflict sanitization.

============================================================
YOLO V2
============================================================

Existing YOLO V2 remains the jewellery-category grounding model.

Current categories:

    0 ring
    1 earring
    2 pendant
    3 necklace
    4 bracelet
    5 bangle
    6 brooch
    7 other_jewellery

YOLO V2 answers primarily:

    "WHAT TYPE OF JEWELLERY IS THIS?"

Gemini answers:

    "WHAT DOES THE DESIGN LOOK LIKE AND WHAT DOES THE USER WANT?"

Do not treat YOLO as the complete design understanding system.

Do not silently replace YOLO V2.

Do not retrain it.

============================================================
CATEGORY CONSISTENCY
============================================================

The recently fixed category mismatch problem must remain fixed.

Canonical category normalization must be used consistently.

For example:

    Earring
    Earrings
    earring
    earrings

must resolve to:

    earring

Do not allow:

    backend = Earring
    frontend = Ring

because of enum/string mismatch.

The UI, Gemini, YOLO, prompt compiler and renderer must use a consistent
canonical category representation.

============================================================
CRITICAL CATEGORY CONFLICT RULE
============================================================

If the current source/reference is a necklace but the user explicitly
requests an earring, do NOT silently render the necklace while the UI
claims it is an earring.

The existing Phase F conflict protection must remain.

A conflict should be clearly surfaced to the user.

The user must be able to resolve it intentionally.

Possible resolution:

    Use User Category
    Use Blueprint Category

Do not silently choose one.

Also ensure that a manual category selection remains authoritative
when the user explicitly changes the category in the UI.

Example:

Prompt:
    "Create an earring."

User manually selects:
    Ring

Expected:

    Ring remains the selected category.

    The UI clearly communicates the disagreement.

    The application does not silently switch to Earring.

Do not regress the Phase F fix.

============================================================
CREATE NEW DESIGN FLOW
============================================================

When the user clicks:

    NEW DESIGN

ONLY the metadata dialog should initially appear.

For example:

    Create New Jewellery Design

    Design Name
    Category
    Status
    other existing metadata

After the user completes the dialog, show:

    OPEN IN CANVA

Do NOT immediately open a large rendering form.

Do NOT force the user to enter rendering parameters before entering
the workspace.

The Canva workspace becomes the primary design environment.

============================================================
OPEN EXISTING DESIGN FLOW
============================================================

When the user clicks an existing design:

    Design Card
        ↓
    Design Detail / entry state
        ↓
    OPEN IN CANVA
        ↓
    Canva workspace

Do not unnecessarily expose a giant metadata dialog again.

============================================================
CRITICAL BUG #1 — DESIGN DETAIL INFINITE LOADING
============================================================

There is an existing serious bug:

When a user opens a design, the application can become stuck on:

    "Loading jewellery design details..."

The loading state can remain indefinitely.

Clicking the X/close button can also fail to recover the user.

FIX THIS AS PART OF THIS BRANCH.

Do not merely increase a timeout.

Find the real root cause.

Audit:

- routing
- route parameters
- design ID
- API calls
- Supabase queries
- authentication
- RLS/ownership
- loading state
- useEffect dependencies
- async state lifecycle
- stale requests
- component unmounting
- close/navigation handlers

The Design Detail flow must have:

    LOADING
    SUCCESS
    ERROR
    NOT FOUND

It must NEVER have:

    LOADING FOREVER

============================================================
CLOSE/X RECOVERY REQUIREMENT
============================================================

The close/X button MUST remain functional even if:

- design fetch is slow
- design fetch fails
- backend is unavailable
- Supabase fails
- malformed response occurs
- authentication expires
- request is still in progress

The user must always be able to leave the screen.

Closing must NOT depend on a successful API request.

Example:

    Open Design
        ↓
    Loading
        ↓
    User clicks X
        ↓
    Immediately return to previous/designs screen

No stuck overlay.

No blocked navigation.

No invisible loading state remaining after navigation.

============================================================
DESIGN DETAIL ERROR STATES
============================================================

If fetch fails:

    Unable to load this jewellery design.

    [Try Again]
    [Back to Designs]

If design does not exist:

    Design not found.

    [Back to Designs]

Do not expose raw backend stack traces.

============================================================
STATE / RACE CONDITION PROTECTION
============================================================

Test:

    Design A
       ↓
    Back
       ↓
    Design B
       ↓
    Back
       ↓
    Design A

No stale state.

No wrong design.

No previous design appearing inside the new design.

If a request for Design A finishes after the user already opened Design B,
Design A's response must not overwrite Design B.

Use appropriate cancellation or request identity protection.

============================================================
ORIGINAL INPUT ↔ RENDER COMPARISON
============================================================

For DOODLE → RENDER and IMAGE → RENDER, provide a button that lets the
user compare the source/reference with the generated render.

Example button:

    COMPARE
or:
    VIEW ORIGINAL & RENDER

For Doodle:

    ORIGINAL DOODLE
          │
          │
          ▼
    GENERATED RENDER

For Image:

    UPLOADED IMAGE
          │
          │
          ▼
    GENERATED RENDER

The comparison UI should show them side-by-side.

Example:

┌─────────────────────────┬─────────────────────────┐
│                         │                         │
│     ORIGINAL DOODLE     │    GENERATED RENDER    │
│                         │                         │
│       ✏️ Sketch         │     💎 Photorealistic  │
│                         │                         │
└─────────────────────────┴─────────────────────────┘

For image input:

┌─────────────────────────┬─────────────────────────┐
│                         │                         │
│     UPLOADED IMAGE      │    GENERATED RENDER    │
│                         │                         │
│     Original Photo      │    JewelMind Output     │
│                         │                         │
└─────────────────────────┴─────────────────────────┘

This comparison feature is NOT required for Text → Render because
there is no original visual input.

============================================================
COMPARISON + ITERATIVE RENDERING
============================================================

The comparison system must understand render iterations.

Example:

    Original Doodle
         ↓
      Render 1
         ↓
    User modification
         ↓
      Render 2

The UI must not accidentally compare the current render with an old
unrelated render.

Track render/source relationships.

Each render should know its relevant source/reference.

Conceptually:

    sourceId
    sourceType
    renderId
    parentRenderId
    createdAt
    prompt/version
    designState/version

Use existing database architecture where possible.

Do not create unnecessary database tables unless needed.

============================================================
GEMINI AI BUTTON
============================================================

The chat input must include an AI enhancement button.

Example:

    [+] [Ask JewelMind to modify the design...] [✨ AI] [Send]

The exact visual design can be refined.

Behavior:

AI OFF:

    User prompt
        ↓
    User presses Enter
        ↓
    Render

AI ON:

    User prompt
        ↓
    Gemini enhancement
        ↓
    Enhanced prompt
        ↓
    Animated replacement
        ↓
    User reviews/edits
        ↓
    Enter
        ↓
    Render

The AI button must NOT automatically trigger rendering.

Gemini enhancement must not silently render.

The user must retain control.

============================================================
PROMPT REPLACEMENT ANIMATION
============================================================

When Gemini enhances a prompt, the original prompt should transition
into the enhanced prompt using a polished fading/replacement animation.

For example:

    Original prompt
          ↓
    subtle fade / transition
          ↓
    Enhanced prompt

Do not make the animation excessive.

It should feel professional and fast.

The enhanced prompt remains fully editable.

The user can:

- edit it
- undo/revert it
- render it
- continue chatting

Existing "Revert" behavior should be preserved or improved.

============================================================
ADD BUTTON / IMAGE UPLOAD
============================================================

The chat input must have an Add (+) button.

Clicking it allows the user to attach an image.

Requirements:

- image-only input
- supported MIME types
- reasonable file-size validation
- preview before submission
- remove attachment
- replace attachment
- clear attachment
- safe object URL cleanup
- no accidental non-image file upload

The image becomes part of the current design context.

============================================================
GEMINI CHAT CONTEXT
============================================================

Gemini should receive only the context necessary for the current task.

Depending on workflow, this may include:

TEXT MODE:

    category
    user prompt
    current design state

DOODLE MODE:

    doodle image
    category
    user prompt
    current design state
    previous design state where relevant

IMAGE MODE:

    uploaded image
    category
    user prompt
    current design state
    previous design state where relevant

REDESIGN MODE:

    current render/reference
    current design state
    user's new instruction
    previous relevant context

Do not send unnecessary secrets.

Gemini API keys must remain server-side.

Never expose Gemini API keys in frontend source code.

============================================================
GEMINI FAILURE / FALLBACK
============================================================

Gemini must remain optional.

If Gemini is unavailable:

- missing API key
- invalid API key
- quota exceeded
- timeout
- HTTP error
- malformed response
- service unavailable

the application must not crash.

Existing deterministic/text fallback behavior should remain.

IMPORTANT:

If the system did not visually analyze an image/doodle because Gemini
was unavailable, DO NOT falsely claim that it understood the image.

Use an honest fallback message.

Example:

    "Visual analysis is unavailable. Your text instructions will be
     used with the available design context."

Do not fabricate visual attributes.

============================================================
TEXT-ONLY MODE WITHOUT GEMINI
============================================================

Text → Render must still work if Gemini is unavailable.

The existing prompt compiler should handle the user's direct prompt.

The renderer must remain usable without Gemini.

============================================================
RENDERER INTEGRATION
============================================================

The existing Renderer V2 remains the production renderer.

Do not create Renderer V3.

Do not change:

- ControlNet model
- SD1.5 base
- Appearance LoRA
- model weights
- training checkpoints

unless absolutely necessary for an integration bug.

Do not modify model files.

Do not retrain.

Existing parameters such as:

- control strength
- guidance scale
- steps
- seed
- resolution
- geometry adapter

must remain controlled by the existing renderer configuration.

Gemini must not be allowed to arbitrarily modify safety-critical
renderer configuration.

============================================================
PROMPT COMPILER
============================================================

Continue using the existing Prompt Compiler.

Its responsibility is to turn:

    current design state
        +
    explicit user requirements
        +
    Gemini structured understanding
        +
    category grounding
        +
    applicable source/reference context

into the final renderer prompt.

The renderer should not receive arbitrary raw Gemini output.

Use structured data and deterministic compilation.

The existing Phase E.1 prompt-fidelity safeguards MUST remain.

============================================================
HIDDEN RENDERER PROMPT
============================================================

For Doodle → Render and Image → Render:

The internal renderer prompt generated from Gemini does not need to be
shown to the client.

The user-facing interface should focus on:

- current design understanding
- user request
- current design state
- optional enhanced prompt
- render result

Do not expose internal system instructions.

============================================================
CHAT CONVERSATION DESIGN
============================================================

The side chat should visually distinguish:

USER
    "Make the stone blue."

JEWELMIND
    "I'll update the gemstone while preserving the current
     jewellery structure."

Then provide an action such as:

    [Apply & Render]

or allow the user to press Enter/Send according to the chosen UX.

Do not force a render after every conversational response.

The AI should be able to discuss the design without immediately
generating an image if the interaction calls for clarification.

============================================================
USER APPROVAL
============================================================

For significant AI-generated changes, the user must remain in control.

The workflow should support:

    User request
        ↓
    Gemini interpretation
        ↓
    Updated design state / enhanced prompt
        ↓
    User reviews
        ↓
    Render

Do not silently make major design changes.

============================================================
DESIGN STATE EXAMPLE
============================================================

Example current state:

    Category:
        Earring

    Metal:
        18K Yellow Gold

    Gemstone:
        Diamond

    Cut:
        Pear

    Style:
        Minimalist

    Geometry:
        Long curved drop

User:

    "Change the diamond to blue sapphire."

Gemini should produce a structured modification like:

    gemstone:
        diamond → blue sapphire

Everything else remains unchanged unless the user requests otherwise.

Then renderer receives the compiled result.

============================================================
ANOTHER DESIGN STATE EXAMPLE
============================================================

User uploads a necklace image.

Current:

    Category:
        Necklace

    Metal:
        Silver

    Gemstone:
        Diamond

User:

    "Make this 18K yellow gold with emeralds."

Expected:

    Category:
        Necklace

    Metal:
        18K Yellow Gold

    Gemstone:
        Emerald

    Preserve:
        reference necklace structure

No accidental conversion to:

    Ring
    Earring
    Diamond

============================================================
NO STALE PREVIOUS DESIGN CONTEXT
============================================================

This is especially important because previous testing exposed stale
state issues.

If the user previously rendered:

    Necklace

and then starts:

    Earring

the necklace must not leak into the earring generation.

Clear or replace:

- current source image
- current doodle
- current category
- current prompt
- current Gemini context
- current render reference
- current design state

when starting a genuinely new design.

At the same time, iterative modifications within the SAME design must
preserve context.

Correct distinction:

    NEW DESIGN
        → clear previous design context

    SAME DESIGN / MODIFY
        → preserve current design context

============================================================
DESIGN OPEN / CANVA ENTRY
============================================================

For an existing design:

    Designs
      ↓
    Select design
      ↓
    Design entry/detail
      ↓
    Open in Canva

The user should not be trapped in a loading screen.

For a newly created design:

    New Design
      ↓
    Metadata dialog
      ↓
    Open in Canva
      ↓
    Empty creative workspace

============================================================
EMPTY CANVA WORKSPACE
============================================================

When the user opens a newly created design, the workspace should clearly
support:

    Draw something
    Upload an image
    Ask JewelMind to create something

The user should immediately understand the three modes.

Possible empty-state content:

    Start designing with JewelMind

    ✏️ Draw
    Upload
    ✨ Describe your design

Do not overload the screen with forms.

============================================================
CANVA WORKSPACE UX
============================================================

The workspace should contain:

1. Main canvas / visual workspace
2. Render area
3. Collapsible Gemini side chat
4. Basic design controls
5. Current category/context
6. Source/reference controls
7. Render history where appropriate
8. Compare button for visual-source workflows
9. Save functionality
10. Navigation back to Designs/Studio

Use the existing JewelMind visual language.

Maintain:

- dark premium aesthetic
- gold accent
- professional jewellery-studio feel
- strong typography hierarchy
- responsive behavior
- Tailwind
- shadcn/ui

Do not turn it into a generic chatbot UI.

============================================================
RESPONSIVE BEHAVIOR
============================================================

Desktop:

    Canvas + Render + collapsible right AI panel

Tablet:

    adaptable workspace
    chat can become overlay/drawer

Mobile:

    AI chat should become a drawer/sheet
    source/render can switch between tabs or stacked views
    no horizontal overflow

The workspace must remain usable.

============================================================
ACCESSIBILITY
============================================================

Ensure:

- keyboard navigation
- Enter to send/render where appropriate
- Escape to close panels/modals
- accessible buttons
- tooltips for icon-only controls
- visible focus states
- screen-reader labels
- sensible disabled states
- loading announcements where appropriate

============================================================
SECURITY
============================================================

Preserve existing security.

Never expose:

- Gemini API key
- Supabase service-role key
- internal credentials
- backend secrets
- stack traces

Image uploads must be validated.

Users must not be able to access another user's private design merely by
changing a design ID.

============================================================
SUPABASE / STORAGE
============================================================

Reuse existing storage architecture.

Do not duplicate images unnecessarily.

For uploaded source images:

- store safely
- associate with the current design
- preserve ownership
- clean temporary object URLs
- use existing storage conventions

For renders:

- associate render with current design
- preserve render history where supported
- preserve source/reference relationship

Do not redesign the database unless required.

============================================================
STUDIO INTEGRATION
============================================================

Existing Studio must continue working.

A generated render should remain compatible with Studio.

The user should be able to:

    Render
      ↓
    Save
      ↓
    Studio
      ↓
    View / manage / download / delete
      ↓
    Production workflow

Do not break existing Studio functionality.

============================================================
PRODUCTION MANAGEMENT
============================================================

Do not remove or break:

- Production Management
- Production Optimization
- existing design metadata
- existing production workflows

This phase is primarily the creative workspace and AI interaction layer.

============================================================
AI RENDERING BACKWARD COMPATIBILITY
============================================================

Existing manual rendering must continue working.

The following must continue:

    Manual prompt → Render

    Category selection → Render

    Sketch → Render

    Existing Studio render workflows

    Gemini unavailable → fallback render

Do not force Gemini into every render.

============================================================
DO NOT HIDE EXISTING FUNCTIONALITY
============================================================

This is a UX redesign/integration, not a feature deletion.

Existing functionality should either:

- remain accessible
- move into the new workspace
- be represented by a better UX

Do not simply remove controls because the new workspace looks cleaner.

============================================================
PHASE F CATEGORY FIX PRESERVATION
============================================================

Preserve all fixes from the recently completed category-consistency
work.

Especially:

- canonical category normalization
- backend category validation
- conflict detection
- HTTP 409 conflict protection
- manual category authority
- correct UI state
- no false "Active Rendering Conditioning"
- no stale blueprint/category mismatch

Do not regress these fixes.

============================================================
DESIGN DETAIL BUG — DEEP TESTING
============================================================

Test:

1. Open Design A
2. Load detail
3. Open Canva
4. Close Canva
5. Open Design B
6. Return
7. Open Design A

Also:

1. Open Design A
2. Immediately click X
3. Verify exit

Also:

1. Disconnect/fail backend
2. Open Design
3. Verify error
4. Click X
5. Verify exit

Also:

1. Open invalid design ID
2. Verify "Design not found"
3. Click Back
4. Verify Designs page

Never allow infinite loading.

============================================================
GEMINI WORKFLOW TEST MATRIX
============================================================

Test all three workflows.

-----------------------------------
TEXT → RENDER
-----------------------------------

Input:

    "Create a platinum ring with an oval sapphire."

Test:

- direct render
- AI enhancement
- editable enhanced prompt
- Enter to render
- Gemini unavailable
- user changes enhanced prompt
- category consistency

-----------------------------------
DOODLE → RENDER
-----------------------------------

Input:

    hand-drawn jewellery sketch

Test:

- Gemini visual understanding
- render
- hidden renderer prompt
- current design state
- comparison button
- modify via chat
- second render
- previous/current reference handling

-----------------------------------
IMAGE → RENDER
-----------------------------------

Input:

    jewellery image

Test:

- upload
- preview
- remove
- Gemini image understanding
- user prompt
- AI enhancement
- render
- comparison button
- modify via chat
- second render

============================================================
ITERATIVE REDESIGN TEST MATRIX
============================================================

Test:

Render 1:

    platinum pendant + sapphire

Modification:

    "Make the sapphire larger."

Expected:

    pendant remains pendant
    platinum remains platinum
    sapphire remains sapphire
    only requested change occurs

Modification 2:

    "Change the metal to rose gold."

Expected:

    sapphire remains
    pendant remains
    geometry remains as much as renderer allows
    metal changes

Modification 3:

    "Make the chain thinner."

Expected:

    current design remains
    chain changes

No random reset to an unrelated design.

============================================================
PROMPT FIDELITY REGRESSION
============================================================

Preserve all Phase E.1 regression cases, including:

1. platinum round brilliant diamond thin shank ring
2. 18k yellow gold emerald oval pendant
3. rose gold minimalist necklace with small diamonds
4. silver hoop earring with three diamonds
5. platinum brooch with blue sapphire
6. yellow gold bangle with engraved floral pattern, no gemstone invention
7. white gold tennis bracelet with round diamonds
8. art deco brooch sterling silver baguette diamonds black onyx
9. vintage floral pendant rose gold oval blue sapphire + diamond accents
10. user edit emerald → pear shaped
11. Gemini unavailable oval sapphire pendant in platinum
12. no gemstone platinum minimalist ring
13. negative prompt safety
14. pipeline prompt builder integration

Do not break them.

============================================================
NO AI MODEL TRAINING
============================================================

Absolutely NO:

- YOLO training
- ControlNet training
- LoRA training
- dataset generation
- bulk image generation
- model replacement

This is an application integration/UI/UX/state-management phase.

============================================================
PERFORMANCE
============================================================

Do not make the workspace unnecessarily slow.

Avoid:

- duplicate Gemini requests
- duplicate render requests
- duplicate image uploads
- repeated YOLO inference
- unnecessary Supabase calls
- infinite polling
- repeated state-triggered API calls

AI enhancement should only happen when the user explicitly requests it.

Rendering should only happen when the user explicitly sends/renders.

Do not automatically render after every Gemini response.

============================================================
ERROR HANDLING
============================================================

Every asynchronous workflow must have:

    loading
    success
    error
    cancellation

No indefinite spinners.

For rendering:

    Preparing design...
    Understanding design...
    Rendering...
    Complete

If render fails:

    Render failed.

    [Try Again]

Do not lose the current design state.

============================================================
IMPLEMENTATION PROCESS
============================================================

STEP 1 — INSPECT

Before making substantial changes:

Inspect:

- current frontend routing
- current Designs page
- Design Detail page
- New Design dialog
- existing canvas
- existing AiRenderModal
- current Gemini UX
- current Gemini backend
- current renderer service
- Prompt Compiler
- YOLO integration
- ControlNet integration
- Studio
- Supabase design/media schema
- current render history architecture
- current category normalization
- Phase F fixes

Do not rewrite components blindly.

Reuse existing services and components where appropriate.

STEP 2 — ARCHITECTURE PLAN

Before implementation, determine:

- which existing components can be extended
- which components need restructuring
- how current design state should work
- how Gemini chat context should work
- how source/reference images are represented
- how render history is represented
- how iterative redesign will reference previous outputs
- how comparison mode should obtain source/render pairs

Do not create unnecessary duplicate architecture.

STEP 3 — IMPLEMENT

Implement the complete workspace and bug fixes.

STEP 4 — TEST

Run unit, integration, and browser tests.

STEP 5 — REAL MANUAL QA

Actually use the application.

Do not rely only on unit tests.

============================================================
REQUIRED TESTS
============================================================

Run existing backend tests:

    pytest backend/tests

Run AI tests:

    pytest tests/ai

Run frontend tests:

    npm test -- --run

Run production build:

    npm run build

If project commands differ, inspect package configuration and use the
correct existing commands.

============================================================
BROWSER QA
============================================================

Perform real browser testing.

Test:

A. New design
B. Open in Canva
C. Empty workspace
D. Draw
E. Doodle → Render
F. Compare doodle/render
G. Text → Render
H. AI enhancement
I. Enhanced prompt animation
J. Image upload
K. Image → Render
L. Compare image/render
M. Gemini side chat
N. Modify current design
O. Second render
P. Third render
Q. Collapse chat
R. Reopen chat
S. Close workspace
T. Open existing design
U. Design Detail loading
V. Error state
W. Immediate close while loading
X. Navigation back
Y. Studio
Z. Existing manual rendering

============================================================
REAL AI/GPU VALIDATION
============================================================

Where practical, use the existing RTX 4060 environment for real smoke
tests.

Do not train.

Validate at least:

1. Text → Render
2. Doodle → Render
3. Image → Render
4. Iterative redesign
5. One category-consistency conflict
6. One Gemini enhancement

Use the existing production models.

Do not modify their weights.

============================================================
VISUAL QUALITY
============================================================

Do not claim visual success merely because an API returned 200.

For the real GPU smoke tests:

Actually inspect the generated outputs.

Confirm:

- correct jewellery category
- reasonable geometry adherence
- requested material
- requested gemstone
- prompt fidelity
- no obvious stale-source contamination
- no unrelated jewellery type
- no accidental necklace/ring/earring substitution

============================================================
IMPORTANT "GEMINI LIVE" CLARIFICATION
============================================================

The desired user experience is that Gemini can see the current doodle or
uploaded image and understand it conversationally.

Use the existing Gemini integration and currently supported multimodal
API mechanism.

Do NOT invent an unsupported "Gemini Live" API implementation.

If the current project has a supported Gemini Live/multimodal mechanism,
inspect and use it appropriately.

Otherwise implement the same user-facing conversational experience using
the existing supported Gemini backend integration.

The requirement is:

    Gemini can understand the current visual context conversationally.

Do not fabricate APIs, SDK methods, models, or capabilities.

============================================================
NO HARDCODED TEST DATA
============================================================

Do not make the application appear to work by hardcoding:

    "earring"
    "necklace"
    "ring"

or fake Gemini responses.

All category/design data must come from the actual application state,
YOLO, Gemini, user input, or existing backend logic.

============================================================
NO MOCK FALLBACK FOR PRODUCTION YOLO
============================================================

Do not reintroduce the previous YOLO mock fallback bug.

Production inference must use the actual YOLO V2 model.

If production dependencies/model are unavailable, fail explicitly and
honestly rather than returning fake classifications.

============================================================
UI DESIGN REQUIREMENTS
============================================================

The workspace should feel:

- premium
- professional
- modern
- minimal
- jewellery-focused
- creative
- AI-native

Use:

- current JewelMind dark theme
- gold accent
- existing typography
- Tailwind
- shadcn/ui
- subtle animations
- polished hover/focus states
- clean spacing

Do not over-animate.

The AI chat should feel integrated into the design studio, not like a
generic ChatGPT clone.

============================================================
IMPORTANT: DO NOT OVERWRITE THE CURRENT UI BLINDLY
============================================================

Before modifying the UI, inspect the current components and preserve
useful functionality.

The goal is:

    RESTRUCTURE + IMPROVE

not:

    DELETE + REBUILD EVERYTHING WITHOUT CONTEXT

============================================================
REPORT
============================================================

Create:

    docs/PHASE_G_CANVA_AI_WORKSPACE_REPORT.md

The report must contain:

1. Branch name
2. Starting main commit
3. Architecture audit
4. Current architecture discovered
5. New workspace architecture
6. Text → Render implementation
7. Doodle → Render implementation
8. Image → Render implementation
9. Gemini side-chat implementation
10. Current design state implementation
11. Iterative redesign implementation
12. Previous-render/reference implementation
13. Comparison mode
14. AI enhancement button
15. Prompt animation
16. Category consistency preservation
17. Design Detail infinite-loading bug root cause
18. Design Detail fix
19. Close/X recovery fix
20. Error handling
21. Race-condition protection
22. Supabase/storage changes, if any
23. Files changed
24. Tests added
25. Backend test results
26. AI test results
27. Frontend test results
28. Production build results
29. Browser QA
30. RTX 4060 smoke tests
31. Actual visual validation
32. Model integrity verification
33. Confirmation that no training occurred
34. Security audit
35. Performance observations
36. Known limitations
37. Screenshots/evidence where useful

============================================================
MODEL INTEGRITY
============================================================

Explicitly verify that these were NOT retrained/replaced:

YOLO V2:

    runs/segment/runs/segment/runs/jewellery/
    yolo11m-seg-jewelmind-v2-continued/weights/best.pt

ControlNet V2:

    outputs/rendering_v2_controlnet/
    controlnet_rendering_v2_final

SD1.5 base model

Appearance LoRA

Also confirm datasets were not modified.

============================================================
GIT RULES
============================================================

The ONLY branch allowed for this work is:

    phase-g-canva-ai-workspace

Create it from current `main`.

During implementation:

    commits are NOT allowed
    pushes are NOT allowed
    merges are NOT allowed

Do not commit until I review the report.

Do not push until I explicitly approve.

Do not merge until I explicitly approve.

============================================================
FINAL ACCEPTANCE CRITERIA
============================================================

The phase is considered PASS only if:

[ ] New Design opens metadata dialog first
[ ] Metadata dialog has Open in Canva
[ ] Existing design can open into Canva workspace
[ ] Design Detail no longer gets stuck indefinitely
[ ] Close/X works while loading
[ ] Close/X works after loading failure
[ ] Back navigation works
[ ] Browser Back works
[ ] Direct design URL works
[ ] Invalid design gives proper not-found state
[ ] API failure gives proper error state
[ ] Retry works
[ ] No stale design state
[ ] Design A → B → A works
[ ] Existing category consistency fix remains intact
[ ] Manual category selection remains authoritative
[ ] Category conflicts are surfaced
[ ] No false active conditioning state
[ ] Canva-like workspace exists
[ ] Gemini side chat exists
[ ] Chat can collapse
[ ] Chat can reopen
[ ] Text → Render works
[ ] Doodle → Render works
[ ] Image → Render works
[ ] AI enhancement button works
[ ] Enhanced prompt is editable
[ ] Enhanced prompt replacement has polished animation
[ ] User can render with Enter/Send
[ ] Add/+ image upload works
[ ] Image preview works
[ ] Image removal works
[ ] Gemini receives image context where appropriate
[ ] Gemini receives doodle context where appropriate
[ ] Gemini respects explicit user intent
[ ] Gemini does not expose hidden renderer instructions
[ ] Gemini failure is non-blocking
[ ] Text rendering works without Gemini
[ ] Current design state is maintained
[ ] Chat understands current design
[ ] User can modify current design conversationally
[ ] Previous render/current reference is used appropriately for redesign
[ ] Render 2 preserves Render 1 design identity where appropriate
[ ] Render 3 preserves current design identity where appropriate
[ ] Doodle/source ↔ render comparison works
[ ] Image/source ↔ render comparison works
[ ] Comparison does not use stale unrelated renders
[ ] Text mode does not require visual comparison
[ ] Studio remains functional
[ ] Existing manual rendering remains functional
[ ] YOLO V2 remains the real production detector
[ ] ControlNet V2 remains unchanged
[ ] SD1.5 remains unchanged
[ ] Appearance LoRA remains unchanged
[ ] No AI model retraining
[ ] No dataset modification
[ ] No secrets exposed
[ ] Backend tests pass
[ ] AI tests pass
[ ] Frontend tests pass
[ ] Production build passes
[ ] Browser QA passes
[ ] RTX 4060 smoke tests pass
[ ] Actual render outputs inspected
[ ] No fake/mock production AI behavior
[ ] No hardcoded category behavior
[ ] No unnecessary duplicate AI requests
[ ] No unnecessary duplicate renders
[ ] No infinite loading states
[ ] No broken existing functionality

============================================================
FINAL INSTRUCTION
============================================================

Implement the complete JewelMind Canva-like AI creative workspace and
the Design Detail loading/close bug fix described above.

Do not hallucinate APIs or capabilities.

Inspect the existing code before changing it.

Reuse the existing JewelMind architecture wherever possible.

Do not create a second renderer.

Do not retrain any model.

Do not replace YOLO V2.

Do not replace ControlNet V2.

Do not replace SD1.5.

Do not replace Appearance LoRA.

Do not expose Gemini API keys.

Do not expose hidden renderer prompts.

Do not fabricate visual understanding when Gemini is unavailable.

Do not silently override explicit user intent.

Do not silently mix previous design context into a new design.

Do not silently mix categories.

Stay on:

    phase-g-canva-ai-workspace

After implementation:

1. Run all tests.
2. Run production build.
3. Perform real browser QA.
4. Perform real RTX 4060 smoke validation where applicable.
5. Inspect actual generated images.
6. Create:

    docs/PHASE_G_CANVA_AI_WORKSPACE_REPORT.md

7. Check git status.
8. STOP.

DO NOT COMMIT.
DO NOT PUSH.
DO NOT MERGE.

Wait for my review.