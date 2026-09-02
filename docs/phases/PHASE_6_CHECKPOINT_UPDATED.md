# PHASE 6 — JewelMind Jewellery Component Detection (YOLO)

## 0. Phase Objective

Implement JewelMind's jewellery component-detection AI pipeline using **YOLO11 instance segmentation**. This phase must build a reproducible dataset, training, evaluation, and inference workflow—not merely download a pretrained model.

Primary goals:
- research and validate suitable jewellery datasets;
- define an evidence-based JewelMind component taxonomy;
- prepare/validate YOLO segmentation data;
- fine-tune a pretrained YOLO model on the user's **local NVIDIA RTX 4060**;
- benchmark YOLO11s-seg vs YOLO11m-seg where feasible;
- evaluate quantitatively and qualitatively;
- provide a reusable inference interface for later AI phases;
- keep model binaries/datasets/secrets out of Git.

---

# 1. Mandatory User Requirements

### 1.1 Local GPU first

The user's **NVIDIA RTX 4060** is the primary training machine. Do not use paid cloud GPU training by default.

Before any long training run, verify:

```bash
nvidia-smi
```

and:

```bash
python -c "import torch; print('PyTorch:', torch.__version__); print('CUDA:', torch.cuda.is_available()); print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'); print('Torch CUDA:', torch.version.cuda)"
```

The phase report must record GPU name, VRAM if available, PyTorch version, CUDA availability and runtime.

### 1.2 Step-by-step training guidance

Create:

```text
docs/ai/YOLO_TRAINING_GUIDE.md
```

Write it for an undergraduate developer on Windows. It must explain, in order:

1. opening the project;
2. activating the existing Python environment;
3. checking `python --version` and pip;
4. verifying the RTX 4060/CUDA;
5. installing only required dependencies;
6. downloading/preparing the dataset;
7. validating annotations;
8. visually inspecting annotations;
9. running a short GPU smoke test;
10. benchmarking the candidate models;
11. starting the real training command manually;
12. monitoring with `nvidia-smi -l 2`;
13. understanding training output;
14. stopping safely;
15. resuming from `last.pt`;
16. locating `best.pt`/`last.pt`;
17. validating the final model;
18. running inference;
19. reviewing prediction images;
20. copying/recording the final model path without committing it.

**Do not automatically start a multi-hour training run.** Prepare it and give the user the exact command; the user should manually start the long run so they can monitor their RTX 4060.

---
# 2. Python Environment — Reuse First, Create Only If Needed

Before creating any environment, inspect the repository and existing Python environments. **Do not create a duplicate environment if a suitable YOLO/AI training environment already exists.**

Check for existing environments such as:

```text
ai/vision/yolo/.venv
ai/vision/yolo/venv
ai/yolo/.venv
ai/yolo/venv
existing documented Conda environment
existing documented YOLO training environment
```

Also inspect existing project documentation/configuration before deciding.

### If a suitable environment already exists

Reuse it. Record:

- environment type (Conda/venv);
- environment name/path;
- Python version;
- `uv` version;
- PyTorch version;
- CUDA availability;
- Ultralytics version.

Do not create another environment for the same YOLO pipeline.

### If no suitable environment exists

Create **one dedicated YOLO training environment inside the YOLO folder**, using **Miniconda + uv**. Prefer a structure similar to:

```text
ai/vision/yolo/
├── .venv/
├── datasets/
├── models/
├── training/
├── inference/
└── ...
```

Use Miniconda to provide the Python environment and `uv` for fast dependency/environment management. Use the exact approach that is compatible with the existing repository; do not create multiple competing environments.

Document the exact Windows commands used in `docs/ai/YOLO_TRAINING_GUIDE.md`.

Before installing dependencies, check:

```bash
conda --version
uv --version
python --version
python -m pip --version
```

Install a PyTorch build compatible with the RTX 4060. Do not blindly install a system-wide CUDA toolkit. Prefer the appropriate PyTorch CUDA runtime/package.

Verify with:

```python
import torch

print("PyTorch:", torch.__version__)
print("CUDA available:", torch.cuda.is_available())

if torch.cuda.is_available():
    print("GPU:", torch.cuda.get_device_name(0))
    print("CUDA:", torch.version.cuda)
    print("VRAM GB:", round(torch.cuda.get_device_properties(0).total_memory / 1024**3, 2))
```

