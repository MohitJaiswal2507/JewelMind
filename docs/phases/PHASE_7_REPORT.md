# JewelMind — Phase 7 Engineering & Architecture Report
# Generative Diffusion & ControlNet Jewellery Sketch Rendering

> **TRAINING STATUS**: **MANUAL TRAINING REQUIRED — NOT EXECUTED BY ANTIGRAVITY**  
> In accordance with the non-negotiable Phase 7 contract rules, Antigravity has not executed, scheduled, or resumed any LoRA or ControlNet model training. All training scripts, dataset tools, configurations, and manual training guides have been prepared for manual execution by the operator on the local RTX 4060 GPU.
>
> **GPU SMOKE-TEST STATUS**: **EMPIRICALLY VERIFIED ON RTX 4060**  
> The real GPU diffusion forward inference smoke test has been executed on the local NVIDIA GeForce RTX 4060 Laptop GPU. Empirical latency, peak VRAM, and output artifacts are documented in Section 17.1.

---

## 1. Executive Summary

JewelMind Phase 7 introduces the Generative AI Rendering layer to the platform, bridging 2D jewellery design sketches (or canvas drawings) and downstream physical manufacturability validation. 

The core requirement of Phase 7 is:
> *"Transform a jewellery blueprint sketch into a photorealistic fine jewellery product photograph while preserving the underlying sketch geometry (silhouettes, stone placement, prong settings, symmetry, and ring shank dimensions) on a local NVIDIA GeForce RTX 4060 Laptop GPU (8 GB VRAM)."*

Phase 7 achieves this via a modular, local-first architecture:
1. **Input Normalization & Conditioning**: Preprocesses sketches with letterbox aspect-ratio preservation and extracts structural contours using **LineArt** (primary) and **Canny** (secondary) processors.
2. **Generative Conditioning Pipeline**: Couples **Stable Diffusion 1.5** with **ControlNet v1.1** in FP16 precision.
3. **Hardware Safety**: Employs memory slicing (attention slicing and VAE slicing) and strict in-process serialization locks ensuring safe execution within the ~6.1 GB free VRAM ceiling on Windows.
4. **Backend & Frontend**: Exposes an authenticated FastAPI endpoint (`POST /api/v1/ai/render`) returning structured `RenderResult` telemetry, integrated with the Design Studio `StudioMediaDetails` and `AiRenderModal`.
5. **Prompt Architecture & Token Bounds**: Strictly bounds positive prompt length (33–42 tokens) within SD 1.5's 77-token CLIP limit, eliminating token truncation and preserving metal and gemstone descriptions.
6. **Manual Training Subsystem**: Provides a complete training preparation suite (`ai/training/` and `configs/jewellery_lora.yaml`) along with a comprehensive operator guide (`PHASE_7_MANUAL_TRAINING_GUIDE.md`) for human-controlled LoRA fine-tuning.

---

## 2. Git Branch & Tracking Status

* **Active Branch**: `phase-7-diffusion-controlnet` (branched from `main`).
* **Merge Status**: **READY FOR USER REVIEW — UNMERGED**.
* **Remote Status**: Not pushed to origin.
* **Git Safety**:
  - All large model binaries (`*.safetensors`, `*.bin`, `*.pt`, `*.ckpt`) are strictly excluded via `.gitignore`.
  - `models/diffusion/`, `models/cache/`, `checkpoints/`, `runs/`, `outputs/`, and `.env` are verified untracked.
  - The generated smoke-test image `outputs/rendering/render_bd34d3f2a64c_42.png` is preserved on disk and ignored by Git.

---

## 3. Existing Architecture Inspected

Prior to implementation, the existing JewelMind monorepo was thoroughly analyzed:
* **Backend (`backend/app/`)**: FastAPI master router at `backend/app/api/v1/router.py`, JWT auth dependencies in `app.api.deps`, SQLAlchemy models (`User`, `Design`, `DesignMedia`), and standard Pydantic schemas.
* **AI Subsystems (`ai/`)**: Phase 6 YOLO component detection (`ai/vision/`), existing dataset layouts (`ai/vision/datasets/sample/`), and Ultralytics inference contracts.
* **Frontend (`frontend/src/`)**: Vite + React 18 + TypeScript + Tailwind CSS design system, Design Studio media drawer (`components/studio/StudioMediaDetails.tsx`), canvas sketch storage, and API client wrappers.
* **No Unnecessary Rewrites**: No changes were made to authentication, database schemas, canvas tools, or Phase 6 YOLO detection.

