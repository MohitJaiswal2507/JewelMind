You are implementing PHASE 11 of the JewelMind project.

IMPORTANT:
This is a phase-by-phase capstone project. You MUST inspect the existing repository and understand what is already implemented before changing anything.

==================================================
PROJECT
==================================================

Project:
JewelMind
AI-Powered Jewellery Design, Analysis & Production Planning Platform

Master plan:
PLAN.md

Current status:
Phases 0–10 are completed and merged into main.

Current branch:
Create and work ONLY on:

phase-11-production-management

DO NOT work directly on main.

==================================================
PHASE 11 OBJECTIVE
==================================================

Implement:

PHASE 11 — PRODUCTION MANAGEMENT

According to PLAN.md, this phase consists of:

- Production orders
- Workers
- Machines
- Capacity
- Priorities
- Deadlines

The purpose of this phase is to create the complete production-management foundation that Phase 12 can later use for OR-Tools production optimization.

==================================================
CRITICAL SCOPE BOUNDARY
==================================================

DO NOT implement Phase 12 in this phase.

DO NOT implement OR-Tools optimization.

DO NOT implement automatic production scheduling.

DO NOT implement schedule optimization.

DO NOT implement ML prediction models.

DO NOT implement cost prediction.

DO NOT implement production-time prediction.

DO NOT implement wastage prediction.

DO NOT implement manufacturability analysis.

DO NOT implement deployment.

DO NOT redesign the existing AI rendering pipeline.

DO NOT retrain YOLO.

DO NOT retrain ControlNet.

DO NOT modify the trained ControlNet model.

DO NOT modify existing Phase 6–10 AI functionality unless absolutely required for compatibility.

Phase 11 is specifically the BUSINESS / PRODUCTION MANAGEMENT FOUNDATION.

==================================================
STEP 1 — INSPECT THE REPOSITORY
==================================================

Before writing code:

1. Read PLAN.md completely.
2. Inspect README.md.
3. Inspect the current repository structure.
4. Inspect backend architecture.
5. Inspect frontend architecture.
6. Inspect database models/schema/migrations.
7. Inspect authentication and authorization.
8. Inspect existing Design entities.
9. Inspect existing AIJob / rendering entities.
10. Inspect existing API conventions.
11. Inspect existing frontend UI conventions.
12. Inspect existing tests.
13. Read relevant docs/phases reports from previous phases.
14. Determine exactly what already exists and what can be reused.

DO NOT duplicate existing models, utilities, API patterns, components, or authentication logic.

Before implementation, create a short internal implementation plan based on the actual repository.

==================================================
STEP 2 — ARCHITECTURE PRINCIPLE
==================================================

Production Management must integrate cleanly with the existing JewelMind architecture.

The conceptual flow is:

User
  ↓
Design
  ↓
Production Order
  ↓
Workers / Machines / Capacity / Priority / Deadline
  ↓
Production Management
  ↓
Phase 12 Optimization

Phase 11 does NOT perform optimization.

It stores and manages the information required by Phase 12.

==================================================
STEP 3 — DATABASE DESIGN
==================================================

Inspect the existing database architecture first.

Implement appropriate persistent entities for:

1. ProductionOrder
2. Worker
3. Machine

You may introduce supporting entities/enums only when genuinely necessary.

Do NOT blindly copy this schema if the existing architecture suggests a better normalized structure.

------------------------------------------
PRODUCTION ORDER
------------------------------------------

A production order should support at minimum:

- id
- design_id
- quantity
- priority
- deadline
- status
- created_at
- updated_at

Consider whether the existing project conventions require:

- user_id / owner_id
- notes
- timestamps
- soft deletion
- audit information

Use existing project conventions rather than inventing conflicting patterns.

Production order must reference an existing Jewellery Design.

A production order MUST NOT contain a duplicate copy of the design itself.

------------------------------------------
PRIORITY
------------------------------------------

Implement a controlled priority value.

Recommended levels:

LOW
MEDIUM
HIGH
URGENT

Use the project's existing enum conventions if available.

Do not store arbitrary uncontrolled priority strings if the architecture already supports enums.

