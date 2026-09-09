# RENDERING V2 — R2-2 CONTROLNET ARCHITECTURE & TRAINING PIPELINE INTEGRATION

You are working on the JewelMind project.

Current branch:
phase-multi-jewellery-yolo-v2-training

Previous phase:
R2-1 Dataset Engineering

R2-1 is COMPLETE and APPROVED.

Dataset:
ai/vision/datasets/rendering_v2/

Current validated dataset:
- 1,429 conditioning-target pairs
- 994 train
- 289 validation
- 146 test
- 8 categories:
  ring
  earring
  pendant
  necklace
  bracelet
  bangle
  brooch
  other_jewellery
- 512x512 RGB PNG
- Canny conditioning
- metadata.jsonl
- DATASET_MANIFEST.json
- validation passed with 0 errors
- no cross-split leakage

==================================================
OBJECTIVE
==================================================

Prepare the complete Rendering V2 ControlNet training pipeline.

IMPORTANT:

DO NOT start full GPU training.

DO NOT run a 100/300/500-step training job.

DO NOT download any new datasets or models.

DO NOT modify Rendering V1 production artifacts.

DO NOT modify the existing V1 ControlNet or V1 Appearance LoRA.

This phase is TRAINING PIPELINE INTEGRATION ONLY.

The only GPU work permitted is a very small loader/model smoke test if absolutely required, and it must NOT become a real training run.

==================================================
1. AUDIT EXISTING RENDERING V1
==================================================

Inspect the existing V1 implementation and document:

- base Stable Diffusion model
- ControlNet model
- existing 300-step ControlNet
- existing checkpoints
- Appearance LoRA
- tokenizer/text encoder configuration
- VAE
- scheduler
- image preprocessing
- conditioning preprocessing
- image resolution
- precision
- optimizer
- learning rate
- gradient accumulation
- gradient checkpointing
- batch size
- checkpoint format
- resume mechanism
- inference configuration

Do not modify V1.

The existing V1 300-step model must remain usable as a fallback/baseline.

==================================================
2. AUDIT RENDERING V2 DATASET
==================================================

Inspect:

ai/vision/datasets/rendering_v2/

Verify programmatically:

- train/val/test structure
- conditioning files
- target files
- metadata.jsonl
- category values
- source values
- image dimensions
- RGB channels
- conditioning/target pairing
- missing files
- corrupt files
- duplicate files
- category distribution
- source distribution

Do not regenerate the dataset unless a genuine blocking corruption is found.

Do not download anything.

==================================================
3. DESIGN THE V2 TRAINING ARCHITECTURE
==================================================

Use the existing SD1.5 + ControlNet architecture as the starting point because it already runs successfully on the RTX 4060 8GB.

Design a V2 architecture for:

conditioning image
        +
category/material/gemstone/style prompt
        ↓
Stable Diffusion 1.5
        +
ControlNet
        +
optional Appearance LoRA
        ↓
photorealistic jewellery image

The architecture must support all eight categories.

Do NOT create eight separate models.

Use one unified category-aware model.

The category should be represented through text conditioning.

==================================================
4. TRAINING CONFIGURATION
==================================================

Create a dedicated Rendering V2 training configuration.

Do not overwrite V1 configurations.

Suggested initial configuration:

- Base model: existing local SD1.5
- ControlNet: existing pretrained lineart/Canny-compatible ControlNet
- Resolution: 512x512
- Batch size: 1 or 2 depending on actual VRAM
- Gradient accumulation: 4 if needed
- FP16: enabled
- Gradient checkpointing: enabled
- xFormers/SDPA if already supported
- Learning rate: approximately 1e-5
- AdamW
- cosine scheduler
- warmup
- checkpoint saving
- deterministic seed
- workers=0 on Windows

Do NOT blindly copy these values if the existing V1 implementation uses a safer configuration.

Explain the final chosen values.

==================================================
5. DATA LOADER
==================================================

Create a dedicated Rendering V2 dataset loader.

It must:

1. Read metadata.jsonl.
2. Load conditioning image.
3. Load target image.
4. Verify pairing.
5. Normalize images correctly.
6. Convert conditioning to the expected ControlNet format.
7. Convert target to the expected diffusion training format.
8. Tokenize the prompt.
9. Preserve category metadata.
10. Preserve source metadata.

The loader must fail clearly on invalid samples.

Do NOT silently substitute missing images.

==================================================
6. PROMPT HANDLING
==================================================

Create a robust prompt composition system.

The prompt must support:

- category
- material
- gemstone
- style
- setting
- optional descriptive text

Example:

"jewelmind professional studio photograph of a luxury solitaire ring, 18k yellow gold, brilliant diamond, prong setting, photorealistic jewellery product photography"

Do NOT hardcode one category.

Do NOT force every sample to be a ring.

Handle the existing metadata honestly.

If material/gemstone information is unavailable, do not invent detailed attributes.

Use available metadata and reasonable generic jewellery wording only where necessary.