---

## 4. Model Candidates Researched

A detailed investigation was documented in `docs/phases/PHASE_7_MODEL_RESEARCH.md`:

| Architecture | Parameters | Native Res | 8GB VRAM Feasibility | Latency (RTX 4060) | Geometric Precision | Recommendation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Stable Diffusion 1.5 + ControlNet v1.1** | ~1.3B (UNet + CN) | 512×512 | **Proven: 3.33 GiB peak VRAM** | **Measured: 16.33s** (20 steps) | **High** (LineArt/Canny contour lock) | **SELECTED PRIMARY** |
| **SDXL 1.0 + ControlNet SDXL** | ~3.5B | 1024×1024 | **High OOM Risk** (>8.5 GB) | >35s (estimated with offload) | Moderate (soft prongs) | Rejected (VRAM ceiling) |
| **SDXL Lightning / Turbo** | ~3.5B | 512 / 1024 | **Poor** (~7.5 GB static) | ~12s – 18s (estimated) | Degraded contour lock | Rejected (distillation drift) |
| **FLUX.1-schnell / dev** | ~12B | 1024×1024 | **Unviable** (>16 GB) | >60s (estimated 4-bit offload) | Coarse edge adapter | Rejected (incompatible 8GB) |

*Note: Latency and VRAM for SD 1.5 are empirically measured. Figures for other candidates represent architectural estimates from hardware research.*

---

## 5. Selected Model & Selection Rationale

* **Selected Engine**: **Stable Diffusion 1.5 (`runwayml/stable-diffusion-v1-5`)**
* **Selected Adapters**: **ControlNet v1.1 LineArt (`lllyasviel/control_v11p_sd15_lineart`)** with **Canny (`lllyasviel/control_v11p_sd15_canny`)** fallback.
* **Rationale**:
  1. **Empirically Proven 8 GB Hardware Compatibility**: Real execution consumed **3,410.4 MiB (3.33 GiB)** peak VRAM, leaving **4,777.1 MiB (58.3%)** of free VRAM headroom on the 8 GB RTX 4060 Laptop GPU.
  2. **Geometry Preservation (Design Intent & Behavior)**: ControlNet v1.1 LineArt is structurally designed to constrain generative diffusion to the sketch contours, capturing vector strokes, prongs, and stone facets without double-edge blurring. *(Note: While geometry alignment is enforced via zero-convolution conditioning, visual verification of intricate filigree remains an essential operator step.)*
  3. **Inference Latency**: Real measured runtime was **16.33 seconds** for 20 denoising steps.
  4. **Licensing**: CreativeML Open RAIL-M and Apache 2.0; commercial use is subject to the applicable license terms.
  5. **LoRA Ecosystem**: Native compatibility with specialized jewellery, metal finish, and studio lighting LoRA adaptations.

---

## 6. ControlNet Selection

1. **Primary: LineArt (`control_v11p_sd15_lineart`)**:
   - Designed for CAD sketches, digital tablet drawings, and pencil blueprints.
   - Bilateral filtering removes paper grain; adaptive thresholding preserves fine gemstone bezel edges.
2. **Secondary: Canny (`control_v11p_sd15_canny`)**:
   - Standard OpenCV dual-threshold gradient magnitude edge detector (100 / 200).
   - Fast, zero-model preprocessing, ideal for high-contrast raster blueprints.

---

## 7. Licensing & Commercial Compliance

| Component | Checkpoint / Repo | License | Commercial Permissibility |
| :--- | :--- | :--- | :--- |
| **Base Pipeline** | `runwayml/stable-diffusion-v1-5` | CreativeML Open RAIL-M | Permitted for commercial CAD rendering |
| **ControlNet Adapters** | `lllyasviel/control_v11p_sd15_*` | Apache 2.0 | Permitted without restrictions |
| **Diffusers / PEFT** | Hugging Face open-source | Apache 2.0 | Permitted |
| **OpenCV / Pillow** | Standard vision libraries | Apache 2.0 / HPND | Permitted |

---

## 8. Environment & Hardware Verification

