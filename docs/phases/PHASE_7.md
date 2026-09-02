# JewelMind — PHASE 7
# Diffusion + ControlNet Jewellery Sketch Rendering
# Antigravity IDE Execution Instructions

## 0. PHASE CONTRACT

Implement **PHASE 7 — AI Jewellery Rendering with Diffusion + ControlNet**.

Phase 6 (YOLO11 jewellery component segmentation) is complete and merged into `main`.

Phase 7 adds the rendering layer:

    Jewellery Sketch
          ↓
    Sketch Preprocessing
          ↓
    ControlNet Conditioning
          ↓
    Diffusion Rendering
          ↓
    Photorealistic Jewellery Image
          ↓
    Future:
    YOLO → XGBoost → Manufacturability → OR-Tools

The goal is a real, reproducible, local-first AI rendering subsystem — not a fake demo.

---

# 1. NON-NEGOTIABLE RULES

### Do not break existing phases

Do not unnecessarily rewrite:
- authentication
- jewellery CRUD
- Supabase integration
- Design Studio / canvas
- Phase 6 YOLO implementation
- existing API contracts

Inspect and reuse existing architecture.

### Do not start expensive training automatically

You may run:
- dependency checks
- CUDA checks
- model compatibility checks
- preprocessing tests
- small inference smoke tests

Do NOT automatically start:
- LoRA training
- ControlNet training
- diffusion fine-tuning
- large benchmark sweeps

If training is needed, STOP and give the user exact step-by-step instructions. The user will manually start long GPU jobs.

### Local GPU first

Target:

    NVIDIA GeForce RTX 4060 Laptop GPU
    8 GB VRAM

Use the local GPU whenever practical.

Do not introduce a paid AI API.

Optional Hugging Face/ZeroGPU fallback may be documented, but it must not be mandatory.

### Reuse the existing AI environment

First inspect the existing environment.

Prefer the Phase 6 `tgpu` Miniconda environment if compatible.

Do NOT create duplicate environments.

If a new environment is genuinely necessary, use Miniconda + uv and explain why `tgpu` cannot be reused.

### Never commit model/data artifacts

Never commit:

    *.pt
    *.pth
    *.safetensors
    *.ckpt
    *.bin
    *.onnx

Also never commit:
- generated image datasets
- model caches
- generated outputs
- `.env`
- API tokens
- Hugging Face tokens

### No fake AI

Do not create hard-coded/fake generated images or fake progress.

If real diffusion inference cannot run, document the exact blocker honestly.

---

# 2. GIT SETUP

Create:

    git checkout main
    git pull
    git checkout -b phase-7-diffusion-controlnet

Verify:

    git status
    git branch --show-current

Do not merge the branch.

Do not push unless explicitly instructed.

---

# 3. INSPECT EXISTING JEWELMIND FIRST

Before implementation inspect:

    frontend/
    backend/
    ai/
    tests/
    docs/

Inspect Phase 6 specifically.

Find:
- AI service structure
- YOLO inference code
- Pydantic schemas
- FastAPI AI routes
- image upload handling
- Design Studio/canvas
- Supabase Storage integration
- `.env` handling
- test conventions

Do not duplicate existing infrastructure.

---

# 4. RESEARCH BEFORE CHOOSING A MODEL

Create:

    docs/phases/PHASE_7_MODEL_RESEARCH.md

Research realistic candidates for an RTX 4060 8GB.

At minimum investigate:

1. Stable Diffusion 1.5 + ControlNet
2. SDXL + ControlNet
3. SDXL Lightning/Turbo-style alternatives where compatible
4. Other open-weight options only if they provide a meaningful advantage

For every candidate document:

- model/checkpoint
- architecture
- ControlNet compatibility
- expected VRAM
- 8GB practicality
- inference speed
- image quality
- geometry/control fidelity
- LoRA compatibility
- ecosystem support
- license
- commercial-use implications
- download size
- offload/quantization options
- strengths
- weaknesses

Do not choose solely because an image looks good.

The key requirement is:

    preserve jewellery sketch geometry

while improving:
- metal realism
- gemstones
- reflections
- lighting
- materials
- presentation quality

---

# 5. MODEL SELECTION

Use this priority:

1. Geometry preservation
2. Runs reliably on RTX 4060 8GB
3. ControlNet support
4. Reproducibility
5. Licensing
6. Speed
7. Visual quality
8. Future LoRA compatibility