==================================================
7. CONTROLNET CONDITIONING
==================================================

Verify that the current conditioning images are compatible with the selected ControlNet.

Important:

R2-1 produced Canny conditioning.

Do NOT incorrectly use DWPose human-pose maps as ControlNet jewellery conditioning.

The training pipeline must consume the actual Rendering V2 conditioning images.

Document:

- conditioning value range
- channels
- normalization
- resize behavior
- expected ControlNet input format

==================================================
8. VRAM SAFETY
==================================================

The target GPU is:

NVIDIA RTX 4060 Laptop GPU
8GB VRAM

Design the training pipeline specifically for this constraint.

Implement/check:

- fp16
- gradient checkpointing
- gradient accumulation
- memory-efficient attention if already available
- CUDA cache handling where appropriate
- batch-size fallback
- safe checkpointing

Do not increase VRAM requirements unnecessarily.

The pipeline must be able to resume after interruption.

==================================================
9. PILOT CONFIGURATION
==================================================

Create a tiny pilot configuration.

The pilot must be intentionally small.

Example:

- 1–2 epochs or equivalent tiny run
- very small subset of the training data
- batch 1
- 512x512
- fp16
- gradient checkpointing

The purpose is ONLY to verify:

dataset loader
→ tokenizer
→ VAE
→ text encoder
→ ControlNet
→ forward pass
→ loss
→ backward pass
→ optimizer step
→ checkpoint save
→ checkpoint resume

Do NOT run this pilot automatically if it could take significant time.

Prepare the exact command for me to run manually.

==================================================
10. CHECKPOINT / RESUME DESIGN
==================================================

Implement or verify robust checkpointing.

A checkpoint should preserve enough state to resume:

- ControlNet weights
- optimizer
- scheduler
- scaler if used
- global step
- epoch
- configuration

The pipeline must distinguish:

- fresh V2 training
- resume V2 training
- V1 baseline model

Never overwrite V1 checkpoints.

==================================================
11. EVALUATION HOOKS
==================================================

Prepare evaluation support for:

### Structural
- geometry
- topology
- edge/conditioning adherence

### Jewellery details
- gemstones
- prongs
- clasps
- chains
- links
- ornamental details

### Appearance
- material
- gemstone appearance
- photorealism

### Category
- ring
- earring
- pendant
- necklace
- bracelet
- bangle
- brooch
- other_jewellery

### Failure modes
- category collapse
- ring bias
- hallucinated jewellery
- missing components
- malformed chains
- malformed bangles
- incorrect gemstone placement
- excessive dark edge artifacts

Prepare the evaluation code/configuration but do not perform a full evaluation yet.

==================================================
12. V1 BASELINE PROTECTION
==================================================

Explicitly verify that these remain untouched:

- existing V1 ControlNet
- V1 300-step checkpoint
- V1 Appearance LoRA
- existing paired V1 dataset
- current production rendering path

Rendering V2 must be isolated.

==================================================
13. EXPECTED FILES
==================================================

Create only the necessary V2 training infrastructure.

Suggested structure:

ai/
  rendering/
    training/
      rendering_v2_dataset.py
      train_rendering_v2.py
      evaluate_rendering_v2.py
      config_rendering_v2.yaml
      README.md

Use the project's existing organization if equivalent files already exist.

Do not create duplicate implementations unnecessarily.

Also create:

PHASE_RENDERING_V2_R2_2_TRAINING_PIPELINE_REPORT.md

==================================================
14. TESTING
==================================================

Run lightweight tests only.

Verify:

- imports
- configuration loading
- dataset discovery
- metadata parsing
- sample loading
- tensor shapes
- prompt tokenization
- ControlNet compatibility
- model initialization if safe
- checkpoint path handling

Do NOT launch long training.

Report exact results.

==================================================
15. IMPORTANT: NO FULL TRAINING
==================================================

At the end of this phase STOP.

Do NOT start:

- 50 epoch training
- 100 step training
- 300 step training
- 500 step training
- full dataset training

I will manually start the actual training after reviewing your report.

==================================================
16. FINAL REPORT
==================================================

Create:

PHASE_RENDERING_V2_R2_2_TRAINING_PIPELINE_REPORT.md

Include:

1. Existing V1 architecture
2. V2 architecture
3. Dataset integration
4. Dataset loader
5. Prompt system
6. ControlNet conditioning
7. Training configuration
8. VRAM strategy
9. Checkpoint/resume strategy
10. Evaluation design
11. Files created/modified
12. Tests performed
13. V1 preservation verification
14. Exact manual pilot command
15. Exact manual production-training command
16. Expected approximate VRAM usage
17. Expected risks
18. Final readiness status

The final status must be one of:

READY FOR PILOT

or

BLOCKED

Do not claim READY FOR PRODUCTION TRAINING unless the report provides evidence supporting that conclusion.

==================================================
GIT RULE
==================================================

DO NOT commit.

DO NOT push.

DO NOT merge.

Leave the branch ready for my review.

STOP after producing the report.