* **Conda Environment**: `tgpu` (`C:\Users\usern\miniconda3\envs\tgpu`).
* **Python Version**: `3.10.19`
* **GPU**: `NVIDIA GeForce RTX 4060 Laptop GPU` (AD107)
* **Total VRAM**: `8,187.5 MiB` (`8.00 GiB`)
* **PyTorch Version**: `2.9.0+cu130` with `CUDA 13.0` enabled.
* **Backend Host Environment**: Python 3.13.5 (`backend/.venv/`).

---

## 9. Verified Dependencies

The following packages are installed and verified in `tgpu`:
* `diffusers`: `0.36.0`
* `transformers`: `4.57.1`
* `accelerate`: `1.14.0`
* `safetensors`: `0.6.2`
* `Pillow`: `11.3.0`
* `opencv-python`: `4.12.0`
* `torchvision`: `0.24.0+cu130`
* `peft`: `0.14.0`
* `huggingface_hub`: `0.29.0`

---

## 10. Sketch Preprocessing Module

Located under `ai/rendering/preprocessing/`:
* **`base.py` (`ConditioningProcessor`)**:
  - Handles EXIF orientation transposition.
  - Transparent RGBA compositing over solid pure white canvas (`[255, 255, 255]`).
  - High-quality Lanczos / Area letterbox aspect ratio scaling.
  - Calculates `ConditioningMetadata` (original dimensions, padding offsets, edge density).
* **`lineart.py` (`LineArtProcessor`)**:
  - Bilateral filter noise reduction.
  - Background polarity inversion (dark sketch strokes become white conditioning lines).
  - Percentile contrast stretching and noise floor truncation (<30 pixel threshold).
* **`canny.py` (`CannyProcessor`)**:
  - Gaussian blur followed by OpenCV Canny detector with dual thresholds.

---

## 11. Generative Rendering Pipeline

Located under `ai/rendering/pipeline.py`:
* **Execution Flow**:
  1. Validates input sketch dimensions ($\ge 16 \times 16$).
  2. Executes conditioning processor to generate letterboxed conditioning PIL image.
  3. Formulates curated positive prompts and negative prompts from `prompts.py`.
  4. Generates deterministic noise generator using explicit user seed (or random integer).
  5. Acquires `DiffusionModelManager.execution_lock` (enforcing strictly 1 job on GPU).
  6. Executes denoising pass with `torch.inference_mode()` in FP16.
  7. Catches `torch.cuda.OutOfMemoryError` gracefully, flushing VRAM before raising `RenderingOutOfMemoryError`.
  8. Saves rendered output to git-ignored `outputs/rendering/render_<uuid>_<seed>.png`.
  9. Returns PIL image and structured `RenderResult` schema.

---

## 12. Model Manager & Memory Strategy

Located under `ai/rendering/model_manager.py`:
* **Singleton Lifecycle**: Prevents re-instantiating UNet / VAE on every API request.
* **ControlNet Hot-Swapping**: Allows switching between LineArt and Canny adapters in memory without reloading the entire base UNet.
* **VRAM Protections**:
  - Attention slicing (`enable_attention_slicing("auto")`).
  - VAE latent decoding slicing (`enable_vae_slicing()`).
  - Strict serialization lock (`threading.Lock`).
  - Post-inference memory garbage collection (`gc.collect()` and `torch.cuda.empty_cache()`).
  - Telemetry reporting (`get_vram_info()` providing allocated, reserved, and peak VRAM).

---

## 13. Jewellery Prompt Architecture & CLIP Token Fix

Located under `ai/rendering/prompts.py`:

### Diagnosis of Token Truncation Warning
During early testing, Diffusers emitted:
`Token indices sequence length is longer than the specified maximum sequence length for this model (89 > 77). The following part of your input was truncated...`
Analysis of the prompt builder showed that verbose style modifiers (~42 tokens), detailed metal descriptions (~18 tokens), and gemstone descriptions (~25 tokens) totaled 89 tokens. Because SD 1.5's CLIP text encoder strictly processes sequences up to 77 tokens, the trailing gemstone descriptors were truncated.

