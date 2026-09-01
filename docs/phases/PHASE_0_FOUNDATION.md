# PHASE 0 — PROJECT FOUNDATION
## JewelMind
### AI-Powered Jewellery Design, Analysis & Production Planning Platform

**Phase:** 0  
**Phase Name:** Repository & Project Foundation  
**Status:** Not Started  
**Execution:** Antigravity  
**Budget:** ₹0  
**Repository:** JewelMind  
**Branch:** `main`

---

# IMPORTANT INSTRUCTION

You are working on the **JewelMind** project.

This is **Phase 0 only**.

Do NOT implement application features, authentication, AI models, database logic, rendering, YOLO, XGBoost, OR-Tools, production planning, or deployment in this phase.

Your responsibility in this phase is to establish a clean, professional, scalable repository foundation that later phases can build on safely.

**Do not jump ahead.**

Before making any changes:

1. Inspect the existing repository.
2. Read the existing `README.md`.
3. Read the existing `.gitignore`.
4. If `PLAN.md` already exists, read it.
5. Check the current Git status.
6. Understand what is already present.
7. Preserve existing useful work.
8. Do not delete files unless they are clearly temporary/unnecessary and you explain the reason.

At the end of the phase, stop and wait for the user before implementing Phase 1.

---

# 1. PROJECT CONTEXT

JewelMind is a full-stack AI/ML web application designed around this workflow:

```text
Jewellery Sketch
       ↓
AI Rendering
       ↓
Jewellery Component Detection
       ↓
Feature Extraction
       ↓
Material Prediction
       ↓
Cost Estimation
       ↓
Production Time Prediction
       ↓
Wastage Prediction
       ↓
Manufacturability Analysis
       ↓
Production Order
       ↓
Production Optimization
       ↓
Optimized Production Schedule
```

The project combines:

```text
Modern Web Development
        +
Computer Vision
        +
Generative AI
        +
Machine Learning
        +
Optimization
```

The application must be designed so that the web application and heavy AI computation remain decoupled.

---

# 2. TARGET ARCHITECTURE

The target architecture is:

```text
                         PUBLIC USER
                              │
                              ▼
                    ┌───────────────────┐
                    │ Cloudflare Pages  │
                    │ React + TypeScript│
                    └─────────┬─────────┘
                              │ HTTPS
                              ▼
                    ┌───────────────────┐
                    │      FastAPI      │
                    │    Backend API    │
                    └─────────┬─────────┘
                              │
                 ┌────────────┴────────────┐
                 │                         │
                 ▼                         ▼
        ┌─────────────────┐       ┌─────────────────┐
        │    Supabase     │       │     AI Queue    │
        │ PostgreSQL      │       │                 │
        │ Storage         │       │ Pending Jobs    │
        └─────────────────┘       │ Processing      │
                                  │ Completed       │
                                  └────────┬────────┘
                                           │
                              ┌────────────┴────────────┐
                              │                         │
                              ▼                         ▼
                       ┌──────────────┐        ┌────────────────┐
                       │ RTX 4060     │        │ Hugging Face   │
                       │ AI Worker    │        │ Free/ZeroGPU   │
                       └──────┬───────┘        └───────┬────────┘
                              │                         │
                              └────────────┬────────────┘
                                           ▼
                                      AI Result
                                           │
                                           ▼
                                  Supabase Storage
                                           │
                                           ▼
                                      Web Client
```

The architecture must allow the AI worker implementation to change later without forcing a redesign of the main web application.

---

# 3. TECHNOLOGY DIRECTION

The following stack is the planned direction.

## Frontend

- React
- TypeScript
- Vite
- Tailwind CSS
- React Router
- TanStack Query where appropriate
- React Hook Form where appropriate
- Zod where appropriate

## Backend

- Python
- FastAPI
- Pydantic
- SQLAlchemy
- Alembic
- PostgreSQL

## AI/ML

