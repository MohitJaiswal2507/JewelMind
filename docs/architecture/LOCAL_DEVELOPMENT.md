# Local Development Environment Guide

This document outlines how to set up, run, and develop the JewelMind system locally on a developer workstation.

---

## 1. Prerequisites
- **Operating System:** Windows 10/11, Linux, or macOS.
- **Node.js:** v18+ (tested with v22.15.1) and npm.
- **Python:** Python 3.12+ (tested with Python 3.13.5) with `uv` package manager.
- **Git:** Latest version.
- **GPU (Optional for Phase 0, Recommended for AI phases):** NVIDIA RTX GPU with CUDA 12.x support (RTX 4060 Laptop GPU target).

---

## 2. Repository Layout for Local Development

```text
JewelMind/
├── frontend/             # Runs on http://localhost:5173
├── backend/              # Runs on http://localhost:8000
├── ai/                   # Modular ML scripts & local worker (runs on http://localhost:8001)
├── docs/                 # Documentation
└── tests/                # Automated test suites
```

---

## 3. Quick Start (Phase 0 Foundation)

### 3.1 Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
The web client will be available at `http://localhost:5173`.

### 3.2 Backend Setup
```bash
cd backend
uv venv
# Activate virtual environment:
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Linux/macOS:
source .venv/bin/activate

uv pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
The FastAPI interactive documentation will be available at `http://localhost:8000/docs`.

---

## 4. Environment Configuration
Copy the `.env.example` file in the root directory to `.env` (or configure separate `.env` files in `frontend/` and `backend/` as needed):
```bash
cp .env.example .env
```
Update variable values as appropriate for your local ports and Supabase credentials.
