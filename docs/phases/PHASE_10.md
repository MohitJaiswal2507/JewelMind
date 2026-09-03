# JewelMind — Phase 10: ControlNet Training Infrastructure

## ROLE

You are implementing Phase 10 of the JewelMind capstone project.

This phase is ONLY for building, auditing, testing, and validating the ControlNet training infrastructure.

============================================================
CRITICAL RULE — MANUAL TRAINING ONLY
============================================================

DO NOT perform full ControlNet training.

DO NOT start:
- 100-step training
- 500-step training
- 1000-step training
- multi-epoch training
- background training
- scheduled training
- automatic training
- automatic resume of a previous training run

The actual expensive ControlNet training will be performed MANUALLY by the developer on an NVIDIA RTX 4060 Laptop GPU with 8 GB VRAM.

You may prepare the infrastructure for training and, ONLY after the infrastructure is completely validated, provide a clearly separated manual command for a future 1-step GPU smoke test.

Do not execute the real training command yourself.

============================================================
PROJECT CONTEXT
============================================================

Project:
JewelMind

Goal:
AI-powered jewellery design, analysis, rendering, and production-planning platform.

Current architecture:

PUBLIC JEWELMIND
      |
      v
Cloudflare Pages
      |
      v
FastAPI
      |
      +------> Supabase
      |
      +------> AI Queue
                  |
          +-------+-------+
          |               |
          v               v
       RTX 4060       Hugging Face
       AI Worker      ZeroGPU/free
          |               |
          +-------+-------+
                  |
                  v
              AI Result
                  |
                  v
               Storage
                  |
                  v
              User sees
              rendering

============================================================
PREVIOUS PHASES
============================================================

Phase 5:
- Sketch canvas
- Studio
- Sketch storage
- Supabase Storage
- Rendering UI foundation

Phase 6:
- Jewellery component detection
- YOLO11 segmentation
- Jewellery component taxonomy

Phase 7:
- Stable Diffusion 1.5
- ControlNet LineArt
- Sketch -> photorealistic rendering
- Local RTX 4060 inference
- Successful real GPU inference

Phase 8:
- Appearance LoRA dataset preparation
- 164 authoritative jewellery images
- 147 train
- 17 validation
- deterministic split
- zero train/validation SHA-256 overlap
- captions generated
- dataset validated

Phase 9:
- Appearance LoRA training infrastructure
- Manual LoRA smoke training
- 100-step LoRA experiment
- LoRA inference validation
- Structural conditioning investigation
- Neural LineartDetector evaluation
- Paired ControlNet dataset generation

Phase 9 is already MERGED into main.

============================================================
CURRENT PHASE
============================================================

Phase:
10

Suggested branch:

phase-10-controlnet-training

Do not create or switch branches automatically if the developer has already created the Phase 10 branch.

============================================================
PHASE 9 CONTROLNET PAIRED DATASET
============================================================

The paired dataset has already been generated and validated.

Location:

datasets/controlnet_paired/

Structure:

datasets/controlnet_paired/
├── images/
│   ├── CAND_001.jpg
│   ├── CAND_002.jpg
│   └── ...
│
├── conditioning/
│   ├── CAND_001.png
│   ├── CAND_002.png
│   └── ...
│
└── metadata/
    ├── train.jsonl
    ├── validation.jsonl
    ├── dataset_metadata.json
    └── dataset_summary.json

Dataset:

164 authoritative images

Training:
147

Validation:
17

Train/validation SHA-256 overlap:
0

Corrupted:
0

Missing:
0

Conditioning resolution:
512x512

Conditioning format:
RGB PNG

The conditioning maps were generated using the validated Phase 9 structural preprocessing pipeline.

============================================================
PHASE 9 STRUCTURAL CONDITIONING
============================================================

The recommended structural pipeline from Phase 9 is:

Input jewellery photograph
        |
        v
Normalize input
        |
        v
