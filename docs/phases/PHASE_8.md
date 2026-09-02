# JewelMind — Phase 8: Appearance-LoRA Dataset Preparation

You are working on the JewelMind project.

We have completed the dataset acquisition, reconciliation, and independent curation phases.

The authoritative final curation file is:

datasets/curation/HUMAN_CURATION_FINAL.csv

DO NOT use the older curation CSVs as the source of truth.

The final authoritative curation currently contains:

- 226 total candidates
- 164 KEEP
- 62 REJECT
- 0 REVIEW

The 164 KEEP images are the candidate source for the first JewelMind Appearance-LoRA dataset.

---

# PRIMARY OBJECTIVE

Prepare the 164 curated jewellery images into a clean, reproducible, training-ready dataset for an Appearance LoRA.

This phase is DATASET PREPARATION ONLY.

Do NOT train any model.

Do NOT start GPU inference.

Do NOT launch LoRA training.

Do NOT schedule training.

Do NOT modify the Phase 7 production rendering pipeline.

Do NOT acquire additional images.

Do NOT download additional datasets.

Do NOT silently add rejected images.

---

# SOURCE OF TRUTH

Use ONLY:

datasets/curation/HUMAN_CURATION_FINAL.csv

The only images eligible for this dataset are rows where:

final_triage = KEEP

Expected count:

164 images.

If the actual count differs from 164, STOP and report the discrepancy before preparing the final dataset.

Do not silently correct the discrepancy.

---

# EXISTING IMAGE LOCATION

The authoritative candidate images are under the existing:

datasets/curation/full_candidates/

directory.

Use the image_path information from HUMAN_CURATION_FINAL.csv.

Do not assume filenames based only on candidate IDs.

Resolve every image from the CSV.

---

# IMPORTANT DATASET PURPOSE

This is an APPEARANCE LoRA dataset.

It is intended to teach the model jewellery appearance characteristics such as:

- realistic metal appearance
- gold appearance
- silver/white-metal appearance where available
- metallic highlights
- reflections
- surface texture
- gemstone appearance
- jewellery craftsmanship
- jewellery design appearance
- realistic object photography
- historical and ornamental jewellery appearance
- different jewellery categories and forms

This dataset is NOT intended to directly teach:

sketch → exact same jewellery photograph correspondence.

The pretrained ControlNet remains responsible for structural/sketch conditioning in the current Phase 7 architecture.

---

# PHASE 8 TASKS

## 1. Inspect repository structure

Before modifying anything:

- inspect current datasets directory
- inspect existing training scripts
- inspect existing Phase 6/7 dataset utilities
- inspect existing .gitignore
- inspect existing README/documentation
- inspect existing training configuration

Do not modify unrelated functionality.

Create a short internal understanding of the current dataset/training infrastructure before implementation.

---

# 2. Validate HUMAN_CURATION_FINAL.csv

Programmatically validate:

- CSV exists
- required columns exist
- candidate IDs are unique
- candidate IDs are continuous where expected
- final_triage values are valid
- exactly 164 rows have final_triage = KEEP
- exactly 62 rows have final_triage = REJECT
- no REVIEW rows remain
- every KEEP row has an image_path
- every KEEP image exists
- every KEEP image can be opened successfully

If any check fails:

STOP and report it.

Do not silently repair source data.

---

# 3. Create the Appearance-LoRA dataset directory

Create:

datasets/appearance_lora/

Use this structure:

datasets/appearance_lora/
├── images/
├── metadata/
├── splits/
├── validation/
└── README.md

Do NOT put training images directly in the root.

---

# 4. Copy ONLY KEEP images

Copy the 164 KEEP images into:

datasets/appearance_lora/images/

Do NOT move the originals.

Do NOT delete anything from:

datasets/curation/full_candidates/

Preserve the original candidate files.

Use deterministic filenames.

Recommended format:

CAND_001.jpg
CAND_002.jpg
...

The filename must preserve the original candidate ID so every training image remains traceable.

If an image requires format normalization, document the transformation.

---

# 5. Image integrity validation

For every KEEP image, calculate and record:

- candidate_id
- source
- source_id
- original image path
- output image path
- original width
- original height
- output width
- output height
- file format
- file size
- SHA-256
- image mode/channels
- validation status

