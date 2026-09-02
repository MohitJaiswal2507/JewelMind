# PHASE 5 — JewelMind Interactive Jewellery Design Canvas

## 0. Phase Goal

Transform the existing JewelMind Designs experience into a **real browser-based jewellery design system**, including a professional **Studio media browser/inspector** and a **real interactive jewellery sketch workspace**.

The user must be able to:
- Open a design
- Draw directly on a real canvas using the mouse/pointer
- Use professional sketching tools
- See the sketch workspace beside an AI/design chat panel
- Upload an existing jewellery sketch
- Save the sketch
- Export the sketch as PNG
- Continue using the existing design metadata and future AI-rendering workflow

The visual direction for this phase is based on the supplied reference image.

> **Important:** The reference image is a UI/UX direction. Recreate its layout, hierarchy, density and interaction model, but do not copy proprietary assets or blindly copy exact implementation details.

---

# 1. REQUIRED REFERENCE UI

The Phase 5 workspace should visually follow this structure:

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│  ● ▼   Cursor   Hand   Brush   Eraser   Comment   Layers   Color   +        │
│                                      BLNG / Ring          Undo Redo  View ... │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────────────────────────────┐  ┌──────────────────────┐ │
│  │                                              │  │ Chat                 │ │
│  │                                              │  │ ──────────────────── │ │
│  │                                              │  │                      │ │
│  │          REAL DRAWING CANVAS                 │  │ Prompt suggestions   │ │
│  │                                              │  │ [suggestion] [ ... ] │ │
│  │          Jewellery sketch                   │  │                      │ │
│  │                                              │  │ ┌──────────────────┐ │ │
│  │                                              │  │ │ Ask or request...│ │ │
│  │                                              │  │ └──────────────────┘ │ │
│  │                                              │  │ Classic  Premium      │ │
│  │                                              │  │ Canvas Influence ─●  │ │
│  └──────────────────────────────────────────────┘  └──────────────────────┘ │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

The important visual characteristics are:

### Workspace
- Dark outer application shell
- Dark toolbar/header
- Large light/white drawing canvas
- Canvas occupies the majority of the workspace
- Right-side dark Chat panel
- Rounded cards and panels
- Clear spacing between canvas and chat
- Compact icon-focused toolbar
- Minimal, professional creative-tool appearance

### Canvas
The canvas should be a large white/light drawing surface.

The user should be able to create sketches such as:
- Rings
- Necklaces
- Bracelets
- Earrings
- Pendants
- Other jewellery concepts

The reference screenshot shows a hand-drawn ring sketch on the canvas. The implementation must support the user creating their own drawing; do not hard-code that image as the canvas content.

---

# 2. TECHNOLOGY RULES

## Tailwind CSS — REQUIRED

Use **Tailwind CSS** for:
- Responsive layout
- Spacing
- Sizing
- Typography
- Borders
- Radius
- Backgrounds
- Hover states
- Focus states
- Responsive breakpoints

Do not introduce another CSS framework.

Avoid excessive custom CSS unless technically required for the canvas itself.

---

# 3. shadcn/ui — REQUIRED

Use shadcn/ui for appropriate interface components.

Examples:
- Button
- Tooltip
- Dropdown Menu
- Select
- Slider
- Toggle
- Toggle Group
- Dialog
- Input
- Separator
- Card
- Tabs

For icon-only toolbar buttons:

**Every icon must have a tooltip and accessible label.**

Do not build unnecessary custom UI primitives when shadcn/ui already provides the correct component.

---

# 4. MAIN PAGE LAYOUT

Create a dedicated design workspace layout.

Recommended structure:

```text
DesignWorkspace
├── TopToolbar
│   ├── ToolControls
│   ├── DesignBreadcrumb / DesignName
│   └── History + ViewControls
│
└── WorkspaceBody
    ├── CanvasArea
    │   ├── DrawingCanvas
    │   └── CanvasStatus / Controls
    │
    └── ChatPanel
        ├── ChatHeader
        ├── ConversationArea
        ├── PromptSuggestions
        └── PromptComposer
```

Do not destroy or duplicate the existing Designs architecture.

Inspect the existing Phase 0–4 implementation and integrate into it.

---


