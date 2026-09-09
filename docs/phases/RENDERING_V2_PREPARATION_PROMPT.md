# JewelMind — Rendering V2 Preparation & Audit

You are working on the JewelMind capstone project.

## CURRENT PROJECT STATUS

JewelMind is an AI-powered jewellery design, analysis, and production-planning application.

The current production AI stack already contains:

1. YOLO11m jewellery component segmentation — V1
2. Stable Diffusion 1.5
3. A 300-step custom jewellery ControlNet
4. A jewellery Appearance LoRA
5. Local RTX 4060 AI worker
6. FastAPI backend
7. Supabase storage
8. React + TypeScript + Vite frontend

The current Rendering V1 pipeline supports:

Sketch/Doodle
    ↓
Structural conditioning
    ↓
Stable Diffusion 1.5
    +
Jewellery ControlNet
    +
Appearance LoRA
    ↓
Rendered jewellery image

Rendering V1 has already been tested and is considered a working baseline.

DO NOT break, replace, retrain, delete, rename, or modify the V1 production artifacts.

---

# VERY IMPORTANT — THIS PHASE IS PREPARATION ONLY

## DO NOT START TRAINING

You MUST NOT:

- start ControlNet training
- start LoRA training
- start YOLO training
- run long GPU jobs
- run benchmark training
- launch diffusion training
- modify production model weights
- overwrite V1 checkpoints
- attempt to improve V1 weights

The RTX 4060 is currently being used for YOLO V2 training separately.

Rendering V2 training will happen later manually after the YOLO V2 training/evaluation is complete.

---

# DO NOT DOWNLOAD ANYTHING

You MUST NOT download:

- datasets
- Hugging Face datasets
- Kaggle datasets
- model checkpoints
- ControlNet models
- LoRA models
- Stable Diffusion models
- Git repositories
- large image collections

Use ONLY files, datasets, models, scripts, configuration, and artifacts that already exist locally in the JewelMind project or are already available in the local Hugging Face cache.

If something required for Rendering V2 does not exist locally:

DO NOT download it.

Instead, document:

- what is missing
- where it would be obtained later
- why it is required
- approximate purpose
- whether it is required for training or inference

---

# PRIMARY OBJECTIVE

Your job in this phase is to thoroughly inspect the current JewelMind Rendering V1 implementation and prepare a technically accurate plan for Rendering V2.

We need a report that allows the project owner and ChatGPT to understand exactly:

1. Where Rendering V1 currently stands
2. What data already exists locally
3. What models already exist locally
4. What training artifacts already exist
5. What preprocessing exists
6. What inference pipeline exists
7. What can be reused
8. What must be changed for Rendering V2
9. What datasets are already available locally
10. What data engineering is still required
11. How Sketch → Render V2 should work
12. How Text → Render should work
13. How Photo → Render should work
14. How all three modes should eventually share one architecture
15. What should be trained later
16. What should NOT be retrained
17. What the exact next implementation/training phases should be

DO NOT implement the complete Rendering V2 yet.

This is an AUDIT + PREPARATION phase.

---

# PROJECT SAFETY RULES

Before changing anything:

1. Inspect the current Git branch.
2. Inspect Git status.
3. Identify the current commit.
4. Identify all existing Rendering V1 files.
5. Identify all V1 model artifacts.
6. Identify all existing rendering datasets.
7. Identify all existing AI worker files.
8. Identify all rendering API files.
9. Identify all frontend rendering files.

Do not assume paths.

Find them programmatically.

---

# V1 ARTIFACTS TO LOCATE

Search the repository and local project directories for:

- ControlNet checkpoints
- ControlNet final model
- ControlNet checkpoints such as checkpoint-100 / checkpoint-300
- Appearance LoRA
- Stable Diffusion 1.5 references
- rendering outputs
- rendering datasets
- paired training data
- sketch conditioning maps
- target images
- training metadata
- inference scripts
- preprocessing scripts
- rendering service classes
- AI worker rendering code
- FastAPI rendering endpoints
- frontend rendering components

Known important V1 artifacts include:

ControlNet production model:

outputs/controlnet_jewellery_300/controlnet_jewellery_final

Appearance LoRA:

outputs/appearance_lora/jewellery_lora_final/adapter_model.safetensors