If CUDA cannot see the RTX 4060, **stop before real training** and report the problem.

# 3. Full Training Must Be User-Started

Antigravity may prepare and verify the entire training workflow, including environment setup, dataset preparation, validation, visualization, smoke testing, benchmark scripts, configuration, and the exact final command.

**Antigravity MUST NOT automatically start the long/full training run.**

The intended handoff is:

```text
Environment ready
        ↓
Dataset ready + validated
        ↓
Annotation previews inspected
        ↓
GPU verified
        ↓
Short smoke test passed
        ↓
Benchmark ready
        ↓
USER STARTS REAL TRAINING
```

The final response must clearly tell the user that full training was not started automatically and point them to the step-by-step guide.

## Required user training guide

`docs/ai/YOLO_TRAINING_GUIDE.md` must contain exact commands for the actual paths/environment created by the phase, not generic placeholders where the real values are known.

It must include:

1. Open project.
2. Activate/reuse the YOLO environment.
3. Verify Python and `uv`.
4. Run `nvidia-smi`.
5. Verify PyTorch sees the RTX 4060.
6. Validate the dataset.
7. Open annotation previews and manually inspect them.
8. Run the short GPU smoke test.
9. Run the controlled YOLO11s-seg/YOLO11m-seg benchmark.
10. Choose the final model based on accuracy, mask quality, VRAM and speed.
11. **YOU START REAL TRAINING HERE** — provide the exact command.
12. Monitor another terminal with:

```bash
nvidia-smi -l 2
```

13. Explain GPU utilization, VRAM, temperature and power.
14. Explain `Ctrl+C` interruption and checkpoint/resume using `last.pt` when available.
15. Show where `best.pt` and `last.pt` are stored.
16. Run final validation/evaluation.
17. Run inference on real jewellery sketches.
18. Inspect prediction outputs.
19. Record metrics for `PHASE_6_REPORT.md`.
20. Confirm model weights are ignored by Git.

If CUDA OOM occurs, instruct the user to reduce batch size first, then image size if needed, rather than immediately falling back to CPU.

---


# 2. Branching

Create:

```text
phase-6-yolo-component-detection
```

Start with:

```bash
git status
git switch -c phase-6-yolo-component-detection
```

Do not work directly on `main` and do not merge this phase.

---

# 3. Existing JewelMind Architecture

Do not replace existing architecture.

- Frontend: React + TypeScript + Vite
- Styling: Tailwind CSS
- UI: shadcn/ui
- Backend: FastAPI
- Database: PostgreSQL via Supabase
- AI: Python
- Local training hardware: NVIDIA RTX 4060
- Existing phases: authentication, jewellery design management, sketch upload, interactive design canvas

Do not redesign existing UI or authentication in this phase.

---

# 4. Model Choice

Use **YOLO11 instance segmentation** for this phase.

Benchmark:

```text
YOLO11s-seg
YOLO11m-seg
```

Start from pretrained weights and fine-tune them; do not train from random initialization unless there is a documented experimental reason.

Segmentation is preferred because JewelMind eventually needs approximate component shapes/masks, not only bounding boxes.

Potential component classes are only candidates until the dataset is inspected:

```text
ring_shank
ring_head
band
shoulder
setting
gemstone
prong
bezel
gallery
engraving
```

Do **not** fabricate a component taxonomy. Final classes must be supported by available annotations, actual JewelMind sketches, manufacturing usefulness, class frequency, and realistic visual separability.

---

# 5. Dataset Research

Before training, inspect suitable public jewellery datasets. At minimum investigate relevant Roboflow jewellery datasets and other legally usable open datasets discovered during research.

One known Roboflow jewellery dataset contains about 6.9k images and broad classes such as ring, bracelet, earring, necklace, etc. Treat this as possible bootstrap/broad-jewellery data—not automatically as component-level training data.

For every dataset document:

```text
dataset name
source/URL
license
image count
classes
annotation type
image quality
relevance to JewelMind
redistribution/training permission
limitations
```

Do not scrape illegally. Do not use a dataset with unclear licensing without flagging it.

The dataset strategy should support:

- **Public bootstrap data** — broad jewellery recognition;
- **component-level data** — actual jewellery components;
- **JewelMind-specific data** — our own annotated sketches, which are the long-term important dataset.