# 4A. STUDIO PAGE — REQUIRED VISUAL DIRECTION

The **Studio** area is a separate part of JewelMind from the interactive sketch workspace. Its purpose is to let the user browse generated/uploaded jewellery media and inspect one selected asset in a detailed side panel.

The supplied Studio reference image is the visual direction for this page. Recreate the **layout, hierarchy, density, dark visual language, card treatment, and media-details interaction model** as real responsive UI.

Do NOT use the screenshot as a background or static image.

## Studio Layout

Desktop structure:

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│  JewelMind / app chrome                                                     │
├──────────────┬──────────────────────────────────────────────┬───────────────┤
│              │                                              │               │
│  Sidebar     │  Search                                      │ Media Details │
│              │                                              │               │
│  Account     │  Studio Files (9)                            │ [large image]  │
│  Design      │                                              │               │
│  Studio      │  ┌────────┐ ┌────────┐ ┌────────┐            │ Asset title    │
│  Recent      │  │ media  │ │ media  │ │ media  │            │ metadata       │
│  Trash       │  └────────┘ └────────┘ └────────┘            │               │
│  Settings    │                                              │ Creator        │
│              │  ┌────────┐ ┌────────┐ ┌────────┐            │ Creation date  │
│  Collections │  │ media  │ │ media  │ │ media  │            │ Size           │
│  Summer '25  │  └────────┘ └────────┘ └────────┘            │ Status         │
│  Spring '25  │                                              │               │
│  Winter '24  │                                              │ Download Delete│
│              │                                              │               │
└──────────────┴──────────────────────────────────────────────┴───────────────┘
```

## Left Sidebar

Create a compact dark sidebar containing:

### Account
- User/avatar area
- Design
- Studio — active
- Recent
- Trash
- Settings

### Collections
Provide collection navigation such as:
- Summer '25
- Spring '25
- Winter '24

Collections should be represented as actual interactive navigation/state, not decorative text.

The active Studio item should have a subtle highlighted background.

## Main Studio Content

The main content area should contain:

### Search
A compact search field near the top.

Search should filter the currently loaded Studio media list.

### Heading

```text
Studio Files (N)
```

`N` must be derived from the actual number of available files.

### Media Grid

Use responsive media cards.

Each card should display:
- Thumbnail
- Asset name
- SKU where available
- Media type
- Duration where applicable

Examples from the visual direction:

```text
Pearl Ring - SKU #W250502wg
Twist Earring - SKU #84601
Pearl Love - SKU #40856
Heart Necklace - SKU #681
Butterfly Glasses - SKU #104
Butterfly Bracelet - SKU #40
```

These examples are visual/content references only. Use the existing JewelMind data model and real records where available.

## Media Cards

Cards should:
- Use dark surfaces
- Have rounded corners
- Have subtle borders
- Use large image/video thumbnails
- Maintain consistent aspect ratios
- Show metadata below the thumbnail
- Have a clear hover state
- Be keyboard accessible

Clicking a media card should open/select its details.

Do not navigate away unnecessarily if a side-panel detail view can be used.

---

# 4B. STUDIO MEDIA DETAILS PANEL

The selected media item should open a **right-side Media Details panel** similar to the supplied reference.

The panel should be visually prominent but should not destroy the underlying Studio grid.

## Panel Header

Show:

```text
Media details                                      ×
```

The close button must be a real accessible button.

## Preview

At the top of the panel show a large preview.

Support:
- Images
- Video thumbnails / video preview where the existing media model supports it

The preview should use the available media asset, not a hard-coded screenshot.

## Metadata

Show the selected asset's real metadata where available:

- Asset name
- SKU
- Media type
- Duration
- Creator
- Creation date
- File size
- Status

Example structure:

```text
Pearl Ring - SKU #W250502wg
MP4 - 1m 15s

