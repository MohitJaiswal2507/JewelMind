# AI & Machine Learning Subsystem

This directory contains the AI, Computer Vision, Generative AI, Predictive ML, and Constraint Optimization modules for JewelMind.

---

## Directory Overview
```text
ai/
├── vision/         # Jewellery component detection (YOLO) & OpenCV preprocessing
├── rendering/      # Sketch-to-realistic rendering (Diffusion + ControlNet)
├── prediction/     # Tabular ML models (Material, Cost, Time, Wastage via XGBoost)
├── optimization/   # Production scheduling engine (Google OR-Tools CP-SAT)
├── workers/        # Asynchronous AI job processing workers (RTX 4060 & HF ZeroGPU)
├── common/         # Shared data schemas, payload validators, and helper utilities
├── tests/          # Unit tests for CV, ML pipelines, and optimization solvers
└── README.md       # Overview (this file)
```

---

## Architecture Rule
All AI modules are decoupled from the FastAPI web application. Computation is executed by dedicated workers communicating through standardized job schemas.
