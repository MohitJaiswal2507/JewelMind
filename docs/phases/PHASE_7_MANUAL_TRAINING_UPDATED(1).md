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

### ABSOLUTE TRAINING RULE — USER TRAINS MANUALLY

Antigravity must NEVER start, continue, resume, or schedule any model-training job.

The user will perform ALL training manually on the RTX 4060.

Antigravity IS allowed to:
- inspect the current AI environment
- verify CUDA/GPU compatibility
- research and recommend models
- prepare dataset directory structure
- create dataset validation/preprocessing scripts
- create training configuration files
- create training scripts
- create checkpoint/resume utilities
- create evaluation scripts
- create inference scripts
- create a manual training guide
- perform lightweight preprocessing tests
- perform lightweight non-training inference/smoke tests when safe

Antigravity MUST NOT automatically execute:
- LoRA training
- ControlNet training
- diffusion fine-tuning
- DreamBooth training
- textual inversion
- full dataset preprocessing that launches model training
- long GPU jobs
- large benchmark sweeps
- automatic checkpoint resume
- any command containing a training entry point such as `train.py`, `accelerate launch ...train...`, or equivalent

If training is required, Antigravity must STOP before training and report:

    MANUAL TRAINING REQUIRED

Then provide the user with:
1. exact environment activation command
2. exact dependency installation command, if still needed
3. exact dataset folder structure
4. exact dataset preparation/validation command
5. exact training command
6. recommended starting hyperparameters for RTX 4060 8GB
7. expected VRAM considerations
8. how to monitor GPU usage
9. where checkpoints will be saved
10. how to resume from the latest checkpoint
11. how to recognize successful completion
12. what output/artifacts should be sent back to the assistant for review

The user will run those commands manually and return the results/logs. Only after the user confirms training has completed should Antigravity implement or validate the trained-model integration.

NEVER hide a training command inside another script and execute it automatically.

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

# 27. OPTIONAL JEWELLERY LoRA TRAINING — MANUAL USER EXECUTION ONLY

LoRA fine-tuning may be useful if the base diffusion + ControlNet pipeline does not produce sufficiently jewellery-specific results.

However, training is NOT an Antigravity task.

Antigravity must only prepare everything required for the user to train manually.

## 27.1 What Antigravity must prepare

If LoRA training is justified, create:

    ai/training/
        README.md
        prepare_dataset.py
        validate_dataset.py
        train_lora.py
        evaluate_lora.py
        inference.py
        checkpoints/
        logs/

and an appropriate configuration file such as:

    configs/jewellery_lora.yaml

Adapt the paths to the existing JewelMind architecture instead of blindly creating duplicates.

Also create:

    docs/phases/PHASE_7_MANUAL_TRAINING_GUIDE.md

The guide must explain the complete manual process from dataset preparation through training, checkpointing, evaluation, and inference.

## 27.2 Dataset preparation

Document and validate:

- image licensing/usage rights
- image resolution
- image quality
- jewellery category
- jewellery style
- material
- gemstone information
- captions
- train/validation split
- duplicate detection where practical
- corrupted-image detection

Do not silently scrape or download a copyrighted dataset.

Prefer:
- user-owned images
- appropriately licensed datasets
- self-created/synthetic training pairs where practical

## 27.3 Training configuration

Prepare conservative RTX 4060 8GB defaults.

The configuration should start with memory-safe settings such as:

- batch size: 1
- mixed precision where supported
- gradient accumulation where useful
- gradient checkpointing where supported
- modest training resolution
- checkpoint saving at regular intervals
- resumable `last` checkpoint
- fixed/random seed documented
- configurable learning rate
- configurable number of epochs/steps

Do NOT claim a particular runtime until an actual manual run provides evidence.

## 27.4 Manual execution boundary

When the training files are ready, Antigravity must NOT run the training command.

The report must explicitly say:

    MANUAL TRAINING REQUIRED — NOT EXECUTED BY ANTIGRAVITY

The user will manually execute the command on the RTX 4060.

Example structure only; adapt the exact command to the selected training implementation:

    conda activate tgpu
    cd <JewelMind-project>
    <training command>

