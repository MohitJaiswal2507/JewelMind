# PHASE 1 — ARCHITECTURE & TECHNICAL FOUNDATION
## JewelMind
### Database, API Contract, Configuration & Frontend Integration Foundation

**Phase:** 1  
**Phase Name:** Architecture & Technical Foundation  
**Project:** JewelMind  
**Status:** Not Started  
**Branch:** `phase-1-architecture`  
**Budget:** ₹0  
**Execution:** Antigravity

---

# IMPORTANT — PHASE BOUNDARY

You are working on **JewelMind Phase 1 only**.

Phase 0 established the repository, frontend foundation, FastAPI foundation, AI subsystem structure, documentation, and zero-cost strategy.

This phase now establishes the **technical foundation connecting those pieces**.

Do NOT implement the full application.

Do NOT jump ahead to:

- Authentication
- User registration/login
- Full Supabase integration
- Sketch upload
- AI rendering
- YOLO
- Diffusion
- ControlNet
- XGBoost
- OR-Tools
- AI queue implementation
- Production scheduling
- Final dashboard
- Final production UI
- Deployment

Those belong to later phases.

If a future feature requires a placeholder/interface, create the smallest clean contract necessary and stop there.

---

# 1. OBJECTIVE

The objective of Phase 1 is to establish the architectural contracts that future JewelMind phases will build upon.

At the end of this phase, the project should have:

```text
Frontend
    │
    │ typed API client
    ▼
FastAPI Backend
    │
    ├── configuration
    ├── standardized errors
    ├── logging
    └── database foundation
             │
             ▼
       PostgreSQL/Supabase
```

The actual database service does not need to be connected in this phase unless required for validating the SQLAlchemy/Alembic foundation.

---

# 2. PHASE 1 TARGETS

Complete:

```text
[ ] Review Phase 0 implementation
[ ] Review PLAN.md
[ ] Review architecture documentation
[ ] Establish backend configuration architecture
[ ] Establish SQLAlchemy foundation
[ ] Establish Alembic foundation
[ ] Define initial database conventions
[ ] Define initial core database entities
[ ] Establish API response conventions
[ ] Establish API error conventions
[ ] Establish backend logging foundation
[ ] Establish frontend API client
[ ] Establish frontend/backend development proxy or equivalent local configuration
[ ] Establish frontend API types/contracts
[ ] Ensure CORS/configuration is environment-driven
[ ] Integrate shadcn/ui into frontend
[ ] Verify Tailwind + shadcn/ui responsive foundation
[ ] Update architecture documentation
[ ] Add tests for newly implemented foundations
[ ] Run frontend/backend validation
[ ] Create Phase 1 report
[ ] STOP and wait for user review
```

---

# 3. FIRST ACTION — INSPECT BEFORE MODIFYING

Before changing anything, inspect:

```bash
git status
git branch
git log --oneline --decorate -10
```

Then inspect:

```text
README.md
PLAN.md
.env.example
.gitignore

frontend/
backend/
ai/
docs/
```

Read the Phase 0 documentation, especially:

```text
docs/architecture/ARCHITECTURE.md
docs/architecture/TECH_STACK.md
docs/architecture/DEVELOPMENT_GUIDELINES.md
docs/architecture/LOCAL_DEVELOPMENT.md
docs/deployment/COST_POLICY.md
docs/phases/PHASE_0_REPORT.md
```

Do not assume the Phase 0 implementation matches the report perfectly.

Inspect the actual code.

---

# 4. PRESERVE PHASE 0

Do not rewrite the project unnecessarily.

Do not:

- reset the repository
- delete Phase 0 documentation
- replace the frontend framework
- replace FastAPI
- replace the existing directory architecture
- introduce unrelated dependencies

Improve the existing foundation incrementally.

---

# 5. DATABASE ARCHITECTURE

JewelMind will use a relational database architecture.

Planned direction:

```text
PostgreSQL
    │
    └── Supabase-managed PostgreSQL in deployment
```

The backend should use:

```text
SQLAlchemy
Alembic
Pydantic
```

Do not make Supabase SDK usage the primary ORM layer.

The application architecture should remain portable to normal PostgreSQL.

---

# 6. SQLALCHEMY FOUNDATION

Establish a clean SQLAlchemy architecture.

Recommended conceptual structure:

```text
backend/app/
├── db/
│   ├── base.py
│   ├── session.py
│   └── __init__.py
│
├── models/
│   └── __init__.py
```

If the current Phase 0 structure differs, adapt it rather than creating redundant architecture.