### Resolution
The prompt templates were refactored into focused, high-signal descriptors:
* **Style Anchor**: `"photorealistic fine jewellery product photograph, studio lighting, sharp focus, clean background"` (~13 tokens).
* **Metal Descriptors**: E.g. `"polished 18k yellow gold, warm golden luster"` (~8 tokens).
* **Gemstone Descriptors**: E.g. `"round brilliant diamond, refractive fire and dispersion"` (~8 tokens).
* **Token Verification**: Evaluated with `CLIPTokenizer.from_pretrained('runwayml/stable-diffusion-v1-5')`:
  - Default generated prompts now consume **33 to 42 tokens** (inclusive of start/end tokens).
  - This leaves **~35 tokens of headroom** for user design notes (e.g. `"solitaire engagement ring with four-prong setting"`) without triggering truncation warnings or losing material definitions.

---

## 14. Backend API & Contract Stability

Located under `backend/app/api/v1/ai_rendering.py`:
* **Endpoint**: `POST /api/v1/ai/render`
  - Multipart form upload with authenticated user dependency (`get_current_active_user`).
  - Validates MIME types (`image/png`, `image/jpeg`, `image/webp`).
  - Enforces resolution divisible by 8 for latent diffusion VAE.
  - Safe error handling: maps CUDA OOM to HTTP 507, concurrent busy state to HTTP 503, invalid inputs to HTTP 422.
* **Image Delivery**: `GET /api/v1/ai/render/outputs/{filename}`
  - Delivers rendered output with directory traversal sanitization.
  - Strictly prevents leaking local filesystem paths (`C:\...`).

---

## 15. RenderResult Schema

Located under `ai/rendering/schemas.py`:
```json
{
  "model_version": "runwayml/stable-diffusion-v1-5",
  "controlnet_version": "lllyasviel/control_v11p_sd15_lineart",
  "image_width": 512,
  "image_height": 512,
  "seed": 42,
  "control_type": "lineart",
  "control_strength": 0.8,
  "steps": 20,
  "guidance_scale": 7.5,
  "inference_time_ms": 16331.5,
  "device_used": "cuda:0",
  "output_url": "/api/v1/ai/render/outputs/render_bd34d3f2a64c_42.png",
  "created_at": "2026-09-02T17:55:00Z",
  "conditioning_metadata": {
    "original_size": [640, 480],
    "processed_size": [512, 512],
    "control_type": "lineart",
    "padding": [0, 0, 85, 85],
    "edge_density": 0.0842
  }
}
```

---

## 16. Frontend Integration

* **Modal Component**: `frontend/src/components/studio/AiRenderModal.tsx`
  - Integrated directly into the Design Studio media drawer (`StudioMediaDetails.tsx`).
  - Material selector: 18K Yellow Gold, 18K White Gold, 18K Rose Gold, 950 Platinum, Sterling Silver.
  - Gemstone selector: Diamond, Blue Sapphire, Emerald, Ruby, Amethyst.
  - ControlNet adapter toggle: LineArt vs. Canny Edge.
  - Advanced options: Denoising steps slider (10–30), geometry adherence scale (0.4–1.0), seed input, custom prompt notes.
  - Side-by-side comparison view: compares original sketch side-by-side with generated photorealistic render.
  - Real loading state: displays `"Rendering jewellery..."` with active local GPU indicator.
  - Safe error alerts: maps HTTP 507 (OOM), 503 (busy), and 422 (invalid sketch) to user-friendly messages without exposing stack traces.

---

## 17. Automated Tests & Validation

All tests passed with 100% success rate:

```
============================= test session starts =============================
platform win32 -- Python 3.10.19 (tgpu)
collected 7 items

tests/ai/test_rendering.py::test_rendering_config_defaults PASSED        [ 14%]
tests/ai/test_rendering.py::test_render_request_validation PASSED        [ 28%]
tests/ai/test_rendering.py::test_render_result_schema_sanitization PASSED [ 42%]
tests/ai/test_rendering.py::test_preprocessing_transparency_handling PASSED [ 57%]
tests/ai/test_rendering.py::test_preprocessing_letterbox_aspect_ratio PASSED [ 71%]
tests/ai/test_rendering.py::test_canny_processor_edge_detection PASSED   [ 85%]
tests/ai/test_rendering.py::test_prompt_builder PASSED                   [100%]
============================== 7 passed in 1.81s ==============================

============================= test session starts =============================
platform win32 -- Python 3.13.5 (backend/.venv)
collected 5 items

backend/tests/test_ai_rendering.py::test_render_unauthorized PASSED     [ 20%]
backend/tests/test_ai_rendering.py::test_render_invalid_mime_type PASSED [ 40%]
backend/tests/test_ai_rendering.py::test_render_empty_file PASSED        [ 60%]
backend/tests/test_ai_rendering.py::test_render_invalid_resolution PASSED [ 80%]
backend/tests/test_ai_rendering.py::test_render_success_mock PASSED      [100%]
============================== 5 passed in 0.10s ==============================
```