------------------------------------------
STATUS
------------------------------------------

Production order should have a lifecycle.

At minimum consider:

PENDING
IN_PROGRESS
COMPLETED
CANCELLED

If the existing architecture suggests a better state model, document the decision.

Do not introduce a complicated workflow that is not needed for Phase 11.

------------------------------------------
WORKER
------------------------------------------

Worker should support production-management information such as:

- id
- name
- role/skill
- availability status
- capacity or working capacity
- created_at
- updated_at

The exact fields must fit the project's architecture.

Examples of useful worker information:

- name
- skill/category
- active/inactive
- hours available per day

Do not implement payroll, attendance, HR, salary, or unrelated employee-management features.

------------------------------------------
MACHINE
------------------------------------------

Machine should support:

- id
- name
- type
- availability status
- capacity
- created_at
- updated_at

Examples:

Machine:
Laser Engraver
Type:
Engraving
Capacity:
8 hours/day

Do not implement machine maintenance management unless absolutely required.

==================================================
STEP 4 — CAPACITY
==================================================

Capacity is a core Phase 11 requirement.

The system should represent production capacity in a way that Phase 12 can consume.

Capacity may be associated with:

- workers
- machines
- production availability

The design should make it possible to answer:

"How much production capacity is available?"

For example:

Worker:
8 hours/day

Machine:
10 hours/day

Do NOT build the optimization algorithm yet.

Just make the capacity data available and validated.

Document the capacity model clearly.

==================================================
STEP 5 — DEADLINES
==================================================

Production orders must support deadlines.

Implement:

- deadline storage
- validation
- display
- editing
- overdue identification where appropriate

Validation should prevent obviously invalid data.

For example:

- deadline should be a valid date/time
- quantity must be positive
- required design must exist

If the project already has date/time conventions, reuse them.

==================================================
STEP 6 — BACKEND API
==================================================

Follow the existing FastAPI architecture.

Implement APIs for:

Production Orders:
- create
- list
- retrieve
- update
- cancel/delete according to project conventions

Workers:
- create
- list
- retrieve
- update
- deactivate/delete according to project conventions

Machines:
- create
- list
- retrieve
- update
- deactivate/delete according to project conventions

Do NOT expose unsafe unrestricted database operations.

Every endpoint must respect authentication and authorization.

A user must not be able to access another user's protected production data unless the existing application explicitly supports shared/admin access.

Production orders must validate their associated Design.

Use Pydantic request/response schemas.

Use proper HTTP status codes.

Use the project's existing error-handling conventions.

==================================================
STEP 7 — PRODUCTION ORDER + DESIGN INTEGRATION
==================================================

A Production Order must reference a real existing JewelMind Design.

Example:

Design:
"Diamond Ring"

Production Order:
Quantity: 25
Priority: HIGH
Deadline: 2026-09-15
Status: PENDING

The API should reject:

- nonexistent design IDs
- invalid quantities
- invalid priority
- invalid status transitions if state validation exists
- invalid deadlines

The production-management layer should reuse existing Design records.

DO NOT create a second design/product database.

==================================================
STEP 8 — FRONTEND
==================================================

Implement a professional Production Management section in the existing React + TypeScript application.

Use the existing frontend architecture.

MANDATORY:

- React
- TypeScript
- Tailwind CSS
- shadcn/ui
- existing project components/design system where appropriate

Do NOT introduce another UI framework.

Do NOT create a completely separate visual style.

The UI should feel like a natural part of JewelMind.

==================================================
PRODUCTION MANAGEMENT UI
==================================================

Create an appropriate production-management experience.

At minimum, users should be able to:

1. View production orders.
2. Create a production order.
3. View production-order details.
4. Edit production-order information.
5. Change appropriate status.
6. Cancel a production order if supported.
7. View priority.
8. View deadline.
9. See whether an order is overdue.
10. View associated design.

The list/table should expose useful information such as:

- Design
- Quantity
- Priority
- Deadline
- Status
- Created date
- Actions

Use responsive design.

The page must work on desktop and smaller screens.