Requirements:

- Central database configuration
- SQLAlchemy engine/session factory
- Declarative base
- Clear model import strategy
- Environment-driven database URL
- No hardcoded credentials
- No production database dependency during tests

---

# 7. DATABASE SESSION MANAGEMENT

Create a clean database session dependency suitable for FastAPI.

Conceptually:

```text
FastAPI Request
      │
      ▼
Database Dependency
      │
      ▼
SQLAlchemy Session
      │
      ▼
Database
```

The session must be properly closed/released.

Do not implement business CRUD services yet.

---

# 8. ALEMBIC

Initialize Alembic for database migrations.

Requirements:

```text
alembic/
alembic.ini
```

Configure Alembic so future SQLAlchemy models can be detected.

The migration configuration must use environment configuration rather than hardcoded secrets.

Do not create unnecessary production migrations.

If no actual database tables are implemented in Phase 1, create the migration infrastructure without pretending that business tables exist.

---

# 9. INITIAL DATA MODEL DESIGN

Phase 1 should define the **core conceptual entities**, but should not implement the entire application's database.

Document the future entities:

```text
User
Design
Sketch
AIJob
AIResult
JewelleryComponent
Prediction
ProductionOrder
ProductionSchedule
```

At minimum, document:

- Purpose
- Key relationships
- Important identifiers
- Ownership relationships
- Future lifecycle

Create:

```text
docs/architecture/DATABASE_DESIGN.md
```

---

# 10. CORE ENTITY RELATIONSHIPS

Document the conceptual relationship:

```text
User
 │
 └── Design
       │
       ├── Sketch
       │
       ├── AIJob
       │     │
       │     └── AIResult
       │
       ├── JewelleryComponent
       │
       ├── Prediction
       │
       └── ProductionOrder
               │
               └── ProductionSchedule
```

Important:

This is a conceptual model for Phase 1.

Do not implement every table just because it appears in the diagram.

The detailed schema will be implemented in the relevant database phase.

---

# 11. DATABASE NAMING CONVENTIONS

Document and follow:

## Tables

Use plural or project-consistent naming consistently.

Preferred:

```text
users
designs
sketches
ai_jobs
ai_results
jewellery_components
predictions
production_orders
production_schedules
```

## Primary keys

Prefer UUIDs for major application entities.

Do not add unnecessary custom ID systems.

## Timestamps

Future persisted entities should generally support:

```text
created_at
updated_at
```

where appropriate.

## Foreign keys

Use explicit foreign keys.

## Status fields

Use controlled values/enums where appropriate.

Document status transitions rather than using arbitrary strings everywhere.

---

# 12. API ARCHITECTURE

Establish the backend API structure.

Recommended:

```text
backend/app/api/
├── router.py
├── health.py
└── ...
```

Future route groups:

```text
/api/v1/auth
/api/v1/users
/api/v1/designs
/api/v1/sketches
/api/v1/ai
/api/v1/predictions
/api/v1/production
/api/v1/optimization
```

For Phase 1, only implement what is necessary for the technical foundation.

The existing `/health` endpoint must continue to work.

---

# 13. API VERSIONING

Establish:

```text
/api/v1
```

as the future versioned API prefix.

The health endpoint may remain compatible with the Phase 0 implementation if changing it would break existing tests.

If possible, provide a versioned health endpoint such as:

```text
GET /api/v1/health
```

while preserving the existing endpoint if appropriate.

Do not create duplicate endpoints without a reason.

Document the decision.

---

# 14. STANDARD API RESPONSE CONVENTION

Define a consistent API response philosophy.

For successful responses, use clear structured JSON.

Conceptual example:

```json
{
  "data": {},
  "message": "Request successful"
}
```

Do not force this wrapper onto endpoints where FastAPI's standard response is more appropriate.

The important requirement is consistency.

Document:

```text
docs/api/API_CONVENTIONS.md
```

---

# 15. STANDARD ERROR HANDLING

Create centralized error handling.

Future API errors should provide predictable information.

Conceptual example:

```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "The requested design was not found",
    "details": null
  }
}
```

Do not expose:

- stack traces
- database credentials
- internal file paths
- secrets
- model internals

in production-facing API responses.

Create appropriate custom exception structures only where they provide real value.

---

# 16. HTTP STATUS CODES

Document and use appropriate HTTP status codes.

Examples:

```text
200 OK
201 Created
204 No Content
400 Bad Request
401 Unauthorized
403 Forbidden
404 Not Found
409 Conflict
422 Validation Error
429 Too Many Requests
500 Internal Server Error
503 Service Unavailable
```

