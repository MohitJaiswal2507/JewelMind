JewelMind — Rendering V2 Preparation Phase

Create a new Git branch:

phase-rendering-v2-preparation

IMPORTANT:
This phase is PREPARATION ONLY.

DO NOT:
- train any model
- start GPU training
- modify existing trained weights
- replace the production Rendering V1 model
- change the production AI rendering pipeline
- delete or overwrite existing datasets
- delete existing checkpoints
- commit or push anything
- fabricate metrics or training results

The goal of this phase is to thoroughly inspect the existing JewelMind rendering system and available datasets, then produce a concrete, technically justified Rendering V2 training/integration plan.

==================================================
1. FIRST: INSPECT THE EXISTING RENDERING SYSTEM
==================================================

Before creating anything, inspect the repository and document the actual current implementation.

Focus especially on:

backend/
ai/
frontend/

Find and inspect:

- current AI rendering API
- AI worker
- JewelleryRenderingPipeline
- ControlNet implementation
- Stable Diffusion / SD 1.5 loading
- Appearance LoRA loading
- rendering configuration
- category handling
- prompt construction
- conditioning image preparation
- ControlNet strength
- inference steps
- CFG
- resolution
- seed handling
- scheduler
- model loading/caching
- GPU/device handling
- output persistence
- Supabase render storage
- frontend rendering modal/page
- existing rendering service
- render history/media integration
- any existing rendering tests

Identify the exact production V1 flow.

Document it as:

Input
→ preprocessing
→ conditioning
→ model
→ ControlNet
→ LoRA
→ inference
→ output
→ storage
→ frontend

Do not assume the implementation. Inspect the actual source code.

==================================================
2. INVENTORY ALL EXISTING AI ARTIFACTS
==================================================

Inspect the repository and known local model locations.

Create an inventory containing:

A. Base models
B. ControlNet models
C. JewelMind-trained ControlNet checkpoints
D. Appearance LoRA
E. YOLO V1
F. YOLO V2
G. preprocessors/annotators
H. tokenizer/text encoder components
I. cached Hugging Face models
J. training datasets
K. rendering datasets
L. evaluation outputs
M. generated rendering examples

Known important existing artifacts include:

Production ControlNet:

outputs/controlnet_jewellery_300/controlnet_jewellery_final

Appearance LoRA:

outputs/appearance_lora/jewellery_lora_final/adapter_model.safetensors

YOLO V2:

runs/segment/runs/segment/runs/jewellery/yolo11m-seg-jewelmind-v2-continued/weights/best.pt

Existing rendering system is based on:

- Stable Diffusion 1.5
- ControlNet
- JewelMind-trained ControlNet
- Appearance LoRA
- RTX 4060 8GB

Verify these against the actual repository rather than blindly trusting this description.

For each artifact document:

- path
- type
- purpose
- approximate size if available
- whether it is production-used
- whether it can be reused for Rendering V2
- whether it should remain untouched

==================================================
3. INSPECT THE EXISTING RENDERING TRAINING HISTORY
==================================================

Inspect all existing Rendering V1 training preparation and training artifacts.

Especially inspect:

- Phase 7 diffusion + ControlNet rendering
- Phase 8 appearance LoRA preparation/training
- Phase 9 paired dataset/controlnet preparation
- Phase 10 ControlNet training/integration

Look for:

- dataset structures
- preprocessing scripts
- training scripts
- configs
- training logs
- checkpoints
- validation outputs
- evaluation results
- sample generations
- prompts
- conditioning maps
- LoRA configuration
- ControlNet configuration

Determine exactly what was learned by the existing V1 system and what its limitations are.

DO NOT retrain anything.

==================================================
4. DEFINE THE RENDERING V1 LIMITATIONS
==================================================

Based on actual code and artifacts, identify limitations that Rendering V2 should address.

Evaluate at least:

A. Sketch → Render

B. Text → Render

C. Photo → Render

D. Sketch + Text

E. Photo + Text

F. Category consistency

G. Geometry preservation

H. Fine jewellery detail

I. Material control

J. Gemstone control

K. Background/product photography quality

L. Prompt adherence

M. Conditioning strength

N. Multiple jewellery categories

O. Input image variability

P. Image resolution

Q. inference speed

R. VRAM constraints on RTX 4060 8GB

IMPORTANT:

Do not claim a feature works merely because it is planned.

Clearly separate:

IMPLEMENTED
PARTIALLY IMPLEMENTED
NOT IMPLEMENTED
PLANNED

==================================================
5. INSPECT AVAILABLE DATASETS
==================================================

Inspect ALL locally available Rendering-related datasets.

Do not download large datasets automatically.

Do not create a huge dataset automatically.

First inspect what already exists.

Relevant known datasets include:

1. Jewelry Design Dataset

Hugging Face:
sidd707/jewelry-design-dataset

