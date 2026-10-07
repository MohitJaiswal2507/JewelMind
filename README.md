# JewelMind

> AI-Powered Jewellery Design, Photorealistic Diffusion Rendering, Gemological Vision & Shop Floor Manufacturing OS.

JewelMind is an end-to-end jewellery intelligence platform that bridges high-end creative design and precision workshop manufacturing. It transforms hand-drawn sketches and CAD concepts into photorealistic customer renders, extracts gemological bill of materials via neural vision, and generates mathematically optimized karigar bench schedules using constraint programming—before a single gram of gold is melted.

---

[![React](https://img.shields.io/badge/React-19.0-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.8-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Vite](https://img.shields.io/badge/Vite-6.0-646CFF?style=for-the-badge&logo=vite&logoColor=white)](https://vitejs.dev/)
[![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-v4-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-CUDA_12.1-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)](https://pytorch.org/)
[![Stable Diffusion](https://img.shields.io/badge/Stable_Diffusion-ControlNet-FFA000?style=for-the-badge&logo=stabilityai&logoColor=white)](https://stability.ai/)
[![YOLOv8](https://img.shields.io/badge/YOLO11-Segmentation-00FFFF?style=for-the-badge&logo=ultralytics&logoColor=black)](https://ultralytics.com/)
[![Google OR-Tools](https://img.shields.io/badge/Google_OR--Tools-CP--SAT-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://developers.google.com/optimization)
[![Gemini](https://img.shields.io/badge/Google_Gemini-2.5_Flash-8E75B2?style=for-the-badge&logo=google-gemini&logoColor=white)](https://ai.google.dev/)
[![SQLite](https://img.shields.io/badge/SQLite-SQLAlchemy_2.0-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org/)

---

## 📌 Table of Contents

- [Demo & Resources](#-demo--resources)
- [Installation & Setup](#-installation--setup)
- [Screenshots](#-screenshots)
- [Core Features](#-core-features)
- [Tech Stack](#-tech-stack)
- [System Architecture](#-system-architecture)
- [End-to-End Workflow](#-end-to-end-workflow)
- [Project Structure](#-project-structure)
- [Key Modules Explained](#-key-modules-explained)
- [Automated Testing Suite](#-automated-testing-suite)
- [Future Improvements](#-future-improvements)
- [Contributing](#-contributing)
- [License](#-license)
- [Author & Contact](#-author--contact)
- [Acknowledgements](#-acknowledgements)

---

## 🎥 Demo & Resources

| Resource | Link / Location |
| :--- | :--- |
| **🌐 Local Web App** | [http://localhost:5173](http://localhost:5173) |
| **📑 Interactive API Docs (Swagger)** | [http://localhost:8000/docs](http://localhost:8000/docs) |
| **🔬 Alternative API Docs (ReDoc)** | [http://localhost:8000/redoc](http://localhost:8000/redoc) |
| **🤖 AI Worker Health Endpoint** | [http://localhost:8001/health](http://localhost:8001/health) |

---

## ⚡ Installation & Setup

### Prerequisites
- **Node.js**: `v18.x` or higher (v20+ recommended) & **npm**
- **Python**: `v3.11` (or Python with virtual environment support)
- **NVIDIA GPU (Optional but recommended for AI Worker)**: CUDA 11.8+ / 12.1+ for local Stable Diffusion & YOLO inference
- **Git**

---

### Quickstart (1-Click Launchers)

For rapid development on Windows, launch all decoupled microservices simultaneously:

```cmd
.\launchers\run_all.bat
```

Or start individual services with dedicated bat launchers:
- **FastAPI Backend (Port 8000)**: `.\launchers\run_backend.bat`
- **AI Inference Worker (Port 8001)**: `.\launchers\run_ai.bat`
- **Frontend App (Port 5173)**: `.\launchers\run_frontend.bat`

---

### Manual Setup (Step-by-Step)

#### 1. Clone the repository
```bash
git clone https://github.com/MohitJaiswal2507/JewelMind.git
cd JewelMind
```

#### 2. Backend Setup
```bash
cd backend
python -m venv .venv

# On Windows:
.\.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

#### 3. AI Worker Setup (GPU / CUDA Environment)
```bash
cd ../ai
# Using conda or your preferred python environment:
conda activate tgpu  # Or active virtual environment
pip install -r requirements.txt
```

#### 4. Frontend Setup
```bash
cd ../frontend
npm install
```

#### 5. Environment Variables Configuration
Create a `.env` file in `backend/` (or copy `.env.example`):
```env
PROJECT_NAME="JewelMind"
API_V1_STR="/api/v1"
SECRET_KEY="your-super-secret-jwt-key"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=1440
DATABASE_URL="sqlite:///./jewelmind.db"
GEMINI_API_KEY="your-google-gemini-api-key"
AI_WORKER_URL="http://127.0.0.1:8001"
```

#### 6. Start Development Servers (3 Terminals)

- **Terminal 1 (Backend API):**
  ```bash
  cd backend
  .\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
  ```
- **Terminal 2 (AI GPU Worker):**
  ```bash
  cd ai
  python -m ai.workers.local_worker
  ```
- **Terminal 3 (Frontend Web App):**
  ```bash
  cd frontend
  npm run dev
  ```

Open [`http://localhost:5173`](http://localhost:5173) in your browser.

---

## 🖼️ Screenshots

<details open>
<summary><b>Click to expand / collapse application screenshots</b></summary>

<br />

| View | Preview |
| :--- | :--- |
| **Landing Page** | ![Landing Page](./screenshots/landing_page.png) |
| **Executive Atelier Dashboard** | ![Dashboard](./screenshots/dashboard.png) |
| **Canva: Drawing Desk (Doodle-to-Render)** | ![Canva Drawing Desk](./screenshots/canva_draw2render.png) |
| **Canva: Text-to-Render Prompt Studio** | ![Canva Text to Render](./screenshots/canva_text2render.png) |
| **Canva: Gemological Scan (Image-to-Render)** | ![Canva Image to Render](./screenshots/canva_image2render.png) |
| **Production Studio & Media History** | ![Production Studio](./screenshots/studio.png) |
| **Design Catalogue** | ![Design Catalogue](./screenshots/Design%20Catalogue.png) |
| **Production Command Center** | ![Production Command Center](./screenshots/production.png) |
| **Karigar Shop Floor Terminal** | ![Shop Floor Execution](./screenshots/shop_floor.png) |
| **Workshop Yield & Scrap Analytics** | ![Yield Analytics](./screenshots/analytics.png) |
| **Authentication: Sign In** | ![Sign In](./screenshots/sign_in.png) |
| **Authentication: Sign Up** | ![Sign Up](./screenshots/sign_up.png) |

</details>

---

## ✨ Core Features

- **🎨 Symmetry Drawing Canvas (Canva Workspace)**: Real-time 2-way, 4-way, and radial symmetry drawing engine with stone seat guides, prong aligners, and vector smoothing.
- **👁️ Gemological Computer Vision**: Integrated YOLO11 / YOLOv8 segmentation that automatically classifies stones, counts prongs, detects center gems, and checks manufacturability.
- **✨ Dual AI Rendering Pipelines**:
  - **Local CUDA GPU Pipeline**: Stable Diffusion 1.5 + ControlNet (Canny & Tile) + custom fine-tuned Jewellery LoRA models.
  - **Cloud Multi-Modal Pipeline**: Google Gemini 2.5 Flash for conversational design refinement, style recommendations, and prompts.
- **📋 Automated Bill of Materials (BOM) & Valuation**: Calculates exact metal weights, diamond carats, labor wastage, and Indian market daily bullion rates (24K, 22K, 18K gold).
- **⏱️ Constraint-Based Scheduling (OR-Tools CP-SAT)**: Mathematical optimization that schedules cast, set, polish, and QC tasks across karigar workstations while honoring worker skills and machine limits.
- **🏭 Karigar Workstation Terminal**: Touch-friendly interface with step timers, live job dispatches, material consumption logging, and multi-point QC approval gates.
- **📊 Real-time Yield & Loss Analytics**: Live scrap tracking, planned vs. actual variance reporting, karigar efficiency rankings, and bottleneck discovery.
- **⚡ High-Performance Architecture**: Lazy-loaded route chunks, progressive WebP/JPEG assets, and resilient HTTP timeouts with graceful offline fallbacks.

---

## 🛠️ Tech Stack

| Category | Technology | Description |
| :--- | :--- | :--- |
| **Frontend Framework** | React 19, TypeScript, Vite | Lightning-fast component tree with on-demand code splitting |
| **Styling & Design System** | Tailwind CSS v4, Lucide Icons | Atelier luxury aesthetic with custom gold palettes and fluid animations |
| **Backend Framework** | FastAPI, Pydantic v2, Starlette | High-throughput asynchronous Python REST API with automatic OpenAPI docs |
| **Database & ORM** | SQLite / PostgreSQL, SQLAlchemy 2.0 | Async database access with transactional order and design storage |
| **Authentication** | OAuth2 Password Bearer, PyJWT, Passlib | Secure salt-hashed authentication with configurable session lifespans |
| **Generative AI** | Stable Diffusion 1.5, ControlNet, LoRA | Diffusion pipeline generating photorealistic metal textures and gem fire |
| **Computer Vision** | YOLO11-seg, OpenCV, Pillow | Component contouring, prong detection, and design segmentation |
| **Mathematical Optimization** | Google OR-Tools CP-SAT | Finite-domain constraint programming for workshop bench scheduling |
| **Conversational AI** | Google Gemini 2.5 Flash | Real-time design assistant with contextual gemological knowledge |
| **Testing Suite** | Pytest, Vitest, Playwright | Comprehensive unit, integration, and E2E coverage across frontend & backend |

---

## 🏗️ System Architecture

```mermaid
flowchart TD
    subgraph Client ["Client Browser (React 19 + TypeScript)"]
        UI[Luxury Atelier Frontend]
        CANVA[Canva Drawing Desk & Symmetry Canvas]
        SHOP[Karigar Shop Floor Terminal]
        ANALYTICS[Yield Analytics & Gantt View]
    end

    subgraph APIServer ["FastAPI Backend (Port 8000)"]
        AUTH[Auth & JWT Middleware]
        DESIGNS[Designs & BOM Service]
        PROD[Production Orders Service]
        CPSAT[OR-Tools CP-SAT Scheduler Engine]
        VAL[Live Bullion Valuation Service]
        DB[(SQLAlchemy / SQLite Database)]
    end

    subgraph AIWorker ["Dedicated AI GPU Worker (Port 8001)"]
        DIFFUSION[Stable Diffusion 1.5 + ControlNet Pipeline]
        LORA[Fine-Tuned Jewellery LoRA Weights]
        YOLO[YOLO11-seg Gemological Vision Scanner]
        CV[OpenCV Edge & Symmetry Preprocessors]
    end

    subgraph CloudServices ["External Services"]
        GEMINI[Google Gemini 2.5 Flash API]
    end

    UI -->|REST / JSON / Multipart| AUTH
    CANVA -->|Upload Sketch / Doodle| DESIGNS
    SHOP -->|Log Scrap & Elapsed Time| PROD

    AUTH --> DB
    DESIGNS --> DB
    PROD --> DB
    CPSAT --> PROD
    VAL --> PROD

    DESIGNS -->|Internal Job Dispatch| DIFFUSION
    DESIGNS -->|Computer Vision Parse| YOLO
    DIFFUSION --> LORA
    YOLO --> CV

    DESIGNS <-->|Interactive Atelier Chat| GEMINI
```

---

## 📊 End-to-End Workflow

The 5-stage **Crafting Continuum** bridges every step between initial creative vision and the final hallmarked piece:

```mermaid
sequenceDiagram
    autonumber
    actor Designer as Jewelry Designer
    participant Frontend as Canva Workspace
    participant API as FastAPI Backend
    participant AI as AI Worker (CUDA)
    participant Solver as OR-Tools CP-SAT
    actor Karigar as Workshop Karigar

    Designer->>Frontend: Draw sketch with radial symmetry or upload doodle
    Frontend->>API: Submit concept + style parameters (Metal: 18K Yellow Gold, Gem: Emerald)
    API->>AI: Trigger YOLO11 Segmentation & ControlNet Diffusion
    AI-->>API: Return photorealistic render + detected prongs & stones
    API-->>Frontend: Display photorealistic renders in Studio Media Gallery
    Designer->>Frontend: Approve Design & lock Bill of Materials (BOM)
    Frontend->>API: Generate Production Order with locked metal weights
    API->>Solver: Run CP-SAT multi-resource schedule optimizer
    Solver-->>API: Return optimal job timeline & karigar workstation assignments
    API->>Frontend: Dispatch live schedules to Shop Floor Terminal
    Karigar->>Frontend: Start job timer, log casting metal, complete QC checks
    Frontend->>API: Record actual gold weight, scrap, and finish order
```

---

## 📁 Project Structure

```
JewelMind/
├── backend/                    # FastAPI REST API & Core Business Services
│   ├── app/
│   │   ├── api/                # API route controllers (v1 endpoints)
│   │   │   └── v1/             # Auth, Designs, Production, Execution, Health
│   │   ├── core/               # Configuration, security, JWT helpers
│   │   ├── models/             # SQLAlchemy ORM models (Design, Order, Worker, Machine)
│   │   ├── schemas/            # Pydantic validation schemas
│   │   └── services/           # Services (Auth, Design, Production, OR-Tools Scheduler)
│   ├── tests/                  # Pytest test suite (495+ tests)
│   └── requirements.txt        # Python backend dependencies
├── ai/                         # Dedicated AI GPU Inference Worker
│   ├── rendering/              # Stable Diffusion + ControlNet + LoRA rendering
│   ├── vision/                 # YOLO11 component detection & stone classification
│   ├── optimization/           # Google OR-Tools CP-SAT workshop optimization
│   └── workers/                # Local GPU worker daemon (local_worker.py)
├── frontend/                   # React 19 + TypeScript + Vite Web Application
│   ├── public/
│   │   └── assets/             # Brand SVGs, icons, and web-optimized photography
│   ├── src/
│   │   ├── components/         # Canvas, Navigation, Production, Studio, UI primitives
│   │   ├── context/            # AuthContext and global application state
│   │   ├── hooks/              # useAuth, useDebounce, custom hooks
│   │   ├── pages/              # Landing, Dashboard, Canva Workspace, Studio, Production
│   │   ├── services/           # Type-safe API client, auth, design, and execution services
│   │   └── types/              # TypeScript contracts and domain models
│   ├── package.json            # Node dependencies and build scripts
│   └── vite.config.ts          # Vite build config with reverse proxies
├── launchers/                  # 1-Click execution scripts for Windows
│   ├── run_all.bat             # Concurrently launch Backend, AI Worker, and Frontend
│   ├── run_backend.bat         # Launch FastAPI backend
│   ├── run_ai.bat              # Launch AI GPU worker
│   └── run_frontend.bat        # Launch Vite dev server
├── screenshots/                # Showcase imagery for documentation
└── README.md                   # Project documentation
```

---

## 💡 Key Modules Explained

### 1. Canva Workspace (Drawing Desk)
- Features freehand drawing, straight line guides, eraser, radial symmetry dials (2x, 4x, 8x), and undo/redo stacks.
- Supports **Doodle-to-Render**, **Text-to-Render**, and **Image-to-Render** workflows with real-time prompt builders for precious metal alloys, prong settings, and gemstone cuts.

### 2. Gemological Vision Engine
- Leverages custom YOLO segmentation weights trained on jewellery datasets.
- Automatically isolates center gems, pavé accent stones, prongs, and shanks, calculating bounding dimensions and validating structural casting integrity.

### 3. Production Intelligence & CP-SAT Optimizer
- Solves a Job-Shop Scheduling Problem (JSSP) using Google OR-Tools CP-SAT.
- Balances workstation capacities across 4 major manufacturing stages: **Wax 3D Printing / Casting**, **Stone Setting**, **Polishing & Finishing**, and **Quality Control**.
- Optimizes for minimal makespan while preventing karigar burnout and machine conflicts.

### 4. Live Bullion Valuation & Scrap Tracking
- Dynamic BOM calculation accounting for density conversion factors (e.g., silver wax model weight to 18K gold equivalent).
- Integrates daily gold, platinum, and silver rates with karat purity adjustments (999, 916, 750) and records alloy additions and scrap recovery percentages.

---

## 🧪 Automated Testing Suite

JewelMind enforces continuous quality assurance across all layers:

### 1. Backend Pytest Suite
```powershell
.\backend\.venv\Scripts\pytest backend/tests
```
> **Status:** 495 passed tests covering JWT authentication, design persistence, production state machines, and schedule constraints.

### 2. Frontend Vitest Suite
```powershell
cd frontend
npm test -- --run
```
> **Status:** 12 test suites (132 tests) passed cleanly with 100% coverage over navigation, canvas tools, scheduling, and valuation arithmetic.

### 3. Production Build Validation
```powershell
cd frontend
npm run build
```
> **Status:** Compiles clean TypeScript with on-demand code splitting and sub-second Vite production bundling.

---

## 🚀 Future Improvements

- [ ] **3D WebGL / Three.js Model Viewer**: Direct GLTF / OBJ interactive 3D model rotation and stone facet rendering in the browser.
- [ ] **RFID / Barcode Scanner Integration**: Physical workshop batch tracking via Bluetooth barcode scanners at each workbench.
- [ ] **Automated Customer Quotation PDF**: One-click export of luxury branded spec sheets with photorealistic renders, BOM breakdowns, and hallmark certification certificates.
- [ ] **Hallmarking & Laser Inscription Ledger**: Serialized micro-inscriptions tracking diamond cert numbers (GIA, IGI) directly through production.
- [ ] **Multi-Tenant Factory Management**: Support for multi-branch jewellery manufacturers with distributed workshop dispatching.

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

Distributed under the **MIT License**. See `LICENSE` for more information.

---

## 👨‍💻 Author & Contact

**Mohit Jaiswal**  
*Undergraduate Computer Science Student*

- **GitHub**: [@MohitJaiswal2507](https://github.com/MohitJaiswal2507)
- **Email**: [mohitjasiwal2507@gmail.com](mailto:mohitjasiwal2507@gmail.com)

---

## 🙏 Acknowledgements

- [Ultralytics YOLO](https://github.com/ultralytics/ultralytics)
- [Hugging Face Diffusers & ControlNet](https://github.com/huggingface/diffusers)
- [Google OR-Tools](https://developers.google.com/optimization)
- [Google Gemini API](https://ai.google.dev/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [React](https://react.dev/) & [Tailwind CSS](https://tailwindcss.com/)
- [Lucide Icons](https://lucide.dev/)