Do not return `200 OK` for every failure.

---

# 17. LOGGING FOUNDATION

Create a centralized backend logging configuration.

Requirements:

- Standard Python logging
- Environment-aware log level
- Useful request/service information
- No secrets in logs
- No raw credentials
- No unnecessary debug output in production

Future logs should help answer:

```text
What happened?
When?
Which service?
Which request/job?
What failed?
```

Do not implement distributed tracing in Phase 1.

---

# 18. REQUEST IDENTIFICATION

If practical within the existing architecture, introduce a lightweight request/correlation ID concept.

The goal is:

```text
Request
   ↓
request_id
   ↓
logs
   ↓
future AI job
```

Do not build a complex observability platform.

A simple implementation is preferred.

---

# 19. CONFIGURATION

Improve the Phase 0 Pydantic settings configuration.

Configuration must support:

```text
development
testing
production
```

without hardcoded environment assumptions.

Potential configuration:

```env
APP_ENV=development
LOG_LEVEL=INFO

BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:5173

DATABASE_URL=

SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=

AI_WORKER_URL=
AI_WORKER_TOKEN=
```

Do not require every variable to have a real value in Phase 1.

Only add variables actually needed.

---

# 20. 🔐 ENVIRONMENT SETUP

## IMPORTANT

Do not commit `.env`.

The repository must contain:

```text
.env.example    ✅
.env            ❌
```

Phase 1 should only require a real `.env` if a feature implemented in this phase actually needs it.

If a database connection is required for migration testing:

1. Tell the user exactly which variable is required.
2. Update `.env.example`.
3. User fills the real value locally.
4. Verify `.env` is ignored.
5. Never print or commit the secret.

Do not invent credentials.

Do not place secrets inside source code.

---

# 21. FRONTEND API CLIENT

Create a clean API service layer.

Recommended conceptual structure:

```text
frontend/src/
├── services/
│   ├── api/
│   │   ├── client.ts
│   │   └── ...
│   └── ...
```

The frontend must not scatter raw `fetch()` calls throughout components.

Create a reusable API client capable of:

```text
GET
POST
PUT/PATCH
DELETE
```

where appropriate.

Do not implement feature-specific API calls that do not exist yet.

---

# 22. FRONTEND API CONFIGURATION

Frontend API base URL must be environment-driven.

Example:

```env
VITE_API_URL=http://localhost:8000
```

Do not hardcode:

```text
http://localhost:8000
```

throughout the application.

Document the environment variable.

Remember:

> Anything prefixed with `VITE_` can be exposed to the browser.

Therefore:

**Never put private secrets in Vite environment variables.**

---

# 23. FRONTEND/BACKEND LOCAL DEVELOPMENT

Configure a clean local development flow.

Preferred conceptual setup:

```text
Frontend
http://localhost:5173
        │
        ▼
FastAPI
http://localhost:8000
```

Use Vite proxying or environment-driven API URLs as appropriate.

Avoid unnecessary proxy complexity.

CORS must remain environment-driven.

---

# 24. API TYPE SAFETY

Create TypeScript types for common API structures.

Examples:

```text
ApiError
HealthResponse
ApiResponse<T>
```

Do not generate dozens of unused domain types yet.

Future domain types will be introduced alongside their feature phases.

---

# 25. SHADCN/UI — REQUIRED

This is now a **mandatory JewelMind frontend standard**.

Phase 0 established Tailwind CSS.

Phase 1 must integrate **shadcn/ui** properly.

Use shadcn/ui for reusable interface components rather than creating unnecessary custom equivalents.

At minimum, establish the component system cleanly and demonstrate it with a small number of appropriate components.

Potential examples:

```text
Button
Card
Badge
Separator
```

Only install components actually needed.

Do not install the entire shadcn/ui catalog.

---

# 26. TAILWIND CSS — REQUIRED

Tailwind CSS is the standard styling system for JewelMind.

All future frontend work must prioritize:

```text
Tailwind CSS
+
shadcn/ui
```

Requirements:

- Responsive-first layouts
- Mobile support
- Tablet support
- Desktop support
- Consistent spacing
- Consistent typography
- No unnecessary CSS duplication

Use responsive Tailwind breakpoints appropriately.

Do not build fixed-width layouts that break on smaller screens.

---

# 27. RESPONSIVE FOUNDATION

Create a minimal responsive foundation page demonstrating:

```text
Mobile
   ↓
Tablet
   ↓
Desktop
```

The purpose is not to create the final JewelMind UI.

