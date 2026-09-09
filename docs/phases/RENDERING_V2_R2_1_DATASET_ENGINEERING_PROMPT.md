# JewelMind — Rendering V2 R2-1 Dataset Engineering

## PHASE

Rendering V2 — R2-1 Dataset Engineering

## OBJECTIVE

Prepare the first candidate Rendering V2 training dataset using ONLY data that already exists locally.

This phase is DATA ENGINEERING ONLY.

---

# 🚨 ABSOLUTE RULES

## DO NOT TRAIN ANY MODEL

You MUST NOT:

- train ControlNet
- train LoRA
- train YOLO
- start diffusion training
- run long GPU jobs
- run model fine-tuning
- run benchmark training
- modify any model weights

YOLO V2 training is being handled separately.

Rendering V2 training will happen later and only after this dataset has been reviewed.

---

# 🚨 DO NOT DOWNLOAD ANYTHING

You MUST NOT:

- download datasets
- download images
- download models
- download Hugging Face files
- download Kaggle files
- download Roboflow files
- download checkpoints
- access external datasets for bulk acquisition

Use ONLY files that already exist locally.

If something is missing, document it instead of downloading it.

---

# 🚨 DO NOT MODIFY RENDERING V1

Rendering V1 is the working baseline.

Do NOT:

- modify V1 model weights
- overwrite V1 checkpoints
- replace V1 preprocessing
- change V1 inference behavior
- change production rendering behavior
- delete V1 datasets
- rename V1 artifacts

Rendering V2 data engineering must be isolated.

---

# CURRENT BASELINE

Previous audit report:

PHASE_RENDERING_V2_PREPARATION_REPORT.md

Rendering V1 currently has:

- Stable Diffusion 1.5
- 300-step jewellery ControlNet
- Appearance LoRA
- 164 paired ControlNet samples
- 164 Appearance LoRA samples
- local DWPose jewellery dataset
- local MET jewellery archive
- YOLO V2 dataset
- existing structural/LineArt preprocessing

Known local paths include:

datasets/controlnet_paired/

datasets/appearance_lora/

datasets/curation/

ai/vision/datasets/raw/met_jewellery/

ai/vision/datasets/raw/jewelry-dwpose/

ai/vision/datasets/jewellery_v2/

Do not assume these are the only relevant paths.

Search programmatically.

---

# PRIMARY GOAL

Create the first candidate:

ai/vision/datasets/rendering_v2/

containing high-quality paired data suitable for future jewellery ControlNet training.

The conceptual relationship is:

CONDITIONING
     ↓
TARGET JEWELLERY IMAGE

Example:

Sketch / LineArt
        ↓
Jewellery Product Image

The dataset must NOT simply be a collection of jewellery photographs.

Each training sample needs a meaningful relationship between:

- conditioning
- target
- category
- source
- metadata

---

# STEP 1 — RECHECK REPOSITORY STATE

Before doing anything:

Run:

git status

git branch --show-current

git log -1 --oneline

Record the results in the report.

Confirm that the current branch is the expected working branch.

Do NOT create a commit.

Do NOT push.

---

# STEP 2 — INVENTORY LOCAL DATA

Programmatically inspect:

## A. ControlNet V1 dataset

datasets/controlnet_paired/

Determine:

- number of samples
- conditioning files
- target files
- pairing mechanism
- dimensions
- formats
- category metadata
- prompt metadata
- duplicate status
- corruption
- existing split

---

## B. Appearance LoRA dataset

datasets/appearance_lora/

Determine:

- image count
- caption count
- caption quality
- category information
- material information
- gemstone information
- dimensions
- duplicate status

This data may be useful for later Appearance LoRA V2.

Do NOT blindly include it in ControlNet training.

---

## C. MET archive

ai/vision/datasets/raw/met_jewellery/

Inspect:

- total images
- available metadata
- category distribution
- image dimensions
- file types
- duplicate status
- image quality
- whether each image can reasonably become a rendering target

Known categories may include:

- bangle
- brooch
- other
- pendant

Do not assume these categories are correct without inspecting the metadata.

---

## D. DWPose dataset

ai/vision/datasets/raw/jewelry-dwpose/

Inspect the locally available records.

Known fields may include:

- target
- mask
- dwpose
- prompt
- zoom
- pose_quality

IMPORTANT:

DWPose is HUMAN POSE.

Do NOT use DWPose keypoints as jewellery structural conditioning.

The useful components for Rendering V2 may instead be:

- target jewellery image
- jewellery mask
- prompt
- crop/isolation information

Determine this programmatically.

---

## E. Existing curated data

datasets/curation/

Inspect:

- retained images
- rejected images
- metadata
- category
- source
- captions/titles

---

