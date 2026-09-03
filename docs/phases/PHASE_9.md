# JEWELMIND — PHASE 9
# APPEARANCE LoRA TRAINING READINESS + INFRASTRUCTURE AUDIT

You are working on the JewelMind repository.

Phase 8 has already been completed and merged into `main`.

We are now beginning:

PHASE 9 — Appearance LoRA Training

IMPORTANT:
This phase is preparation and audit only.

DO NOT start model training.
DO NOT launch GPU training.
DO NOT run a training job.
DO NOT schedule training.
DO NOT automatically resume an existing training job.
DO NOT download large model checkpoints unless absolutely required for inspection.
DO NOT modify the production inference pipeline.

The actual training will be performed MANUALLY by the project owner on an NVIDIA RTX 4060 Laptop GPU with 8 GB VRAM after this phase is reviewed.

==================================================
1. OBJECTIVE
==================================================

Audit the existing JewelMind training infrastructure and make it READY for the first manual Appearance LoRA training run.

The purpose of this phase is to determine:

1. What training script currently exists.
2. Whether it is appropriate for Appearance LoRA training.
3. What dependencies it requires.
4. Whether the existing `tgpu` environment can run it.
5. What command-line arguments/settings are supported.
6. Whether checkpointing/resume works correctly.
7. Whether validation works correctly.
8. Whether mixed precision / gradient accumulation / memory optimization are implemented.
9. Whether the 8 GB RTX 4060 can reasonably run the intended configuration.
10. What exact manual command the project owner should run later.

DO NOT actually execute the training.

==================================================
2. EXISTING DATASET
==================================================

The authoritative Phase 8 dataset is:

datasets/appearance_lora/

Expected dataset:

- Total images: 164
- Training images: 147
- Validation images: 17
- Split seed: 42
- Train/validation SHA-256 overlap: 0
- Captions: 164
- Empty captions: 0

The authoritative curation source was:

datasets/curation/HUMAN_CURATION_FINAL.csv

DO NOT change the curated dataset in this phase.

DO NOT add new images.

DO NOT remove images.

DO NOT regenerate the curation.

DO NOT modify the train/validation split unless a genuine technical defect is discovered.

==================================================
3. TRAINING SCRIPT AUDIT
==================================================

Locate and inspect the current Appearance LoRA training implementation.

In particular inspect:

- scripts/train_lora.py
- related training modules
- configuration files
- requirements files
- environment files
- dataset loaders
- checkpoint utilities
- validation utilities
- LoRA implementation

Determine exactly what training architecture is currently implemented.

The expected first-stage approach is:

Stable Diffusion 1.5
        +
UNet Appearance LoRA

This is NOT ControlNet training.

The purpose of this LoRA is primarily to improve:

- jewellery material appearance
- gold/silver appearance
- gemstones
- reflections
- highlights
- product-photo appearance
- jewellery visual style

It is NOT expected to directly learn sketch-to-photo geometry correspondence.

Do not silently redesign the architecture.

If the existing script is unsuitable, document precisely why.

==================================================
4. VERIFY BASE MODEL
==================================================

Inspect how the base Stable Diffusion model is configured.

Expected base model:

runwayml/stable-diffusion-v1-5

Verify:

- model identifier
- local cache handling
- tokenizer
- text encoder
- VAE
- UNet
- scheduler
- LoRA target modules

Do not download the full model merely for inspection if it is not already available.

Do not expose credentials or secrets.

==================================================
5. VERIFY LoRA IMPLEMENTATION
==================================================

Determine:

- LoRA library being used
- target UNet modules
- rank
- alpha
- dropout
- trainable parameters
- frozen parameters
- optimizer
- scheduler
- learning rate
- weight decay
- gradient clipping
- mixed precision
- gradient checkpointing
- xFormers / memory-efficient attention if implemented
- 8-bit optimizer if implemented
- EMA if implemented
- checkpoint format

Document the actual implementation.

Do not invent settings that the code does not support.