Detect:

- corrupted files
- unreadable files
- zero-byte files
- unsupported formats
- unexpected color modes
- duplicate output files

Do NOT automatically remove an image because it has an unusual aspect ratio.

Record the aspect ratio.

---

# 6. Do NOT aggressively crop jewellery

This is important.

Do NOT blindly center-crop every image into a square.

Jewellery geometry and complete silhouettes are important.

Do not remove parts of:

- rings
- earrings
- necklaces
- pendants
- bracelets
- bangles
- brooches

through destructive cropping.

If resizing is necessary, preserve the original aspect ratio.

Do not upscale tiny images merely to claim that they meet a resolution requirement.

---

# 7. Training resolution strategy

The base rendering pipeline currently uses Stable Diffusion 1.5 / ControlNet at 512×512.

However, do NOT destroy the original images just to make them 512×512.

Keep the curated source images intact.

If training-ready resized versions are created, use a separate generated dataset directory and document:

- source dimensions
- target dimensions
- resize method
- padding/cropping policy

Prefer aspect-ratio-preserving processing.

If a final training framework requires buckets or square images, prepare that in a reproducible preprocessing script rather than manually editing images.

---

# 8. Metadata

Create:

datasets/appearance_lora/metadata/dataset_metadata.csv

It must include at minimum:

- candidate_id
- image_path
- source
- source_id
- category
- category_confidence
- license
- original_width
- original_height
- output_width
- output_height
- sha256
- training_split
- caption_file
- validation_status

Every row must correspond to exactly one training image.

Expected rows:

164.

---

# 9. Captions

Create a caption for every KEEP image.

Store them separately:

datasets/appearance_lora/images/CAND_001.txt
datasets/appearance_lora/images/CAND_002.txt
...

OR use the exact caption structure required by the existing training framework if one already exists in the repository.

Before creating captions, inspect the existing training implementation.

Do not invent a completely incompatible caption format.

---

# 10. Caption philosophy

Captions should describe observable visual properties.

Do NOT create fictional information.

Do NOT hallucinate:

- gemstone type
- metal purity
- historical period
- manufacturer
- exact material
- dimensions
- provenance

unless explicitly supported by the metadata.

Useful observable concepts include:

- jewellery category
- visible metal color
- gemstone presence when clearly visible
- ornate/simple construction
- filigree
- engraved details
- chain
- cabochon
- polished metal
- textured metal
- studio/object photograph
- isolated object
- neutral/dark/light background when visually obvious

Keep captions concise and consistent.

Do NOT put candidate IDs into captions unless the existing training strategy explicitly requires them.

Do NOT introduce an arbitrary trigger token without documenting why it is required.

---

# 11. Caption generation must be reproducible

Do not manually create 164 unrelated captions without traceability.

Implement a deterministic caption-generation script.

For example:

scripts/prepare_appearance_lora_dataset.py

The script should:

1. read HUMAN_CURATION_FINAL.csv
2. select final_triage = KEEP
3. resolve image paths
4. validate images
5. copy/prepare training images
6. generate captions from metadata + allowed observable attributes
7. generate metadata
8. generate train/validation split
9. generate validation report

The script should be rerunnable without producing inconsistent results.

---

# 12. Train/validation split

Create a deterministic split.

Do NOT randomly split differently every time.

Use a fixed random seed.

Target approximately:

- 90% training
- 10% validation

For 164 images this should be approximately:

- 148 training
- 16 validation

If duplicate/similar designs are detected, avoid placing obvious same-design views into different splits where possible.

The split must be deterministic and documented.

Create:

datasets/appearance_lora/splits/train.csv
datasets/appearance_lora/splits/validation.csv

---

# 13. Duplicate leakage check

Before finalizing the split:

Check SHA-256 duplicates and perceptual similarity.

Important:

Perceptual similarity is NOT automatic proof of duplicate design.

Do not remove visually distinct jewellery merely because the hash is similar.

However, obvious duplicate images or identical representations should not appear in both train and validation.

Report any suspected leakage.

---

# 14. Category distribution

Generate a report of the 164 KEEP images by:

- ring
- earring
- pendant
- necklace
- bracelet
- bangle
- brooch
- other

Also report percentages.

Do NOT rebalance by duplicating images.