Do not automatically choose SDXL because it is newer.

A smaller SD 1.5 + ControlNet pipeline is acceptable — and potentially preferable — if it is more reliable on 8GB.

Document rejected candidates and why.

Do not invent benchmark numbers.

---

# 6. ENVIRONMENT AND DEPENDENCIES

Inspect `tgpu` first.

Expected Phase 6 environment includes PyTorch/CUDA and Ultralytics.

Verify:

    conda activate tgpu
    python -c "import torch; print(torch.__version__); print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'NO GPU')"
    nvidia-smi

Do not blindly upgrade PyTorch.

Install only packages actually required.

Likely packages:

- diffusers
- transformers
- accelerate
- safetensors
- Pillow
- OpenCV

Use:

    uv pip install ...

only where required.

Record actual versions in the report.

---

# 7. RTX 4060 8GB MEMORY STRATEGY

Initial target:

    512 × 512
    batch size = 1

Use fp16 where compatible.

Evaluate only useful memory optimizations such as:
- attention slicing
- VAE slicing
- VAE tiling
- CPU offload
- sequential CPU offload

Do not enable everything blindly.

The application must fail gracefully on CUDA OOM.

Never allow uncontrolled concurrent diffusion jobs.

Initial GPU policy:

    one rendering job at a time

Document the reason.

---

# 8. CONTROLNET RESEARCH AND SELECTION

Evaluate which conditioning type best fits jewellery sketches:

- Canny
- LineArt
- Soft Edge/HED
- Scribble
- Depth where meaningful

For clean jewellery blueprint/sketch images, specifically investigate LineArt and Canny.

Select a primary conditioning approach based on evidence.

Create an abstraction so future processors can be added:

    ConditioningProcessor
       ├── CannyProcessor
       ├── LineArtProcessor
       ├── SoftEdgeProcessor
       └── future processors

Do not implement unnecessary processors just for completeness.

---

# 9. SKETCH PREPROCESSING

Create a clean preprocessing module under the existing AI architecture.

A possible structure:

    ai/rendering/
        __init__.py
        config.py
        schemas.py
        pipeline.py
        preprocessing/
            __init__.py
            base.py
            lineart.py
            canny.py
        inference/
            __init__.py
            render.py

Adapt this to existing JewelMind conventions.

Pipeline:

1. Validate uploaded image.
2. Preserve original.
3. Normalize orientation.
4. Convert to required color format.
5. Handle transparency.
6. Resize while preserving aspect ratio.
7. Pad/crop according to model requirements.
8. Create ControlNet conditioning image.
9. Return conditioning metadata.

Never overwrite the user's original sketch.

---

# 10. JEWELLERY PROMPT SYSTEM

Create configurable prompt handling.

Do not scatter prompts through source files.

Positive prompt should target concepts such as:

    photorealistic fine jewellery product photograph,
    premium precious metal,
    polished metal,
    realistic gemstone,
    studio lighting,
    realistic reflections,
    luxury product presentation

Negative prompt should discourage:

- malformed jewellery
- extra gemstones
- missing gemstones
- extra prongs
- duplicated components
- deformed ring
- melted metal
- broken geometry
- distorted symmetry
- text
- watermark
- unrelated objects

Prompting is not the primary geometry-control mechanism. ControlNet is.

---

# 11. GEOMETRY PRESERVATION

This is the core Phase 7 requirement.

Generated output should preserve where possible:

- overall silhouette
- major jewellery structures
- stone location
- proportions
- symmetry
- visible prong/setting structure

Implement simple, explainable validation.

Possible metrics:
- Canny edge overlap
- structural similarity
- mask overlap when Phase 6 detections are available

Do not create a complicated research metric unnecessarily.

Visually inspect outputs as well.

If geometry changes significantly, document it.

---

# 12. PHASE 6 INTEGRATION

Do NOT retrain YOLO.

Design an optional future-compatible path:

    Sketch
      ↓
    YOLO component masks
      ↓
    Conditioning
      ↓
    ControlNet
      ↓
    Diffusion

For Phase 7, direct sketch → ControlNet rendering may remain the primary implementation.

Document future uses of Phase 6 masks:
- preserve gemstone area
- preserve shank
- protect prongs
- component-specific prompting
- targeted inpainting
- material-specific rendering