# STEP 3 — DEFINE THE RENDERING V2 TAXONOMY

Use exactly:

0 ring
1 earring
2 pendant
3 necklace
4 bracelet
5 bangle
6 brooch
7 other_jewellery

Do NOT create another category system.

Where an existing source uses:

other

normalize it to:

other_jewellery

Preserve the original category in metadata.

Example:

canonical_category: "other_jewellery"
source_category: "other"

---

# STEP 4 — DESIGN THE DATASET SCHEMA

Create:

ai/vision/datasets/rendering_v2/

with:

train/
val/
test/

Each split should contain:

conditioning/
target/

and metadata.

Preferred structure:

ai/vision/datasets/rendering_v2/

    train/
        conditioning/
        target/
        metadata.jsonl

    val/
        conditioning/
        target/
        metadata.jsonl

    test/
        conditioning/
        target/
        metadata.jsonl

Also create:

DATASET_MANIFEST.json

Do NOT populate the dataset blindly.

---

# STEP 5 — DEFINE METADATA

Every generated sample should have metadata similar to:

{
  "id": "...",
  "source_dataset": "...",
  "source_id": "...",
  "canonical_category": "ring",
  "source_category": "...",
  "conditioning_type": "lineart",
  "conditioning_path": "...",
  "target_path": "...",
  "prompt": "...",
  "material": "...",
  "gemstone": "...",
  "width": 512,
  "height": 512,
  "sha256_conditioning": "...",
  "sha256_target": "...",
  "split": "train"
}

Only include fields that are actually known.

DO NOT fabricate:

- materials
- gemstones
- categories
- prompts
- styles

Unknown values should be:

null

or:

"unknown"

according to the schema design.

---

# STEP 6 — PAIRING STRATEGY

This is the MOST IMPORTANT part of this phase.

Do not create fake pairs.

A valid ControlNet training pair requires:

conditioning image
+
corresponding target image

The conditioning must represent the geometry/structure of the target.

Valid examples:

Jewellery photo
→ lineart derived from THAT SAME PHOTO
→ same jewellery photo as target

OR

Existing sketch
→ corresponding jewellery target

OR

Existing structural conditioning
→ corresponding target

Invalid:

Random lineart
+
unrelated jewellery photo

Do NOT create those.

---

# STEP 7 — EXISTING V1 PAIRS

Preserve the existing 164 verified V1 pairs.

Determine whether they can be copied or referenced safely into Rendering V2.

Prefer non-destructive copying/symlinking/reference metadata if practical.

Do NOT modify the originals.

Record:

- how many are usable
- category distribution
- train/val/test distribution
- whether any duplicates exist with new sources

---

# STEP 8 — MET → RENDERING PAIRS

For MET images that are suitable:

1. Load the image.
2. Validate it.
3. Determine category from existing metadata.
4. Normalize category.
5. Create a structural LineArt representation using the existing local preprocessing implementation.
6. Pair that conditioning representation with the SAME source image as target.
7. Resize/pad consistently.
8. Store metadata.
9. Compute hashes.
10. Mark the source image.

IMPORTANT:

The generated lineart is derived from the target image.

This is a valid paired relationship.

Do NOT create unrelated synthetic targets.

---

# STEP 9 — DWPose → RENDERING PAIRS

For DWPose records:

Use the target image and jewellery mask where useful.

Do NOT use DWPose human keypoints as jewellery conditioning.

Evaluate whether the mask can be used to:

- isolate jewellery
- remove background
- create a cleaner target
- create a silhouette/structural representation

For each candidate:

1. Validate target.
2. Validate mask.
3. Confirm mask is non-empty.
4. Confirm jewellery occupies a meaningful portion of the image.
5. Apply mask/crop only if it improves the jewellery target.
6. Generate structural conditioning from the isolated jewellery image if appropriate.
7. Pair conditioning with the corresponding target.

Do NOT include records where the relationship is ambiguous.

---

# STEP 10 — MULTI-JEWELLERY IMAGES

Be careful with images containing:

- multiple rings
- earrings
- necklace + pendant
- bracelet + watch
- multiple jewellery pieces
- jewellery worn on humans

Do NOT blindly treat every image as a single-object training pair.

If a single target contains multiple jewellery objects:

Determine whether the object can be safely isolated.

If not:

mark the sample:

multi_object_ambiguous

and exclude it from the initial paired dataset.

Do not invent object-specific targets.

---

# STEP 11 — WATCH FILTER

Watches are NOT one of our Rendering V2 jewellery categories.

Exclude obvious watches/watch-only samples.

Do NOT map watches into:

other_jewellery

unless there is a strong project-defined reason already supported by metadata.

Default policy:

watch-only = EXCLUDE

---

