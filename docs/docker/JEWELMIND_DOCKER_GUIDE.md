# JewelMind Dockerization & Environment Reproducibility Guide

Welcome to the official containerization guide for **JewelMind** — the full-stack AI jewellery design and rendering platform.

This guide provides end-to-end instructions for deploying JewelMind locally or in production using Docker and Docker Compose with NVIDIA GPU acceleration.

---

## 1. System Prerequisites

Before running JewelMind in containers, ensure your host environment meets the following specifications:

- **Operating System:** Linux (Ubuntu 22.04+ recommended) or Windows 11 with WSL 2.
- **Docker Engine:** Docker 24.0+ / Docker Desktop 4.25+.
- **Docker Compose:** Compose v2 (`docker compose version` >= 2.20.0).
- **GPU Hardware:** NVIDIA GPU with at least 8 GB VRAM (e.g., NVIDIA GeForce RTX 4060, RTX 3080, A4000/A5000).
- **NVIDIA Driver:** Driver version >= 535.xx.
- **NVIDIA Container Toolkit:** `nvidia-container-toolkit` installed on host/WSL2.

---

## 2. Docker & NVIDIA Container Toolkit Setup

### On Linux (Ubuntu/Debian)
```bash
# 1. Install Docker Engine
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 2. Configure NVIDIA Container Toolkit repository
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
  && curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

# 3. Install nvidia-container-toolkit and restart Docker
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

### On Windows (WSL 2)
1. Install latest NVIDIA Game Ready / Studio Driver on Windows host (WSL2 uses host driver automatically).
2. Install Docker Desktop for Windows and check **"Use the WSL 2 based engine"**.
3. Under Settings -> Resources -> WSL Integration, enable integration with your default WSL distro.

---

## 3. Architecture Overview

JewelMind utilizes a clean 3-tier container architecture:

```
                            JEWELMIND
                               |
             +-----------------+-----------------+
             |                                   |
        FRONTEND                             BACKEND API
     (React 19 + Nginx)                   (FastAPI REST)
        Port: 5173                          Port: 8000
                                                 |
                                            HTTP Proxy
                                                 |
                                            AI INFERENCE
                                         (Dedicated Worker)
                                            Port: 8001
                                                 |
                                       +---------+---------+
                                       |                   |
                                    YOLO11-seg         ControlNet
                                    (Detection)        + LoRA SD1.5
                                                           |
                                                      NVIDIA GPU
                                                       (RTX 4060)
```

- **Frontend Container (`jewelmind-frontend`):** Multi-stage build (Node 20 Alpine builder -> Nginx 1.27 Alpine runtime). Serves static SPA bundle with gzip, security headers, and caching.
- **Backend Container (`jewelmind-backend`):** FastAPI application with Supabase integration and production OR-Tools optimizer. Communicates with AI inference worker over internal Docker network.
- **AI Worker Container (`jewelmind-ai`):** Dedicated PyTorch CUDA 12.1 runtime worker. Loads trained ControlNet 1000-step renderer, Appearance LoRA, and YOLO11 segmenter with GPU acceleration.

---

## 4. Environment Configuration

Copy the example environment template and configure your project keys:

```bash
cp .env.example .env
```

Ensure the following variables are set in `.env`:

```ini
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
DATABASE_URL=postgresql://postgres:password@db.your-project.supabase.co:5432/postgres

# Ports
FRONTEND_PORT=5173
BACKEND_PORT=8000
AI_WORKER_PORT=8001

# AI Worker Internal Routing
AI_WORKER_URL=http://ai:8001
```

> **Security Note:** Never commit `.env` or paste live API keys into Dockerfiles.

---

## 5. Model Volume Strategy & External Assets

To keep Docker images lean (< 4GB) and portable, **multi-gigabyte model weights are never baked into container image layers**. Instead, they are mounted as read-only volumes at runtime.

### Required Model Directory Structure
Ensure the host repository retains the following directories:

```
JewelMind/
├── models/
│   └── diffusion/
│       └── models--runwayml--stable-diffusion-v1-5/
├── outputs/
│   ├── rendering_v2_controlnet/
│   │   └── controlnet_rendering_v2_final/
│   │       ├── diffusion_pytorch_model.safetensors
│   │       └── config.json
│   └── appearance_lora/
│       └── jewellery_lora_final/
│           └── adapter_model.safetensors
└── runs/
    └── segment/
        └── runs/
            └── jewellery/
                └── yolo11m-seg-jewelmind-v2-continued/
                    └── weights/
                        └── best.pt
```

In `docker-compose.yml`, these are mounted directly into `/app`:
- `./models:/app/models:ro`
- `./outputs:/app/outputs:ro`
- `./runs:/app/runs:ro`

---

## 6. Docker Compose Commands

### Build Container Images
```bash
docker compose build
```

### Start Services in Detached Mode
```bash
docker compose up -d
```

### View Status & Health
```bash
docker compose ps
```

### View Live Logs
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f ai
docker compose logs -f backend
docker compose logs -f frontend
```

### Stop Services
```bash
docker compose down
```

### Stop and Remove Named Volumes
```bash
docker compose down -v
```

---

## 7. Development vs Production Usage

### Production Mode (Default)
Runs immutable containers with pre-built static assets and optimized multi-worker servers:
```bash
docker compose up -d
```

### Development Mode (with Live Reloading)
To enable live backend and AI code reload with bind mounts:
```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up
```

---

## 8. GPU Verification & Health Checks

### Test GPU Visibility in Container
```bash
docker compose exec ai nvidia-smi
```

### Test PyTorch CUDA Availability inside AI Container
```bash
docker compose exec ai python -c "import torch; print('CUDA Available:', torch.cuda.is_available()); print('Device:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A')"
```

### Service Health Check Endpoints
- **Frontend:** `GET http://localhost:5173/health` -> HTTP 200 `healthy`
- **Backend:** `GET http://localhost:8000/api/v1/health` -> HTTP 200 `{"status":"ok"}`
- **AI Worker:** `GET http://localhost:8001/health` -> HTTP 200 `{"status":"healthy","device":"cuda","gpu_available":true}`

---

## 9. Troubleshooting & FAQ

### Issue: "NVIDIA Container Toolkit not detected"
**Fix:** Ensure `nvidia-ctk runtime configure --runtime=docker` was run and Docker was restarted (`sudo systemctl restart docker`). On Windows WSL2, check that Docker Desktop has WSL integration enabled.

### Issue: "Model weights not found at runtime"
**Fix:** Verify that the `./models`, `./outputs`, and `./runs` folders exist in the project root before running `docker compose up`. Docker Compose mounts them as read-only volumes.

### Issue: "Port 5173 or 8000 already in use"
**Fix:** Override the port in `.env` (e.g., `FRONTEND_PORT=3000` or `BACKEND_PORT=8080`) or stop host processes using those ports.

---

## 10. What is Intentionally Excluded from Docker Images

The following items are excluded by `.dockerignore` to ensure rapid builds, security, and reproducible deployments:
1. `node_modules/` and local Python virtual environments (`.venv/`, `venv/`).
2. `.env` and all secret credentials.
3. Multi-GB model weights (`*.safetensors`, `*.pt`, `*.bin`).
4. Training datasets, raw images, and temporary caches (`.pytest_cache`, `__pycache__`).
5. Build caches (`dist/`, `.vite/`).