Avoid tightly coupling the two systems unnecessarily.

---

# 13. DIFFUSION MODEL MANAGER

Do not reload the model for every request.

Implement an appropriate model lifecycle:

    Backend startup/lazy initialization
             ↓
       DiffusionModelManager
             ↓
        Load pipeline once
             ↓
       Render requests
             ↓
          output

Because the GPU has 8GB VRAM:
- consider lazy loading
- document model residency
- avoid loading YOLO and diffusion simultaneously if unsafe
- use offload/unload strategy if needed

The backend must not randomly OOM.

---

# 14. RENDERING API

Follow existing FastAPI conventions.

If no equivalent exists, implement:

    POST /api/v1/ai/render

Do not duplicate an existing endpoint.

Support appropriate inputs such as:
- sketch/image
- prompt
- negative prompt
- seed
- control type
- control strength
- inference steps
- resolution

Use sensible defaults and bounds.

Do not expose every internal pipeline parameter.

Example conceptual configuration:

    control_type = "lineart"
    control_strength = 0.8
    steps = 20
    guidance_scale = 7.0
    seed = 12345
    width = 512
    height = 512

Adapt to the actual selected model.

---

# 15. RESULT SCHEMA

Create a stable rendering response, for example:

    RenderResult

    {
      "model_version": "...",
      "controlnet_version": "...",
      "image_width": 512,
      "image_height": 512,
      "seed": 12345,
      "control_type": "lineart",
      "control_strength": 0.8,
      "steps": 20,
      "guidance_scale": 7.0,
      "inference_time_ms": 0,
      "device_used": "cuda:0",
      "output_url": "...",
      "created_at": "..."
    }

Do not expose local filesystem paths.

Keep the API contract stable.

---

# 16. GPU CONCURRENCY

Because the GPU is only 8GB:

- serialize rendering jobs initially
- use a lock/queue appropriate to the existing backend architecture
- prevent simultaneous diffusion jobs
- return a clean busy/error response if appropriate

Do not introduce Redis/Celery/RabbitMQ merely for this phase unless existing architecture already uses them.

A simple in-process mechanism is acceptable for the capstone.

Document that production scaling would require a proper worker/queue later.

---

# 17. REPRODUCIBILITY

Every render should support a seed.

Record:

- model version
- ControlNet version
- seed
- steps
- guidance scale
- control strength
- resolution
- conditioning type

Attempt reproducibility under the same model/environment.

Do not claim mathematically exact reproducibility across different hardware/software versions.

---

# 18. OUTPUT STORAGE

Do not store generated images in Git.

Prefer existing Supabase Storage if already appropriate.

Otherwise use a Git-ignored local directory such as:

    outputs/rendering/

Do not return private local filesystem paths.

Do not commit generated images.

---

# 19. FRONTEND INTEGRATION

Inspect the existing Design Studio.

Do not redesign the entire application.

Expose only the minimum real functionality needed to demonstrate Phase 7.

User flow:

1. Open a jewellery design.
2. Upload/select a sketch.
3. Select conditioning mode if exposed.
4. Enter/adjust prompt.
5. Generate.
6. Show a real loading state.
7. Display the generated result.
8. Allow comparison with the original sketch.
9. Show useful metadata where appropriate.

Use existing:
- Tailwind CSS
- shadcn/ui
- JewelMind design system

Do not show fake percentage progress.

Use simple status:

    Rendering jewellery...

---

# 20. FRONTEND ERROR STATES

Handle:

### CUDA OOM
    Rendering exceeded available GPU memory.
    Try a lower resolution or wait for the current GPU job to finish.

### Model unavailable
    Rendering model is not available.
    Check the local AI environment.

### Invalid sketch
    Please upload a valid jewellery sketch.

### Backend unavailable
    AI rendering service is unavailable.

Never expose stack traces to users.

Log detailed errors server-side.

---

# 21. TESTING

Add unit tests for:

### Configuration
- valid defaults
- invalid resolution
- invalid steps
- control strength bounds
- seed

### Preprocessing
- RGB
- grayscale
- transparency
- invalid image
- aspect-ratio preservation

### Schemas
- RenderResult validation
- required metadata
- no local path leakage

### API
- request validation
- invalid input
- model unavailable
- safe error responses

### Model manager
Tests must not download huge models.

Mock the model manager where appropriate.

The normal test suite must remain fast.