Letterbox resize to 512x512
        |
        v
Bilateral filtering
d=9
sigma=75
        |
        v
Neural LineartDetector
        |
        v
Noise floor threshold
< 35
        |
        v
Percentile contrast normalization
        |
        v
RGB structural conditioning image

Configuration used:

target_size = 512
noise_floor = 35
bilateral_d = 9
bilateral_sigma = 75
coarse = false
use_neural_lineart = true
device = CUDA

Phase 9 tested this pipeline on a 10-image subset and then generated the complete 164-image paired dataset.

============================================================
IMPORTANT PHASE 9 FINDING
============================================================

YOLO11 segmentation from Phase 6 was investigated as an object-isolation mechanism.

It was NOT selected as the mandatory conditioning pipeline because the model performed poorly enough on uncurated jewellery photographs:
- fragmented detections
- missed major structures
- false positives
- inconsistent masks

Therefore:

DO NOT replace the Phase 9 structural conditioning dataset with YOLO-generated conditioning.

The existing Phase 9 paired dataset is the authoritative dataset for Phase 10.

============================================================
CONTROLNET TRAINING OBJECTIVE
============================================================

The eventual training objective is:

Jewellery photograph
        |
        +----------------------+
        |                      |
        v                      v
conditioning map          target photograph
        |                      |
        v                      |
     ControlNet                |
        |                      |
        +---------> SD 1.5 <---+
                       |
                       v
                generated image

The purpose of ControlNet adaptation is NOT merely to improve jewellery material appearance.

The primary objective is:

LEARN STRUCTURAL CORRESPONDENCE BETWEEN THE CONDITIONING MAP AND THE TARGET JEWELLERY IMAGE.

The existing Appearance LoRA should NOT be treated as a substitute for ControlNet structural learning.

Phase 9 demonstrated that the Appearance LoRA improved material/style characteristics but did not reliably preserve:
- gemstone geometry
- prongs
- setting structure
- shoulder geometry
- ring head geometry
- exact jewellery topology

Therefore Phase 10 focuses on structural conditioning.

============================================================
TECHNICAL BASELINE
============================================================

Existing environment:

Conda environment:
tgpu

Hardware:

NVIDIA GeForce RTX 4060 Laptop GPU

VRAM:
8 GB

Known environment:

Python:
3.10.19

PyTorch:
2.9.0+cu130

CUDA:
13.0

torchvision:
0.24.0+cu130

diffusers:
0.36.0

transformers:
4.57.1

accelerate:
1.14.0

safetensors:
0.6.2

datasets:
4.4.1

PEFT:
0.20.0

opencv-python-headless:
5.0.0.93

controlnet-aux:
0.0.10

Existing Stable Diffusion baseline:

runwayml/stable-diffusion-v1-5

Existing ControlNet used in Phase 7:

lllyasviel/control_v11p_sd15_lineart

============================================================
ARCHITECTURAL REQUIREMENT
============================================================

Before writing new code:

AUDIT the existing repository.

Inspect:

ai/
scripts/
configs/
tests/
datasets/
requirements files
pyproject.toml
existing Phase 7 rendering code
existing Phase 9 preprocessing code
existing Phase 9 LoRA training code

Reuse existing utilities where appropriate.

DO NOT create duplicate implementations of:
- model loading
- dataset handling
- device selection
- configuration parsing
- checkpoint handling
- image normalization
- seed handling
- logging
- memory management

Prefer extending existing infrastructure.

============================================================
PHASE 10 DELIVERABLES
============================================================

Implement the following.

------------------------------------------------------------
1. CONTROLNET DATASET LOADER
------------------------------------------------------------

Create a robust paired dataset loader.

It must load:

conditioning image
target image
caption/prompt
metadata

from:

datasets/controlnet_paired/metadata/train.jsonl

and:

datasets/controlnet_paired/metadata/validation.jsonl

Requirements:

- deterministic
- explicit train/validation split
- no random reassignment
- verify paths
- fail clearly on missing files
- RGB conversion
- consistent tensor dimensions
- conditioning image and target image must remain aligned
- preserve metadata
- support DataLoader
- support batch size 1

Do not silently ignore broken samples.

Provide clear validation errors.

------------------------------------------------------------
2. JSONL VALIDATION
------------------------------------------------------------

Implement dataset metadata validation.

Validate:

- JSON syntax
- required fields
- image path exists
- conditioning path exists
- target image readable
- conditioning image readable
- dimensions valid
- RGB compatibility
- train/validation separation
- duplicate IDs
- duplicate file references
- SHA-256 leakage where practical

Do not modify the authoritative dataset while validating it.

------------------------------------------------------------
3. CONTROLNET TRAINING CONFIGURATION
------------------------------------------------------------

Create a dedicated configuration.

Suggested:

configs/controlnet_jewellery.yaml

Configuration should explicitly define:

base_model:
    runwayml/stable-diffusion-v1-5

controlnet:
    architecture:
        Stable Diffusion 1.5 compatible
    conditioning:
        lineart / structural
    conditioning_channels:
        3

dataset:
    train_dir:
    validation_dir:
    train_metadata:
    validation_metadata:

training:
    resolution: 512
    batch_size: 1
    gradient_accumulation_steps: appropriate safe default
    mixed_precision: fp16
    gradient_checkpointing: true
    max_train_steps: configurable
    learning_rate: configurable
    checkpointing_steps: configurable
    validation_steps: configurable
    seed: 42

memory:
    enable_gradient_checkpointing: true
    enable_memory_efficient_attention: true where supported
    allow_tf32: configurable
    attention_slicing: configurable

The exact values must be based on the existing repository conventions and actual RTX 4060 constraints.

Do not blindly copy configuration from generic internet examples.

------------------------------------------------------------
4. CONTROLNET MODEL SETUP
------------------------------------------------------------

Implement model initialization for:

Stable Diffusion 1.5
+
ControlNet

Use Diffusers-compatible architecture.

The training implementation should make it clear which components are:

TRAINABLE:
- ControlNet

FROZEN:
- VAE
- text encoder
- base UNet, unless there is a strong repository-specific reason otherwise

The goal is ControlNet adaptation, not full Stable Diffusion retraining.

Do not silently train the entire SD 1.5 model.

------------------------------------------------------------
5. MEMORY OPTIMIZATION
------------------------------------------------------------

The hardware target is:

RTX 4060 Laptop
8 GB VRAM

Therefore the infrastructure MUST prioritize memory safety.

Use where compatible:

- fp16
- batch size 1
- gradient accumulation
- gradient checkpointing
- memory-efficient attention / SDPA
- VAE memory optimizations
- explicit device handling

Do NOT assume xformers is installed.

If xformers is absent, use PyTorch SDPA or another supported native mechanism.

Do not add heavyweight dependencies without justification.

Do not install packages automatically.

If a package is required, report it to the developer and provide the exact uv command separately.

------------------------------------------------------------
6. TRAINING LOOP
------------------------------------------------------------

Implement a correct ControlNet training loop.

Conceptually:

conditioning image
        ↓
ControlNet
        ↓
residuals
        ↓
frozen SD1.5 UNet
        ↓
noise prediction
        ↓
MSE loss against target noise

Use standard diffusion training logic compatible with SD 1.5.

Important:

The conditioning image is NOT the target.

The target is the original jewellery photograph.

The conditioning image controls the generation.

The model should learn:

conditioning structure
        ->
target jewellery appearance/structure

Do not accidentally train:

conditioning -> conditioning

or:

target -> target

------------------------------------------------------------
7. PROMPT HANDLING
------------------------------------------------------------

Use the captions/prompts already present in the paired metadata.

Do not create an entirely new captioning system unless required.