Do NOT synthetically create extra images.

Do NOT reject additional images merely to force mathematical balance.

---

# 15. Dataset quality report

Create:

datasets/appearance_lora/validation/APPEARANCE_LORA_DATASET_REPORT.md

Include:

## Dataset summary

- source candidate count
- KEEP count
- training count
- validation count
- rejected count

## Image validation

- readable
- corrupted
- unsupported
- unusual dimensions
- duplicates

## Category distribution

Table.

## Resolution distribution

Minimum / maximum / median dimensions.

## Aspect ratio distribution

Report unusual aspect ratios.

## Caption validation

Check:

- missing captions
- empty captions
- excessively long captions
- unsupported claims
- inconsistent terminology

## Duplicate/leakage validation

Report findings.

## License traceability

Preserve source/license metadata from HUMAN_CURATION_FINAL.csv.

Do NOT make new licensing claims.

---

# 16. Dataset manifest

Create:

datasets/appearance_lora/metadata/MANIFEST.json

It must contain:

- dataset name
- dataset version
- creation timestamp
- source CSV
- number of source candidates
- number of KEEP images
- train count
- validation count
- preprocessing script
- random seed
- image list
- hashes
- categories

The manifest must make it possible to trace every training image back to its CAND_ID.

---

# 17. README

Create:

datasets/appearance_lora/README.md

Explain:

- purpose
- source dataset
- 164-image selection
- directory structure
- preprocessing
- caption strategy
- train/validation split
- validation procedure
- reproducibility
- how to regenerate
- explicit statement that training has NOT been performed in Phase 8

---

# 18. Git safety

Update .gitignore if necessary.

Large generated model files must remain ignored.

Do NOT commit:

- model checkpoints
- LoRA weights
- CUDA caches
- temporary files
- generated model artifacts

Dataset images may be large.

Before deciding whether to commit or ignore them, inspect the existing repository policy and report the recommended approach.

Do NOT blindly commit hundreds of large image files if the repository is not intended to contain them.

---

# 19. TESTING

Add tests for the dataset-preparation functionality.

At minimum test:

1. KEEP filtering
2. expected 164 KEEP count
3. missing image detection
4. corrupted image detection
5. metadata row count
6. deterministic train/validation split
7. no train/validation duplicate SHA
8. caption existence
9. manifest generation
10. category counting

Run all relevant tests.

Also run:

- backend tests
- frontend TypeScript checks if applicable
- project build if applicable

Do not modify unrelated code just to make tests pass.

---

# 20. CRITICAL: NO TRAINING

This phase MUST NOT:

- execute LoRA training
- download a LoRA model
- start CUDA training
- run training epochs
- generate LoRA checkpoints
- modify the rendering model
- modify ControlNet weights

The RTX 4060 will be used manually in the next phase.

---

# 21. FINAL REPORT

Create:

PHASE_8_APPEARANCE_LORA_DATASET_REPORT.md

Include:

## 1. What was done

## 2. Source dataset

Confirm:

226 candidates
164 KEEP
62 REJECT

## 3. Prepared dataset

Confirm actual number of prepared images.

## 4. Train/validation split

Provide exact counts.

## 5. Category distribution

Table.

## 6. Image validation

Results.

## 7. Duplicate validation

Results.

## 8. Caption validation

Results.

## 9. Files created

List every important generated file.

## 10. Tests

Show exact results.

## 11. Problems encountered

Do not hide discrepancies.

## 12. Training readiness

Classify:

READY FOR MANUAL TRAINING

or

NOT READY

Explain why.

---

# IMPORTANT STOP CONDITION

If any of these occur:

- fewer than 164 KEEP rows
- missing KEEP images
- corrupted KEEP images
- unresolved duplicate leakage
- missing captions
- metadata mismatch
- inconsistent candidate IDs
- unclear image-to-candidate mapping

DO NOT silently fix the issue.

Stop and report it.

---

# FINAL RESPONSE REQUIREMENT

When finished, report:

1. exact number of images prepared
2. exact train/validation counts
3. category distribution
4. validation results
5. tests passed
6. files created
7. whether the dataset is READY for manual Appearance-LoRA training

Do NOT train the LoRA.

Do NOT commit or push anything.

Wait for my review.