---

# 22. REAL GPU SMOKE TEST

Create a manual smoke-test script.

It must:

1. Verify CUDA.
2. Load the selected model.
3. Load one jewellery sketch.
4. Generate one 512×512 image.
5. Use batch size 1.
6. Record:
   - model
   - device
   - VRAM before
   - peak VRAM if available
   - inference time
   - output path
7. Verify the generated image exists.
8. Exit with success/failure.

Do not automatically execute this during every `pytest`.

The first model download/loading may take significant time.

---

# 23. SMALL BENCHMARK

After the smoke test works, benchmark only a few settings.

Start with:

    512 × 512
    batch 1
    10–20 steps
    fp16

Record:

- cold-start/load time
- warm inference time
- peak VRAM
- model
- ControlNet
- resolution
- steps

Do not run dozens of combinations.

The goal is feasibility on RTX 4060 8GB.

---

# 24. QUALITY VALIDATION

Use a small fixed set of jewellery sketches.

Where possible include:
- ring
- pendant
- necklace
- earrings
- bracelet/bangle

Use fixed seeds for comparison.

Inspect:

### Geometry
- silhouette preserved?
- proportions preserved?
- stone position preserved?
- symmetry preserved?
- major structures preserved?

### Realism
- realistic metal?
- realistic gemstones?
- plausible reflections?
- plausible lighting?

### Failure modes
- extra stones?
- missing stones?
- extra prongs?
- deformed jewellery?
- melted geometry?
- duplicated components?
- unrelated objects?

Document failures honestly.

This is a proof-of-concept, not automatically production quality.

---

# 25. OPTIONAL PHASE 6 CROSS-CHECK

If the trained Phase 6 YOLO model is available:

1. Detect components in the original sketch.
2. Detect components in the generated image.
3. Compare major geometry/components.
4. Record observations.

Do NOT retrain YOLO.

This is a sanity check, not a formal scientific benchmark.

---

# 26. MODEL STORAGE

Use configurable model directories.

Do not hard-code user-specific absolute paths.

Document:
- exact model identifier
- revision/version
- local cache/model directory
- license
- download mechanism
- checksum if practical

An environment variable/config value such as:

    JEWELMIND_MODEL_DIR

is acceptable.

Never commit credentials.

---

# 27. FUTURE LoRA PLAN — DO NOT TRAIN

Prepare documentation for future jewellery-specific LoRA fine-tuning.

Do NOT start LoRA training now unless explicitly instructed.

Document:
- required training data
- captions
- jewellery styles
- validation split
- overfitting prevention
- RTX 4060 constraints
- checkpoints
- resume procedure
- GPU monitoring

Standing training rule:

Whenever future training is performed:
1. Use local RTX 4060.
2. Reuse `tgpu` if compatible.
3. Use checkpoints.
4. Save resumable `last` checkpoint.
5. Explain how to resume.
6. Explain GPU monitoring.
7. Explain expected runtime.
8. Never force restart from epoch 1 after interruption.

---

# 28. DO NOT OVERENGINEER

Do not add:
- Kubernetes
- distributed inference
- multi-GPU
- cloud GPU infrastructure
- production autoscaling
- unnecessary message brokers
- microservices for trivial components

Keep the implementation:
- understandable
- reproducible
- local-first
- maintainable
- demonstrable

---

# 29. REQUIRED DOCUMENTATION

Create:

    docs/phases/PHASE_7_MODEL_RESEARCH.md
    docs/phases/PHASE_7_REPORT.md

`PHASE_7_REPORT.md` must contain:

1. Executive summary
2. Branch
3. Existing architecture inspected
4. Model candidates
5. Selected model
6. Selection rationale
7. ControlNet selection
8. Licensing
9. Environment
10. GPU verification
11. Dependencies
12. Preprocessing
13. Rendering architecture
14. Model manager
15. API
16. RenderResult schema
17. Frontend integration
18. GPU memory strategy
19. Smoke-test result
20. Benchmark result
21. Quality validation
22. Phase 6 integration status
23. Future LoRA plan
24. Limitations
25. Tests
26. Git safety
27. Merge readiness

If something was not implemented, write:

    NOT IMPLEMENTED IN PHASE 7

Do not invent results.

---

# 30. ACCEPTANCE CRITERIA

