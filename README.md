# 💎 JewelMind: AI-Powered Jewelry Design & Production Suite

JewelMind is an enterprise-grade AI jewelry design, photorealistic diffusion rendering, computer vision component detection, and constraint-based production scheduling platform.

---

## ⚡ Quick Start (Shortest Commands)

You can launch any service directly from the project root with **1-word commands**:

| Service | Short Command (from root) | Port & Local URL |
|---|---|---|
| **All Services at Once** | `.\run_all.bat` | Launches Backend, AI Worker & Frontend |
| **FastAPI Backend** | `.\run_backend.bat` | [http://127.0.0.1:8000](http://127.0.0.1:8000) (Docs: [`/docs`](http://127.0.0.1:8000/docs)) |
| **AI GPU Worker** | `.\run_ai.bat` | [http://127.0.0.1:8001](http://127.0.0.1:8001) (Health: [`/health`](http://127.0.0.1:8001/health)) |
| **Frontend UI** | `.\run_frontend.bat` | [http://localhost:5173](http://localhost:5173) |

---

## 🏗️ Architecture Overview

JewelMind operates across **three decoupled services**:

```text
┌─────────────────────────────────────────────────────────────┐
│                   Frontend (React + Vite)                   │
│                    http://localhost:5173                    │
└──────────────────────────────┬──────────────────────────────┘
                               │ (REST / JSON / Multipart)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 FastAPI Backend Service                     │
│                    http://127.0.0.1:8000                    │
│   (Auth, Designs, Production, OR-Tools CP-SAT Optimizer)    │
└──────────────────────────────┬──────────────────────────────┘
                               │ (Internal HTTP Job Dispatch)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                Dedicated AI Worker (PyTorch)                │
│                    http://127.0.0.1:8001                    │
│    (ControlNet Diffusion, SD1.5, LoRA, YOLO11-seg on CUDA)   │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 Prerequisites

Before starting, ensure you have:

1. **Node.js** (v18+ or v22+) & **npm**
2. **Python** (3.11+ or 3.13+)
3. **Miniconda / Conda** with the `tgpu` PyTorch CUDA environment
4. Configured environment variables in `.env` (Database, Supabase storage, JWT secrets)

---

## 🚀 Step-by-Step Multi-Terminal Execution

If you prefer running services manually across separate terminal windows:

---

### 🔹 Terminal 1: FastAPI Backend Service (Port 8000)

```powershell
# Short shortcut:
.\run_backend.bat

# Or direct command:
.\backend\.venv\Scripts\python.exe -m uvicorn --app-dir backend app.main:app --host 127.0.0.1 --port 8000 --reload
```

- **Backend URL:** [http://127.0.0.1:8000](http://127.0.0.1:8000)  
- **Interactive Swagger Docs:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)  
- **Health Check:** [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

### 🔹 Terminal 2: AI GPU Inference Worker (Port 8001)

```powershell
# Short shortcut:
.\run_ai.bat

# Or direct command:
C:\Users\usern\miniconda3\envs\tgpu\python.exe -m ai.workers.local_worker
```

- **AI Worker URL:** [http://127.0.0.1:8001](http://127.0.0.1:8001)  
- **Health Check:** [http://127.0.0.1:8001/health](http://127.0.0.1:8001/health)

---

### 🔹 Terminal 3: Frontend Web Application (Port 5173)

```powershell
# Short shortcut:
.\run_frontend.bat

# Or direct command:
cd frontend
npm run dev
```

- **Web App URL:** [http://localhost:5173](http://localhost:5173)

---

## 🧪 Running Automated Tests

### 1. Backend Unit & Integration Tests
```powershell
.\backend\.venv\Scripts\pytest backend/tests
```

### 2. AI Subsystem & Computer Vision Tests
```powershell
C:\Users\usern\miniconda3\envs\tgpu\python.exe -m pytest ai/tests
```

### 3. Frontend TypeScript & Production Build Validation
```powershell
cd frontend
npm run build
```

---

## 📂 Project Structure

```text
JewelMind/
├── run_backend.bat     # Shortcut to launch FastAPI backend
├── run_ai.bat          # Shortcut to launch AI GPU worker
├── run_frontend.bat    # Shortcut to launch Vite frontend
├── run_all.bat         # 1-click launcher for all 3 services
├── backend/            # FastAPI REST API, database schemas, OR-Tools optimization
│   ├── app/
│   │   ├── api/        # Endpoint routers (Auth, Designs, Production, AI, Analytics)
│   │   ├── core/       # Security, JWT tokens, configuration
│   │   ├── models/     # SQLAlchemy ORM models
│   │   ├── schemas/    # Pydantic schemas
│   │   └── services/   # Business logic & repository services
│   └── tests/          # Backend test suite
├── ai/                 # AI, generative diffusion, computer vision, and ML
│   ├── vision/         # YOLO11 component detection & OpenCV preprocessors
│   ├── rendering/      # Stable Diffusion + ControlNet + LoRA rendering pipeline
│   ├── optimization/   # Google OR-Tools CP-SAT production scheduling
│   └── workers/        # Asynchronous AI workers (local_worker.py)
├── frontend/           # React 19 + TypeScript + Vite + Tailwind CSS UI
│   ├── src/
│   │   ├── components/ # Canvas studio, UI widgets, Gantt chart, Studio gallery
│   │   └── pages/      # Dashboard, Studio, Production, Settings, Auth
└── docs/               # Architecture diagrams, specifications, and QA reports
```