==================================================
6. VERIFY DATA LOADING
==================================================

Inspect the dataset loader.

Verify:

- image loading
- caption loading
- tokenizer behavior
- maximum token length
- image resizing
- aspect-ratio handling
- random cropping
- center cropping
- horizontal flipping
- normalization
- shuffling
- deterministic seed
- validation loading

IMPORTANT:

Do not introduce horizontal flipping automatically.

Jewellery can be asymmetric, and horizontal flipping can change design semantics.

Do not introduce destructive center cropping.

The Phase 8 dataset intentionally preserved source aspect ratios.

If the training implementation currently performs a crop/resize operation, document exactly what it does and whether it is safe.

==================================================
7. TOKENIZATION / CAPTION SAFETY
==================================================

Verify the maximum prompt/token length supported by the SD 1.5 text encoder.

The Phase 7 rendering pipeline previously encountered a prompt-length warning.

Confirm that training captions:

- do not silently exceed the supported token length
- are tokenized consistently
- do not lose important jewellery descriptors due to truncation

If the current dataset captions are longer than the supported length, report this.

Do NOT rewrite the captions automatically in this phase.

==================================================
8. VALIDATION INFRASTRUCTURE
==================================================

Inspect the existing validation-loss implementation.

Verify:

- validation dataset is separate from training
- validation loss is calculated correctly
- validation does not update model weights
- model is switched to evaluation mode where appropriate
- validation is deterministic where intended
- validation metrics are saved
- training loss and validation loss are clearly distinguished

Do not run a full training job.

If a tiny non-training dataset-loading test is useful, it may be run.

==================================================
9. CHECKPOINT / RESUME AUDIT
==================================================

Inspect checkpoint functionality.

Verify that checkpoints preserve all necessary state:

- LoRA weights
- optimizer state
- scheduler state
- scaler state if applicable
- epoch
- global step
- gradient accumulation state where relevant
- random state if implemented

Verify checkpoint naming.

Verify resume logic.

Previously identified checkpoint/resume issues have already been fixed in the training infrastructure. Confirm that those fixes are still present.

Pay particular attention to:

- checkpoint-last parsing
- global_step
- gradient accumulation
- optimizer restore
- scheduler restore
- GradScaler restore

Do not actually resume training.

==================================================
10. RTX 4060 8 GB COMPATIBILITY AUDIT
==================================================

The target machine is:

GPU:
NVIDIA GeForce RTX 4060 Laptop GPU

VRAM:
8 GB

The Phase 7 ControlNet rendering baseline successfully ran on this GPU.

Do not claim training VRAM requirements based only on theory.

Instead inspect the actual training code and identify memory-heavy operations.

Determine a SAFE starting configuration for manual training.

Possible parameters to evaluate include:

- resolution
- batch size
- gradient accumulation
- mixed precision
- gradient checkpointing
- optimizer
- number of workers
- LoRA rank
- number of epochs
- save frequency

Do not start training to measure VRAM.

Clearly distinguish:

FACTUAL CODE FINDINGS
from
EXPECTED/ESTIMATED RESOURCE REQUIREMENTS.

==================================================
11. DEPENDENCY AUDIT
==================================================

Inspect the current environment/dependency requirements.

Determine whether the existing:

`tgpu`

Conda environment can support the training script.

Check versions of relevant packages if available:

- Python
- PyTorch
- torchvision
- CUDA
- diffusers
- transformers
- accelerate
- peft
- safetensors
- datasets
- bitsandbytes if used

Do not reinstall or upgrade packages automatically.

Do not break the existing environment.

If changes are required, document the exact changes that should be made manually.

==================================================
12. TRAINING OUTPUT STRUCTURE
==================================================

Inspect or establish a clean output convention.

Recommended:

outputs/
└── appearance_lora/
    ├── checkpoints/
    ├── logs/
    ├── validation/
    └── final/

Model artifacts must NOT be committed to Git.

Ensure appropriate `.gitignore` rules exist for:

- LoRA checkpoints
- optimizer checkpoints
- tensorboard logs
- large model artifacts
- generated validation images
- temporary training files

Do not delete existing artifacts.

==================================================
13. TESTS
==================================================

Add or update tests ONLY where needed to verify training infrastructure.

Tests may cover:

- dataset loading
- caption loading
- tokenizer handling
- configuration validation
- checkpoint discovery
- checkpoint metadata parsing
- resume configuration
- LoRA configuration
- output directory handling

DO NOT create a fake test that claims training succeeded.

DO NOT perform a real training run.

Run only safe tests that do not launch GPU training.

==================================================
14. MANUAL TRAINING COMMAND
==================================================

At the end of this phase, provide the project owner with a proposed manual training command.

IMPORTANT:

The command must NOT be automatically executed.

The report must explain every important parameter.

Example structure only:

python scripts/train_lora.py \
    --dataset ... \
    --output_dir ... \
    --resolution ... \
    --batch_size ... \
    --gradient_accumulation_steps ... \
    --learning_rate ... \
    --num_epochs ... \
    ...

DO NOT invent CLI arguments.

The command must use only arguments actually supported by the current script.

If the script needs modification before training, make those modifications first and document them.

==================================================
15. BASELINE COMPARISON PLAN
==================================================

Document how the trained LoRA will later be evaluated against the Phase 7 baseline.

The baseline is:

- SD 1.5
- ControlNet LineArt
- 512x512
- batch size 1
- 20 inference steps
- seed 42
- real jewellery sketch
- RTX 4060 Laptop GPU
- successful inference
- approximately 16.33 seconds latency
- approximately 3.33 GiB peak VRAM

The same:

- sketch
- prompt
- seed
- resolution
- ControlNet
- inference steps

should be used before/after LoRA when possible.

The evaluation should examine:

1. Jewellery category preservation
2. Geometry preservation
3. Metal appearance
4. Gemstone appearance
5. Reflections/highlights
6. Product-photo realism
7. Background quality
8. Unwanted object transformation
9. Prompt adherence

IMPORTANT:

Appearance LoRA should not be judged only by training loss.

The actual generated images matter.

==================================================
16. FILES / DOCUMENTATION
==================================================

Create:

`PHASE_9_TRAINING_READINESS_REPORT.md`

The report must contain:

1. Executive summary
2. Current training architecture
3. Training script audit
4. Dataset compatibility
5. Caption/tokenization audit
6. LoRA configuration
7. Optimizer/scheduler audit
8. Validation audit
9. Checkpoint/resume audit
10. Dependency/environment audit
11. RTX 4060 8 GB compatibility assessment
12. Recommended starting configuration
13. Exact manual training command
14. Expected output structure
15. Git/artifact safety
16. Baseline evaluation plan
17. Known risks
18. Required manual actions by project owner
19. Final readiness verdict

==================================================
17. STRICT SCOPE RULES
==================================================

DO NOT:

- train the LoRA
- launch GPU training
- resume training
- schedule training
- perform production inference
- modify Phase 7 rendering behavior
- modify the curated dataset
- acquire new data
- change the curation
- commit
- push
- merge
- expose secrets
- commit model weights

You MAY:

- inspect code
- inspect configuration
- inspect the dataset structure
- inspect metadata
- inspect dependencies
- fix genuine training-infrastructure bugs
- add safe unit tests
- update `.gitignore`
- improve documentation
- prepare the manual training command

==================================================
18. FINAL RESPONSE
==================================================

When finished, report:

PHASE 9 TRAINING READINESS: PASS / PASS WITH CHANGES / BLOCKED

Also provide:

- what was inspected
- what was changed
- tests performed
- exact training architecture
- recommended initial configuration
- exact manual command
- known risks
- whether the project owner can now manually start training

Again:

DO NOT START TRAINING.

WAIT FOR THE PROJECT OWNER TO MANUALLY RUN THE TRAINING AFTER THIS PHASE IS REVIEWED.