# STEP 12 — IMAGE QUALITY FILTERS

Reject samples that are:

- corrupted
- unreadable
- empty
- extremely blurry
- extremely tiny
- mostly background
- jewellery not visible
- severely occluded
- irrelevant
- non-jewellery
- watch-only
- unusable multi-object images
- invalid masks
- empty masks
- invalid conditioning

Do NOT use an arbitrary quality threshold without documenting it.

Record rejection reasons.

---

# STEP 13 — MASK QUALITY

For masked DWPose images:

Calculate:

- mask area
- image area
- mask ratio
- bounding box
- foreground dimensions

Reject masks that are:

- empty
- nearly empty
- extremely fragmented
- obviously unrelated to jewellery
- too small to be useful

Report thresholds used.

---

# STEP 14 — IMAGE NORMALIZATION

For valid samples:

Target:

- RGB
- consistent output size
- preserve aspect ratio
- pad rather than distort

Preferred training resolution:

512 × 512

Conditioning:

- compatible with existing ControlNet preprocessing
- same spatial dimensions as target
- valid image format
- deterministic preprocessing

Do NOT upscale tiny images into fake high-resolution training data.

---

# STEP 15 — DEDUPLICATION

Perform:

## Exact duplicate detection

SHA-256.

## Near duplicate detection

Perceptual hash where practical.

IMPORTANT:

Deduplicate BEFORE train/val/test splitting.

No source image should appear in multiple splits.

For derived conditioning:

the target identity is the primary deduplication identity.

---

# STEP 16 — TRAIN / VAL / TEST SPLIT

Use:

70% train
20% validation
10% test

approximately.

BUT:

split by SOURCE IMAGE / SOURCE OBJECT, not randomly by derived conditioning.

This prevents leakage.

If multiple derived representations originate from one source image:

they MUST stay in the same split.

Use deterministic hashing so the split is reproducible.

---

# STEP 17 — CATEGORY BALANCE

Do NOT artificially duplicate minority classes.

First calculate the actual distribution.

Report:

- ring
- earring
- pendant
- necklace
- bracelet
- bangle
- brooch
- other_jewellery

If classes are severely imbalanced:

report it.

Do NOT automatically generate synthetic images.

Do NOT fabricate samples.

We will decide later whether balancing is necessary.

---

# STEP 18 — TARGET DATASET SIZE

Do NOT force the dataset to reach 1,200 samples.

The previous audit suggested ~1,200 as a possible target, but this is NOT a hard requirement.

Quality is more important than quantity.

Produce:

1. total valid candidates
2. total rejected
3. rejection reasons
4. final candidate count
5. category distribution
6. source distribution

If only 500 excellent pairs exist:

keep 500.

Do NOT add weak samples just to reach 1,200.

---

# STEP 19 — CONTACT SHEETS

Create lightweight contact sheets for QA.

At minimum:

- random train examples
- random validation examples
- random test examples
- each jewellery category
- examples from MET
- examples from DWPose
- existing V1 pairs
- rejected examples by major rejection reason if practical

For each contact sheet show:

conditioning | target | category

These are extremely important for manual review.

---

# STEP 20 — VALIDATION SCRIPT

Create:

ai/vision/training/scripts/validate_rendering_v2_dataset.py

It should check:

- missing conditioning
- missing target
- invalid image
- invalid dimensions
- RGB/RGBA consistency
- empty files
- duplicate targets
- duplicate conditioning
- split leakage
- category validity
- metadata validity
- mismatched pairs
- invalid paths
- missing metadata
- mask issues where applicable

Exit code:

0 = valid

non-zero = errors

Warnings should be clearly separated from errors.

---

# STEP 21 — DATASET PREPARATION SCRIPT

Create:

ai/vision/training/scripts/prepare_rendering_v2_dataset.py

Requirements:

- deterministic
- non-destructive
- resumable if practical
- clear logging
- rejection reasons
- metadata generation
- SHA-256 hashing
- deterministic train/val/test split
- no network access
- no model training
- no model downloads

The script should support a dry-run mode.

Example:

python ai/vision/training/scripts/prepare_rendering_v2_dataset.py --dry-run

Then actual preparation:

python ai/vision/training/scripts/prepare_rendering_v2_dataset.py

ONLY if it is lightweight and uses existing local data.

---

# STEP 22 — NO GPU-HEAVY PROCESSING

If existing LineArt preprocessing can run efficiently on CPU, prefer CPU.

Do NOT occupy the GPU needed for YOLO V2 training.

If LineArt preprocessing requires significant GPU memory:

DO NOT run a large batch.

Instead:

- document it
- create the script
- optionally test on ONE sample only
- stop

The priority is:

YOLO V2 training > Rendering V2 preprocessing

---