Known approximate information:
~6,157 images
Categories include bracelet, earring, necklace and ring.
MIT license.

2. AI-driven jewellery dataset

Known:
~123 images
Ring / bracelet / necklace / earrings
CC0.

3. raresense jewelry DWPose dataset

Known:
~11,147 samples
target / mask / dwpose / prompt / zoom / pose_quality
MIT
contains jewellery categories including ring, bracelet, necklace, earring and some watch/multi-jewellery examples.

4. raresense Single_panel_training_flux_jewelry

Known:
~16,403 rows
source / target / mask / prompt
768x768
jewellery-oriented
includes ring / bracelet / earring / necklace and many prompt categories.

5. Existing JewelMind paired ControlNet dataset.

6. Existing Appearance LoRA dataset.

7. Any other rendering-related dataset already present locally.

IMPORTANT:

Verify dataset metadata from actual local files or existing project documentation where possible.

Do not automatically assume that every dataset is suitable.

==================================================
6. DATASET SUITABILITY AUDIT
==================================================

For every candidate Rendering V2 dataset, evaluate:

- licensing
- category coverage
- number of useful images
- image resolution
- image quality
- background quality
- jewellery visibility
- object scale
- duplicates
- near duplicates
- train/test leakage risk
- captions/prompts
- masks
- control maps
- human/body presence
- multi-jewellery scenes
- suitability for text conditioning
- suitability for image conditioning
- suitability for ControlNet
- suitability for LoRA
- suitability for product-style rendering

Create a comparison table.

Use categories:

RECOMMENDED
POSSIBLY USEFUL
NOT RECOMMENDED

Do not use datasets with unclear licensing merely because they are large.

==================================================
7. DESIGN THE RENDERING V2 ARCHITECTURE
==================================================

Design a unified Rendering V2 architecture.

The target system should eventually support:

TEXT → RENDER

SKETCH → RENDER

PHOTO → RENDER

SKETCH + TEXT → RENDER

PHOTO + TEXT → RENDER

Do NOT design five independent pipelines.

Prefer a unified architecture with modular conditioning.

Propose how the system should process:

Text conditioning
Image conditioning
Sketch conditioning
Category conditioning
Material conditioning
Gemstone conditioning
Optional negative prompts

Explain how these conditioning signals should interact.

Also determine where YOLO V2 can contribute.

For example, investigate whether YOLO V2 can provide:

- category detection
- jewellery localization
- masks
- structural hints
- automatic category inference
- crop/region extraction

Do not assume YOLO should be directly connected to diffusion if it is not technically useful.

==================================================
8. RENDERING V2 MODEL STRATEGY
==================================================

Evaluate possible approaches under the project constraints:

Budget:
₹0

GPU:
RTX 4060 Laptop GPU
8GB VRAM

Existing stack:
PyTorch
Diffusers
Stable Diffusion
ControlNet
LoRA

Consider:

A. Improve existing ControlNet

B. Train a new jewellery-specific ControlNet

C. Improve/retrain Appearance LoRA

D. Train separate LoRAs for specific attributes

E. Use IP-Adapter/image conditioning if feasible

F. Use ControlNet + LoRA + text conditioning

G. Use image-to-image as part of the photo workflow

H. Use existing pretrained components rather than training everything from scratch

For every approach explain:

- expected benefit
- VRAM requirements
- dataset requirements
- training complexity
- inference complexity
- risk
- whether it is realistic on RTX 4060 8GB
- whether it should be part of V2

Do not select a model merely because it is newer.

Prioritize something realistically trainable and deployable for this project.

==================================================
9. PROPOSE THE ACTUAL RENDERING V2 TRAINING PLAN
==================================================

Create a concrete staged training plan.

It must be similar in discipline to the successful YOLO V2 process.

For example:

Stage 0:
Dataset validation

Stage 1:
Small smoke experiment

Stage 2:
Small training experiment

Stage 3:
Validation/evaluation

Stage 4:
Full training

Stage 5:
A/B comparison against Rendering V1

Stage 6:
Integration

But determine the actual stages based on your inspection.

For each stage specify:

- model
- dataset
- training objective
- expected input
- expected output
- resolution
- batch size
- gradient accumulation
- learning rate
- optimizer
- precision
- gradient checkpointing
- expected VRAM
- approximate training duration if reasonably estimable
- success criteria
- artifacts produced

IMPORTANT:

These are PLANS only.

Do not execute training.

==================================================
10. DESIGN THE RENDERING V2 DATASET
==================================================

Propose the exact dataset structure.

For example, determine whether V2 needs:

source images
target images
masks
conditioning maps
captions
category labels
material labels
gemstone labels
metadata

Define a reproducible directory structure.

Also define:

- train split
- validation split
- test split
- leakage prevention
- duplicate detection
- category balancing
- minimum samples
- maximum samples
- resolution policy
- preprocessing
- augmentation
- caption generation
- quality filtering