The purpose is to prove that the styling system works responsively.

Test at least:

```text
Small/mobile viewport
Tablet-sized viewport
Desktop viewport
```

Do not spend time on visual polish yet.

---

# 28. UI DEVELOPMENT STRATEGY

The project has two UI stages.

## Stage 1 — Development UI

During feature development:

```text
Functional
Responsive
Accessible
Consistent
Tailwind
shadcn/ui
```

## Stage 2 — Final UI recreation

After the major application functionality is complete:

```text
Full visual redesign/refinement
Design system
Animations
Micro-interactions
Loading states
Empty states
Error states
AI result visualization
Production dashboards
Responsive refinement
```

Do NOT perform the final visual redesign during Phase 1.

---

# 29. FRONTEND ARCHITECTURE

Keep these boundaries:

```text
components/
    reusable UI

pages/
    route-level screens

layouts/
    page layouts

services/
    API/external communication

hooks/
    reusable React logic

types/
    TypeScript contracts

utils/
    pure utility functions
```

Do not put API calls directly inside large page components.

Do not create unnecessary global state.

---

# 30. BACKEND ARCHITECTURE

Maintain:

```text
api/
    HTTP routes

core/
    configuration, security, logging

db/
    database connection/session

models/
    SQLAlchemy models

schemas/
    Pydantic request/response models

services/
    business logic
```

Routes should remain thin.

Conceptually:

```text
Route
  ↓
Schema validation
  ↓
Service
  ↓
Repository/DB
```

Do not implement a repository abstraction unless it is actually useful.

Avoid enterprise-style overengineering.

---

# 31. TESTING

Add tests for Phase 1 functionality.

At minimum:

## Backend

Test:

```text
/health
configuration loading
error handling where implemented
database/session setup where practical
```

## Frontend

At minimum ensure:

```text
TypeScript compilation
production build
responsive foundation renders
API client compiles correctly
```

Do not introduce a large frontend testing framework unless needed.

---

# 32. DATABASE TESTING POLICY

Do not make tests depend on a paid external database.

Preferred future direction:

```text
Unit tests
    ↓
Mock/test database
```

or another reproducible local testing approach.

If Phase 1 does not require actual database execution, do not force external Supabase credentials into automated tests.

---

# 33. DOCUMENTATION TO CREATE/UPDATE

Create/update:

```text
docs/architecture/DATABASE_DESIGN.md
docs/api/API_CONVENTIONS.md
docs/architecture/CONFIGURATION.md
docs/phases/PHASE_1_REPORT.md
```

Update where necessary:

```text
README.md
PLAN.md
docs/architecture/ARCHITECTURE.md
docs/architecture/TECH_STACK.md
docs/architecture/LOCAL_DEVELOPMENT.md
```

Documentation must describe the actual implementation state.

---

# 34. UML PREPARATION

Do not create the final UML suite yet.

However, update:

```text
docs/uml/README.md
```

to reflect the Phase 1 architecture.

The future diagrams will include:

```text
Use Case Diagram
Class Diagram
Sequence Diagrams
Activity Diagram
Component Diagram
Deployment Diagram
```

Phase 1 should provide enough architecture information for these diagrams to be created accurately in later phases.

---

# 35. DEPENDENCY DISCIPLINE

Only install dependencies required for Phase 1.

Expected backend additions may include:

```text
SQLAlchemy
Alembic
pydantic-settings
```

depending on what Phase 0 already contains.

Expected frontend additions may include the dependencies required by:

```text
shadcn/ui
```

Do NOT install:

```text
PyTorch
Ultralytics
Diffusers
ControlNet
XGBoost
OR-Tools
```

unless there is an extremely specific Phase 1 reason.

There isn't expected to be one.

---

# 36. SECURITY BASELINE

Ensure:

```text
[ ] No secrets in source code
[ ] No secrets in Git
[ ] No service-role key in frontend
[ ] No stack traces in API responses
[ ] CORS is configurable
[ ] Environment values are externalized
[ ] Logs do not expose credentials
```

Do not implement full authentication in this phase.

---

# 37. GIT SAFETY

Do not:

```text
force push
reset user work
rewrite history
delete main
```

Before changes:

```bash
git status
```

After changes:

```bash
git status
git diff
```

Review all modified files.

---

# 38. VALIDATION CHECKLIST

Before declaring Phase 1 complete:

## Backend

```text
[ ] FastAPI starts
[ ] Existing /health still works
[ ] API versioning foundation works if implemented
[ ] SQLAlchemy imports correctly
[ ] Alembic configuration works
[ ] Settings load correctly
[ ] Logging works
[ ] Error handling works
[ ] Backend tests pass
```