# STEP 23 — DATASET MANIFEST

Create:

ai/vision/datasets/rendering_v2/DATASET_MANIFEST.json

It should contain:

- dataset version
- creation timestamp
- source datasets
- source counts
- accepted counts
- rejected counts
- split counts
- category counts
- preprocessing version
- image resolution
- deduplication method
- split method
- validation status

Do not include absolute user-specific paths if avoidable.

---

# STEP 24 — LICENSE / SOURCE TRACKING

Do not search the internet.

Use only licensing information already present locally.

For each source, record:

- source name
- local source path
- license if known
- license evidence location if known
- usage status

If license is unknown:

license_status = unknown

Do NOT assume a license.

---

# STEP 25 — TESTING

Run:

- dataset preparation dry run
- lightweight actual preparation
- validation script
- metadata consistency checks

Do NOT run:

- ControlNet training
- LoRA training
- YOLO training
- large GPU benchmarks

---

# STEP 26 — FINAL REPORT

Create:

PHASE_RENDERING_V2_R2_1_DATASET_ENGINEERING_REPORT.md

The report must contain:

# 1. Executive Summary

State:

- preparation status
- total candidates
- final accepted pairs
- rejected pairs
- whether dataset is training-ready
- whether training was started

Expected:

TRAINING NOT STARTED.

---

# 2. Git State

Include:

- branch
- commit
- git status
- changed files

---

# 3. Source Dataset Statistics

Table:

| Source | Candidates | Accepted | Rejected | Notes |
|---|---:|---:|---:|---|

---

# 4. Final Dataset Statistics

Table:

| Split | Samples |
|---|---:|
| Train | |
| Val | |
| Test | |
| Total | |

---

# 5. Category Distribution

Table:

| Category | Train | Val | Test | Total |
|---|---:|---:|---:|---:|

---

# 6. Conditioning Distribution

Table:

| Conditioning | Samples |
|---|---:|
| LineArt | |
| Canny | |
| Mask/Silhouette | |
| Other | |

Only list representations actually created.

---

# 7. Rejection Reasons

Table:

| Reason | Count |
|---|---:|

Examples:

- corrupt
- empty mask
- tiny object
- duplicate
- ambiguous multi-object
- watch
- non-jewellery
- poor quality
- missing metadata

---

# 8. Dataset Leakage Audit

Report:

- exact duplicate leakage
- perceptual duplicate leakage
- source-image split leakage
- duplicate target count

Expected:

0 leakage.

If not zero:

STOP and clearly report the problem.

---

# 9. Pair Quality Assessment

Explain:

- how conditioning is derived
- how target is selected
- why they are correctly paired
- whether any pairing ambiguity remains

---

# 10. Category Balance

Explain whether the dataset is balanced enough for initial training.

Do not automatically fix imbalance.

---

# 11. Contact Sheets

List generated contact sheets and their paths.

---

# 12. Files Created

List every file created.

Especially:

- prepare_rendering_v2_dataset.py
- validate_rendering_v2_dataset.py
- metadata
- manifest
- contact sheets
- report

---

# 13. Files Modified

Clearly list every modified existing file.

Prefer:

NONE

If anything was modified, explain why.

---

# 14. V1 Safety Check

Explicitly confirm:

- V1 ControlNet unchanged
- V1 LoRA unchanged
- V1 datasets unchanged
- V1 inference code unchanged
- V1 production behavior unchanged

---

# 15. Training Readiness

Classify as exactly one:

NOT READY

READY FOR PILOT

READY FOR FULL TRAINING

Do NOT mark READY FOR FULL TRAINING merely because the dataset exists.

Consider:

- category balance
- pair quality
- leakage
- dataset size
- conditioning quality
- metadata completeness

---

# 16. Recommended Next Step

The recommended next step should be:

Rendering V2 Conditioning Validation / QA

NOT training automatically.

We need to review the dataset first.

---

# 🚨 FINAL STOP CONDITION

After completing this phase:

STOP.

Do NOT:

- train
- download
- push
- commit
- merge
- replace V1
- start Rendering V2 training
- automatically proceed to R2-4

The project owner will review:

PHASE_RENDERING_V2_R2_1_DATASET_ENGINEERING_REPORT.md

before any training begins.

---

# FINAL RESPONSE TO PROJECT OWNER

When done, respond briefly with:

1. Dataset engineering completed.
2. Number of accepted pairs.
3. Number of rejected samples.
4. Category distribution summary.
5. Validation result.
6. Contact sheets created.
7. Files/scripts created.
8. Confirmation that no training occurred.
9. Confirmation that nothing was downloaded.
10. Confirmation that V1 was untouched.
11. Exact report filename.
12. Recommended next step.

Then STOP.

# END