Do not generate the dataset yet.

==================================================
11. CATEGORY TAXONOMY
==================================================

Rendering V2 must align with JewelMind's application categories:

0 Ring
1 Earring
2 Pendant
3 Necklace
4 Bracelet
5 Bangle
6 Brooch
7 Other Jewellery

Explain how category conditioning will work.

Do not hard-code Ring as a universal fallback.

The system should reject invalid categories rather than silently treating them as Ring.

==================================================
12. EVALUATION PLAN
==================================================

Design a proper Rendering V2 evaluation framework.

It should compare V1 vs V2 on the same evaluation set.

Evaluate:

1. Geometry preservation
2. Structural fidelity
3. Category correctness
4. Prompt adherence
5. Material correctness
6. Gemstone correctness
7. Fine detail
8. Product realism
9. Background quality
10. Hallucinated/spurious elements
11. Human/body leakage
12. Visual quality
13. inference time
14. VRAM usage

Define an objective scoring rubric.

Prefer a 1–5 scoring rubric where appropriate.

Create a fixed evaluation set.

The evaluation must include all 8 jewellery categories where sufficient data exists.

==================================================
13. ZERO-BUDGET / RTX 4060 FEASIBILITY
==================================================

Explicitly determine what is realistically possible with:

RTX 4060 Laptop GPU
8GB VRAM

Avoid proposing training that clearly requires expensive cloud GPUs.

Use techniques such as:

- fp16
- gradient checkpointing
- gradient accumulation
- memory-efficient attention / SDPA where compatible
- batch size 1 or 2 when necessary
- lower resolution for experiments
- cached latents where appropriate

Estimate VRAM and training time conservatively.

==================================================
14. IMPLEMENTATION PLAN
==================================================

After the model/data strategy, define what code should eventually be changed.

Identify:

Backend files
AI worker files
Training scripts
Dataset scripts
Configuration files
Frontend files
Tests

Clearly separate:

PREPARATION CHANGES NOW

from:

FUTURE V2 IMPLEMENTATION CHANGES

During this preparation phase, only create planning/audit artifacts.

Do not modify production rendering code.

==================================================
15. REQUIRED DELIVERABLES
==================================================

Create:

A. Rendering V2 preparation report:

PHASE_RENDERING_V2_PREPARATION_REPORT.md

It must contain:

1. Executive Summary
2. Current V1 Architecture
3. Existing Artifact Inventory
4. Existing Training History
5. V1 Limitations
6. Dataset Inventory
7. Dataset Licensing/Suitability
8. Dataset Comparison Table
9. Proposed V2 Architecture
10. Model Strategy
11. Dataset Design
12. Category Strategy
13. Training Plan
14. Evaluation Plan
15. RTX 4060 Feasibility
16. Implementation Plan
17. Risks
18. Recommended Final Approach
19. Explicit list of things NOT to do yet

B. Machine-readable inventory if useful:

ai/rendering/training/configs/rendering_v2_plan.yaml

This must be a PLAN/configuration document only.

Do not make it trigger training automatically.

C. Dataset audit if needed:

ai/rendering/training/reports/

D. Optional architecture diagram:

docs/rendering_v2_architecture.md

==================================================
16. VALIDATION
==================================================

Before finishing:

- verify all referenced paths exist
- verify model files exist
- verify dataset paths exist
- verify training logs exist
- verify the documented V1 pipeline against source code
- verify dataset licenses from available metadata/documentation
- verify no training was accidentally started
- verify no production files were changed
- verify V1 checkpoints remain untouched
- verify V2 planning files are internally consistent

Run only lightweight inspection/audit commands.

No GPU training.

==================================================
17. GIT SAFETY
==================================================

At the end run:

git status
git diff --stat

Do NOT commit.

Do NOT push.

Do NOT merge.

Report:

- current branch
- files created
- files modified
- files untouched
- GPU training performed: YES/NO
- production V1 modified: YES/NO
- datasets downloaded: YES/NO
- final recommended V2 approach
- exact next manual action after my review

==================================================
FINAL REQUIREMENT
==================================================

The final report must make one clear recommendation.

Do not give me an unfocused list of possibilities.

After inspecting the actual JewelMind implementation and available datasets, select the most realistic Rendering V2 strategy for:

- ₹0 budget
- RTX 4060 8GB
- JewelMind's existing SD1.5 + ControlNet + LoRA foundation
- all 8 jewellery categories
- Text → Render
- Sketch → Render
- Photo → Render
- future Sketch + Text
- future Photo + Text

Explain WHY this approach is recommended.

Again:

NO TRAINING.
NO GPU TRAINING.
NO PRODUCTION PIPELINE CHANGES.
NO COMMIT.
NO PUSH.

Only preparation, inspection, auditing, architecture, dataset analysis, and a concrete training plan.