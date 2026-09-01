# JewelMind — Phase 2: Authentication & User Management

> **Execution document for Antigravity**
>
> This phase must be completed independently. Do **not** begin Phase 3 or implement heavy AI/design functionality.
> Read the existing project structure and Phase 0/Phase 1 documentation before making changes.
> Preserve the architecture already established in the repository.

---

## 1. Phase Information

**Phase:** 2  
**Name:** Authentication & User Management  
**Git Branch:** `phase-2-authentication`  
**Base Branch:** `main`

### Objective

Build a complete, secure and testable authentication foundation for JewelMind.

At the end of this phase, a user should be able to:

1. Create an account.
2. Log in.
3. Receive an authenticated session/token.
4. Access protected backend endpoints.
5. Retrieve their own profile using an authenticated endpoint.
6. Log out.
7. Have invalid/expired credentials rejected correctly.
8. Use authentication through the React frontend.

This phase establishes the identity layer that later phases will use for jewellery designs, sketches, AI jobs, renderings, production planning and user-owned data.

---

# 2. Important Project Rules

Follow these rules throughout Phase 2.

### 2.1 Do not redesign the whole UI

The current goal is functionality and architecture.

Use:

- **Tailwind CSS** for responsive styling.
- **shadcn/ui** for UI components.
- Existing project styling conventions where available.

Do not spend this phase recreating the final polished JewelMind visual design.

The detailed UI refinement/recreation will happen later after the core application functionality is working.

### 2.2 Do not implement future phases

Do NOT implement:

- AI jewellery generation
- Sketch-to-rendering AI
- Image generation models
- Production planning engine
- Jewellery design database beyond what authentication requires
- Manufacturing workflows
- Advanced dashboards
- Marketplace functionality
- Final branding/visual redesign

Only create the foundation required for authentication and user management.

### 2.3 Preserve Phase 1 architecture

Before coding:

1. Read the Phase 0 documentation.
2. Read the Phase 1 architecture documentation.
3. Inspect the existing backend structure.
4. Inspect the existing frontend structure.
5. Reuse existing configuration, database, error handling, logging and API conventions.
6. Do not replace working architecture merely to introduce a different pattern.

If an implementation decision is necessary and Phase 1 already defines a convention, follow Phase 1.

---

# 3. Git Workflow

Create the branch:

```bash
git checkout main
git pull origin main
git checkout -b phase-2-authentication
```

All Phase 2 work must happen on:

```text
phase-2-authentication
```

Do not commit Phase 2 directly to `main`.

Before finishing:

```bash
git status
git diff
```

Review all changes.

Run all required tests and validation.

Commit using a meaningful message, for example:

```bash
git add .
git commit -m "feat: implement authentication and user management"
git push -u origin phase-2-authentication
```

Do NOT merge into `main` automatically.

The project owner will review the Phase 2 report and merge the branch manually.

---

# 4. Backend Scope

## 4.1 User Model

Create the User database model according to the conventions established in Phase 1.

Minimum conceptual fields:

- `id`
- `email`
- `password_hash`
- `full_name` or equivalent display-name field
- `is_active`
- `created_at`
- `updated_at`

Use appropriate constraints.

### Email

Email must be:

- required
- normalized consistently
- unique
- validated

Do not store plaintext passwords.

### Password

Never store:

```text
password
```

directly in the database.

Only a secure password hash may be stored.

Use a modern, maintained password hashing implementation compatible with the project's Python version and existing dependency strategy.

Document the selected hashing approach in the Phase 2 report.

---

# 5. Database Migration

Create the required Alembic migration for the User table.

The migration must:

- create the user table
- create the unique email constraint/index
- create required timestamps/fields
- follow the existing naming conventions
- be reversible where practical

Do not manually modify the database without a migration.

Verify that:

```bash
alembic upgrade head
```

works successfully.

Also verify that the migration can be downgraded and reapplied in a safe development environment if the existing migration strategy supports this.

---

# 6. Authentication Architecture

Implement an authentication mechanism appropriate for the existing JewelMind architecture.

The preferred design is:

```text
React Frontend
      │
      │ Login/Register
      ▼
FastAPI Authentication API
      │
      ├── Validate input
      ├── Hash/verify password
      ├── Create/verify JWT
      │
      ▼
PostgreSQL
      │
      ▼
Authenticated User
```

Use JWT-based authentication unless Phase 1 explicitly establishes another compatible mechanism.

### Token requirements

The implementation must include:

- secure token signing
- configurable secret through environment variables
- configurable token expiration
- user identity in token claims
- validation of token signature
- validation of expiration
- rejection of malformed/invalid tokens

Do not hard-code secrets.

---

# 7. Environment Variables

Do not commit real secrets.

Update `.env.example` with the variables required for authentication.

For example, conceptually:

```env
JWT_SECRET_KEY=
JWT_ALGORITHM=
ACCESS_TOKEN_EXPIRE_MINUTES=
```

Use the exact naming conventions already established in Phase 1 if equivalent variables already exist.

### Important

The real `.env` file must remain ignored by Git.

Never commit:

```text
.env
.env.local
```

or any file containing real credentials/secrets.

The Phase 2 report must clearly explain:

- which variables were added
- what each variable does
- where the developer should place the local values
- which values are safe defaults
- which values must be generated/secret

Do not place real secret values in documentation.

---

# 8. Authentication API

Implement clean API endpoints following the existing API versioning and routing conventions.

At minimum, support:

## Register

```http
POST /api/v1/auth/register
```

Expected behavior:

1. Validate request data.
2. Normalize email.
3. Check whether the email already exists.
4. Reject duplicate email appropriately.
5. Validate password requirements.
6. Hash the password.
7. Create the user.
8. Return a safe user representation.

Never return:

```text
password
password_hash
JWT secret
```

in an API response.

---

## Login

```http
POST /api/v1/auth/login
```

Expected behavior:

1. Validate credentials.
2. Find user.
3. Verify password hash.
4. Reject invalid credentials without leaking sensitive information.
5. Generate authentication token(s) according to the selected architecture.
6. Return the authenticated session/token response.

---

## Current User

```http
GET /api/v1/auth/me
```

This must be protected.

A valid authenticated request should return the current user's safe profile.

An unauthenticated request must be rejected.

---

## Logout

```http
POST /api/v1/auth/logout
```

Implement logout according to the chosen token/session architecture.

If the architecture uses stateless short-lived JWT access tokens, document what logout means operationally and how token lifetime/security is handled.

If refresh tokens or server-side sessions are implemented, revoke/invalidate the refresh session appropriately.

Do not claim that a stateless JWT is server-side revoked if the implementation does not actually support revocation.

---

# 9. Authentication Dependency / Guard

Create a reusable backend authentication dependency/helper.

Conceptually:

```text
Request
  │
  ▼
Authentication Dependency
  │
  ├── No credentials → 401
  ├── Invalid token → 401
  ├── Expired token → 401
  ├── Unknown user → 401
  │
  ▼
Current User
  │
  ▼
Protected Endpoint
```

Future modules must be able to reuse this dependency without duplicating authentication logic.

Do not put authentication checks manually inside every endpoint.

---

# 10. Password Validation

Define sensible password requirements.

At minimum:

- non-empty
- reasonable minimum length
- reject obviously invalid input

Do not create unnecessarily complicated password rules that make development/testing difficult.

Use Pydantic validation consistent with Phase 1.

Return useful validation errors without exposing sensitive information.

---

# 11. API Schemas

Create request/response schemas for authentication.

Conceptually:

```text
UserCreate
LoginRequest
UserResponse
TokenResponse
```

Use the existing project schema conventions.

User response schemas must never expose:

```text
password_hash
```

---

# 12. HTTP Error Handling

Use the centralized exception/error handling architecture from Phase 1.

Authentication should correctly handle:

### 400

Invalid request data where appropriate.

### 401

- invalid credentials
- missing credentials
- invalid token
- expired token

### 409

Duplicate registration email if this matches the project's established API convention.

Do not expose whether a login email exists in a way that creates unnecessary account enumeration risk.

---

# 13. Frontend Authentication

Implement the basic authentication UI using the existing React architecture.

Required screens/components:

### Registration

Fields:

- Full name
- Email
- Password
- Confirm password

Include:

- client-side validation
- loading state
- error state
- success handling
- responsive layout