- PyTorch
- OpenCV
- YOLO / Ultralytics
- Hugging Face Diffusers
- ControlNet
- scikit-learn
- XGBoost
- Pandas
- NumPy
- Google OR-Tools

## Infrastructure

- GitHub
- Cloudflare Pages for frontend
- Supabase for PostgreSQL/storage
- Free-tier compatible backend hosting
- Local RTX 4060 as primary AI development worker
- Hugging Face free/ZeroGPU as an optional secondary AI worker

Do not install the heavy AI stack during Phase 0.

---

# 4. PHASE 0 OBJECTIVES

Complete the following:

```text
[ ] Inspect current repository
[ ] Establish final project identity as JewelMind
[ ] Create/update PLAN.md
[ ] Create professional README.md
[ ] Create final project directory structure
[ ] Create docs structure
[ ] Create backend foundation structure
[ ] Create frontend foundation structure
[ ] Create AI foundation structure
[ ] Create tests structure
[ ] Create scripts structure
[ ] Create proper .gitignore
[ ] Add environment templates
[ ] Establish configuration conventions
[ ] Establish Git conventions
[ ] Add development documentation
[ ] Add architecture documentation placeholder
[ ] Verify repository integrity
[ ] Produce Phase 0 report
```

---

# 5. DO NOT IMPLEMENT THESE IN PHASE 0

The following are explicitly OUT OF SCOPE:

```text
Authentication
Database models
Database migrations
User registration
Login
JWT
OAuth
Jewellery CRUD
Sketch upload
Supabase integration
AI rendering
Diffusion
ControlNet
YOLO
Model training
XGBoost
Prediction APIs
OR-Tools
Production scheduling
AI queue implementation
Cloud deployment
Docker deployment
Payment systems
Email systems
Notifications
Admin dashboard
Production dashboard
```

Create structure/placeholders for future work where useful, but do not implement these features.

---

# 6. REPOSITORY STRUCTURE

Establish a clean structure similar to:

```text
JewelMind/
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── layouts/
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── types/
│   │   ├── utils/
│   │   └── assets/
│   └── README.md
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── main.py
│   ├── tests/
│   ├── requirements/
│   └── README.md
│
├── ai/
│   ├── vision/
│   ├── rendering/
│   ├── prediction/
│   ├── optimization/
│   ├── workers/
│   ├── common/
│   ├── tests/
│   └── README.md
│
├── docs/
│   ├── architecture/
│   ├── uml/
│   ├── ai/
│   ├── api/
│   ├── datasets/
│   ├── deployment/
│   └── phases/
│
├── datasets/
│   └── README.md
│
├── models/
│   └── README.md
│
├── scripts/
│   └── README.md
│
├── tests/
│   ├── integration/
│   └── e2e/
│
├── .env.example
├── .gitignore
├── PLAN.md
├── README.md
└── LICENSE/NOTICE placeholder only if needed
```

Do not create meaningless empty files throughout the repository.

If a directory needs to exist in Git but contains no implementation yet, use a concise `README.md` explaining its purpose rather than arbitrary placeholder files.

---

# 7. FRONTEND FOUNDATION

Initialize a minimal React + TypeScript frontend using Vite.

Requirements:

- React
- TypeScript
- Vite
- Tailwind CSS
- ESLint
- Proper TypeScript configuration
- Clean source structure

The frontend should have only a minimal foundation page.

Create a simple JewelMind landing/foundation screen confirming that the frontend is running.

Do NOT build the final UI in Phase 0.

The frontend must be structured so future phases can add:

```text
Authentication
Dashboard
Design Management
Sketch Upload
AI Rendering
AI Results
Predictions
Production Planning
Scheduling
```

without restructuring the entire project.

---

# 8. BACKEND FOUNDATION

Create the FastAPI application foundation.

The backend should have:

```text
backend/
└── app/
    ├── api/
    ├── core/
    ├── models/
    ├── schemas/
    ├── services/
    └── main.py
```

Create a minimal FastAPI application.

Provide a simple health endpoint:

```text
GET /health
```

The response should clearly indicate that the JewelMind API is running.

Example concept:

```json
{
  "status": "ok",
  "service": "JewelMind API"
}
```

Do not add authentication or database functionality.

---

# 9. API STRUCTURE

Establish the future API organization without implementing business logic.

Planned structure:

```text
/api
├── /auth
├── /users
├── /designs
├── /sketches
├── /ai
├── /predictions
├── /production
└── /optimization
```

At Phase 0, these can remain unimplemented.

Document the purpose of each API area.

---

# 10. AI FOUNDATION

Create the AI directory structure:

```text
ai/
├── vision/
├── rendering/
├── prediction/
├── optimization/
├── workers/
├── common/
└── tests/
```

Add README files explaining future responsibilities.

## vision/

Future:

- image preprocessing
- jewellery component detection
- YOLO
- OpenCV

## rendering/

Future:

- sketch preprocessing
- diffusion
- ControlNet
- LoRA
- rendering pipeline

## prediction/

Future:

- feature engineering
- material prediction
- cost prediction
- production-time prediction
- wastage prediction

## optimization/

Future:

- production scheduling
- constraints
- OR-Tools

## workers/

Future:

- AI job workers
- local RTX 4060 worker
- optional cloud worker
- worker capability management

Do not implement these systems now.

---

# 11. AI WORKER PRINCIPLE

Document this architectural rule:

> The backend creates and tracks AI jobs, while AI workers perform heavy computation.

Future flow:

```text
Frontend
   ↓
FastAPI
   ↓
AI Job
   ↓
Worker Selection
   ↓
AI Worker
   ↓
Model Inference
   ↓
Result Storage
   ↓
Job Completion
   ↓
Frontend
```

The AI worker must remain independently replaceable.

Possible workers:

```text
RTX 4060 Worker
Hugging Face Worker
Future Cloud GPU Worker
```

---

# 12. ENVIRONMENT VARIABLES

Create:

```text
.env.example
```

Do NOT create a real `.env` with secrets.

Document future variables such as:

```text
APP_ENV=
BACKEND_URL=
FRONTEND_URL=

DATABASE_URL=

SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=

JWT_SECRET=

AI_WORKER_URL=
AI_WORKER_TOKEN=
```

Use placeholder values only.

Clearly document that secrets must never be committed.

---

# 13. GITIGNORE

Replace/improve the existing `.gitignore` so it covers the entire project.

It should account for:

## Python

```text
__pycache__/
*.py[cod]
.venv/
venv/
env/
.pytest_cache/
.mypy_cache/
```

## Node

```text
node_modules/
dist/
build/
.vite/
```

## Environment

```text
.env
.env.*
!.env.example
```

## IDE

```text
.vscode/*
.idea/
*.swp
```

## AI/model artifacts

```text
*.pt
*.pth
*.ckpt
*.safetensors
*.onnx
*.bin
```

## Large/generated data

```text
datasets/raw/
datasets/processed/
outputs/
generated/
```

Do not blindly ignore files that should be version-controlled.

The exact final `.gitignore` should be appropriate to the actual project structure.

---

# 14. DATASET POLICY

Create:

```text
datasets/README.md
```

Document:

- Datasets will not be committed directly if they are large.
- Dataset sources must be documented.
- Licenses must be checked.
- Train/validation/test splits must be documented.
- Synthetic data must be clearly labeled.
- Personal/private manufacturing data must not be committed.
- Dataset preprocessing must be reproducible.

Future dataset folders may be:

```text
datasets/
├── raw/
├── processed/
├── annotations/
└── README.md
```

Do not download datasets in Phase 0.

---

# 15. MODEL POLICY

Create:

```text
models/README.md
```

Document:

- Large model weights must not be committed to Git.
- Model source and version must be documented.
- License must be documented.
- Download instructions will be added in the relevant AI phase.
- Model checksums/version information may be documented where useful.

Potential future model categories:

```text
object detection
image generation
image conditioning
tabular prediction
optimization
```

Do not download model weights in Phase 0.

---

# 16. DOCUMENTATION STRUCTURE

Create:

```text
docs/
├── architecture/
├── uml/
├── ai/
├── api/
├── datasets/
├── deployment/
└── phases/
```

Add README files explaining what each directory will contain.

Future UML documentation will include:

```text
Use Case Diagram
Class Diagram
Sequence Diagrams
Activity Diagram
Component Diagram
Deployment Diagram
```

Do not create final UML diagrams yet unless they are simple architecture placeholders.

---

# 17. PLAN.MD

Create or update `PLAN.md`.

It must contain the complete JewelMind master plan.

Important changes:

- Use **JewelMind** as the official project name.
- Remove temporary product naming where appropriate.
- Keep the ₹0 budget constraint.
- Keep the RTX 4060 worker architecture.
- Keep the optional Hugging Face worker architecture.
- Keep the complete AI/web/production workflow.
- Keep the phase roadmap.
- Clearly mark Phase 0 as the current phase.
- Do not claim future functionality has already been implemented.

If the existing `PLAN.md` from the project planning stage is available, preserve its useful architectural content and improve it rather than unnecessarily rewriting the entire project plan.

---

# 18. README.MD

Create a professional initial README.

It should contain:

# JewelMind

A short description:

> JewelMind is an AI-powered jewellery design, analysis, and production planning platform that connects jewellery sketches with AI rendering, computer vision, predictive analytics, manufacturability analysis, and production optimization.

Include sections:

```text
Overview
Problem
Proposed Solution
Core Workflow
Key Features
Technology Stack
Architecture
AI/ML Components
Project Structure
Development Status
Budget Strategy
Roadmap
Documentation
```

At this stage clearly state:

```text
Project Status: Foundation / Phase 0
```

Do not pretend that AI features already work.

---

# 19. TECHNOLOGY DECISION DOCUMENT

Create:

```text
docs/architecture/TECH_STACK.md
```

Explain why each planned technology exists.

At minimum:

## React

For component-based frontend development.

## TypeScript

For type safety and maintainability.

## Vite

For frontend development/build tooling.

## Tailwind CSS

For rapid and consistent UI development.

## FastAPI

For a Python-native backend that integrates naturally with AI/ML.

## PostgreSQL

For structured relational business data.

## Supabase

For PostgreSQL and storage using a free-tier-oriented architecture.

## PyTorch

For deep-learning workloads and GPU acceleration.

## YOLO

For jewellery component detection.

## Diffusion + ControlNet

For sketch-to-render generation while preserving structural information.

## XGBoost

For structured manufacturing predictions.

## OR-Tools

For constrained production scheduling.

## RTX 4060

For local AI development and inference without paying for cloud GPU compute.

---

# 20. DEVELOPMENT CONVENTIONS

Create:

```text
docs/architecture/DEVELOPMENT_GUIDELINES.md
```

Document conventions such as:

## Naming

Python:

```text
snake_case
```

TypeScript/React:

```text
camelCase
PascalCase for components/types
```

## Git

Use meaningful commits:

```text
feat:
fix:
refactor:
docs:
test:
chore:
```

Examples:

```text
feat: initialize frontend
feat: add authentication
feat: add AI job system
fix: handle failed rendering jobs
docs: update architecture
```

## Secrets

Never commit secrets.

## Large Files

Never commit model weights or large datasets.

## Code Quality

Prefer:

- small functions
- clear names
- type safety
- modular code
- useful comments
- no unnecessary abstraction

Do not over-engineer.

---

# 21. PYTHON ENVIRONMENT STRATEGY

The Python side will eventually contain both backend and AI/ML workloads.

Use a reproducible environment strategy.

Recommended direction:

```text
Python 3.12
uv
```

However, do NOT install the entire AI stack during Phase 0.

Document that future phases will create appropriate Python environments and dependency groups.