Do not execute this command automatically.

## 27.5 Checkpoint and resume instructions

The manual guide must explain:

1. where checkpoints are written
2. how to monitor GPU VRAM
3. how to stop safely
4. how to resume from `last`
5. how to select the best checkpoint
6. how to validate the trained LoRA
7. how to roll back to the base model if the LoRA is worse

Never require restarting from step 1 after an interruption when a valid checkpoint exists.

## 27.6 What the user should return after training

After manual training, the user should provide:

- training command used
- final/last checkpoint information
- training logs
- peak VRAM
- number of images
- training steps/epochs
- validation results
- example generated outputs
- observed failure cases

The assistant can then review the results and guide the next manual step.

## 27.7 ControlNet training

Do NOT train a ControlNet by default.

Prefer an existing compatible pretrained ControlNet for the selected base model.

Only if experiments demonstrate that an existing ControlNet is insufficient should a custom ControlNet training plan be considered.

If custom ControlNet training becomes necessary:

    STOP — MANUAL TRAINING REQUIRED

Do not execute it automatically.

## 27.8 Standing rule for every future training operation

For ALL future JewelMind model training:

1. User starts the training manually.
2. User monitors the RTX 4060 manually.
3. User shares logs/results with the assistant.
4. Assistant reviews the results.
5. Assistant provides the next exact manual command if needed.
6. Antigravity only implements code/configuration/documentation.
7. Antigravity never launches the training job.

This rule applies even if a training script is already available.

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
    docs/phases/PHASE_7_MANUAL_TRAINING_GUIDE.md

If training is not required for the selected pipeline, still document why a pretrained
base model + pretrained ControlNet is sufficient for this phase.

If training is required, the report must clearly state:

    MANUAL TRAINING REQUIRED — NOT EXECUTED BY ANTIGRAVITY

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

### Training safety
- [ ] No training job was launched by Antigravity.
- [ ] No automatic checkpoint resume was performed.
- [ ] Manual training guide exists if training is required.
- [ ] Exact manual training command is documented.
- [ ] RTX 4060 8GB starting settings are documented.
- [ ] Checkpoint/resume procedure is documented.
- [ ] Training status is explicitly marked as NOT EXECUTED BY ANTIGRAVITY.

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
Prepare the manual training guide if training is justified.

## STEP 17
STOP BEFORE ANY TRAINING.

Tell the user exactly what to run manually on the RTX 4060.

Do NOT execute the training command.

## STEP 18
After the user manually completes training (only if training is required), validate the returned checkpoint/model with controlled inference.

## STEP 19
Run small benchmark.

## STEP 20
Run fixed validation set.

## STEP 21
Document quality and limitations.

## STEP 22
Create `PHASE_7_REPORT.md`.

## STEP 23
Run relevant complete tests.

## STEP 24
Perform Git safety review.

## STEP 25
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
- any training command is ready to execute
- the user has not explicitly started the manual training process
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

    Training:
    NOT REQUIRED / MANUAL TRAINING REQUIRED / MANUAL TRAINING COMPLETED

    Training executed by Antigravity:
    NO

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

# 34. ABSOLUTE TRAINING BOUNDARY

Antigravity is an implementation and preparation agent for this phase.

It must NEVER:
- launch model training
- resume model training
- run long GPU training jobs
- silently execute a training script
- download a large training checkpoint and begin training without user action

The user owns the training step.

The assistant will guide the user manually, step-by-step, including:
- dataset preparation
- environment setup
- training command
- VRAM monitoring
- checkpoint handling
- resume
- evaluation
- inference
- troubleshooting

Only after the user reports the manual training result should the trained model be integrated into the application.

---

# 35. CORE SUCCESS QUESTION

The phase is not successful merely because the generated image looks attractive.

The real question is:

    "Can JewelMind reliably transform a jewellery sketch into a more realistic jewellery rendering while preserving the sketch geometry on an RTX 4060 8GB?"

All implementation and validation should help answer that question.

If the answer is only partially yes, document exactly where and why.

END OF PHASE 7
