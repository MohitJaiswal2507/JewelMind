# JewelMind — Phase 14: Testing & Security

**Branch:** `phase-14-testing-security`  
**Depends on:** Phase 13 — Complete Dashboard

## 1. Objective

Harden and validate the completed JewelMind application.

Phase 14 focuses on:

- Authentication and authorization
- Multi-tenant isolation
- IDOR/object-level authorization
- Secret and environment-variable security
- Supabase Storage security
- CORS and API hardening
- File-upload validation
- AI endpoint and local-worker security
- Database/migration validation
- Frontend route protection
- Error handling
- Regression testing
- End-to-end verification

### Strict scope

Do **not**:

- retrain ControlNet, YOLO, or Appearance LoRA
- modify trained model weights
- regenerate training datasets
- redesign the application
- implement Phase 15 deployment
- implement Phase 16 final documentation/presentation work

Make only changes required by verified security or testing findings.

---

# 2. Current Architecture

## Frontend

- React + TypeScript
- Vite
- Tailwind CSS
- shadcn/ui
- Dashboard
- Designs
- Design Detail
- Canvas Workspace
- Studio
- Production

## Backend

- Python + FastAPI
- SQLAlchemy
- Alembic
- JWT authentication
- PostgreSQL/Supabase
- Supabase Storage
- AI rendering proxy
- YOLO component-detection proxy
- Production APIs
- OR-Tools optimization
- Dashboard aggregation

## AI

- YOLO11m-seg JewelMind
- Stable Diffusion 1.5
- pretrained ControlNet
- JewelMind 300-step ControlNet
- JewelMind Appearance LoRA
- local AI worker
- RTX 4060 CUDA inference

---

# 3. Git Workflow

Create:

```powershell
git checkout main
git pull origin main
git checkout -b phase-14-testing-security
```

Never commit directly to `main`.

Do not commit, push, or merge until the phase has been reviewed.

---

# 4. Initial Inspection — No Changes

Before modifying anything, inspect:

```text
PLAN.md
backend/
frontend/
ai/
alembic/
tests/
backend/tests/
.gitignore
```

Review:

- authentication
- JWT handling
- current-user dependencies
- ownership filtering
- SQLAlchemy queries
- Supabase configuration
- Storage handling
- CORS
- environment configuration
- frontend route protection
- AI worker
- AI endpoints
- production endpoints
- dashboard endpoint
- existing tests
- Git-tracked files

Create:

```text
PHASE_14_INITIAL_SECURITY_AUDIT.md
```

Classify findings as:

```text
PASS
WARNING
HIGH
CRITICAL
```

Do not modify code before this audit.

---

# 5. Authentication Testing

Verify:

### Registration

- required fields are validated
- duplicate emails are rejected
- passwords are hashed
- passwords are never stored/logged in plaintext
- malformed requests fail safely

### Login

- invalid credentials fail
- valid credentials succeed
- JWT is generated correctly
- JWT contains only necessary claims
- invalid tokens fail
- expired tokens fail

### Protected endpoints

Verify unauthenticated requests are rejected for every currently protected endpoint, including the discovered equivalents of:

```text
/auth/me
/designs
/designs/{id}
/designs/{id}/sketch
/ai/render
/ai/components/detect
/production/*
/production/optimize
/production/schedules/*
/dashboard/overview
```

Use the actual route inventory from the code rather than assuming this list is exhaustive.

---

# 6. Multi-Tenant Isolation

Create two test users:

```text
User A
User B
```

Create User A resources:

- design
- sketch
- production order
- schedule
- associated AI/render data where applicable

Using User B's JWT, attempt every applicable:

```text
GET
POST
PUT/PATCH
DELETE
```

Expected:

- User B cannot read User A resources
- User B cannot modify User A resources
- User B cannot delete User A resources
- User B cannot access User A sketches/renders through protected APIs
- User B cannot manipulate User A production data
- User B cannot access User A schedules
- dashboard data remains isolated

Backend authorization is authoritative. Do not rely on frontend hiding.

Add automated regression tests for every discovered tenant boundary.

---

# 7. IDOR Testing

For every endpoint accepting identifiers such as:

```text
design_id
order_id
schedule_id
worker_id
machine_id
asset_id
```

replace the identifier with another user's identifier and verify access is denied.

Expected behavior should follow the existing API contract, normally:

```text
401 / 403 / 404
```

Do not leak unnecessary information about another user's resources.

---

# 8. Supabase Security Audit

Review:

- Supabase URL
- anonymous key
- service-role key
- database connection configuration
- Storage bucket
- upload paths
- sketch URLs
- render URLs