---

## 17.1 Real GPU Smoke-Test Telemetry (EMPIRICALLY VERIFIED)

The real GPU diffusion smoke test was executed directly on the local RTX 4060 GPU using `scripts/smoke_test_rendering.py`. The actual measured telemetry is recorded below:

| Telemetry Metric | Measured Value | Operational Assessment |
| :--- | :--- | :--- |
| **Device Used** | `cuda:0` (NVIDIA GeForce RTX 4060 Laptop GPU) | Real local hardware acceleration confirmed |
| **Total Hardware VRAM** | `8,187.5 MiB` (8.00 GiB) | Native hardware capacity |
| **Base Model Loaded** | `runwayml/stable-diffusion-v1-5` (FP16) | Verified loaded in VRAM |
| **ControlNet Loaded** | `lllyasviel/control_v11p_sd15_lineart` (FP16) | Verified loaded in VRAM |
| **Input Test Sketch** | `ai/vision/datasets/sample/train/images/ring_train_000.jpg` | Real dataset sketch processed |
| **Output Resolution** | `512 × 512` (Batch Size = 1) | Target resolution achieved |
| **Sampling Steps & Seed** | `20 steps`, `Seed: 42` | Deterministic generation |
| **Inference Latency** | **16,331.5 ms (16.33 seconds)** | Complete 20-step denoising pass |
| **Total Pipeline Runtime** | **16.37 seconds** | Includes sketch preprocessing and disk I/O |
| **Peak Active VRAM** | **3,410.4 MiB (3.33 GiB)** | Well below 6.1 GB Windows usable window |
| **VRAM Headroom** | **4,777.1 MiB free (58.3%)** | 3.33 GiB peak VRAM was observed in the smoke-test configuration, leaving substantial VRAM headroom for the tested 512x512 workload. |
| **Output File Saved** | `outputs/rendering/render_bd34d3f2a64c_42.png` | Output successfully written to disk |
| **File Existence on Disk** | **TRUE** | Verified on filesystem |

---

## 18. Manual Training Subsystem (Operator Ready)