Creator                         BLNG Team
Creation date                   Sep 02, 2024 - 06:30 PM
Size                            15 MB
Status                          Approved
```

Do not invent values when the backend does not provide them.

## Status

Use a compact status badge.

Example:

```text
✓ Approved
```

Status should come from the actual media/design record.

## Actions

At the bottom of the panel provide:

```text
[ Download ]    [ Delete ]
```

### Download
- Download the actual selected media asset
- Use a sensible filename

### Delete
- Destructive action
- Require confirmation using a shadcn/ui Dialog
- Delete only the selected media
- Refresh the grid after successful deletion
- Show an appropriate error state if deletion fails

Do not fake deletion.

---

# 4C. STUDIO RESPONSIVENESS

Use Tailwind CSS.

### Desktop
Use the three-region composition:

```text
Sidebar | Media Grid | Details Panel
```

### Tablet
- Narrow the sidebar
- Reduce media columns
- Keep the details panel usable

### Mobile
Prefer:

```text
Top navigation
Search
Media grid
Details as Dialog / Drawer
```

Do not force a permanent right-side panel that causes horizontal overflow on small screens.

Use shadcn/ui Dialog/Sheet/Drawer patterns where appropriate.

---

# 4D. STUDIO COMPONENT REQUIREMENTS

Use reusable React components such as:

```text
Studio
├── StudioSidebar
├── StudioHeader
├── StudioSearch
├── MediaGrid
├── MediaCard
├── MediaDetailsPanel
├── MediaPreview
├── MediaMetadata
└── MediaActions
```

Use shadcn/ui for appropriate primitives:
- Button
- Input
- Badge
- Dialog
- Sheet
- Tooltip
- Separator
- Dropdown Menu where needed

Use Tailwind CSS for layout and responsive behavior.

---

# 4E. STUDIO DATA/ARCHITECTURE RULES

The Studio must use the existing JewelMind architecture.

Before implementation:
1. Inspect existing design/media models.
2. Inspect existing APIs.
3. Inspect existing storage configuration.
4. Reuse existing media records where possible.
5. Do not create a parallel media database.
6. Do not hard-code fake media records as the production implementation.

If real media storage is not yet available:
- Build the UI and clean data-access abstraction.
- Use clearly documented development fixtures only if necessary.
- Do not present fixture data as production data.

Any backend/schema changes must use the existing migration architecture.

---

# 4F. STUDIO UX REQUIREMENTS

The Studio should feel like a professional creative/media management application.

Desired characteristics:
- Dark charcoal interface
- Subtle borders
- Muted secondary text
- Rounded media cards
- Large visual thumbnails
- Compact metadata
- Strong selected-state treatment
- Spacious but information-dense layout
- Minimal visual noise

Avoid:
- Generic dashboard-card styling
- Excessive gradients
- Excessive shadows
- Oversized controls
- Bright multicolor UI
- Unnecessary animations

The selected media details panel should feel like a natural inspector panel of a professional creative tool.

---

# 5. TOP TOOLBAR

The toolbar should visually resemble the supplied reference.

Include, at minimum:

### Left-side tools

1. Workspace / menu control
2. Selection tool
3. Hand / pan tool
4. Brush / pencil
5. Eraser
6. Comment/annotation tool
7. Layers
8. Color control
9. Add tool/menu

### Center

Show the current design context:

```text
BLNG / Ring
```

Use the actual design/category/name from the existing design model rather than hard-coding this exact text.

### Right-side controls

Include:
- Undo
- Redo
- Canvas/view mode
- Split/view options if supported
- More/view menu
- Zoom percentage

Example:

```text
↶   ↷   [view] [split] [layout]   100% ▼
```

Use shadcn/ui tooltips and menus.

---

# 6. REAL DRAWING CANVAS

This is the most important Phase 5 requirement.

The browser must contain a **real interactive drawing canvas**.

Do not create:
- A fake image
- A static SVG
- A screenshot
- A visual placeholder
- A div pretending to be a canvas

The user must physically draw with a mouse/pointer.

Use:
- HTML Canvas API, OR
- A suitable drawing/canvas library already compatible with the project

Do not add a large new dependency unless justified.

---

# 7. DRAWING TOOLS

At minimum implement:

### Brush / Pencil
- Freehand drawing
- Adjustable stroke width
- Adjustable color
- Smooth pointer movement

### Eraser
- True erase behaviour
- Adjustable size

### Selection
If a full object selection implementation is feasible within this phase, implement it.

If not, provide a clean selection tool foundation and document the limitation.

### Hand / Pan
Allow users to move around the canvas without drawing.

### Line
Draw straight lines.

### Rectangle
Draw rectangles.

### Ellipse
Draw circles/ellipses.

### Comment / Annotation
Provide a lightweight annotation capability if supported by the existing architecture.

If full collaborative comments are outside the current architecture, implement a local canvas annotation interaction and document the limitation.

---

# 8. DRAWING CONTROLS

Provide controls for:

- Stroke color
- Brush size
- Eraser size
- Opacity where appropriate
- Active tool
- Zoom

Use shadcn/ui components where appropriate.

Example toolbar interaction:

```text
Brush  ●  4px
Eraser ●  12px
Color  ●
Zoom   100%
```

The exact visual treatment should follow the reference's compact professional-tool aesthetic.

---

# 9. UNDO / REDO

Implement proper drawing history.

Requirements:

- Undo last drawing operation
- Redo undone operation
- Multiple undo levels
- Multiple redo levels
- Undo/redo without page reload
- Buttons disabled when no history is available

History should not become unnecessarily huge.

Use an efficient representation suitable for the selected canvas implementation.

---

# 10. CLEAR CANVAS

Provide a clear action.

Because clearing is destructive:

1. User clicks Clear
2. Show a shadcn/ui confirmation dialog
3. User confirms
4. Canvas clears
5. History is updated/reset appropriately

Do not clear immediately without confirmation.

---

# 11. GRID + SYMMETRY

Provide lightweight jewellery-design aids.

### Grid
Toggle:
- Grid ON
- Grid OFF

The grid should be an editing aid.

### Vertical Symmetry

Provide:
- Symmetry OFF
- Symmetry ON

At minimum show a clear vertical centre guide.

If reliable mirrored freehand drawing can be implemented without destabilising the canvas, implement mirrored strokes.

Do not over-engineer this feature.

---

# 12. ZOOM / VIEW

Implement:

- Zoom percentage display
- Zoom in
- Zoom out
- Reset zoom
- Fit canvas where practical

The toolbar should visually communicate the current zoom similarly to the supplied reference.

---

# 13. RIGHT-SIDE CHAT PANEL

The reference UI includes a Chat panel.

Phase 5 should create the **UI foundation** for this panel while respecting the existing JewelMind architecture.

Structure:

```text
Chat
────────────────────