Ensure tokenizer behavior is safe.

Avoid the CLIP prompt truncation problem previously encountered during Phase 7.

If prompts exceed tokenizer limits:
- truncate safely
- log the behavior
- do not crash

------------------------------------------------------------
8. NOISE / SCHEDULER
------------------------------------------------------------

Use the appropriate SD 1.5 training scheduler/noise formulation.

Make all relevant scheduler settings explicit.

Ensure:
- random timestep sampling
- noise addition
- correct latent scaling
- correct prediction target
- reproducible seed behavior

Do not invent a custom diffusion objective.

------------------------------------------------------------
9. CHECKPOINTING
------------------------------------------------------------

Implement safe checkpoint support.

Requirements:

- checkpoint at configurable intervals
- save ControlNet weights
- save optimizer state
- save scheduler state
- save scaler state if applicable
- save global step
- save training configuration
- support resume

Example:

outputs/controlnet_jewellery/
    checkpoints/
        checkpoint-200/
        checkpoint-400/
        ...
    final/

Do not delete existing checkpoints.

Do not overwrite unrelated experiments.

Do not automatically resume training.

Resume must be explicitly requested by the developer.

------------------------------------------------------------
10. VALIDATION
------------------------------------------------------------

Implement validation without modifying model weights.

Validation should include:

- validation loss
- optional deterministic validation image generation
- fixed seed
- fixed validation samples
- conditioning image saved alongside output
- target image saved/referenced
- generated image saved

A useful validation structure:

outputs/controlnet_jewellery/validation/
    step-XXXX/
        sample_001_conditioning.png
        sample_001_target.png
        sample_001_generated.png

Do not run expensive validation training automatically.

------------------------------------------------------------
11. TRAINING METRICS
------------------------------------------------------------

Log:

- global step
- epoch
- train loss
- validation loss
- learning rate
- samples/step
- elapsed time
- GPU memory where practical
- checkpoint location

Do not report a model as "good" merely because loss decreases.

Visual validation remains necessary.

------------------------------------------------------------
12. REPRODUCIBILITY
------------------------------------------------------------

Implement deterministic seed handling where practical.

Default seed:

42

Seed:
- Python
- NumPy
- PyTorch
- CUDA

where compatible.

Record:
- seed
- config
- git branch
- dataset metadata
- base model
- ControlNet initialization
- training steps

------------------------------------------------------------
13. TRAINING ENTRYPOINT
------------------------------------------------------------

Create a clear entrypoint consistent with the existing project.

For example:

scripts/train_controlnet.py

or extend an existing training entrypoint if that is cleaner.

The command should support configuration overrides such as:

--config
--max_train_steps
--output_dir
--learning_rate
--resume_from_checkpoint

Do NOT automatically run the command.

------------------------------------------------------------
14. SMOKE-TEST MODE
------------------------------------------------------------

Provide a dedicated smoke-test mode.

Smoke test must mean:

- load dataset
- load models
- load one batch
- perform one forward pass
- perform one backward pass
- perform one optimizer step
- save a temporary test checkpoint
- report GPU memory
- exit

Smoke test must NOT:
- continue training
- loop for multiple steps
- automatically resume
- start a long-running process

Suggested interface:

--max_train_steps 1

or a dedicated:

--smoke_test

Use whichever fits the existing training architecture better.

IMPORTANT:

Antigravity must NOT execute this GPU smoke test automatically.

After the code is complete, provide the developer with the exact command to run manually.

------------------------------------------------------------
15. TESTS
------------------------------------------------------------

Add automated tests for:

Dataset:
- JSONL parsing
- missing file handling
- image loading
- conditioning loading
- RGB conversion
- tensor dimensions
- deterministic indexing

Model:
- configuration loading
- ControlNet initialization path
- trainable/frozen parameter verification

Training:
- one-batch shape compatibility
- noise/timestep compatibility
- forward pass where practical
- loss calculation
- optimizer setup
- checkpoint serialization