The backend and AI worker may later use separate dependency sets/environments if dependency conflicts or GPU-specific requirements make that preferable.

Do not force everything into one enormous Python environment.

---

# 22. FRONTEND DEPENDENCY POLICY

Only install dependencies actually required by Phase 0.

Do not install every library listed in the future technology stack.

For example, do NOT install:

```text
YOLO
PyTorch
Diffusers
XGBoost
OR-Tools
```

during frontend initialization.

Future phases should introduce dependencies when their functionality is implemented.

---

# 23. BACKEND DEPENDENCY POLICY

Only install what is required for the minimal FastAPI foundation.

Future phases will add:

```text
SQLAlchemy
Alembic
authentication libraries
Supabase integration
AI queue dependencies
```

when those features are actually implemented.

Do not prematurely create a complex backend.

---

# 24. ARCHITECTURE DOCUMENTATION

Create:

```text
docs/architecture/ARCHITECTURE.md
```

Explain:

1. Frontend
2. Backend
3. Database
4. Storage
5. AI Queue
6. AI Workers
7. AI Result flow
8. Production planning
9. Deployment direction

Include the conceptual architecture:

```text
User
 ↓
Cloudflare Pages
 ↓
FastAPI
 ├── Supabase
 └── AI Queue
       ├── RTX 4060 Worker
       └── Optional Hugging Face Worker
```

Clearly mark this as the **target architecture**, not necessarily fully implemented architecture.

---

# 25. TEST FOUNDATION

Create the basic test structure.

Do not write extensive tests yet.

At minimum:

```text
backend/tests/
ai/tests/
tests/integration/
tests/e2e/
```

The Phase 0 backend should have a minimal health endpoint test if the chosen testing setup is lightweight and appropriate.

Do not build a large testing framework unnecessarily.

---

# 26. LOCAL DEVELOPMENT DOCUMENTATION

Create:

```text
docs/architecture/LOCAL_DEVELOPMENT.md
```

Document the expected future local environment:

```text
Developer Laptop
│
├── Frontend
│   └── React + TypeScript
│
├── Backend
│   └── FastAPI
│
├── AI Worker
│   └── Python
│
└── RTX 4060
    └── AI inference/training
```

Do not require every component to be operational in Phase 0.

---

# 27. ZERO-COST POLICY

Create:

```text
docs/deployment/COST_POLICY.md
```

Document:

> JewelMind is being developed with a strict ₹0 budget.

Target free/owned resources:

```text
GitHub
Cloudflare Pages
Supabase free tier
Free-tier backend hosting where suitable
Hugging Face free/ZeroGPU where available
Developer-owned RTX 4060
```

Important:

Free-tier limits and provider policies may change.

Do not hard-code claims that a particular provider will always remain free.

The architecture should remain portable.

---

# 28. CODE QUALITY REQUIREMENTS

Antigravity must:

- Avoid unnecessary dependencies.
- Avoid dead code.
- Avoid placeholder business logic pretending to be functional.
- Avoid hardcoded secrets.
- Avoid hardcoded production URLs.
- Avoid large generated files.
- Avoid committing model weights.
- Keep frontend and backend separated.
- Keep AI code separated from backend business logic.
- Use clear folder boundaries.
- Keep configuration centralized.
- Keep documentation synchronized with actual implementation.

---

# 29. GIT SAFETY

Before making changes:

```bash
git status
```

After implementation:

```bash
git status
git diff
```

Review the changed files.

Do not reset or discard existing user work.

Do not force-push.

Do not rewrite Git history.

Do not modify GitHub repository settings.

---

# 30. VALIDATION CHECKLIST

Before declaring Phase 0 complete, verify:

## Repository

```text
[ ] Git repository is valid
[ ] main branch is intact
[ ] No accidental deletion
[ ] No secrets committed
[ ] No large model files committed
[ ] No large datasets committed
```

## Frontend

```text
[ ] React starts
[ ] TypeScript compiles
[ ] Vite works
[ ] Tailwind works
[ ] Basic JewelMind page renders
```

