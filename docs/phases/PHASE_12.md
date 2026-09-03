JewelMind — PHASE 12 IMPLEMENTATION PROMPT
===========================================

PHASE NAME:
Phase 12 — Production Optimization

BRANCH:
phase-12-production-optimization

IMPORTANT:
You are implementing ONLY Phase 12.
Do not implement Phase 13, 14, 15, or 16.
Do not modify or retrain any existing AI model.
Do not modify ControlNet, YOLO, Stable Diffusion, LoRA, datasets, training pipelines, or model weights.
Do not redesign unrelated existing functionality.

==================================================
1. FIRST: INSPECT THE EXISTING PROJECT
==================================================

Before writing any code:

1. Confirm the current Git branch and repository state.
2. Read PLAN.md completely enough to understand the Phase 12 objective.
3. Inspect the existing Phase 11 implementation:
   - ProductionOrder
   - Worker
   - Machine
   - ProductionService
   - Production API routes
   - Production frontend
   - Alembic migration
   - Existing tests
4. Inspect the existing authentication/authorization architecture.
5. Inspect existing frontend styling/component conventions.
6. Inspect existing backend dependency management.
7. Inspect existing documentation structure.

Do NOT assume names, schemas, routes, or database relationships.
Reuse the existing Phase 11 architecture wherever appropriate.

Before implementation, provide a short internal implementation plan.

==================================================
2. PHASE 12 OBJECTIVE
==================================================

Build the first intelligent production scheduling and optimization layer of JewelMind using:

Google OR-Tools
CP-SAT Solver

The system should take Phase 11 production data and generate an optimized production schedule while respecting:

- Production order priorities
- Production order deadlines
- Production order quantities
- Worker availability
- Worker capacity
- Worker skills
- Machine availability
- Machine capacity
- Production sequencing constraints where applicable

The output should be a structured production schedule that can be displayed in the JewelMind UI.

==================================================
3. SCOPE
==================================================

Phase 12 includes:

A. OR-Tools integration
B. Scheduling data model
C. Scheduling/optimization service
D. Production constraints
E. Optimization objectives
F. Schedule generation API
G. Schedule persistence where appropriate
H. Schedule visualization UI
I. Schedule validation
J. Automated tests
K. Documentation

Phase 12 does NOT include:

- ML prediction models
- Cost prediction ML
- Labor-hour prediction ML
- Metal wastage prediction ML
- New AI training
- ControlNet training
- YOLO training
- LoRA training
- Diffusion model changes
- AI model weight modifications
- Deployment
- Final dashboard redesign
- Final security audit
- Capstone presentation work

==================================================
4. OR-TOOLS DEPENDENCY
==================================================

Add Google OR-Tools using the project's existing dependency management conventions.

Prefer the existing uv workflow if that is how the backend dependencies are currently managed.

Do NOT introduce unnecessary dependencies.

Verify the installed OR-Tools version.

Document the chosen version.

Do NOT silently change unrelated dependencies.

==================================================
5. UNDERSTAND PHASE 11 DATA
==================================================

Use the existing Phase 11 entities as the source of truth.

ProductionOrder provides:

- id
- design_id
- quantity
- priority
- deadline
- status

Worker provides:

- id
- name
- skill
- capacity_hours_per_day
- is_available

Machine provides:

- id
- name
- machine_type
- capacity_hours_per_day
- is_available

Do not duplicate these entities.

Do not create a second production-order database.

==================================================
6. SCHEDULING DATA MODEL
==================================================

Design a clean representation for an optimized production schedule.

The schedule should be able to represent at minimum:

- schedule/job ID
- production order ID
- worker ID
- machine ID where required
- start time/day
- end time/day
- allocated duration
- quantity/batch information
- scheduling status
- optimization metadata where useful

The design must support future extension.

Avoid overengineering.

If persistence is needed, create an appropriate database model and Alembic migration.

If a transient solver-result representation is sufficient for part of the workflow, keep that distinction clear.

==================================================
7. PRODUCTION PROCESS MODEL
==================================================

Do NOT invent unrealistic jewellery manufacturing processes without documenting the assumption.

Phase 12 needs a practical scheduling abstraction.

Use the existing Phase 11 worker skill and machine type fields.

Create a clean mapping/configuration layer for production operations where necessary.

For example, a future operation may require:

- specific worker skill
- machine type
- estimated duration
- required capacity

Do NOT hard-code a giant unrealistic manufacturing ruleset.

The architecture should make it easy to add more operation requirements later.

If the existing database does not contain operation-level manufacturing estimates, create a minimal, transparent Phase 12 abstraction rather than pretending the system has data it does not have.

Document all assumptions.

==================================================
8. CP-SAT MODEL
==================================================

Implement the scheduling model using OR-Tools CP-SAT.

Use integer time units appropriate for CP-SAT.

Do NOT use floating-point variables where CP-SAT integer modeling is required.

The model should consider:

### Production order constraints

- Each schedulable order must receive a valid schedule.
- Quantity must be respected.
- Completed/cancelled orders should not be scheduled unless explicitly requested by the API.
- Deadlines must be represented.
- Priority must influence optimization.