Existing paired dataset:

164 paired samples

Do not assume these are the only relevant artifacts.

Search for everything.

---

# IMPORTANT EXISTING V1 KNOWLEDGE

The current V1 ControlNet was manually trained using:

- Stable Diffusion 1.5
- pretrained lineart ControlNet
- frozen UNet
- frozen VAE
- frozen CLIP
- trainable ControlNet
- batch size 1
- gradient accumulation 4
- fp16
- gradient checkpointing
- SDPA
- learning rate 1e-5
- 300 training steps
- 512x512 conditioning
- high-resolution RGB target images

The final production model is:

outputs/controlnet_jewellery_300/controlnet_jewellery_final

Production ControlNet strength:

1.0

A/B testing showed 1.0 was slightly cleaner/tighter than 0.8.

The 300-step model was better than the 100-step model across:

- geometry
- topology
- fine detail
- material/appearance
- gemstone/prongs
- product realism

No spurious-element/hallucination issue was observed in the evaluation set.

A live smoke test successfully generated jewellery using:

- RTX 4060
- CUDA
- SD1.5
- 300-step ControlNet
- Appearance LoRA
- 512x512
- 20 steps
- seed 42

DO NOT repeat training.

DO NOT modify these artifacts.

Use this information only as baseline context and verify the actual implementation.

---

# RENDERING V2 PRODUCT GOAL

Rendering V2 should eventually support one unified AI Studio with three primary modes:

## MODE 1 — SKETCH → RENDER

User provides:

- doodle
- jewellery sketch
- canvas drawing
- structural sketch

Optional:

- jewellery category
- material
- gemstone
- style
- custom text prompt

Expected:

Sketch
→ structural conditioning
→ category-aware rendering
→ realistic jewellery render

This already exists in V1.

Rendering V2 should improve it rather than replacing the working V1 blindly.

---

# MODE 2 — TEXT → RENDER

User provides natural-language instructions such as:

"Modern platinum ring with a central emerald and six small diamonds."

or:

"Minimalist 18K yellow gold necklace with an emerald pendant."

The future pipeline should support:

Text
→ category/material/gemstone/style understanding
→ jewellery-aware generation
→ realistic render

IMPORTANT:

Do NOT pretend the current ControlNet is already a proper text-to-render system.

Determine what existing V1 components can be reused and what additional training/fine-tuning would actually be necessary.

---

# MODE 3 — PHOTO → RENDER

User uploads an existing jewellery photograph.

Example:

Photo of a gold ring

User asks:

"Convert this to platinum with a sapphire gemstone."

Potential future pipeline:

Photo
→ jewellery detection/segmentation
→ category identification
→ structural representation
→ user instruction
→ ControlNet / diffusion rendering
→ realistic redesigned jewellery

Rendering V2 must be designed so that Photo → Render can eventually use the new multi-jewellery YOLO V2 model.

Do not implement this entire feature now unless the existing architecture already supports pieces of it safely.

Document what needs to be added later.

---

# UNIFIED ARCHITECTURE

Rendering V2 should NOT become three completely separate AI systems.

We want one conceptual rendering pipeline:

Input
    ↓
Input Mode
    ├── Sketch
    ├── Photo
    └── Text
    ↓
Input Understanding
    ↓
Jewellery Category
    ↓
Material / Gemstone / Style
    ↓
Structural / Semantic Conditioning
    ↓
Jewellery-aware Diffusion
    ↓
Optional Appearance LoRA
    ↓
Rendered Image
    ↓
Supabase Storage
    ↓
Frontend Studio

The exact implementation should be determined after auditing the existing code.

---

# CATEGORY TAXONOMY

Rendering V2 should use the same unified jewellery taxonomy being used for YOLO V2:

0. Ring
1. Earring
2. Pendant
3. Necklace
4. Bracelet
5. Bangle
6. Brooch
7. Other Jewellery

Do not create random duplicate category systems.

Find the existing category enums/constants/types in the project and document whether they already match this taxonomy.

---

# DATASETS TO AUDIT

DO NOT DOWNLOAD ANYTHING.

Inspect only what already exists locally.

Known relevant data sources/artifacts may include:

## Existing V1 paired data

164 paired samples.

