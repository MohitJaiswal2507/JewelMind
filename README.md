# JewelMind
### AI-Powered Jewellery Design, Analysis & Production Planning Platform

> **Status:** Authentication & User Management / Phase 2  
> **Budget Constraint:** ₹0 (Zero paid infrastructure, APIs, GPU rentals, or subscriptions)  
> **Development Target:** Local RTX 4060 + Free Tier Cloud Ecosystem  

---

## 1. Overview
**JewelMind** is an end-to-end full-stack AI/ML decision-support web application that connects the complete lifecycle of jewellery manufacturing:
From initial freehand sketch upload, through generative AI visual rendering, automated computer vision component detection, machine learning estimation (material, cost, time, and wastage), down to constraint-based production scheduling.

---

## 2. The Problem
Traditional jewellery design and manufacturing operations are fragmented:
- Designers produce sketches with no immediate realistic preview.
- Material and gemstone counts are estimated manually or by trial.
- Costing, labor time, and scrap metal wastage calculations are error-prone.
- Manufacturability issues (e.g. fragile prongs or excessive joint complexity) are only discovered on the shop floor.
- Workshop schedules, artisan allocations, and machine queues are managed manually with spreadsheets.

---

## 3. Proposed Solution
JewelMind unifies this entire workflow into a single cohesive platform. It empowers jewellery designers, artisans, and manufacturing managers with AI-powered decision support without replacing human craftsmanship.

---

## 4. Core Workflow
```text
Jewellery Sketch
       ↓
AI Realistic Rendering (Diffusion + ControlNet)
       ↓
Component Detection (YOLO / Ultralytics)
       ↓
Design Feature Extraction
       ↓
Material & Gemstone Prediction
       ↓
Cost Estimation (Hybrid ML + Rule-based)
       ↓
Production Time Prediction (XGBoost)
       ↓
Wastage Prediction (XGBoost)
       ↓
Manufacturability Analysis & Scoring
       ↓
Production Order Creation
       ↓
Constraint Optimization (Google OR-Tools)
       ↓
Optimized Production Schedule
```

---

## 5. Key Features
- **Design & Sketch Management:** Upload and manage sketches across multiple jewellery categories (rings, necklaces, earrings, bracelets, bangles, pendants).
- **Sketch-to-Render AI:** Generate photorealistic jewellery visualizations while maintaining sketch geometry using structural conditioning.
- **Component Detection & Tagging:** Automatically detect and count gemstones, clasps, beads, hooks, and connectors.
- **Predictive Analytics:** Accurate estimations for metal weight, production hours, manufacturing costs, and material wastage.
- **Manufacturability Scoring:** Pre-production feasibility ratings and risk warnings.
- **Smart Workshop Scheduling:** Automated schedule generation optimizing artisan skills, machine availability, order deadlines, and priorities.

---

## 6. Target Architecture
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

---

## 7. Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | React 19, TypeScript, Vite, Tailwind CSS, React Router |
| **Backend** | Python, FastAPI, Pydantic, Uvicorn (SQLAlchemy / PostgreSQL planned) |
| **Database & Storage** | PostgreSQL / Supabase Free Tier, Supabase Object Storage |
| **Computer Vision** | OpenCV, PIL, YOLO / Ultralytics |
| **Generative AI** | PyTorch, Hugging Face Diffusers, ControlNet, LoRA |
| **Tabular ML** | XGBoost, scikit-learn, Pandas, NumPy |
| **Optimization** | Google OR-Tools (Constraint Programming) |
| **Hosting & Infra** | Cloudflare Pages, Local RTX 4060 GPU Worker, Optional Hugging Face ZeroGPU |

---