Conversation/messages area


Prompt suggestions
[ suggestion ] [ suggestion ]

┌──────────────────────────────┐
│ Ask or request anything...   │
└──────────────────────────────┘

[ + ] [ Classic ] [ Premium ]   ↑

Canvas Influence ─────●── 60%
```

### Requirements

- Dark panel
- Clear header
- Scrollable conversation area
- Prompt suggestions
- Prompt input
- Send button
- Model/mode controls if supported by existing architecture
- Canvas Influence slider

Use shadcn/ui components.

---

# 14. CHAT FUNCTIONALITY

Do not invent an AI backend if the existing project does not yet provide one.

The panel should be architecturally ready for future AI integration.

If an existing AI/chat API already exists:
- Reuse it.

If it does not exist:
- Build a clean UI/state layer.
- Allow prompt submission to produce an appropriate "not connected / future AI worker" state rather than pretending an AI response happened.

Do not fake successful AI generations.

---

# 15. CANVAS INFLUENCE

Add a slider similar to the supplied reference:

```text
Canvas Influence ─────────●── 60%
```

Use a shadcn/ui Slider.

For Phase 5 this is primarily a design-control/state foundation.

Do not claim that it changes AI generation unless a real AI pipeline already exists.

Persist the selected value in the design workspace state.

---

# 16. PROMPT SUGGESTIONS

Show useful jewellery-specific suggestions.

Examples:

- "A watch made of yellow gold and multiple gemstones."
- "A necklace with pearls and ruby gemstones."
- "Create a minimal platinum ring with a round diamond."
- "Design a vintage-inspired gemstone pendant."

Suggestions should be reusable and easy to extend.

Do not hard-code fake AI output.

---

# 17. EXISTING SKETCH UPLOAD

Keep the existing upload workflow.

Users should still be able to upload:
- PNG
- JPG
- WEBP

Respect the existing size restrictions.

After upload:
- Validate file
- Display preview
- Allow use as reference/current sketch where appropriate
- Preserve the existing design record

Do not remove the existing upload capability.

---

# 18. IMAGE / REFERENCE HANDLING

The canvas workspace may support an uploaded image as a reference layer.

If implemented:

```text
Layers
├── Drawing
└── Reference Image
```

Reference image should be:
- Movable where practical
- Toggleable
- Non-destructive to the drawing

If full layer manipulation is too large for this phase, provide a clean foundation and document the limitation.

---

# 19. SAVE SKETCH

Implement a real Save action.

Before implementation inspect existing backend/domain APIs.

Preferred flow:

```text
Canvas
   ↓
