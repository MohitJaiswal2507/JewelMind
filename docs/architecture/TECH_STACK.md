# Technology Stack & Decision Rationale

This document details the selected technologies for JewelMind and the specific rationale behind each choice.

---

## 1. Web Frontend

### React 19 + TypeScript
- **Rationale:** React provides a mature, component-driven UI paradigm essential for building complex dashboards, interactive side-by-side render comparators, and scheduling views. TypeScript adds compile-time type safety across complex data schemas (AI job statuses, component bounding boxes, schedule timelines).

### Vite
- **Rationale:** Instant Hot Module Replacement (HMR), extremely fast build times, and clean ES module resolution compared to legacy bundlers.

### Tailwind CSS
- **Rationale:** Utility-first styling enabling rapid creation of modern, responsive, and aesthetically polished interfaces with consistent design tokens (colors, typography, spacing).

---

## 2. Web Backend

### FastAPI (Python)
- **Rationale:**
  - Python-native framework allowing seamless interop with data science and AI libraries.
  - Asynchronous request handling via `asyncio` and `uvicorn`.
  - Automatic OpenAPI / Swagger interactive documentation generation.
  - Strict data validation and serialization through Pydantic models.

### PostgreSQL & Supabase
- **Rationale:**
  - Robust relational schema constraints and ACID compliance for business-critical entities (designs, components, job tracking, orders, schedules).
  - Supabase provides a production-grade managed PostgreSQL instance and S3-compatible asset storage on a generous free tier aligned with the ₹0 budget constraint.

---

## 3. Computer Vision & Generative AI

### OpenCV & PIL
- **Rationale:** High-performance preprocessing of freehand sketches (edge detection, background cleanup, line normalization, thresholding, color space transforms).

### YOLO (Ultralytics)
- **Rationale:** State-of-the-art real-time object detection architecture. Efficient to fine-tune on custom annotated jewellery datasets (stones, hooks, clasps, beads, connectors) and runs with high frames/sec on the RTX 4060 laptop GPU.

### PyTorch & Hugging Face Diffusers (ControlNet)
- **Rationale:**
  - Standard deep learning ecosystem with first-class CUDA support.
  - ControlNet provides structural conditioning (line art / canny / depth) ensuring the generative diffusion process respects the geometry of the designer's original sketch.

---

## 4. Machine Learning & Predictive Analytics

### XGBoost & scikit-learn
- **Rationale:** Gradient boosted decision trees excel on structured tabular data (geometric metrics, component counts, metal karat, dimensions). Superior performance over neural networks on small-to-medium tabular datasets with fast training and low inference latency.

### Pandas & NumPy
- **Rationale:** Fundamental data structures and vector mathematical routines for feature matrix generation and synthetic data synthesis.

---

## 5. Operations Research & Optimization

### Google OR-Tools (CP-SAT Solver)
- **Rationale:** Industry-leading constraint satisfaction and optimization engine. Ideal for complex workshop job-shop scheduling (allocating artisans with variable skills and machines to production batches with strict deadlines and priority weights).

---

## 6. Hardware & Deployment

### NVIDIA GeForce RTX 4060 (Laptop GPU)
- **Rationale:** 8GB VRAM with Tensor Cores provides sufficient local compute capacity for YOLO training/inference, mixed-precision (FP16) diffusion rendering with ControlNet, and XGBoost training without requiring cloud GPU rentals.

### Cloudflare Pages
- **Rationale:** High-performance global CDN edge hosting with unlimited bandwidth on the free tier for the single-page React frontend.