Verify:

```text
SUPABASE_SERVICE_ROLE_KEY
```

is backend-only.

Verify it is never:

- bundled into frontend code
- returned through an API
- stored in client-visible configuration
- committed to Git

## Public bucket caveat

If `jewelmind-assets` remains public, document it honestly.

Use wording similar to:

> Backend APIs enforce tenant ownership. The current Supabase asset bucket is public, so possession of an asset URL may allow direct retrieval.

Do not falsely claim that public Storage URLs provide private per-user isolation.

Do not redesign Storage architecture during this phase unless a small, clearly justified fix is required.

---

# 9. Secret Audit

Search repository/configuration for:

```text
.env
.env.*
*.key
*.pem
credentials*
secrets*
JWT_SECRET
SUPABASE_SERVICE_ROLE_KEY
DATABASE_URL
password=
api_key=
token=
secret=
```

Do not print actual secret values.

Verify:

```text
.env
.env.local
```

and other secret-bearing files are ignored.

Check:

```powershell
git ls-files
git status
```

If a real credential is discovered in tracked history, report it immediately and do not reproduce the credential in any report.

---

# 10. Git Artifact Audit

Ensure no accidental tracked files include:

- `.env`
- credentials
- tokens
- private keys
- database dumps
- model checkpoints
- large model weights
- datasets
- Hugging Face caches
- Python environments
- Node modules
- generated images
- temporary files

Existing local model files must remain usable but should not be accidentally committed.

---

# 11. CORS Audit

Inspect FastAPI CORS.

Verify:

- local frontend origin works
- configured production origins can be supplied later
- arbitrary origins are not unnecessarily allowed
- credential configuration is appropriate

Avoid unrestricted:

```python
allow_origins=["*"]
```

when authenticated credentialed requests require restricted origins.

Do not break local development.

---

# 12. API Input Validation

Review all major APIs for:

- invalid UUIDs
- missing fields
- empty strings
- negative quantities
- zero quantities where invalid
- invalid enum values
- invalid dates
- impossible date ranges
- oversized values
- invalid AI parameters
- oversized image uploads
- invalid production parameters

Test examples:

```text
quantity = 0
quantity = -1
horizon_days = 0
horizon_days = extremely large
solver_limit = negative
invalid category
invalid priority
invalid UUID
empty title
oversized image
unsupported file extension
```

Expected behavior is controlled validation, normally HTTP 400/422 as appropriate.

---

# 13. AI Endpoint Security

Review the actual current endpoints for:

```text
AI rendering
YOLO component detection
```

Verify:

- authentication is required
- design ownership is enforced
- arbitrary filesystem paths cannot be supplied
- arbitrary model paths cannot be supplied
- arbitrary URLs cannot cause untrusted server-side fetching
- AI parameters have sensible validation/ranges
- image inputs are validated
- user input cannot execute shell commands
- frontend cannot select server-side executable/model paths

The frontend must never control:

```text
Python executable
model filesystem path
worker command
server filesystem destination
service credentials
```

---

# 14. AI Worker Security

Inspect `ai/workers/local_worker.py` and related communication.

Verify:

- intended bind address is used
- it is not accidentally exposed publicly
- no arbitrary code execution exists
- no arbitrary model paths are accepted
- no shell commands are derived from requests
- input/output paths are controlled
- temporary files are safe
- secrets are not exposed

Document that the local worker is intended for controlled local use unless the architecture explicitly says otherwise.

Do not make it internet-facing.

---

# 15. File Upload Security

Review sketch/image uploads.

Verify:

- extension validation
- MIME/content validation where practical
- upload size limits
- safe generated filenames
- UUID-based storage names
- no path traversal
- executable files are rejected
- user-controlled paths are not directly joined into filesystem paths

Test names such as:

```text
../../test.png
..\..\test.png
image.exe
image.php
image<script>.png
```

Never execute uploaded files.

---

# 16. Database Security

Review SQLAlchemy and raw SQL usage.

Verify:

- ORM/parameterized queries are used
- user input is never interpolated into SQL
- ownership filters are present
- cascading relationships behave correctly
- deleted resources do not leave unauthorized access
- migrations are consistent

Run:

```powershell
alembic current
alembic heads
```

Expected:

```text
one current head
```

Do not modify old migrations just to make tests pass.

---

# 17. Error Handling

Verify production-facing API responses do not expose:

- passwords
- JWT secrets
- Supabase credentials
- database credentials
- Python tracebacks
- unnecessary filesystem paths
- model filesystem paths
- internal credentials