==================================================
WORKER MANAGEMENT UI
==================================================

Provide a Worker management interface.

Users should be able to:

- view workers
- add workers
- edit workers
- activate/deactivate workers

Display useful information such as:

- name
- skill/role
- availability
- capacity

Do NOT build unnecessary HR features.

==================================================
MACHINE MANAGEMENT UI
==================================================

Provide a Machine management interface.

Users should be able to:

- view machines
- add machines
- edit machines
- activate/deactivate machines

Display:

- machine name
- type
- availability
- capacity

==================================================
PRODUCTION DASHBOARD / SUMMARY
==================================================

If appropriate within the existing dashboard architecture, provide a compact production summary.

Useful metrics:

- Total production orders
- Pending orders
- In-progress orders
- Completed orders
- Overdue orders
- Active workers
- Available machines

These are deterministic database-derived values.

DO NOT use AI or ML for these numbers.

Do not overbuild the dashboard.

==================================================
VALIDATION
==================================================

Frontend validation should provide clear feedback.

Backend must independently validate everything.

Examples:

quantity:
> 0

deadline:
valid date/time

priority:
allowed enum only

status:
allowed state only

design:
must exist

worker capacity:
must be non-negative

machine capacity:
must be non-negative

Names:
must satisfy existing project validation rules.

==================================================
AUTHORIZATION / SECURITY
==================================================

Follow existing authentication and authorization.

Production data must not leak across users.

Do not trust IDs supplied by the frontend.

Verify ownership/permissions server-side.

Do not expose database credentials.

Do not modify .env files with secrets.

Do not commit secrets.

==================================================
PHASE 12 COMPATIBILITY
==================================================

This is extremely important.

Phase 12 will introduce:

Google OR-Tools

for production optimization.

Therefore Phase 11 data structures must make it possible for Phase 12 to obtain:

- production orders
- quantities
- priorities
- deadlines
- workers
- worker capacity
- machines
- machine capacity
- availability
- relevant relationships

Do NOT implement the optimizer now.

Instead, ensure the data model is clean and structured enough for an optimizer to consume later.

If useful, create a clean service/repository layer that Phase 12 can later consume.

==================================================
API DESIGN
==================================================

Follow existing endpoint naming conventions.

Potential conceptual structure:

/api/v1/production/orders
/api/v1/production/workers
/api/v1/production/machines

But FIRST inspect the current API architecture and use the project's existing conventions.

Do not blindly create conflicting routes.

==================================================
TESTING
==================================================

Testing is mandatory.

Add backend tests for:

Production Orders:
- create
- retrieve
- list
- update
- invalid quantity
- invalid deadline
- invalid priority
- nonexistent design
- authorization

Workers:
- create
- retrieve
- list
- update
- deactivate
- validation

Machines:
- create
- retrieve
- list
- update
- deactivate
- validation

Production relationships:
- order references design
- protected access
- invalid references rejected

Add frontend tests where the existing frontend testing infrastructure supports them.

At minimum verify:

- forms render
- validation works
- API integration works
- important user interactions work

Do not weaken or delete existing tests.

Run the COMPLETE existing test suite relevant to the modified systems.

==================================================
REGRESSION SAFETY
==================================================

Existing functionality MUST continue working.

Especially protect:

- Authentication
- Design management
- Sketch upload
- Studio
- AI rendering
- YOLO/component detection
- ControlNet rendering
- Existing AI APIs
- Existing frontend routes

Do not modify Phase 10 model files or training outputs.

Do not retrain anything.

==================================================
DATA MIGRATION
==================================================

If database migrations are required:

1. Use the project's existing migration system.
2. Create proper migration files.
3. Do not modify existing migration history destructively.
4. Ensure migrations are reproducible.
5. Document how to apply them.

If the project uses Supabase migrations, follow the existing Supabase migration conventions.

==================================================
DEPENDENCIES
==================================================

Do NOT add dependencies unless necessary.

Before adding a package:

1. Check whether the project already has equivalent functionality.
2. Prefer existing dependencies.
3. If a dependency is required, explain why.
4. Keep the ₹0 project constraint in mind.