### Research
- [ ] Multiple diffusion candidates researched.
- [ ] ControlNet choices researched.
- [ ] Licensing researched.
- [ ] RTX 4060 feasibility assessed.
- [ ] Model choice justified.

### Environment
- [ ] Existing `tgpu` reused if compatible.
- [ ] CUDA verified.
- [ ] No unnecessary duplicate environment.
- [ ] Dependencies documented.

### Rendering
- [ ] Real diffusion pipeline implemented.
- [ ] Real ControlNet conditioning implemented.
- [ ] No fake outputs.
- [ ] 512×512 batch-1 inference works OR exact limitation documented.
- [ ] GPU usage verified.

### Backend
- [ ] Rendering endpoint exists.
- [ ] Validation exists.
- [ ] Stable RenderResult exists.
- [ ] Errors handled safely.
- [ ] GPU jobs are controlled.

### Frontend
- [ ] Design Studio can exercise real rendering OR exact missing-integration reason documented.
- [ ] Loading state exists.
- [ ] Error state exists.
- [ ] Original/rendered comparison exists if integration is implemented.

### Quality
- [ ] Fixed validation sketches used.
- [ ] Geometry preservation inspected.
- [ ] Rendering realism inspected.
- [ ] Failure cases documented.
- [ ] No false production-quality claims.

### Git
- [ ] No model binaries tracked.
- [ ] No generated images tracked.
- [ ] No `.env` tracked.
- [ ] `.gitignore` reviewed.
- [ ] `git diff` reviewed.
- [ ] `git status` reviewed.

---

# 31. EXACT EXECUTION ORDER

Follow this order:

## STEP 1
Create branch.

## STEP 2
Inspect current JewelMind architecture.

## STEP 3
Inspect Phase 6 AI implementation.

## STEP 4
Research diffusion candidates.

## STEP 5
Create `PHASE_7_MODEL_RESEARCH.md`.

## STEP 6
Select the most practical model.

## STEP 7
Verify/reuse `tgpu`.

## STEP 8
Install only required dependencies.

## STEP 9
Implement preprocessing.

## STEP 10
Implement ControlNet diffusion pipeline.

## STEP 11
Implement model manager and GPU-safe execution.

## STEP 12
Implement backend API.

## STEP 13
Implement RenderResult.

## STEP 14
Implement minimal frontend integration.

## STEP 15
Run unit tests.

## STEP 16
Run manual GPU smoke test.

## STEP 17
Run small benchmark.

## STEP 18
Run fixed validation set.

## STEP 19
Document quality and limitations.

## STEP 20
Create `PHASE_7_REPORT.md`.

## STEP 21
Run relevant complete tests.

## STEP 22
Perform Git safety review.

## STEP 23
STOP.

Do NOT merge.

Do NOT begin Phase 8.

---

# 32. IMPORTANT: STOP CONDITIONS

STOP and ask the user before continuing if:

- a model requires unexpectedly large VRAM
- CUDA OOM occurs repeatedly
- PyTorch must be replaced/upgraded in a way that could break Phase 6
- a paid API is required
- licensing is unclear for the intended use
- LoRA/ControlNet training becomes necessary
- the existing `tgpu` environment is incompatible and a new environment is required
- Supabase schema changes are required beyond this phase
- major frontend architecture changes are required

Do not silently make high-risk decisions.

---

# 33. FINAL USER REPORT

At the end respond exactly in this style:

    PHASE 7 STATUS

    Branch:
    ...

    Selected diffusion model:
    ...

    ControlNet:
    ...

    GPU:
    ...

    CUDA:
    ...

    Peak VRAM:
    ...

    Smoke test:
    PASS / FAIL

    Warm inference time:
    ...

    Frontend integration:
    COMPLETE / NOT IMPLEMENTED

    Tests:
    ...

    Known limitations:
    ...

    Report:
    docs/phases/PHASE_7_REPORT.md

    Merge status:
    READY FOR USER REVIEW

Then STOP.

Do not merge.
Do not push.
Do not begin Phase 8.

---

# 34. CORE SUCCESS QUESTION

The phase is not successful merely because the generated image looks attractive.

The real question is:

    "Can JewelMind reliably transform a jewellery sketch into a more realistic jewellery rendering while preserving the sketch geometry on an RTX 4060 8GB?"

All implementation and validation should help answer that question.

If the answer is only partially yes, document exactly where and why.

END OF PHASE 7
