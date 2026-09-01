# JewelMind Environment Setup Guide

> **Project:** JewelMind — AI Jewellery Design, Analysis & Production Planning Platform  
> **Database:** Supabase Managed PostgreSQL (Free Tier)  
> **Backend:** FastAPI + SQLAlchemy 2.0 + Alembic  
> **Frontend:** React + Vite + Tailwind CSS + shadcn/ui  
> **Budget Spent:** ₹0  

---

## 1. Overview
JewelMind uses a centralized environment variable architecture loaded via Pydantic Settings (`backend/app/core/config.py`) and Vite environment variables (`import.meta.env`).

---

## 2. Environment Files Organization

| Location | Purpose | Tracked in Git? |
| :--- | :--- | :--- |
| `.env` | Master environment file for backend services & local scripts | ❌ **No** (Strictly Gitignored) |
| `.env.example` | Template for master environment variables | ✅ **Yes** |
| `backend/.env` | Backend-specific environment fallback | ❌ **No** (Strictly Gitignored) |
| `frontend/.env` | Local frontend environment variables (`VITE_*`) | ❌ **No** (Strictly Gitignored) |
| `frontend/.env.example` | Template for frontend environment variables | ✅ **Yes** |

---

## 3. Required Environment Variables

### Backend Configuration (`.env` / `backend/.env`)

```env
# Application Environment (development, testing, production)
APP_ENV=development
DEBUG=true
LOG_LEVEL=INFO

# Service URLs
BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:5173

# Database (Supabase PostgreSQL Session Pooler)
DATABASE_URL=postgresql://postgres.<PROJECT_REF>:<URL_ENCODED_PASSWORD>@<POOLER_HOST>:5432/postgres
DB_ECHO_LOG=false

# Authentication & JWT Security
JWT_SECRET_KEY=<GENERATED_LOCALLY_MIN_32_CHARS>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Supabase Storage & Free Tier Keys (Future Phases)
SUPABASE_URL=https://<PROJECT_REF>.supabase.co
SUPABASE_ANON_KEY=<ANON_KEY>
SUPABASE_SERVICE_ROLE_KEY=<SERVICE_ROLE_KEY>
SUPABASE_STORAGE_BUCKET=jewelmind-assets
```

### Frontend Configuration (`frontend/.env`)

```env
# Frontend API Base Target URL
VITE_API_URL=http://localhost:8000
```

---

## 4. How to Obtain the Supabase Connection String

1. Log into your [Supabase Dashboard](https://supabase.com/dashboard).
2. Select your project $\rightarrow$ Click on the **Connect** button in the top navigation bar.
3. Under **Type / Framework**, select **URI**.
4. Choose **Session Pooler** (Port `5432`) or **Transaction Pooler** (Port `6543`).
5. Copy the connection URI:
   ```text
   postgresql://postgres.<PROJECT_REF>:[YOUR-PASSWORD]@<POOLER_HOST>:5432/postgres
   ```
6. Replace `[YOUR-PASSWORD]` with your actual database password.
   > **Note on Special Characters:** If your database password contains characters like `@`, `#`, `$`, `%`, or `/`, URL-encode them (e.g. `@` becomes `%40`) or use an alphanumeric password to avoid URI parsing issues.

---

## 5. Starting the Application Locally

### Running the Backend

From the repository root (or `backend/` directory):

```bash
# Windows PowerShell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at:
- **API Root / Health:** `http://localhost:8000/api/v1/health`
- **Interactive OpenAPI Docs:** `http://localhost:8000/docs`
- **Alternative ReDoc Docs:** `http://localhost:8000/redoc`

### Running the Frontend

In a separate terminal:

```bash
cd frontend
npm run dev
```

The web application will open at:
- `http://localhost:5173`

---

## 6. Verifying Database Connectivity & Migrations

### Verify Connection via Python

```bash
cd backend
.venv\Scripts\python.exe -c "
from app.db.session import engine
from sqlalchemy import text
with engine.connect() as conn:
    print('Connection OK:', conn.execute(text('SELECT version();')).scalar())
"
```

### Run Alembic Migrations

```bash
cd backend
.venv\Scripts\alembic.exe upgrade head
```

### Check Current Migration Revision

```bash
cd backend
.venv\Scripts\alembic.exe current
```

---

## 7. Security Rules
1. **Never commit `.env` or `backend/.env`**: Ensure `.gitignore` ignores all `.env*` files except `.env.example`.
2. **Never expose passwords in URLs**: Scrub connection strings before printing logs or creating reports.
3. **Keep JWT Secrets Random**: Generate 32+ character cryptographically random secrets locally via Python `secrets.token_urlsafe(32)`.