In accordance with Section 27 and the user instructions:
* **Training Script**: [`ai/training/train_lora.py`](file:///c:/Users/usern/Desktop/JewelMind/ai/training/train_lora.py)
  - Features PEFT LoRA, FP16 mixed precision, gradient checkpointing, and automatic checkpoint resumption from `checkpoint-last`.
  - **Status: NOT EXECUTED BY ANTIGRAVITY**.
* **Dataset Utilities**:
  - Preparation: [`ai/training/prepare_dataset.py`](file:///c:/Users/usern/Desktop/JewelMind/ai/training/prepare_dataset.py)
  - Validation: [`ai/training/validate_dataset.py`](file:///c:/Users/usern/Desktop/JewelMind/ai/training/validate_dataset.py)
* **Inference & Evaluation**:
  - [`ai/training/evaluate_lora.py`](file:///c:/Users/usern/Desktop/JewelMind/ai/training/evaluate_lora.py)
  - [`ai/training/inference.py`](file:///c:/Users/usern/Desktop/JewelMind/ai/training/inference.py)
* **Configuration**: [`configs/jewellery_lora.yaml`](file:///c:/Users/usern/Desktop/JewelMind/configs/jewellery_lora.yaml)
* **Operator Guide**: [`docs/phases/PHASE_7_MANUAL_TRAINING_GUIDE.md`](file:///c:/Users/usern/Desktop/JewelMind/docs/phases/PHASE_7_MANUAL_TRAINING_GUIDE.md)

---

## 19. Phase 6 Integration Status

* **Status**: Decoupled and future-ready.
* **Compatibility**: Phase 6 YOLO component segmentations (`ring_train_000.jpg`, etc.) provide reference geometry. The direct sketch $\to$ ControlNet $\to$ Diffusion pipeline operates standalone, with clean abstraction allowing Phase 6 component masks to be passed as localized inpainting or condition guidance in future phases.

---

## 20. Known Limitations & Architectural Bounds

1. **Native Resolution**: Model operates at $512 \times 512$ to maintain the 8 GB VRAM budget on the laptop GPU. Upscaling to $1024 \times 1024$ or $2048 \times 2048$ should use a dedicated ESRGAN / Real-ESRGAN super-resolution pass.
2. **Geometry Preservation Reality**: While ControlNet conditioning enforces strong structural boundary adherence (preventing gross hallucinations like missing ring shanks), it does not guarantee mathematical invariance. Complex micro-prongs or delicate pavé settings may show slight stylistic interpretation and require human review.
3. **Sequential GPU Serialization**: Only one rendering job can occupy the GPU at any time. Multi-user concurrent rendering requires external worker queues (Celery/Redis) in production.

---

## 21. Acceptance Criteria Checklist

### Research & Architecture
- [x] Multiple diffusion candidates researched (`docs/phases/PHASE_7_MODEL_RESEARCH.md`).
- [x] ControlNet LineArt vs Canny researched and justified.
- [x] Licensing verified (CreativeML Open RAIL-M & Apache 2.0).
- [x] RTX 4060 8GB feasibility assessed and empirically confirmed.
- [x] Model choice justified based on geometry preservation and memory stability.

### Environment & Safety
- [x] Existing `tgpu` Miniconda environment verified and reused.
- [x] PyTorch 2.9.0+cu130 with CUDA verified on RTX 4060 Laptop GPU.
- [x] Dependencies documented and verified.
- [x] No duplicate virtual environment created.

### Rendering Subsystem
- [x] Stable Diffusion 1.5 + ControlNet v1.1 pipeline implemented.
- [x] Preprocessing module with LineArt and Canny processors created.
- [x] Aspect-ratio letterbox padding and transparency compositing implemented.
- [x] Prompt and negative prompt builder implemented with CLIP 77-token ceiling compliance.
- [x] Single-job serialization lock implemented.
- [x] Attention slicing and VAE slicing enabled.
- [x] Real GPU inference execution: **EMPIRICALLY VERIFIED ON RTX 4060** (16.33s latency, 3.33 GiB peak VRAM).

### Backend API
- [x] `POST /api/v1/ai/render` implemented with validation.
- [x] `GET /api/v1/ai/render/outputs/{filename}` implemented with path sanitization.
- [x] Stable `RenderResult` schema validated without local filesystem leakage.
- [x] Safe HTTP error handling (507 OOM, 503 busy, 422 validation).

### Frontend
- [x] Design Studio `StudioMediaDetails` integration implemented.
- [x] `AiRenderModal` with material, gemstone, adapter, steps, and seed controls.
- [x] Side-by-side blueprint vs render comparison view implemented.
- [x] Real loading indicator without fake percentage progress.

### Manual Training Boundary
- [x] **NO training job was launched, executed, or resumed by Antigravity.**
- [x] Training configuration created (`configs/jewellery_lora.yaml`).
- [x] Dataset preparation and validation scripts created (`ai/training/`).
- [x] Resumable PEFT LoRA training script created (`ai/training/train_lora.py`).
- [x] Comprehensive manual guide created (`docs/phases/PHASE_7_MANUAL_TRAINING_GUIDE.md`).
- [x] Training status explicitly designated as **MANUAL TRAINING REQUIRED — NOT EXECUTED BY ANTIGRAVITY**.

### Git Safety
- [x] No model binaries (`*.safetensors`, `*.bin`, `*.pt`) tracked.
- [x] No generated images or outputs tracked.
- [x] `.gitignore` updated and verified.
- [x] Branch unmerged, ready for operator review.

---

## 22. Merge Readiness

**STATUS: READY FOR USER REVIEW**  
The generative diffusion rendering subsystem, API endpoints, Design Studio frontend modal, and manual LoRA training infrastructure are completely implemented, verified with passing unit tests, and empirically validated via local GPU smoke test. Antigravity has stopped at the training boundary in accordance with user instructions.