Do not claim generic jewellery datasets prove fine-grained sketch-component detection.

---

# 6. Data Structure

Adapt to the existing repository, but create a clean structure similar to:

```text
ai/vision/
├── datasets/
│   ├── raw/
│   ├── processed/
│   └── README.md
├── models/
│   └── README.md
├── training/
│   ├── configs/
│   ├── scripts/
│   └── README.md
├── inference/
├── evaluation/
└── README.md
```

Large datasets and model outputs stay outside Git.

---

# 7. Model/Artifact Git Policy

Never commit these by default:

```text
*.pt
*.pth
*.onnx
*.safetensors
*.bin
runs/
checkpoints/
large datasets
```

Update `.gitignore` as necessary. Keep reproducibility documentation so another developer can recreate/download the model.

Never commit `.env`, credentials, Supabase secrets, Hugging Face tokens, or API keys.

---

# 8. Python/PyTorch Setup

Use the existing AI/backend Python environment where appropriate. Do not create unnecessary competing environments.

Before installing:

```bash
python --version
python -m pip --version
```

Check whether PyTorch already exists. If installation is needed, install a PyTorch build compatible with the user's NVIDIA GPU rather than blindly installing a system CUDA toolkit.

Verify:

```python
import torch
assert torch.cuda.is_available(), "CUDA GPU is not available"
print(torch.cuda.get_device_name(0))
```

Use the Ultralytics Python package:

```python
from ultralytics import YOLO
```

Record the installed Ultralytics version.

---

# 9. Dataset Format and Validation

Use standard YOLO segmentation format and a dataset YAML such as:

```yaml
path: ...
train: ...
val: ...
test: ...
names:
  0: ...
  1: ...
```

Create a validator such as:

```text
ai/vision/training/scripts/validate_dataset.py
```

Validate:

- images exist;
- expected labels exist;
- class IDs are in range;
- segmentation polygons are valid;
- corrupt/empty files are reported;
- image/label matching is correct;
- duplicates/near-duplicates are identified where practical;
- train/validation/test leakage is checked where practical.

Create a summary containing image counts, instance counts and class distribution.

---

# 10. Splits and Class Balance

Use the source dataset's official split when appropriate. For new JewelMind-specific data, use a reproducible starting split around:

```text
70% train
20% validation
10% test
```

Use a fixed seed. Prevent near-duplicate sketches from crossing splits.

Calculate per-class image/instance counts and identify severe imbalance. Do not duplicate minority classes without documenting it.

---

# 11. Annotation Visualization

Before long training, create sample visualizations showing:

```text
original image + ground-truth masks + class labels
```

The user must be able to visually confirm that labels actually describe the intended components.

**Do not start multi-hour training before this check.**

---

# 12. GPU Smoke Test

Before real training, run a short GPU smoke test, approximately 1–3 epochs or another intentionally tiny run.

Purpose:

- verify model loading;
- verify dataset loading;
- verify CUDA;
- verify forward/backward pass;
- verify segmentation labels;
- detect VRAM/OOM problems.

Use `device=0`. Document the result.

---

# 13. Model Benchmark

Benchmark YOLO11s-seg and YOLO11m-seg where the dataset and RTX 4060 allow it.

First use a controlled short experiment rather than two full long trainings. Compare:

```text
VRAM usage
training speed
inference speed
validation performance
mask quality
precision/recall
mAP50
mAP50-95
```

If `YOLO11m-seg` causes CUDA OOM, reduce batch size first, then image size if necessary. Close other GPU applications. Do not immediately switch to CPU.

Choose the final model based on accuracy/quality versus RTX 4060 resource usage and document the reason.

---

# 14. Real Training

Once dataset validation, annotation inspection and benchmark are successful, prepare the exact real-training command.

Example pattern only:

```python
from ultralytics import YOLO

model = YOLO("yolo11m-seg.pt")

model.train(
    data="path/to/jewellery.yaml",
    epochs=100,
    imgsz=640,
    device=0,
    project="runs/jewellery",
    name="yolo11m-seg-jewelmind",
)
```

Do not blindly copy the example. Select epochs, batch size, image size, workers, augmentation and other parameters from actual dataset/GPU results.

The training configuration must record:

```text
model
pretrained checkpoint
dataset/dataset version
image size
batch size
epochs
optimizer
learning rate
seed
device
workers
augmentation
early stopping/patience
```

---

# 15. RTX 4060 Monitoring Guide

Teach the user to open another terminal during training:

```bash
nvidia-smi -l 2
```

Explain:

- GPU utilization;
- GPU memory usage;
- temperature;
- power usage.

If CUDA OOM occurs:

1. reduce batch size;
2. close other GPU programs;
3. retry the smoke test;
4. lower image size only if necessary;
5. then consider the smaller model.

The RTX 4060 should remain the primary training device.

---

# 16. Training Outputs

Use a dedicated run directory, for example:

```text
runs/jewellery/yolo11m-seg-jewelmind/
├── weights/
│   ├── best.pt
│   └── last.pt
├── results.csv
├── results.png
└── ...
```

Document actual outputs produced by the installed Ultralytics version.

---

# 17. Evaluation

Evaluate validation and test sets as appropriate.

Record at minimum:

```text
precision
recall
mAP50
mAP50-95
segmentation/mask metrics
per-class performance
inference time per image
```

Inspect qualitative predictions and include examples of:

```text
good detection
missed component
false positive
poor segmentation
ambiguous component
```

Never report only one mAP number.

If the dataset only supports broad jewellery classes, explicitly state:

```text
Current capability: broad jewellery recognition.
Not yet proven: fine-grained jewellery component detection from sketches.
```

---

# 18. JewelMind-Specific Dataset Roadmap

Prepare infrastructure for future annotated sketches, for example:

```text
ai/vision/datasets/jewelmind_components/
```

Document how to add:

```text
image
YOLO segmentation label
class
source
annotation status
review status
```

Only add component classes that can be supported by actual annotations.

---

# 19. Inference Script

Create:

```text
ai/vision/inference/predict_components.py
```

It should accept arguments similar to:

```text
--model
--source
--conf
--output
--device
```

Example:

```bash
python ai/vision/inference/predict_components.py --model path/to/best.pt --source path/to/sketch.png --conf 0.25 --device 0
```

Normalize model output into a stable JewelMind schema such as:

```json
{
  "detections": [
    {
      "class_id": 0,
      "class_name": "gemstone",
      "confidence": 0.91,
      "bbox": [x1, y1, x2, y2],
      "mask": []
    }
  ]
}
```

Use the real mask data rather than an empty placeholder in the actual implementation.

---

# 20. AI Service Boundary

Do not put YOLO training code inside FastAPI request handlers.

Create a clean AI inference/service boundary compatible with the existing architecture. Training is an offline/local workflow.

A future conceptual pipeline is:

```text
Jewellery Sketch
      ↓
YOLO Component Detector
      ↓
Structured Components
      ↓
Feature Extraction
      ↓
XGBoost prediction
      ↓
Cost / Time / Wastage
      ↓
OR-Tools production optimization
```

Do not implement XGBoost, diffusion or OR-Tools in Phase 6.

---

# 21. Optional Minimal API Integration

Only after local inference works, a minimal authenticated endpoint may be added, such as:

```text
POST /api/v1/ai/components/detect
```

Return:

```json
{
  "model_version": "...",
  "detections": []
}
```

Do not make FastAPI start long training processes. Do not build full asynchronous worker infrastructure in this phase.

---

# 22. Frontend Integration

If integration is added, keep it minimal. The existing Design Studio may eventually display:

```text
Detected Components
- component name
- confidence
- visual region/mask
```

Never use fake AI results. If the model is unavailable, show an explicit not-ready/disabled state.

Do not redesign the Design Studio.

---

# 23. Model Versioning

Create documentation such as:

```text
docs/ai/models/YOLO_COMPONENT_MODEL.md
ai/vision/models/README.md
```

Record:

```text
model name
model family
Ultralytics version
base checkpoint
dataset version
class taxonomy
training configuration
training date
evaluation metrics
Git commit
local model path
```

Do not commit binary weights.

---

# 24. License Documentation

Document the licenses of:

1. Ultralytics software/model family;
2. every public dataset used;
3. pretrained weights;
4. JewelMind's own annotations.

Ultralytics currently documents AGPL-3.0 and Enterprise licensing options. For an academic project, document the selected usage assumptions clearly. Do not claim the model is automatically suitable for commercial deployment; a future commercial deployment requires a separate license review.