## Backend

```text
[ ] FastAPI starts
[ ] /health works
[ ] No database dependency yet
[ ] No authentication dependency yet
```

## Documentation

```text
[ ] README.md
[ ] PLAN.md
[ ] Architecture documentation
[ ] Tech stack documentation
[ ] Development guidelines
[ ] Dataset policy
[ ] Model policy
[ ] Cost policy
[ ] Local development documentation
```

## Structure

```text
[ ] frontend/
[ ] backend/
[ ] ai/
[ ] docs/
[ ] datasets/
[ ] models/
[ ] scripts/
[ ] tests/
```

---

# 31. DO NOT FAKE VERIFICATION

If something could not be tested, say so.

For example:

```text
Frontend build: PASSED
Backend health endpoint: PASSED
AI worker: NOT IMPLEMENTED — Phase 0 scope
Supabase: NOT CONNECTED — future phase
Rendering: NOT IMPLEMENTED — future phase
```

Do not report something as tested if it was not actually tested.

---

# 32. PHASE 0 REPORT

At the end, create:

```text
docs/phases/PHASE_0_REPORT.md
```

The report must contain:

## 1. Phase Objective

What Phase 0 was intended to establish.

## 2. Completed Work

List everything actually completed.

## 3. Files Created

List important files.

## 4. Files Modified

List important modified files.

## 5. Technology Decisions

Summarize the stack and important architecture decisions.

## 6. Validation

Include actual commands/tests run and their results.

## 7. Repository Status

Confirm whether the repository is clean or has expected uncommitted changes.

## 8. Known Issues

List anything that remains.

## 9. Explicitly Not Implemented

Mention features intentionally deferred to future phases.

## 10. Next Phase

State that Phase 1 will establish the deeper technical architecture and application foundation.

---

# 33. FINAL PHASE 0 OUTPUT

When finished, provide the user with a concise summary:

```text
PHASE 0 COMPLETE

Repository:
✓ ...

Frontend:
✓ ...

Backend:
✓ ...

AI:
✓ Structure established
✗ Models not implemented by design

Documentation:
✓ ...

Validation:
✓ ...

Known issues:
- ...

Next phase:
Phase 1 — Architecture & Technical Foundation
```

Do not automatically start Phase 1.

---

# 34. STOP CONDITION

After Phase 0 is complete:

**STOP.**

Do not continue to Phase 1 automatically.

Wait for explicit user instruction.

The user will review the repository and decide when to proceed.

---

# 35. MOST IMPORTANT RULES

1. **Phase 0 only.**
2. Do not jump ahead.
3. Inspect before modifying.
4. Preserve existing work.
5. Keep the architecture modular.
6. Keep AI separate from the web backend.
7. Do not commit secrets.
8. Do not commit datasets/model weights.
9. Do not install unnecessary heavy AI dependencies.
10. Test what you actually implement.
11. Document actual state honestly.
12. Do not automatically proceed to Phase 1.
13. Keep the project ₹0-cost oriented.
14. Use the RTX 4060 as the primary local AI development resource later.
15. Keep Hugging Face as an optional worker, not a hard dependency.
16. Treat the architecture in `PLAN.md` as the source of truth.
17. Do not invent datasets, model performance, or deployment capabilities.
18. Prefer simple, maintainable student-level engineering over unnecessary enterprise complexity.

---

# PHASE 0 SUCCESS CRITERIA

Phase 0 is successful when a new developer can clone the JewelMind repository and immediately understand:

```text
What is JewelMind?
        ↓
What problem does it solve?
        ↓
What is the target architecture?
        ↓
Where is the frontend?
        ↓
Where is the backend?
        ↓
Where will AI live?
        ↓
Where will datasets/models live?
        ↓
Where is the documentation?
        ↓
How will future phases extend the system?
```

The repository should feel like the foundation of a serious capstone project, while containing only the amount of implementation appropriate for Phase 0.