serialize sketch
   ↓
existing Design/Sketch API
   ↓
existing database/storage architecture
```

Do NOT create a separate design database.

Do NOT duplicate the existing design model.

Save:
- Current sketch state
- Relevant metadata
- Design association
- Updated timestamp where appropriate

Show:
- Saving
- Saved
- Save failed

If persistence infrastructure is not yet available, implement the cleanest architecture supported by the existing system and explicitly document the remaining work.

---

# 20. EXPORT PNG

Provide:

**Export PNG**

Requirements:
- Export only the drawing/sketch
- Do not capture browser UI
- Do not include chat panel
- Do not include toolbar
- Grid should not be exported by default
- Use a sensible filename based on the design name

Example:

```text
shadow-ring-sketch.png
```

---

# 21. RESPONSIVE DESIGN

Use Tailwind responsive utilities.

### Desktop

Preferred:

```text
Canvas: ~70–80%
Chat:   ~20–30%
```

The canvas should remain the primary focus.

### Tablet

- Reduce chat width
- Allow toolbar wrapping
- Preserve drawing area

### Small screens

If necessary:
- Stack Chat below canvas
- Collapse secondary toolbar actions
- Use menus for less-important tools
- Keep the drawing canvas usable

Do not create unusable horizontal overflow.

---

# 22. VISUAL DESIGN DIRECTION

Use the supplied screenshot as the primary UI reference.

### Desired characteristics

- Professional creative application
- Dark charcoal/black chrome
- White/light canvas
- Subtle borders
- Rounded panels
- Compact controls
- Minimal visual noise
- Strong hierarchy
- High-quality spacing
- Modern typography
- Subtle active states
- Tool-focused interface

Avoid:
- Excessive gradients
- Huge buttons
- Generic dashboard cards
- Excessive shadows
- Bright multicolor UI
- Cluttered controls

The canvas must visually dominate the workspace.

---

# 23. DO NOT RECREATE THE SCREENSHOT AS AN IMAGE

The screenshot is a **design reference only**.

Every important element must be implemented as real UI.

For example:

- Toolbar = actual buttons
- Canvas = actual canvas
- Chat = actual React component
- Slider = actual slider
- Suggestions = actual buttons
- Zoom = actual state
- Undo/redo = actual functionality

Do not use the screenshot as a background.

---

# 24. ACCESSIBILITY

Implement:

- Keyboard-accessible toolbar
- Accessible labels
- Tooltips
- Focus states
- Good contrast
- Keyboard shortcuts where practical

Recommended shortcuts:

```text
Ctrl/Cmd + Z  Undo
Ctrl/Cmd + Shift + Z  Redo
B  Brush
E  Eraser
H  Hand
V  Select
```

Do not allow shortcuts to interfere with text inputs.

---

# 25. PERFORMANCE

The canvas should remain responsive.

Avoid:
- Re-rendering the entire React tree on every pointer movement
- Storing raw canvas pixels in global React state on every stroke
- Excessive history duplication

Keep high-frequency pointer/drawing state close to the canvas implementation.

---

# 26. ARCHITECTURE RULE

Before writing code:

1. Inspect Phase 0
2. Inspect Phase 1
3. Inspect Phase 2
4. Inspect Phase 3
5. Inspect Phase 4
6. Inspect existing Designs page
7. Inspect existing design models
8. Inspect existing APIs
9. Inspect existing Tailwind configuration
10. Inspect existing shadcn/ui setup

Then integrate.

Do not rewrite working architecture unnecessarily.

---

# 27. DATABASE RULE

Continue using the existing database architecture.

Never create:

```text
New Design DB
New Sketch DB
New Product DB
```

as parallel systems.

If a schema change is genuinely required:
- Use the existing migration system
- Add a reversible migration
- Test it
- Document it

---

# 28. SECURITY

Never commit:

- `.env`
- Database passwords
- API keys
- Supabase service-role keys
- Tokens
- Private credentials

Verify:

```bash
git status
git diff
git ls-files .env
```

`.env` must remain ignored.

Use `.env.example` for required variable names.

---

# 29. TESTING

### Frontend tests

Verify:

- Workspace renders
- Canvas renders
- Brush draws
- Eraser works
- Line works
- Rectangle works
- Ellipse works
- Tool switching works
- Undo works
- Redo works
- Clear confirmation works
- Grid toggle works
- Symmetry guide works
- Zoom works
- Export works
- Upload validation works
- Chat UI works
- Prompt suggestions work
- Canvas Influence slider works
- Responsive layout works

### Backend

If backend changes are made:

- Add API tests
- Run existing backend tests
- Verify database behaviour

### Build

Run the frontend production build.

Run the backend test suite.

Fix Phase 5 regressions before completion.

---

# 30. DOCUMENTATION

Create:

```text
docs/phases/PHASE_5_REPORT.md
```

Include:

1. Phase objective
2. Reference UI interpretation
3. Features implemented
4. Canvas technology
5. Toolbar implementation
6. Chat panel implementation
7. Upload workflow
8. Save workflow
9. Export workflow
10. Backend changes
11. Database changes
12. Files created
13. Files modified
14. Testing
15. Build validation
16. Security verification
17. Known limitations
18. Next phase recommendation

---

# 31. PHASE 5 COMPLETION CHECKLIST

Phase 5 is complete only if:

- [ ] Studio page follows the supplied media-library reference layout
- [ ] Studio sidebar/navigation exists
- [ ] Studio media search and responsive grid work
- [ ] Studio media details inspector works
- [ ] Studio download/delete actions use real data where supported
- [ ] Real drawing canvas exists
- [ ] User can draw with mouse/pointer
- [ ] Brush works
- [ ] Eraser works
- [ ] Selection foundation exists
- [ ] Hand/pan works
- [ ] Line works
- [ ] Rectangle works
- [ ] Ellipse works
- [ ] Color works
- [ ] Brush size works
- [ ] Eraser size works
- [ ] Undo works
- [ ] Redo works
- [ ] Clear confirmation works
- [ ] Grid toggle works
- [ ] Symmetry guide works
- [ ] Zoom works
- [ ] Save workflow works
- [ ] PNG export works
- [ ] Existing upload still works
- [ ] Chat panel exists
- [ ] Prompt suggestions exist
- [ ] Prompt input exists
- [ ] Canvas Influence slider exists
- [ ] Tailwind is used for responsive UI
- [ ] shadcn/ui is used for appropriate components
- [ ] No duplicate database architecture exists
- [ ] No secrets are committed
- [ ] Frontend build passes
- [ ] Backend tests pass where applicable
- [ ] Phase 5 report exists

---

# 32. GIT WORKFLOW

Create and work on:

```bash
phase-5-sketch-canvas
```

Do NOT work directly on `main`.

Before committing:

```bash
git status
git diff
git ls-files .env
```

Then:

```bash
git add .
git commit -m "feat: add interactive jewellery sketch workspace"
git push -u origin phase-5-sketch-canvas
```

Do not merge into main automatically.

Stop after pushing the branch.

I will review and merge it myself.

---

# 33. FINAL ANTIGRAVITY INSTRUCTION

Read this entire `PHASE_5.md` before making changes.

Use the supplied reference screenshots as the visual direction: one for the interactive sketch workspace and one for the Studio media browser/details inspector.

The most important outcome is:

> **When I open JewelMind in the browser, I should see a professional dark creative workspace with a large white jewellery drawing canvas on the left and a dark Chat panel on the right, and I must be able to actually draw on the canvas with my mouse/pointer.**

Do not declare Phase 5 complete if the canvas is only visual.

After completing the phase, produce:

```text
docs/phases/PHASE_5_REPORT.md
```

Then provide a short final summary containing:

- What Antigravity implemented
- What was tested
- What passed
- Known limitations
- Files changed
- Git branch
- Commit hash
- Exact run/test commands

Wait for my review before merging to `main`.