## Frontend

```text
[ ] React starts
[ ] TypeScript has zero errors
[ ] Tailwind works
[ ] shadcn/ui is configured
[ ] Responsive layout works
[ ] API client compiles
[ ] Production build passes
```

## Repository

```text
[ ] .env is not tracked
[ ] .env.example is tracked
[ ] No secrets committed
[ ] No model weights committed
[ ] No datasets committed
[ ] No unnecessary dependencies
```

## Documentation

```text
[ ] Database design
[ ] API conventions
[ ] Configuration
[ ] Architecture updated
[ ] UML documentation updated
[ ] Phase 1 report
```

---

# 39. DO NOT FAKE VALIDATION

Only report tests actually executed.

Good:

```text
Frontend build: PASSED
Backend tests: PASSED
Alembic configuration check: PASSED
shadcn/ui integration: VERIFIED
```

If something was not tested:

```text
Database connection: NOT TESTED — no external database configured
```

Do not claim success without verification.

---

# 40. PHASE 1 REPORT

Create:

```text
docs/phases/PHASE_1_REPORT.md
```

Use this structure:

```markdown
# Phase 1 Completion Report

## 1. Objective

## 2. Completed Work

## 3. Database Foundation

## 4. API Foundation

## 5. Configuration

## 6. Logging & Error Handling

## 7. Frontend API Integration

## 8. Tailwind & shadcn/ui

## 9. Tests & Validation

## 10. Files Created

## 11. Files Modified

## 12. Issues / Known Limitations

## 13. Explicitly Not Implemented

## 14. Environment Variables Required

## 15. Next Phase
```

Be specific.

Include actual commands and results.

---

# 41. ENVIRONMENT VARIABLES REPORTING

If this phase requires environment variables, the report must state:

```text
Variable:
Purpose:
Required for:
Where configured:
```

Never include the actual secret value.

Example:

```text
DATABASE_URL
Purpose: PostgreSQL connection
Required for: local migration testing
Value: configured locally, not committed
```

---

# 42. PHASE 1 SUCCESS CRITERIA

Phase 1 is successful when the project has a clean technical bridge:

```text
                 JewelMind Frontend
                         │
                         │ typed API client
                         ▼
                   FastAPI /api/v1
                         │
              ┌──────────┼──────────┐
              │          │          │
              ▼          ▼          ▼
          Schemas     Services    Errors
                         │
                         ▼
                    SQLAlchemy
                         │
                         ▼
                    PostgreSQL
```

while maintaining:

```text
Tailwind CSS
+
shadcn/ui
+
Responsive frontend
```

The project should now be ready for future feature development without repeatedly changing the basic architecture.

---

# 43. STOP CONDITION

When all Phase 1 objectives are complete:

**STOP.**

Do not begin Phase 2.

Do not implement authentication automatically.

Do not implement database business logic beyond the approved Phase 1 foundation.

Wait for the user to review:

```text
PHASE_1_REPORT.md
```

The user will decide whether to merge the branch into `main`.

---

# 44. FINAL RESPONSE TO USER

At the end of your execution, provide a concise summary:

```text
PHASE 1 COMPLETE

Database:
✓ ...

API:
✓ ...

Configuration:
✓ ...

Frontend API:
✓ ...

Tailwind:
✓ ...

shadcn/ui:
✓ ...

Validation:
✓ ...

Known issues:
- ...

Environment variables:
- ...

Branch:
phase-1-architecture

Waiting for review.
```

Do not tell the user to merge until all validations have been completed and the report has been created.

---

# MOST IMPORTANT RULES

1. Phase 1 only.
2. Inspect Phase 0 before changing anything.
3. Preserve Phase 0 work.
4. Do not implement future application features.
5. Use PostgreSQL-compatible architecture.
6. Use SQLAlchemy + Alembic.
7. Keep FastAPI routes thin.
8. Keep configuration environment-driven.
9. Never commit `.env`.
10. Never expose secrets to the frontend.
11. Tailwind CSS is mandatory.
12. shadcn/ui is mandatory for reusable UI components.
13. Responsive design is mandatory.
14. Do not perform the final UI redesign yet.
15. Do not install heavy AI dependencies yet.
16. Test everything actually implemented.
17. Document actual implementation, not planned functionality.
18. Keep the project ₹0-cost oriented.
19. Do not force external paid services into tests.
20. Stop after Phase 1 and wait for user review.