Secrets must never be logged.

---

# 18. Frontend Security

Inspect:

```text
frontend/src/App.tsx
frontend/src/services/
frontend/src/pages/
frontend/src/components/
```

Verify:

- protected views require authentication
- logout clears auth state
- expired tokens are handled
- unauthorized responses do not leave stale protected data visible
- no service-role credential exists in frontend code
- no hardcoded passwords/tokens exist
- unsafe HTML rendering is not used without justification

---

# 19. Route Protection

While logged out, directly navigate to all protected application views, including:

```text
/dashboard
/designs
/designs/{id}
/designs/{id}/workspace
/studio
/production
```

Expected:

```text
Unauthenticated
    ↓
Login/Register
```

After login:

```text
Authenticated
    ↓
Protected application
```

Verify logout returns to the public/authentication state.

---

# 20. Production & OR-Tools Security

Test:

```text
production orders
workers
machines
optimization
schedules
```

Verify:

- users cannot read another user's production orders
- users cannot modify another user's production resources
- users cannot delete another user's schedules
- optimization only uses authenticated user's resources
- schedule retrieval is tenant-isolated

Add cross-user scheduling tests.

Do not modify the CP-SAT solver architecture unless a verified security issue requires it.

---

# 21. Dashboard Security

Test:

```text
GET /api/v1/dashboard/overview
```

using:

- User A
- User B
- invalid token
- expired token

Verify only the authenticated user's:

- design counts
- production counts
- schedules
- deadlines
- recent designs
- recent renders
- category distribution
- priority/status distribution

appear.

---

# 22. Security Regression Tests

Add focused tests for:

### Authentication

- invalid login
- duplicate registration
- missing token
- invalid token
- expired token

### Authorization

- cross-user design access
- cross-user design modification
- cross-user design deletion
- cross-user production access
- cross-user schedule access
- cross-user dashboard isolation

### Validation

- invalid UUID
- invalid enum
- invalid quantity
- invalid dates
- invalid optimization parameters

### AI

- unauthenticated rendering
- unauthorized design rendering
- unauthorized detection
- invalid category
- invalid image/input

### Configuration

- service-role key not exposed to frontend
- CORS behavior
- environment configuration

---

# 23. Baseline Regression

Phase 13 baseline:

```text
Backend: 85 passed
AI regression: 95 passed
Frontend build: 0 errors
```

Run the existing suites before and after security modifications.

If test counts increase because Phase 14 tests are added, explain the difference.

Target:

```text
0 failed
0 unexpected errors
0 regressions
```

---

# 24. Backend Tests

Use the project's established commands.

Preferred backend test execution:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/
```

Use the exact environment discovered during inspection if different.

For startup validation:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

AI worker when required:

```powershell
C:\Users\usern\miniconda3\envs\tgpu\python.exe -m ai.workers.local_worker
```

Do not assume paths if inspection shows different paths.

---

# 25. AI Regression

Do not retrain anything.

Run the existing AI regression suite.

Verify:

- YOLO loads
- ControlNet loads
- Appearance LoRA loads
- inference path remains unchanged
- CUDA works when worker is running
- model weights are unchanged

If a live GPU test is needed, perform only a minimal smoke test.

Record:

```text
device
model used
success/failure
inference time
output existence
```

Never record secrets.

---

# 26. Frontend Build

Run:

```powershell
npm --prefix frontend run build
```

Expected:

```text
TypeScript errors = 0
Vite build errors = 0
```

Do not hide errors with unnecessary:

```text
@ts-ignore
any
eslint-disable
```

---

# 27. Full End-to-End Smoke Test

After automated tests pass:

```text
Login
  ↓
Dashboard
  ↓
Create Design
  ↓
Canvas
  ↓
Save Sketch
  ↓
AI Render
  ↓
Supabase Render Persistence
  ↓
YOLO Detection
  ↓
Production Order
  ↓
OR-Tools Optimization
  ↓
Gantt Schedule
  ↓
Refresh
  ↓