### Login

Fields:

- Email
- Password

Include:

- loading state
- error state
- successful authentication state
- responsive layout

### Authenticated User State

Create a reusable frontend authentication state mechanism.

It should allow the application to determine:

```text
loading
authenticated
unauthenticated
```

and expose the current user where appropriate.

Follow the existing frontend architecture rather than introducing an unnecessary state-management library.

---

# 14. Protected Frontend Route

Create a minimal protected route/page to prove authentication works.

For example:

```text
/dashboard
```

The page does not need to be the final JewelMind dashboard.

It only needs to demonstrate:

```text
Unauthenticated user
        │
        ▼
     Login

Authenticated user
        │
        ▼
   Protected page
```

Display basic user information such as:

```text
Welcome, <name>
Email: <email>
```

Do not build the final dashboard in this phase.

---

# 15. Logout Frontend Flow

Add a logout action.

After logout:

1. Authentication state must be cleared.
2. User must no longer be treated as authenticated.
3. Protected pages must no longer be accessible.
4. User should be redirected to the appropriate unauthenticated page.

---

# 16. API Client

Use the existing frontend API client architecture from Phase 1.

Do not create random `fetch()` calls throughout components.

Authentication requests should go through the project's centralized API layer.

The API base URL must come from environment configuration.

For Vite, follow the existing convention for public frontend environment variables.

Do not put secrets in frontend environment variables.

Remember:

> Anything exposed to a browser frontend is potentially public.

---

# 17. CORS

Verify the existing FastAPI CORS configuration.

Authentication requests from the frontend must work locally.

The configuration must not use an unnecessarily broad production policy such as blindly allowing every origin.

Use environment-based configuration where appropriate.

Example development relationship:

```text
Frontend
http://localhost:5173

        │
        ▼

Backend
http://localhost:8000
```

Document the CORS configuration.

---

# 18. Security Requirements

Implement the following:

- Password hashing
- No plaintext passwords
- No password hash in API responses
- Configurable JWT secret
- Configurable token expiration
- Input validation
- Authentication dependency
- Correct 401 handling
- No secrets committed
- `.env` remains ignored
- Avoid sensitive data in logs
- Avoid returning passwords/tokens unnecessarily
- Avoid hard-coded credentials

Do not add insecure demo credentials to the repository.

---

# 19. Testing

Testing is a mandatory part of this phase.

## Backend tests

Create tests for at least:

### Registration

- valid registration succeeds
- duplicate email is rejected
- invalid email is rejected
- invalid password is rejected
- password is stored hashed

### Login

- valid credentials succeed
- invalid password fails
- unknown account fails
- token/session is generated correctly

### Authentication

- valid authentication succeeds
- missing authentication fails
- malformed token fails
- expired token fails
- unknown user/token identity fails

### `/me`

- authenticated request returns current user
- unauthenticated request returns 401

### Logout

Test according to the selected token/session strategy.

---

# 20. Frontend Validation

Verify manually and/or through appropriate tests:

### Registration

```text
Register
   ↓
Validation
   ↓
API request
   ↓
Account created
```

### Login

```text
Login
   ↓
API request
   ↓
Authentication
   ↓
Protected page
```

### Logout

```text
Logout
   ↓
Auth state cleared
   ↓
Protected page blocked
```

### Responsive UI

Verify authentication pages at:

- desktop
- tablet
- mobile

Use Tailwind responsive utilities.

Use shadcn/ui components where appropriate.

---

# 21. Manual Acceptance Test

Antigravity must perform this complete manual test before reporting completion.

### Test 1 — Registration

Create a new user.

Expected:

```text
Account created successfully
```

### Test 2 — Duplicate registration

Register the same email again.

Expected:

```text
Request rejected
```

### Test 3 — Login

Use valid credentials.

Expected:

```text
Authentication successful
```

### Test 4 — Invalid login

Use an incorrect password.

Expected:

```text
Authentication rejected
```

### Test 5 — Protected endpoint

Open:

```text
GET /api/v1/auth/me
```

with valid authentication.

Expected:

```text
Current user returned
```

### Test 6 — Unauthenticated request

Call `/me` without valid authentication.

Expected:

```text
401 Unauthorized
```

### Test 7 — Logout

Logout from the frontend.

Expected:

```text
User becomes unauthenticated
Protected page inaccessible
```

---

# 22. Documentation

Create:

```text
docs/phases/PHASE_2_REPORT.md
```

The report must contain:

## 22.1 Summary

What was implemented.

## 22.2 Architecture

Explain:

```text
Frontend
   ↓
Auth API
   ↓
Authentication Service
   ↓
User Model
   ↓
PostgreSQL
```

## 22.3 Files Changed

List important files created/modified.

## 22.4 Database Changes

Explain the User table and migration.

## 22.5 Authentication Flow

Explain registration, login, token/session validation, `/me`, and logout.

## 22.6 Security

Explain:

- password hashing
- JWT/session security
- secrets
- environment variables
- error handling
- CORS
- logging considerations

## 22.7 Environment Variables

List variable names and explain how the developer should configure them.

Do not include real secrets.

## 22.8 Tests

Report:

```text
Backend tests: PASS/FAIL
Frontend build: PASS/FAIL
Manual authentication flow: PASS/FAIL
Migration validation: PASS/FAIL
Secret scan/repository check: PASS/FAIL
```

Include actual numbers where possible.

## 22.9 Known Issues

Only list real issues.

Do not hide failures.

## 22.10 Phase Boundary

Explicitly state that AI rendering, sketch processing, jewellery design workflows and production planning were intentionally NOT implemented in Phase 2.

## 22.11 Next Phase

State what Phase 3 is expected to address based on the existing project plan, but do not implement it.

---

# 23. Final Validation Checklist

Before declaring Phase 2 complete:

- [ ] Phase 0 documentation reviewed
- [ ] Phase 1 documentation reviewed
- [ ] Existing architecture preserved
- [ ] `phase-2-authentication` branch created
- [ ] User model implemented
- [ ] Alembic migration created
- [ ] Registration API implemented
- [ ] Login API implemented
- [ ] `/me` API implemented
- [ ] Logout API implemented
- [ ] Authentication dependency implemented
- [ ] Password hashing implemented
- [ ] JWT/session security implemented
- [ ] Environment variables documented
- [ ] No real secrets committed
- [ ] `.env` remains ignored
- [ ] CORS verified
- [ ] Frontend registration page implemented
- [ ] Frontend login page implemented
- [ ] Frontend auth state implemented
- [ ] Protected page implemented
- [ ] Logout flow implemented
- [ ] Tailwind responsiveness verified
- [ ] shadcn/ui used where appropriate
- [ ] Backend tests pass
- [ ] Frontend build passes
- [ ] Manual auth flow passes
- [ ] Migration validation passes
- [ ] Final Phase 2 report created

---

# 24. Definition of Done

Phase 2 is complete only when:

```text
User
 │
 ├── Register ──────────────► Account created
 │
 ├── Login ────────────────► Authenticated
 │
 ├── Access protected API ─► Allowed
 │
 ├── Access /me ───────────► Own profile returned
 │
 └── Logout ───────────────► Authentication cleared
```

and:

```text
Unauthenticated User
        │
        └── Protected Resource ──► 401 Unauthorized
```

The implementation must be:

- functional
- testable
- documented
- responsive
- secure for a capstone/development environment
- consistent with Phase 1 architecture
- free of committed secrets

---

# 25. Antigravity Execution Instruction

**Read this entire file before making changes.**

Then:

1. Inspect Phase 0 and Phase 1 documentation.
2. Inspect the existing repository structure.
3. Create the `phase-2-authentication` branch.
4. Implement ONLY the work described in this document.
5. Do not proceed to future phases.
6. Run all tests and validation.
7. Fix failures before completion.
8. Create `docs/phases/PHASE_2_REPORT.md`.
9. Review the final Git diff.
10. Ensure no secrets are committed.
11. Commit the Phase 2 work to the branch.
12. Push the branch.
13. Do NOT merge into `main`.
14. Stop and wait for project-owner review.

At the end, provide a concise summary of:

- what was implemented
- tests run and their results
- files created/changed
- environment variables required
- any known issues
- branch name
- commit hash
- confirmation that the branch was NOT merged into `main`