Inspect:

- image count
- train/validation split
- dimensions
- conditioning type
- target type
- category information
- metadata
- filenames
- preprocessing
- duplicate status

---

## Existing DWPose jewellery dataset

A local copy may already exist at:

ai/vision/datasets/raw/jewelry-dwpose

Known fields include:

- target
- mask
- dwpose
- prompt
- zoom
- pose_quality

This dataset has jewellery target images and masks.

IMPORTANT:

DWPose itself represents human pose.

Do NOT treat DWPose as jewellery structural conditioning automatically.

Determine how the target and mask can be useful for Rendering V2.

Document whether the dataset is suitable for:

- appearance training
- mask extraction
- background removal
- category metadata
- photo-to-render preparation
- ControlNet conditioning
- prompt generation

---

## Existing Single-panel jewellery dataset

If already present locally, inspect it.

Known characteristics include:

- source
- target
- mask
- prompt
- category/style information

Determine whether it is suitable for Rendering V2.

Again:

DO NOT download anything.

---

# DATASET AUDIT REQUIREMENTS

For every relevant local dataset, report:

- dataset name
- local path
- total samples
- image dimensions
- file formats
- RGB/RGBA/grayscale
- target availability
- conditioning availability
- mask availability
- prompt availability
- category availability
- material metadata
- gemstone metadata
- source metadata
- duplicate count
- corrupted files
- missing files
- unusable samples
- licensing information if already present locally
- train/val/test split
- likely Rendering V2 usage

Do not fabricate metadata.

If something is unknown:

write UNKNOWN.

---

# DO NOT BUILD THE FINAL DATASET YET

You may inspect existing data and create audit scripts/reports.

You may propose the final dataset layout.

You may create validation utilities if useful.

But DO NOT:

- copy thousands of images
- generate thousands of conditioning maps
- perform expensive preprocessing
- download additional data
- start training
- generate a large derived dataset

This phase should remain lightweight.

---

# PROPOSED RENDERING V2 DATASET

Evaluate whether this structure is appropriate:

ai/vision/datasets/rendering_v2/

    train/
        conditioning/
        target/
        metadata/

    val/
        conditioning/
        target/
        metadata/

    test/
        conditioning/
        target/
        metadata/

Do not create/populate the complete dataset unless it can be done from already-existing local files with negligible cost.

Report whether this structure should be changed.

---

# REPRESENTATION AUDIT

Determine what conditioning representations are currently available.

For example:

- lineart
- edge map
- sketch
- mask
- segmentation
- depth
- DWPose
- silhouette
- photo
- text prompt

For each representation:

1. Where does it come from?
2. Is it currently implemented?
3. Is it suitable for jewellery?
4. Can it be used by the current ControlNet?
5. Would it require a different ControlNet?
6. Would it require training?
7. Is it useful for Sketch → Render?
8. Is it useful for Photo → Render?
9. Is it useful for Text → Render?

---

# MODEL AUDIT

Identify all models currently available locally.

For each model:

- model name
- local path
- framework
- task
- parameters if known
- purpose
- V1/V2
- GPU memory requirement if known
- whether it should be reused
- whether it should be retrained
- whether it should remain frozen

Especially inspect:

- Stable Diffusion 1.5
- ControlNet
- Appearance LoRA
- YOLO V1
- YOLO V2 preparation artifacts
- any CLIP/text encoder
- any segmentation model
- any image encoder
- any preprocessing model

Do not download models.

---

# CURRENT API AUDIT

Inspect:

backend/app/api/

especially rendering-related routes.

Determine:

- current render endpoint
- request schema
- category support
- material support
- gemstone support
- prompt support
- image upload support
- sketch support
- photo support
- persistence behavior
- Supabase integration
- worker communication
- error handling
- authentication
- tenant isolation

Document what must change for Rendering V2.

Do NOT implement the complete API rewrite yet.

---

# AI WORKER AUDIT

Inspect:

ai/workers/

and rendering pipeline/service code.

Determine:

- worker startup
- queue behavior
- rendering request format
- model loading
- ControlNet loading
- LoRA loading
- inference parameters
- CUDA handling
- memory management
- image preprocessing
- output handling
- error handling

Document whether the architecture can support:

mode = sketch
mode = photo
mode = text

without duplicating model loading.

---

# FRONTEND AUDIT

Inspect the existing AI Studio/rendering UI.

Find:

- render modal
- AI rendering service
- canvas integration
- category selector
- material selector
- gemstone selector
- prompt input
- generated image display
- save behavior
- Studio media integration

Determine what already exists and what would need to change for:

[ Sketch ] [ Text ] [ Photo ]

Do NOT redesign the whole UI yet.

This is an audit/preparation phase.

---

# V1 VS V2

Create a clear comparison:

| Capability | Rendering V1 | Rendering V2 Target |
|---|---|---|
| Sketch → Render | Existing | Improved |
| Text → Render | Limited/not complete | Full |
| Photo → Render | Not complete | Full |
| Category awareness | Existing category prompt | Unified 8-category pipeline |
| Material control | Existing | Improved |
| Gemstone control | Existing | Improved |
| Appearance LoRA | Existing | Evaluate/retrain if needed |
| ControlNet | 300-step | Evaluate V2 strategy |
| YOLO | V1 | YOLO V2 |
| Multi-jewellery | Limited | Full |
| Supabase persistence | Existing | Preserve |
| FastAPI | Existing | Extend |
| AI Worker | Existing | Extend |
| RTX 4060 | Existing | Preserve |

Correct any row if the actual code differs.

---

# TRAINING PLAN — PREPARATION ONLY

Prepare a proposed future training plan.

Do NOT execute it.

The plan should answer:

## Stage R2-0
Audit V1.

## Stage R2-1
Prepare/filter existing data.

## Stage R2-2
Build category-aware metadata.

## Stage R2-3
Build conditioning representations.

## Stage R2-4
Prepare ControlNet V2 training.

## Stage R2-5
Prepare Appearance LoRA V2 if needed.

## Stage R2-6
Text-to-render training/fine-tuning strategy.

## Stage R2-7
Photo-to-render strategy.

## Stage R2-8
Evaluation.

## Stage R2-9
V1 vs V2 comparison.

## Stage R2-10
Production integration.

For every stage specify:

- objective
- inputs
- outputs
- GPU requirement
- whether training is required
- whether existing models can be reused
- expected risk
- expected storage requirements
- whether it should happen before or after YOLO V2

---

# RTX 4060 CONSTRAINT

The machine has:

NVIDIA RTX 4060 Laptop GPU
8 GB VRAM

Therefore the future Rendering V2 training plan must be realistic for 8 GB VRAM.

Prefer:

- SD1.5-based approaches
- LoRA
- ControlNet fine-tuning
- fp16
- gradient checkpointing
- SDPA
- small batch sizes
- gradient accumulation
- staged training
- 512x512 where appropriate

Avoid proposing:

- SDXL full training
- FLUX full training
- huge batch sizes
- massive full-model training
- unrealistic VRAM requirements

If a proposed method exceeds the practical limits of an 8 GB RTX 4060, explicitly flag it.

---

# IMPORTANT DATASET QUALITY RULE

Do not assume a dataset is useful merely because it contains jewellery images.

Rendering V2 requires useful relationships between:

- input/conditioning
- target image
- category
- prompt
- material
- gemstone
- style

Explain whether each existing dataset provides these relationships.

Distinguish:

1. image-only datasets
2. paired datasets
3. masked datasets
4. prompt-caption datasets
5. structural-conditioning datasets

This distinction is important.

---

# EXPECTED REPORT

Create:

PHASE_RENDERING_V2_PREPARATION_REPORT.md

The report must contain:

# 1. Executive Summary

Clearly state:

- current status
- what was inspected
- what is ready
- what is missing
- whether the project is ready for Rendering V2 data preparation
- whether training should start yet

Expected conclusion at this stage:

TRAINING NOT STARTED.

---

# 2. Current V1 Architecture

Include an accurate architecture diagram.

Example:

Frontend
    ↓
FastAPI
    ↓
AI Worker
    ↓
SD1.5 + ControlNet + LoRA
    ↓
Supabase
    ↓
Frontend

Modify it if the actual implementation differs.

---

# 3. V1 Artifact Inventory

Table:

| Artifact | Path | Exists | Purpose | Keep Untouched |
|---|---|---:|---|---:|

