# JewelMind — Phase 3: Jewellery Design Management

## Status

Phase: 3
Name: Jewellery Design Management
Branch: phase-3-design-management

Previous Phase:
Phase 2 — Authentication, Environment & Database

Current Objective:
Build the complete Jewellery Design Management foundation on top of the existing authenticated JewelMind architecture.

---

# 1. IMPORTANT DEVELOPMENT RULE

You are working inside the existing JewelMind repository.

DO NOT rebuild the project from scratch.

DO NOT replace the existing architecture.

DO NOT introduce a new framework unnecessarily.

DO NOT remove existing working functionality from Phase 0, Phase 1, or Phase 2.

Before modifying anything:

1. Inspect the existing repository.
2. Read:
   - PLAN.md
   - README.md
   - docs/architecture/*
   - docs/phases/PHASE_2_REPORT.md
   - existing backend configuration
   - existing authentication implementation
   - existing database/migration structure
   - existing frontend structure
3. Understand the existing conventions.
4. Reuse existing components and utilities wherever appropriate.

The existing authentication system must continue working after Phase 3.

---

# 2. PHASE 3 OBJECTIVE

Implement the Jewellery Design Management module.

The user should be able to:

1. Log in.
2. Access a personal design workspace.
3. Create a jewellery design.
4. View their designs.
5. View a single design.
6. Edit a design.
7. Delete a design.
8. Filter/search designs.
9. Categorize designs.
10. Upload/reference a sketch image where the architecture supports it.
11. See design status.
12. Prepare the design data structure that future AI rendering and production-planning phases will consume.

The goal is to establish the core Design entity and complete CRUD workflow.

---

# 3. DO NOT IMPLEMENT AI YET

This phase is NOT the AI generation phase.

Do not implement:

- image generation models
- sketch-to-render AI
- Stable Diffusion
- ControlNet
- LoRA
- Hugging Face inference
- GPU workers
- AI queues
- production prediction
- gemstone prediction
- material prediction

Those belong to later phases.

However, the database and API architecture must be designed so those systems can be added without redesigning the Design entity.

---

# 4. DESIGN DOMAIN

Create a proper Design domain.

A Design belongs to one authenticated User.

Conceptually:

User
 |
 +---- Design
        |
        +---- metadata
        +---- category
        +---- status
        +---- sketch
        +---- future AI rendering
        +---- future production planning

A user must NEVER be able to access another user's designs.

All design queries must be scoped to the authenticated user.

---

# 5. DESIGN DATABASE MODEL

Create the Design SQLAlchemy model following the existing project conventions.

Recommended fields:

- id
- user_id
- name
- description
- category
- status
- sketch_image_url
- rendered_image_url
- ai_prompt
- created_at
- updated_at

Use appropriate database types.

IDs should follow the project's existing ID strategy.

Timestamps should follow the existing project conventions.

Do not duplicate user information inside the Design table.

---

# 6. DESIGN CATEGORY

Create a controlled category system.

Initial categories:

- Ring
- Necklace
- Earrings
- Bracelet
- Bangle
- Pendant
- Other

Do not hard-code category strings throughout the frontend.

Create a central TypeScript representation for frontend usage.

The backend must validate category values.

---

# 7. DESIGN STATUS

Create a controlled design lifecycle.

Initial statuses:

- draft
- ready
- rendering
- rendered
- archived

The system should be designed so future statuses can be introduced without major refactoring.

Do not pretend AI rendering exists yet.

For this phase, the application may primarily use:

draft
ready
archived

The rendering-related states exist for future integration.

---

# 8. DATABASE MIGRATION

Create a proper Alembic migration for the Design table.

The migration must:

1. Create the designs table.
2. Add the user foreign key.
3. Add required constraints.
4. Add appropriate indexes.
5. Respect existing database conventions.
6. Support rollback.

Do not manually modify the production Supabase database.

Use Alembic.

Run:

alembic upgrade head

and verify the migration succeeds.

Also verify:

alembic downgrade -1

if appropriate in the local development environment.

Then restore:

alembic upgrade head

Do not leave the database in a downgraded state.

---

# 9. DATABASE INDEXING

Consider indexes for:

- user_id
- category
- status
- created_at

The most important access pattern is:

"Get all designs belonging to the current authenticated user."

Optimize for that query.

Do not add unnecessary indexes.

---

# 10. BACKEND SCHEMAS

Create Pydantic schemas following the existing project structure.

At minimum:

DesignCreate
DesignUpdate
DesignResponse
DesignListResponse

If the existing API architecture uses a generic response wrapper, follow that convention.

Do not create a second response-format system.

---

# 11. BACKEND API

Create a versioned Design API under the existing API structure.

Suggested endpoints:

POST   /api/v1/designs
GET    /api/v1/designs
GET    /api/v1/designs/{design_id}
PATCH  /api/v1/designs/{design_id}
DELETE /api/v1/designs/{design_id}

Optional filtering:

GET /api/v1/designs?category=ring
GET /api/v1/designs?status=draft
GET /api/v1/designs?search=gold

Only implement filtering that fits naturally into the existing architecture.

Do not over-engineer search.

---

# 12. AUTHORIZATION

This is CRITICAL.

Every Design endpoint must use the existing authentication mechanism.

Example:

User A creates:

Design A

User B must NOT be able to:

- retrieve Design A
- update Design A
- delete Design A
- infer Design A's existence through an API response

Use proper ownership checks.

Do not rely on the frontend for authorization.

Authorization must be enforced in the backend.

---

# 13. ERROR HANDLING

Use the existing JewelMind exception and response conventions.

Expected cases:

404:
Design does not exist OR does not belong to the authenticated user.

400/422:
Invalid design data.

401:
Unauthenticated request.

Do not expose database internals.

Do not return raw SQLAlchemy errors.

---

# 14. FRONTEND DESIGN WORKSPACE

Create a proper authenticated Design Workspace.

Suggested route:

/designs

The page should contain:

- Page heading
- Create Design button
- Search
- Category filter
- Status filter
- Design cards/grid
- Empty state
- Loading state
- Error state

The UI should work well on:

- desktop
- tablet
- mobile

---

# 15. USE TAILWIND CSS

Tailwind CSS is mandatory.

Use Tailwind for:

- spacing
- layout
- grid
- responsive behavior
- typography
- states
- positioning

Do not create a giant custom CSS file for layout.

Follow the existing Tailwind setup.

Responsive breakpoints should be intentional.

Example:

Mobile:
1-column design cards

Tablet:
2-column

Desktop:
3 or 4-column depending on available width.

Do not force a fixed width.

---

# 16. USE SHADCN/UI

shadcn/ui is mandatory for UI components where applicable.

Reuse the existing shadcn components.

Use appropriate components such as:

- Button
- Card
- Input
- Textarea
- Select
- Badge
- Dialog
- Dropdown Menu
- Skeleton
- Alert
- Separator

Only add new shadcn components when actually required.

Do not install an unrelated component library.

Do not introduce Material UI, Chakra UI, Ant Design, Bootstrap, etc.

---

# 17. CREATE DESIGN FORM

Create a design creation/editing interface.

Fields:

Design Name
Description
Category
Status

Prepare the form architecture so sketch upload can be connected cleanly.

Validation should exist on the frontend.

Backend validation remains authoritative.

Show useful validation messages.

Do not allow empty design names.

---

# 18. DESIGN DETAILS PAGE

Create:

/designs/:id

The page should show:

- Design name
- Description
- Category
- Status
- Created date
- Updated date
- Sketch image if available
- Rendered image if available
- Edit action
- Delete action

If there is no sketch:

Show a clean empty state.

If there is no rendered image:

Show:

"AI rendering will be available in a future phase."

Do not create fake AI output.

---

# 19. DESIGN CARD

Each design card should show:

- design name
- category
- status
- thumbnail/placeholder
- updated date
- quick actions

Use shadcn/ui Card.

Use Badge for category/status.

Cards must be responsive.

---

# 20. DELETE DESIGN

Implement a safe deletion flow.

Do NOT immediately delete when the user clicks Delete.

Show a confirmation dialog.

Example:

"Delete this design?"

" This action cannot be undone."

Actions:

Cancel
Delete

Use shadcn/ui Dialog/AlertDialog if available.

---

# 21. SEARCH AND FILTERING

Implement basic client/server-compatible filtering.

Support:

Search by design name.

Filter by:

Category
Status

The UI should make it obvious when filters are active.

Include a clean empty-result state.

Example:

"No designs match your filters."

Provide a clear way to reset filters.

---

# 22. SKETCH IMAGE ARCHITECTURE

Do NOT build the full image upload/storage system unless the existing Phase 3 architecture explicitly requires it.

However, the Design model should contain the appropriate field for a future sketch URL/reference.

Future architecture:

User
 |
Design
 |
Sketch
 |
Object Storage
 |
AI Rendering Worker

Do not store binary image data directly inside PostgreSQL.

Do not store large images as database blobs.

The future implementation will use object storage.

---

# 23. RENDERED IMAGE ARCHITECTURE

The Design entity may contain:

rendered_image_url

but this phase must NOT generate the image.

This field is preparation for the future AI pipeline.

Future flow:

Sketch
   |
   v
AI Queue
   |
   v
GPU / Hugging Face Worker
   |
   v
Rendered Image
   |
   v
Object Storage
   |
   v
Design.rendered_image_url

Do not implement that pipeline now.

---

# 24. FRONTEND API LAYER

Use the existing typed API client.

Do not use random fetch calls throughout components.

Create a Design service following the existing:

frontend/src/services/api/

architecture.

Suggested:

designService.ts

Include typed functions:

createDesign()
getDesigns()
getDesign()
updateDesign()
deleteDesign()

Reuse authentication handling.

---

# 25. TYPESCRIPT TYPES

Create proper Design types.

Example conceptual structure:

Design {
    id
    userId
    name
    description
    category
    status
    sketchImageUrl
    renderedImageUrl
    createdAt
    updatedAt
}

Use the project's actual naming convention.

Do not use `any` unless absolutely unavoidable.

---

# 26. TESTING — BACKEND

Add tests for:

1. Create design while authenticated.
2. Create design without authentication.
3. Get user's designs.
4. Get individual design.
5. Update design.
6. Delete design.
7. Invalid category.
8. Missing design.
9. User cannot access another user's design.
10. User cannot update another user's design.
11. User cannot delete another user's design.
12. Filtering by category.
13. Filtering by status.

Tests must use the existing test infrastructure.

Do not modify tests merely to make them pass.

---

# 27. TESTING — FRONTEND

Verify:

- TypeScript compilation
- production build
- design list renders
- empty state works
- loading state works
- error state works
- create form works
- edit form works
- delete confirmation works
- responsive layout works

Run the existing frontend validation commands.

---

# 28. SECURITY CHECK

Before finishing:

Verify:

- no secrets added
- no `.env` files tracked
- no Supabase password in source code
- no JWT secret in source code
- no credentials in tests
- no hardcoded API keys

Run Git checks.

---

# 29. RESPONSIVENESS REQUIREMENT

Test at minimum:

Mobile:
375px width

Tablet:
768px width

Desktop:
1280px width

Large desktop:
1440px+

The application must not:

- horizontally overflow
- clip buttons
- break forms
- produce unreadable cards
- require desktop-only interactions

---

# 30. ACCESSIBILITY

Use semantic HTML.

Buttons must be actual buttons.

Inputs must have labels.

Dialogs must be keyboard accessible.

Images must have meaningful alt text.

Do not rely only on color to communicate status.

---

# 31. DOCUMENTATION

Update:

README.md

PLAN.md

Create:

docs/phases/PHASE_3_REPORT.md

Also update relevant architecture/UML documentation if the existing project structure requires it.

Document:

- Design entity
- API endpoints
- database migration
- frontend workflow
- authorization model
- testing
- known limitations
- future AI integration points

---

# 32. UML

Update the UML documentation.

At minimum include:

## Class Diagram

User
Design

Relationship:

User 1 ---- * Design

## Use Case Diagram

Authenticated User:

- Create Design
- View Designs
- View Design
- Edit Design
- Delete Design
- Filter Designs

## Sequence Diagram

Create Design:

User
 |
Frontend
 |
API
 |
Auth
 |
Design Service
 |
Database
 |
Response

Keep diagrams consistent with the actual implementation.

---

# 33. DO NOT BUILD FUTURE PHASES

Do not implement:

AI rendering
Sketch-to-image
Production planning
Material prediction
Gemstone recommendation
AI worker
GPU queue
Hugging Face worker
Cloudflare deployment
Production deployment

These are future phases.

Only prepare clean integration points.

---

# 34. CODE QUALITY

Follow existing JewelMind conventions.

Prefer:

- small functions
- clear names
- typed interfaces
- dependency injection
- reusable services
- reusable UI components
- meaningful error handling

Avoid:

- giant components
- duplicated API calls
- duplicated validation
- unnecessary abstractions
- unnecessary dependencies
- placeholder fake functionality

---

# 35. MIGRATION SAFETY

Before migration:

Inspect the existing Alembic state.

After migration:

Verify:

alembic current

Then verify the designs table exists in Supabase.

Do not destroy existing Phase 2 data.

The existing users table must remain intact.

---

# 36. FINAL VALIDATION

Before declaring Phase 3 complete, run:

Backend tests
Frontend tests/build
Database migration validation
Authorization tests
Git secret scan
TypeScript validation

Everything must pass.

If something fails:

FIX IT.

Do not simply document a known failure as "passed".

---

# 37. PHASE 3 COMPLETION REPORT

Create:

docs/phases/PHASE_3_REPORT.md

The report MUST contain:

1. Executive Summary
2. What Was Implemented
3. Database Changes
4. Alembic Migration
5. Backend API
6. Authentication & Authorization
7. Frontend Changes
8. Tailwind Usage
9. shadcn/ui Components
10. Design Workflow
11. API Testing
12. Frontend Testing
13. Security Validation
14. UML Updates
15. Files Created
16. Files Modified
17. Known Limitations
18. Future AI Integration Points
19. Commands Used
20. Final Validation Results

Clearly mark each validation:

PASS
FAIL
NOT APPLICABLE

Do not claim something was tested if it was not actually tested.

---

# 38. STOP CONDITION

When Phase 3 is complete:

STOP.

Do not automatically begin Phase 4.

Do not implement AI.

Do not modify unrelated architecture.

Wait for explicit approval to continue.

---

# 39. FINAL RESPONSE TO ME

When finished, give me a concise summary containing:

Phase 3 Status:
PASS / FAIL

Implemented:
- ...
- ...
- ...

Tests:
- Backend: X/X
- Frontend: PASS/FAIL
- Database: PASS/FAIL
- Security: PASS/FAIL

Files:
- ...

Known Issues:
- ...

Next Phase:
Phase 4 — [name]

Also tell me exactly what I should test manually before I commit and merge the branch.

Remember:

I will review the Phase 3 report first.

I will then test the application.

After I approve it, I will commit the branch and merge it into main.

Do not assume the merge has happened.