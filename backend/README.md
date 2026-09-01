# JewelMind Backend Service

FastAPI-powered asynchronous REST API service for the JewelMind platform.

---

## Architecture
```text
app/
├── api/          # Route handlers & endpoints (Auth, Designs, Sketches, AI, Production, Optimization)
├── core/         # Configuration, security, CORS, and settings management
├── models/       # Database ORM models (SQLAlchemy - Phase 1+)
├── schemas/      # Pydantic data schemas & request/response validators
├── services/     # Business logic & repository services
└── main.py       # FastAPI application entrypoint & middleware configuration
```

---

## Running the Backend (Phase 0)

### 1. Create and Activate Virtual Environment
```bash
uv venv
# Windows:
.venv\Scripts\Activate.ps1
# Linux/macOS:
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
uv pip install -r requirements.txt
```

### 3. Run Development Server
```bash
uvicorn app.main:app --reload --port 8000
```

### 4. Endpoints
- **Root:** `http://localhost:8000/`
- **Health Check:** `http://localhost:8000/health`
- **Swagger Documentation:** `http://localhost:8000/docs`
- **ReDoc Documentation:** `http://localhost:8000/redoc`