Memory:
- configuration correctly enables checkpointing
- fp16 configuration
- no accidental full-model trainability

DO NOT require an 8 GB GPU for unit tests.

Use mocks/stubs where appropriate.

------------------------------------------------------------
16. TRAINABLE PARAMETER AUDIT
------------------------------------------------------------

This is mandatory.

At initialization print/report:

Total parameters
Trainable parameters
Frozen parameters

Explicitly verify that:

ControlNet parameters:
TRAINABLE

Base UNet:
FROZEN

VAE:
FROZEN

Text encoder:
FROZEN

If the implementation intentionally differs, document why.

A silent accidental full-model fine-tune is unacceptable.

------------------------------------------------------------
17. GPU MEMORY REPORT
------------------------------------------------------------

When running the manual smoke test, report:

GPU name
VRAM total
VRAM allocated
VRAM reserved
peak VRAM
CUDA availability

The code should fail clearly if CUDA is required but unavailable.

Do not silently fall back to CPU for the actual training path.

------------------------------------------------------------
18. ARTIFACT / GIT SAFETY
------------------------------------------------------------

Do NOT commit:

- model weights
- generated images
- training checkpoints
- LoRA adapters
- ControlNet checkpoints
- Hugging Face cache
- CUDA cache
- large temporary datasets
- .env
- secrets

Review .gitignore.

Add appropriate patterns if missing.

The authoritative dataset metadata should remain tracked only if the existing repository policy already permits it.

Do not delete or rewrite Phase 9 artifacts.

------------------------------------------------------------
19. DOCUMENTATION
------------------------------------------------------------

Create:

PHASE_10_CONTROLNET_TRAINING_READINESS_REPORT.md

The report must contain:

1. Executive summary
2. Existing infrastructure audit
3. Dataset audit
4. Model architecture
5. Trainable/frozen parameter policy
6. Memory strategy
7. Training configuration
8. Checkpoint strategy
9. Validation strategy
10. Test results
11. GPU compatibility
12. Known limitations
13. Manual training instructions
14. Exact manual smoke-test command
15. What was NOT executed
16. Files changed
17. Final readiness status

The report MUST clearly say:

"Full ControlNet training was NOT executed in Phase 10."

------------------------------------------------------------
20. DO NOT ALTER PHASE 9 DATA
------------------------------------------------------------

The following is authoritative:

datasets/controlnet_paired/

Do not:
- regenerate it
- replace it
- delete samples
- reorder train/validation membership
- modify conditioning images
- modify target images

unless a serious integrity bug is discovered.

If a problem is discovered, STOP and report it rather than silently changing the dataset.

============================================================
CRITICAL DESIGN DECISION
============================================================

Do not combine Appearance LoRA training and ControlNet training into one training operation in this phase.

The first ControlNet experiment should establish whether ControlNet alone can learn structural correspondence.

The eventual experimentation sequence should be:

Experiment A:
Base SD1.5 + pretrained ControlNet

Experiment B:
Fine-tuned jewellery ControlNet

Experiment C:
Fine-tuned jewellery ControlNet + Appearance LoRA

Only compare B and C after B is working.

Do not implement a complicated combined training system prematurely.

============================================================
EXPECTED TRAINING STRATEGY
============================================================

The eventual manual experiments will be staged.

Do NOT execute them now.

Planned future sequence:

Stage 0:
1-step GPU smoke test

Stage 1:
very small manual training experiment

Stage 2:
controlled training experiment

Stage 3:
larger training run if visual results justify it

Stage 4:
compare against:
- Phase 7 pretrained ControlNet
- Appearance LoRA
- ControlNet fine-tune
- ControlNet + Appearance LoRA

No assumption should be made that more steps automatically produce better results.

============================================================
QUALITY GATES
============================================================

Phase 10 is NOT READY if:

- dataset loader is untested
- conditioning/target alignment is wrong
- train/validation leakage exists
- ControlNet is not the trainable component
- base UNet is accidentally trainable
- VAE is accidentally trainable
- text encoder is accidentally trainable
- checkpoint resume is broken
- fp16 configuration is broken
- gradient checkpointing is broken
- smoke-test path is missing
- tests fail
- configuration is ambiguous
- training automatically starts
- large training runs are executed automatically

Phase 10 can be marked:

READY FOR MANUAL GPU SMOKE TEST

only when:

- dataset loader passes
- model initialization passes
- parameter audit passes
- one-batch forward/backward path is implemented
- checkpoint path works
- tests pass
- configuration is reproducible
- RTX 4060 memory strategy is documented
- no full training was executed

============================================================
IMPORTANT — DO NOT OVERENGINEER
============================================================

This is a capstone project.

Prefer:
- simple
- understandable
- reproducible
- maintainable
- well-tested

over:

- overly abstract frameworks
- unnecessary distributed training
- complex orchestration
- cloud training
- paid services
- unnecessary dependencies

The developer has ₹0 budget.

The RTX 4060 Laptop GPU is the primary manual training hardware.

============================================================
IMPORTANT — DO NOT USE PAID SERVICES
============================================================

Do not introduce:
- paid APIs
- paid GPU services
- paid model hosting
- paid datasets
- commercial AI APIs

Use existing open-source tooling.

============================================================
IMPORTANT — UV
============================================================

If a dependency is actually missing:

DO NOT install it automatically.

First report:

PACKAGE REQUIRED:
<package>

WHY:
<reason>

Then provide the exact:

uv pip install <package>

command for the developer.

Existing environment:

tgpu

============================================================
WORKFLOW
============================================================

Follow this order:

STEP 1
Audit repository.

STEP 2
Audit Phase 9 paired dataset.

STEP 3
Audit existing Phase 7 rendering and Phase 9 training utilities.

STEP 4
Design the minimal ControlNet training architecture.

STEP 5
Implement dataset loader.

STEP 6
Implement configuration.

STEP 7
Implement model initialization.

STEP 8
Implement trainable/frozen parameter verification.

STEP 9
Implement training loop.

STEP 10
Implement checkpoint/resume.

STEP 11
Implement validation.

STEP 12
Implement smoke-test mode.

STEP 13
Add automated tests.

STEP 14
Run CPU/unit tests where possible.

STEP 15
Review .gitignore/artifact safety.

STEP 16
Generate the readiness report.

STOP.

Do NOT run full training.

Do NOT automatically run the GPU smoke test.

============================================================
FINAL OUTPUT REQUIRED FROM YOU
============================================================

At the end provide:

1. Short implementation summary
2. Files created
3. Files modified
4. Tests executed
5. Test results
6. Dataset integrity status
7. Trainable/frozen parameter status
8. Memory optimization status
9. Git safety status
10. Whether GPU smoke test was executed
11. Whether full training was executed
12. Exact manual GPU smoke-test command
13. Recommended next action

The final status must be one of:

NOT READY

READY FOR MANUAL GPU SMOKE TEST

READY FOR MANUAL TRAINING

For this phase, the desired final status is:

READY FOR MANUAL GPU SMOKE TEST

NOT:

READY FOR MANUAL TRAINING

because the actual smoke test must still be manually performed and reviewed by the developer.

============================================================
ABSOLUTE FINAL RULE
============================================================

DO NOT TRAIN THE MODEL.

DO NOT START A LONG-RUNNING GPU PROCESS.

DO NOT AUTOMATICALLY RUN TRAINING.

DO NOT DELETE OR MODIFY PHASE 9 DATA.

BUILD THE INFRASTRUCTURE.
TEST THE INFRASTRUCTURE.
REPORT THE INFRASTRUCTURE.
THEN STOP.

The developer will manually run the GPU smoke test after reviewing your report.