### Worker constraints

- Unavailable workers cannot receive work.
- Worker capacity must not be exceeded.
- A worker should not perform overlapping tasks.
- Required skills must be respected.

### Machine constraints

- Unavailable machines cannot receive work.
- Machine capacity must be respected.
- A machine should not perform overlapping tasks.
- Machine requirements must be respected.

### Scheduling constraints

- No impossible overlapping assignments.
- Valid start/end times.
- Duration must be positive.
- Work must occur within the configured scheduling horizon.

==================================================
9. OPTIMIZATION OBJECTIVE
==================================================

Define a transparent optimization objective.

The initial objective should prioritize:

1. Avoiding missed deadlines
2. Respecting urgent/high-priority orders
3. Reducing overall production completion time / makespan
4. Efficiently utilizing available worker and machine capacity

Do NOT claim the solver produces a globally optimal real-world factory schedule unless that is actually guaranteed by the model.

Clearly distinguish:

- hard constraints
- soft constraints
- optimization objectives

Use weighted objectives carefully.

Document the objective function.

==================================================
10. SCHEDULING HORIZON
==================================================

Create a configurable scheduling horizon.

For example:

- start date
- number of production days

Do not hard-code a single date range.

Provide safe defaults.

Validate:

- horizon is positive
- horizon is not unreasonably large
- deadlines are valid
- schedule timestamps are valid

==================================================
11. SOLVER CONFIGURATION
==================================================

Create controlled solver configuration.

At minimum consider:

- time limit
- number of workers/solver threads where appropriate
- deterministic behavior where practical
- solver status

The API must handle:

- OPTIMAL
- FEASIBLE
- INFEASIBLE
- UNKNOWN
- MODEL_INVALID

Do not pretend an infeasible model succeeded.

Return a useful error/result message explaining the state.

==================================================
12. SCHEDULING SERVICE
==================================================

Create a dedicated service layer.

For example:

ProductionOptimizationService

Responsibilities:

- retrieve eligible production orders
- retrieve available workers
- retrieve available machines
- validate scheduling inputs
- build CP-SAT model
- solve model
- translate solver result into domain objects
- validate generated schedule
- return optimization metrics

Do not put CP-SAT logic directly inside FastAPI route handlers.

Keep the solver logic testable independently.

==================================================
13. API
==================================================

Add Phase 12 endpoints under the existing production API architecture.

Example structure:

POST
/api/v1/production/optimize

Purpose:
Generate an optimized production schedule.

Potential request fields:

- order IDs or selection criteria
- scheduling start date
- horizon days
- optional solver time limit

Potential response:

- solver status
- schedule
- unscheduled orders
- objective/metrics
- makespan
- deadline violations if any
- capacity information
- generated timestamp

Add a schedule retrieval endpoint if persistence is implemented.

For example:

GET
/api/v1/production/schedules

GET
/api/v1/production/schedules/{id}

Use the existing authentication conventions.

==================================================
14. AUTHORIZATION / USER ISOLATION
==================================================

This is mandatory.

A user must only be able to optimize and view their own:

- Production Orders
- Workers
- Machines
- Schedules

Never allow cross-user scheduling.

Do not trust IDs supplied by the frontend.

Verify ownership server-side.

Unauthenticated requests must be rejected.

Cross-user resource access must return the existing appropriate error behavior.

==================================================
15. FRONTEND
==================================================

Extend the existing Production UI rather than creating a disconnected page.

Add an optimization/scheduling section.

Suggested flow:

Production Management
        ↓
Select production orders
        ↓
Configure scheduling horizon
        ↓
Click "Optimize Production"
        ↓
Solver runs
        ↓
Show solver status
        ↓
Show optimized schedule

UI should clearly communicate:

- optimization in progress
- successful optimization
- feasible but not proven optimal
- infeasible schedule
- solver failure
- no eligible orders
- missing worker capacity
- missing machine capacity

==================================================
16. SCHEDULE VISUALIZATION
==================================================

Create a useful schedule visualization.

A Gantt/timeline-style interface is preferred.

Example:

Worker A
| Order 1 | Order 1 | Order 4 |

Worker B
| Order 2 | Order 2 | Order 3 |

Machine 1
| Casting | Casting | Free |

Show:

- production order
- worker
- machine
- start
- end
- duration
- priority
- deadline status

Make the UI responsive.

Use existing:

- React
- TypeScript
- Tailwind CSS
- shadcn/ui

Do not introduce another UI framework.

==================================================
17. OPTIMIZATION SUMMARY
==================================================

Show useful metrics after optimization.

For example:

- Orders scheduled
- Orders unscheduled
- Total production time
- Makespan
- Worker utilization
- Machine utilization
- Deadline status
- Solver status
- Optimization runtime

Do not display fabricated values.

All metrics must come from actual solver/domain results.

==================================================
18. INFEASIBLE SCHEDULE HANDLING
==================================================

This is extremely important.

If the model is infeasible:

DO NOT generate fake schedule data.

Instead show:

"Schedule could not be generated with the current constraints."

Provide useful diagnostic information where possible, such as:

- insufficient worker capacity
- insufficient machine capacity
- unavailable required skill
- deadline too restrictive
- invalid production configuration

The backend must return a structured response.

The frontend must handle it gracefully.

==================================================
19. VALIDATION
==================================================

After OR-Tools returns a schedule, perform application-level validation.

Verify:

- no worker overlaps
- no machine overlaps
- all assignments reference valid resources
- unavailable resources were not assigned
- worker skills are valid
- machine requirements are valid
- duration is positive
- schedule is inside the horizon
- deadlines are handled correctly
- production quantities are represented correctly

Do not assume the solver output is valid simply because CP-SAT returned a solution.

==================================================
20. TESTING
==================================================

Add comprehensive Phase 12 tests.

At minimum test:

### Solver

- basic feasible schedule
- multiple orders
- priority handling
- deadline handling
- worker capacity
- worker availability
- worker skill matching
- machine capacity
- machine availability
- machine requirement matching
- no overlapping worker assignments
- no overlapping machine assignments
- scheduling horizon
- infeasible schedule
- solver status handling

### API

- authenticated optimization
- unauthenticated rejection
- user isolation
- invalid request validation
- empty order set
- invalid order ID
- cross-user order protection

### Persistence

If schedules are persisted:

- create schedule
- retrieve schedule
- user isolation
- schedule integrity

### Regression

Run the COMPLETE existing backend test suite.

Run the COMPLETE existing AI regression suite.

Phase 12 must not break:

- YOLO
- Diffusion
- ControlNet
- dataset loaders
- training infrastructure
- authentication
- designs
- sketches
- Studio
- Production Management

==================================================
21. PERFORMANCE / SAFETY
==================================================

Do not allow arbitrary huge optimization requests.

Protect the API against:

- enormous scheduling horizons
- thousands of uncontrolled solver variables
- unreasonable solver time limits

Set safe validation boundaries.

Do not run optimization indefinitely.

Keep the solver configurable.

==================================================
22. DOCUMENTATION
==================================================

Create:

docs/phases/PHASE_12.md

and:

docs/phases/PHASE_12_REPORT.md

Documentation must include:

- objective
- architecture
- OR-Tools version
- CP-SAT model
- hard constraints
- soft constraints
- objective function
- scheduling assumptions
- API endpoints
- database changes
- frontend changes
- solver behavior
- infeasibility handling
- test results
- known limitations
- Phase 13 readiness

Be honest about limitations.

Do not claim production-grade factory optimization if the model is still a capstone-level abstraction.

==================================================
23. GIT SAFETY
==================================================

Work ONLY on:

phase-12-production-optimization

Do NOT commit automatically.

Do NOT push automatically.

Do NOT merge automatically.

Do NOT modify main.

Do NOT delete previous phase work.

Do NOT commit:

- .env
- credentials
- secrets
- model weights
- datasets
- generated images
- cache directories
- temporary files
- huge solver artifacts

Verify .gitignore before finishing.

==================================================
24. FINAL VERIFICATION
==================================================

Before stopping, run:

1. Phase 12 backend tests
2. Complete backend tests
3. Complete AI regression tests
4. Frontend TypeScript check
5. Frontend production build
6. git diff --check

Also verify:

- migration is valid
- API routes are registered
- frontend calls the correct backend endpoints
- authentication is enforced
- user isolation works
- solver handles infeasible models
- no Phase 13 work was added
- no AI model was modified

==================================================
25. FINAL REPORT FORMAT
==================================================

At the end, provide a detailed report containing:

### Phase 12 Status

### What Was Implemented

### OR-Tools / CP-SAT Architecture

### Constraints

### Optimization Objective

### Scheduling Assumptions

### API Endpoints

### Database Changes

### Frontend Changes

### Solver Result Handling

### Infeasibility Handling

### Tests

Show exact numbers:

Backend:
X passed / X failed

Phase 12:
X passed / X failed

AI regression:
X passed / X failed

Frontend:
TypeScript result
Build result

Git:
Current branch
git status
git diff --stat
git diff --check

### Files Created

### Files Modified

### Dependencies Added

### Known Limitations

### Phase 13 Readiness

==================================================
26. VERY IMPORTANT FINAL RULE
==================================================

STOP after the final report.

Do NOT:

- commit
- push
- merge
- start Phase 13
- modify AI models
- train anything
- deploy anything

Wait for my review.

==================================================

SUCCESS CRITERIA
================

Phase 12 is considered successful only if:

1. OR-Tools CP-SAT is genuinely integrated.
2. Production data from Phase 11 is used.
3. Scheduling constraints are real and enforced.
4. Worker and machine conflicts are prevented.
5. Priority/deadline objectives affect scheduling.
6. Infeasible schedules are handled correctly.
7. The generated schedule is validated.
8. The schedule is visible in the frontend.
9. Authentication and user isolation are enforced.
10. Automated tests pass.
11. Existing AI tests continue passing.
12. Frontend builds successfully.
13. No AI models are retrained or modified.
14. No Phase 13 functionality is implemented.
15. No commit/push/merge is performed.

Implement carefully, inspect existing code before making architectural decisions, reuse existing conventions, and stop for my review when complete.