DO NOT add OR-Tools in Phase 11 unless the existing architecture absolutely requires a placeholder—and preferably leave OR-Tools for Phase 12.

==================================================
UI QUALITY
==================================================

The Production Management UI should look like a real business application, not a student CRUD demo.

Use:

- clear hierarchy
- consistent spacing
- useful empty states
- loading states
- error states
- confirmation dialogs for destructive actions
- badges for status/priority
- readable tables
- responsive layouts
- accessible controls

Use existing JewelMind visual language.

Do not spend the entire phase redesigning unrelated screens.

==================================================
DOCUMENTATION
==================================================

Create/update Phase 11 documentation.

At minimum create:

docs/phases/PHASE_11.md

and a completion/readiness report, following the conventions of previous phases.

The report must include:

1. Objective
2. Scope
3. Architecture decisions
4. Database changes
5. API changes
6. Frontend changes
7. Validation
8. Authentication/authorization
9. Files created
10. Files modified
11. Dependencies added
12. Database migrations
13. Tests executed
14. Test results
15. Known issues
16. Limitations
17. Phase 12 requirements
18. What was intentionally NOT implemented

Be honest.

Do not claim something was tested if it was not tested.

==================================================
GIT SAFETY
==================================================

Before implementation:

Verify branch:

phase-11-production-management

Do not modify main.

At the end:

Run:

git status

git diff --check

Review changed files.

Ensure:

.env
credentials
model weights
large datasets
temporary generated images

are NOT staged.

Do not commit automatically.

Do not push automatically.

Do not merge automatically.

STOP after implementation and reporting.

==================================================
IMPORTANT AI / GPU RULE
==================================================

There is NO AI training requirement in Phase 11.

Do NOT:

- train YOLO
- train LoRA
- train ControlNet
- run diffusion training
- run GPU experiments
- modify AI weights
- regenerate AI datasets

Phase 11 is application/business logic work.

==================================================
IMPORTANT PHASE SEPARATION
==================================================

DO NOT implement:

Phase 12:
OR-Tools optimization

Phase 13:
Complete dashboard

Phase 14:
Final testing/security hardening

Phase 15:
Deployment

Phase 16:
Documentation/presentation/viva

Only implement Phase 11.

==================================================
DEFINITION OF DONE
==================================================

Phase 11 is complete only when:

[ ] ProductionOrder database model exists
[ ] Worker database model exists
[ ] Machine database model exists
[ ] Priority is modeled correctly
[ ] Deadline is modeled correctly
[ ] Capacity is modeled correctly
[ ] Production status is modeled correctly
[ ] Production orders reference existing Designs
[ ] Backend CRUD/API exists
[ ] Authentication is enforced
[ ] Authorization is enforced
[ ] Validation exists
[ ] Production management frontend exists
[ ] Production order UI works
[ ] Worker management UI works
[ ] Machine management UI works
[ ] Responsive UI works
[ ] Error/loading/empty states exist
[ ] Backend tests pass
[ ] Frontend tests/build pass where applicable
[ ] Existing regression tests pass
[ ] Database migrations are valid
[ ] Documentation is updated
[ ] Phase completion report is created
[ ] git diff --check passes
[ ] No secrets/model weights/large datasets are staged
[ ] No Phase 12 functionality was implemented

==================================================
FINAL RESPONSE FORMAT
==================================================

When finished, DO NOT commit.

Produce:

PHASE 11 IMPLEMENTATION REPORT

Include:

- Summary
- What was implemented
- Architecture decisions
- Database changes
- API endpoints
- Frontend screens/components
- Validation rules
- Authorization rules
- Tests executed
- Exact test results
- Build result
- Migration result
- Files created
- Files modified
- Dependencies added
- Known issues
- Limitations
- Phase 12 preparation
- Anything that remains incomplete

Then show:

GIT STATUS

and:

GIT DIFF CHECK

Finally state clearly:

READY FOR REVIEW
or
NOT READY FOR REVIEW

STOP and wait for my review.

DO NOT proceed to Phase 12.
DO NOT commit.
DO NOT push.
DO NOT merge.