---

# 4. Dataset Inventory

Table:

| Dataset | Path | Samples | Paired | Mask | Prompt | Categories | Rendering V2 Use |
|---|---|---:|---:|---:|---:|---|---|

---

# 5. Model Inventory

Table:

| Model | Path | Task | V1/V2 | Reuse | Retrain Later |
|---|---|---|---|---|---|

---

# 6. Rendering Pipeline Audit

Explain the exact current flow.

---

# 7. Conditioning Audit

Explain every available conditioning representation.

---

# 8. Text-to-Render Feasibility

Explain what exists and what must be added.

---

# 9. Photo-to-Render Feasibility

Explain what exists and what must be added.

---

# 10. Multi-Jewellery Architecture

Explain how YOLO V2 should eventually integrate with Rendering V2.

Do not assume YOLO V2 is finished.

Clearly mark:

YOLO V2 = CURRENTLY TRAINING SEPARATELY.

---

# 11. Dataset Engineering Plan

Explain how existing data should eventually be converted into Rendering V2 training data.

---

# 12. Training Plan

Detailed staged plan, but DO NOT TRAIN.

---

# 13. Evaluation Plan

Define separate evaluation criteria for:

### Sketch → Render

- geometry
- topology
- fine detail
- gemstone/prongs
- material
- realism
- hallucination

### Text → Render

- prompt adherence
- category
- material
- gemstone
- style
- realism

### Photo → Render

- jewellery identity preservation
- geometry preservation
- requested modification
- unwanted changes
- realism

---

# 14. V1 Fallback Strategy

V1 must remain available until V2 is proven better.

Explain how V2 can be tested without breaking V1.

---

# 15. Risks

Identify risks such as:

- insufficient paired data
- category imbalance
- weak masks
- bad conditioning
- prompt quality
- 8 GB VRAM limitations
- overfitting
- hallucination
- material inconsistency
- photo background complexity
- multi-jewellery images
- licensing uncertainty

---

# 16. Exact Next Steps

Give a numbered sequence of what should happen after this preparation phase.

The first future steps should be something like:

1. Finish YOLO V2 training.
2. Evaluate YOLO V2 per category.
3. Complete Rendering V2 dataset engineering.
4. Validate representations.
5. Run a tiny Rendering V2 smoke/pilot training.
6. Evaluate.
7. Continue to production candidate training only if justified.
8. Integrate with YOLO V2.
9. Implement unified Studio modes.
10. Compare against V1.
11. Only then replace V1 as production default.

Adjust based on your actual findings.

---

# CODE / FILE CHANGES ALLOWED

You MAY:

- create documentation
- create audit scripts
- create lightweight validation scripts
- create configuration drafts
- create metadata schemas
- create empty directory structures if useful
- create test scaffolding
- add comments/documentation
- inspect existing code

You SHOULD NOT:

- modify V1 model files
- modify V1 checkpoints
- retrain models
- download datasets
- download models
- run long preprocessing
- create a huge derived dataset
- change production rendering behavior
- change the frontend UI substantially
- change production API behavior
- commit generated model artifacts

---

# TESTING

Run only lightweight tests necessary to understand the current system.

Do NOT run expensive GPU workloads.

If tests are already available, inspect them and report:

- existing rendering tests
- coverage relevant to V2
- missing tests

Do not change working V1 tests unless absolutely necessary.

---

# GIT SAFETY

At the beginning:

- show current branch
- show git status
- show current commit

At the end:

- show changed files
- show git diff/stat
- ensure no model weights were modified
- ensure no large dataset was accidentally added
- ensure no secrets were added

DO NOT commit.

DO NOT push.

DO NOT merge.

The project owner will review the report first.

---

# FINAL RESPONSE REQUIREMENT

When finished, provide a concise final response containing:

1. What you inspected.
2. What you found.
3. What is already ready.
4. What is missing.
5. What you created.
6. Confirmation that NO training was started.
7. Confirmation that NOTHING was downloaded.
8. Confirmation that V1 was left untouched.
9. The exact report filename.
10. The recommended next step.

STOP after producing the report.

Do not continue into training.

Do not ask to start training.

Do not automatically proceed to the next phase.

# END OF TASK