Data remains available
```

Verify security changes did not break the real application.

---

# 28. Restart Persistence Test

Verify:

1. Start backend.
2. Start frontend.
3. Start AI worker.
4. Use/create a design.
5. Generate a render.
6. Refresh frontend.
7. Restart backend.
8. Refresh frontend.
9. Cloud-backed assets remain available.

Do not rely on local temporary rendering files for persistence.

---

# 29. Security Severity

Use:

### CRITICAL

- authentication bypass
- arbitrary code execution
- unrestricted cross-tenant access
- exposed service-role credentials

### HIGH

- authorization bypass on important resources
- unrestricted dangerous file upload
- exposed credentials
- publicly exposed privileged AI worker

### MEDIUM

- weak validation
- overly permissive CORS
- excessive internal error information

### LOW

- minor hardening/documentation opportunities

---

# 30. Required Reports

Create:

```text
PHASE_14_INITIAL_SECURITY_AUDIT.md
PHASE_14_SECURITY_AUDIT.md
PHASE_14_TEST_REPORT.md
PHASE_14_SECURITY_CHECKLIST.md
PHASE_14_FINAL_REPORT.md
```

## Final report must contain

### Executive Summary

Is JewelMind ready to proceed to deployment preparation?

### Security Posture

Summarize:

- authentication
- authorization
- tenant isolation
- Storage
- AI security
- API validation
- frontend security

### Exact Test Results

Show:

- test suite
- passed
- failed
- skipped
- errors

### Findings

For every finding:

```text
Severity
Area
Description
Evidence
Fix
Status
```

### Remaining Risks

Be honest about unresolved items.

For example, if Storage remains public:

> Backend APIs enforce tenant ownership, but direct possession of a public asset URL permits retrieval.

### Deployment Readiness

Use exactly one:

```text
READY
READY WITH WARNINGS
NOT READY
```

and explain why.

---

# 31. Final Checklist

Before declaring Phase 14 complete:

```text
[ ] Git working tree reviewed
[ ] No secrets tracked
[ ] .env ignored
[ ] Authentication tested
[ ] JWT validation tested
[ ] Multi-tenant isolation tested
[ ] IDOR protection tested
[ ] Supabase security reviewed
[ ] CORS reviewed
[ ] File uploads validated
[ ] Input validation tested
[ ] Error handling reviewed
[ ] Database access reviewed
[ ] AI endpoints secured
[ ] AI worker reviewed
[ ] Production authorization tested
[ ] OR-Tools authorization tested
[ ] Dashboard isolation tested
[ ] Frontend route protection tested
[ ] Backend tests pass
[ ] AI regression tests pass
[ ] Frontend build passes
[ ] End-to-end workflow passes
[ ] Restart persistence passes
[ ] No AI weights changed
[ ] No AI retraining performed
[ ] No Phase 15 work added
[ ] No Phase 16 work added
```

---

# 32. Git Review

Before committing:

```powershell
git status
git diff --check
git diff --stat
git diff
```

Confirm:

- only Phase 14 changes exist
- no secrets are present
- no model weights are present
- no datasets are present
- no temporary files are present
- no unrelated features were modified

**STOP HERE. Do not commit yet.**

Wait for manual review.

---

# 33. Commit — Only After Approval

After explicit approval:

```powershell
git add .
git commit -m "security: harden phase 14 and add security tests"
git push -u origin phase-14-testing-security
```

Do not merge into `main` until reviewed.

---

# 34. Phase Boundary

Phase 14 ends with testing and security hardening.

Do not implement:

- Cloudflare Pages deployment
- production hosting
- production domain
- deployment pipelines
- final presentation
- final viva script
- final capstone documentation package

Those belong to later phases.

---

# 35. Definition of Done

Phase 14 is complete only when:

```text
Authentication secure
        +
Authorization verified
        +
Multi-tenant isolation verified
        +
Secrets protected
        +
Supabase reviewed
        +
AI endpoints protected
        +
File uploads validated
        +
Input validation verified
        +
Production APIs isolated
        +
Dashboard isolated
        +
Security regression tests added
        +
Backend tests pass
        +
AI tests pass
        +
Frontend build passes
        +
End-to-end workflow passes
        +
No AI retraining
        +
No unrelated scope added
```

---

# 36. Antigravity Instructions

You are implementing **Phase 14 — Testing & Security** of JewelMind.

Follow this order:

1. Create `phase-14-testing-security`.
2. Inspect current `main`.
3. Read `PLAN.md`.
4. Produce the initial security audit.
5. Do not modify code until the audit is complete.
6. Identify verified security gaps.
7. Fix only necessary issues.
8. Add security/regression tests.
9. Run backend tests.
10. Run AI regression tests.
11. Build the frontend.
12. Perform cross-user authorization testing.
13. Perform the complete browser smoke test.
14. Verify no secrets are exposed.
15. Verify no model weights changed.
16. Verify no retraining occurred.
17. Review Git diff.
18. Produce all Phase 14 reports.
19. STOP.

**Do not commit, push, or merge.**

Use evidence rather than assumptions. If something is uncertain, report it instead of silently redesigning the system.