## 8. Project Structure
```text
JewelMind/
├── frontend/             # React + TypeScript + Tailwind web client
├── backend/              # FastAPI Python application
├── ai/                   # Modular AI/ML systems (vision, rendering, prediction, optimization)
├── docs/                 # Architectural specs, UML, phase reports, and deployment guides
├── datasets/             # Dataset documentation, raw/processed/annotation schemas
├── models/               # Model artifact registry and download instructions
├── scripts/              # Setup, utility, and maintenance scripts
├── tests/                # Integration and end-to-end testing suites
├── .env.example          # Environment variables template
├── .gitignore            # Git exclusion rules
├── PLAN.md               # Master technical plan
└── README.md             # Project overview (this file)
```

---

## 9. Budget Strategy (₹0 Constraint)
JewelMind is built strictly around a **₹0 infrastructure budget**:
- **Compute:** Local development & AI training/inference powered by an on-device NVIDIA RTX 4060 Laptop GPU.
- **Frontend Hosting:** Cloudflare Pages (free tier).
- **Backend & Database:** Free tier cloud hosting + Supabase managed PostgreSQL & Object Storage.
- **Secondary AI Cloud:** Hugging Face Spaces (free / ZeroGPU) for optional remote demonstration.

---

## 10. Roadmap & Phased Execution
- [x] **Phase 0:** Project Foundation & Repository Structure
- [x] **Phase 1:** Technical Architecture & Application Foundation
- [x] **Phase 2:** Authentication & User Management (Current)
- [ ] **Phase 3:** Jewellery Design Management
- [ ] **Phase 4:** Sketch Upload & Storage Integration
- [ ] **Phase 5:** AI Job Queue & Worker Architecture
- [ ] **Phase 6:** Jewellery Component Detection (YOLO)
- [ ] **Phase 7:** Sketch-to-Rendering Pipeline (Diffusion + ControlNet)
- [ ] **Phase 8:** Design Feature Extraction
- [ ] **Phase 9:** Predictive Analytics (Material, Cost, Time, Wastage via XGBoost)
- [ ] **Phase 10:** Manufacturability Analysis & Scoring
- [ ] **Phase 11:** Production Order Management
- [ ] **Phase 12:** Production Schedule Optimization (OR-Tools)
- [ ] **Phase 13:** Unified Analytics Dashboard
- [ ] **Phase 14:** Comprehensive Testing & Security Hardening
- [ ] **Phase 15:** ₹0 Production Deployment
- [ ] **Phase 16:** Final Documentation, UML, & Capstone Presentation

---

## 11. Documentation
Detailed project documentation is available in [`docs/`](./docs/):
- [`docs/architecture/ARCHITECTURE.md`](./docs/architecture/ARCHITECTURE.md) - System architecture design
- [`docs/architecture/DATABASE_DESIGN.md`](./docs/architecture/DATABASE_DESIGN.md) - Relational entity schemas & diagrams
- [`docs/api/API_CONVENTIONS.md`](./docs/api/API_CONVENTIONS.md) - API /v1 standards & error formatting
- [`docs/architecture/CONFIGURATION.md`](./docs/architecture/CONFIGURATION.md) - Environment variables matrix
- [`docs/architecture/TECH_STACK.md`](./docs/architecture/TECH_STACK.md) - Technology decisions & rationale
- [`docs/architecture/DEVELOPMENT_GUIDELINES.md`](./docs/architecture/DEVELOPMENT_GUIDELINES.md) - Code style & Git conventions
- [`docs/architecture/LOCAL_DEVELOPMENT.md`](./docs/architecture/LOCAL_DEVELOPMENT.md) - Local development setup
- [`docs/deployment/COST_POLICY.md`](./docs/deployment/COST_POLICY.md) - Zero-cost deployment policy
- [`docs/phases/PHASE_0_REPORT.md`](./docs/phases/PHASE_0_REPORT.md) - Phase 0 completion report
- [`docs/phases/PHASE_1_REPORT.md`](./docs/phases/PHASE_1_REPORT.md) - Phase 1 completion report
- [`docs/phases/PHASE_2_REPORT.md`](./docs/phases/PHASE_2_REPORT.md) - Phase 2 completion report