---

# 25. Testing

Add tests for:

### Dataset

```text
YAML loads
class IDs valid
annotation files valid
image/label matching
```

### GPU

```text
CUDA detection helper
device selection
```

### Inference

```text
model loads
single-image inference works
stable output schema
empty detections handled
```

### Backend (if endpoint added)

```text
authentication
valid image
invalid image
no detection
successful detection
```

Do not require the large trained weights in normal unit tests; use mocks/fixtures where appropriate.

---

# 26. Documentation Required

Create/update:

```text
docs/ai/YOLO_TRAINING_GUIDE.md
docs/ai/YOLO_COMPONENT_DETECTION.md
ai/vision/README.md
ai/vision/datasets/README.md
ai/vision/models/README.md
docs/phases/PHASE_6_REPORT.md
```

Adjust paths if equivalent existing locations already exist.

---

# 27. Phase Report

`docs/phases/PHASE_6_REPORT.md` must contain:

## Executive Summary
What was implemented.

## Model
YOLO11s-seg/YOLO11m-seg benchmark and selected model.

## Dataset
Source, license, size, classes, split, annotation type and limitations.

## Taxonomy
Final component classes and why they were selected.

## GPU
GPU name, VRAM, PyTorch, CUDA and whether CUDA was successfully used.

## Training
Epochs, batch size, image size, optimizer, learning rate, device and duration.

## Results
Precision, recall, mAP50, mAP50-95, segmentation metrics and per-class results.

## Qualitative Results
Good detections and representative failure cases.

## Limitations
Especially whether public data really supports fine-grained component detection from sketches.

## Model Location
Local path to the model and how to recreate it.

## Git Safety
Confirm no weights/datasets/secrets were committed.

## Tests
List commands and pass/fail results.

---

# 28. Mandatory Stop Conditions

Stop and ask the user before a major change if:

1. RTX 4060 is not detected;
2. CUDA/PyTorch is broken;
3. dataset licensing is unclear;
4. available annotations cannot support the intended taxonomy;
5. dataset quality is too poor for meaningful training;
6. training repeatedly causes OOM;
7. model licensing creates an unresolved deployment concern;
8. implementation would require paid infrastructure.

Do not silently make a major architecture decision.

---

# 29. Do NOT Do These Things

Do not:

- use paid cloud GPU by default;
- train on CPU when RTX 4060 is available;
- start a multi-hour training job before dataset/annotation validation;
- fabricate component labels;
- call broad jewellery classes component classes;
- commit `.pt`/`.pth`/`.onnx`/`.safetensors` model binaries;
- commit datasets;
- commit secrets;
- implement diffusion in this phase;
- implement XGBoost in this phase;
- implement OR-Tools in this phase;
- replace Supabase;
- replace authentication;
- replace the existing FastAPI architecture;
- redesign the whole frontend.

---

# 30. Exact User Workflow That Must Be Documented

The final guide should make the user's workflow approximately:

### Step 1

```bash
cd JewelMind
```

### Step 2

Activate the project's existing environment.

### Step 3

```bash
nvidia-smi
python -c "import torch; print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"
```

### Step 4

```bash
python ai/vision/training/scripts/validate_dataset.py
```

### Step 5

Open the generated annotation previews and verify them visually.

### Step 6

Run the short GPU smoke test.

### Step 7

Benchmark YOLO11s-seg and YOLO11m-seg.

### Step 8

Select the final model using accuracy, mask quality, speed and VRAM.

### Step 9

Start the real training command manually.

### Step 10

Monitor from another terminal:

```bash
nvidia-smi -l 2
```

### Step 11

Evaluate the trained model.

### Step 12

Run inference on real JewelMind sketches.

### Step 13

Review predictions and failure cases.

### Step 14

Keep `best.pt`, `last.pt`, metrics and metadata outside Git.

---

# 31. Completion Criteria

Phase 6 is complete only when:

- [ ] Phase branch created
- [ ] Dataset research documented
- [ ] Dataset license documented
- [ ] Dataset validation implemented
- [ ] Component taxonomy documented
- [ ] YOLO segmentation pipeline implemented
- [ ] RTX 4060 verification works
- [ ] GPU smoke test completed
- [ ] YOLO11s-seg and YOLO11m-seg benchmark attempted where feasible
- [ ] Final model choice documented
- [ ] Step-by-step training guide created
- [ ] Real local training can be run
- [ ] Evaluation pipeline implemented
- [ ] Inference script implemented
- [ ] Stable inference schema implemented
- [ ] AI service boundary prepared
- [ ] Model binaries excluded from Git
- [ ] Tests pass
- [ ] Existing frontend remains functional
- [ ] `PHASE_6_REPORT.md` created
- [ ] `git status` checked
- [ ] no secrets committed

---

# 32. Final Git Check

Before handoff:

```bash
git status
git diff --stat
git ls-files .env
git diff --check
```

Run the relevant backend tests, frontend typecheck/build and AI tests.

Commit Phase 6 changes, but **do not merge into `main`**. The user will review the report and merge separately.

---

# 33. Final Response After Implementation

Keep the response concise and include:

```text
Phase 6 completed.

Branch:
phase-6-yolo-component-detection

Report:
docs/phases/PHASE_6_REPORT.md

GPU:
RTX 4060 — detected/not detected

Model:
...

Dataset:
...

Training:
ready / completed / blocked

Best model:
...

Tests:
...

Known limitations:
...
```

If long training is ready, explicitly state:

> The training pipeline is ready. I have NOT started the long training run automatically. Follow the step-by-step training guide and start it manually so you can monitor your RTX 4060.

The user's local GPU and control over long-running training take priority over convenience.


# 17A. CHECKPOINTING AND RESUME — REQUIRED

Checkpointing is mandatory for all long-running YOLO training.

The training workflow MUST preserve checkpoints so that if training is interrupted by a power failure, Windows restart, crash, CUDA/runtime error, terminal interruption, or other unexpected event, the user can resume from the latest saved state instead of starting from epoch 0.

At minimum, preserve:

```text
best.pt
last.pt
```

`last.pt` is the primary checkpoint for resuming interrupted training. Do NOT assume `best.pt` is the correct resume point.

Store checkpoints in a predictable run directory such as:

```text
runs/jewellery/<run-name>/weights/
```

Configure checkpoint saving using the capabilities of the installed Ultralytics version. Do not wait until the end of a multi-hour run to save the only checkpoint.

## Resume workflow

The training guide MUST contain a dedicated:

```text
RESUMING INTERRUPTED TRAINING
```

section.

It must explain this workflow:

```text
Training reaches epoch N
        ↓
Power failure / crash / Ctrl+C
        ↓
Restart computer
        ↓
Activate the same YOLO environment
        ↓
Verify RTX 4060 + CUDA
        ↓
Confirm weights/last.pt exists
        ↓
Resume training
        ↓
Training continues from the saved state
```

For Ultralytics, use the appropriate resume mechanism for the installed version, for example:

```python
from ultralytics import YOLO

model = YOLO("runs/jewellery/<run-name>/weights/last.pt")
model.train(resume=True)
```

Do NOT blindly use this example if the installed Ultralytics version requires different syntax. Verify the installed version and document the exact working command.

## Verify the resume

After resuming, the user MUST be shown how to verify that training did not restart from epoch 0.

Check:

```text
training log
epoch number
results.csv
checkpoint metadata
run directory
```

The guide must explain the expected behavior:

```text
Epoch 1 ... Epoch 42
        ↓
INTERRUPTION
        ↓
last.pt
        ↓
resume
        ↓
Epoch 43 ...
```

rather than:

```text
Epoch 1 ... Epoch 42
        ↓
INTERRUPTION
        ↓
Epoch 1 again
```

## Preserve checkpoints

Do NOT automatically delete:

```text
last.pt
best.pt
results.csv
```

after training.

Do not delete the run directory during cleanup.

Each experiment should have a unique run name so an older checkpoint is not accidentally overwritten:

```text
yolo11s-seg-jewelmind-v1
yolo11m-seg-jewelmind-v1
yolo11m-seg-jewelmind-v2
```

## Git policy

Training checkpoints are large binary artifacts and MUST NOT be committed.

Ensure `.gitignore` covers:

```text
*.pt
*.pth
*.onnx
*.safetensors
runs/
checkpoints/
```

The Phase 6 report must confirm that model/checkpoint binaries were not committed.

