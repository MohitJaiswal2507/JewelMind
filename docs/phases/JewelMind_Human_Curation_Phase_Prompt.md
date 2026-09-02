# JewelMind — Human Curation Phase Prompt

The ~300-candidate acquisition is APPROVED.

The acquisition pipeline itself has PASSED validation.

IMPORTANT:
WE ARE NOW ENTERING HUMAN CURATION.

DO NOT TRAIN ANY MODEL.
DO NOT RUN LoRA TRAINING.
DO NOT RUN ControlNet TRAINING.
DO NOT RUN GPU DIFFUSION INFERENCE.
DO NOT MODIFY THE PRODUCTION RENDERING PIPELINE.
DO NOT DOWNLOAD ADDITIONAL DATA YET.
DO NOT COMMIT OR PUSH.

The current pool is:
- 302 fetched
- 226 technically valid/retained
- 188 jewellery relevant
- 38 jewellery uncertain
- 102 DISTINCT
- 124 NEAR_DUPLICATE_REVIEW_REQUIRED
- 0 SHA-256 exact duplicates
- 9/9 tests passing

==================================================
1. CREATE A HUMAN CURATION WORKFLOW
==================================================

Do NOT automatically select the final 150–200 images.

Create a human-reviewable curation dataset/table containing ALL 226 retained candidates.

For every candidate include:

- image preview/path
- source
- source ID
- title
- category
- category confidence
- jewellery relevance
- technical status
- duplicate status
- dHash
- aHash
- SHA-256
- license
- dimensions

Add manual fields:

- jewellery_clearly_visible
- single_primary_object
- sufficient_object_size
- useful_geometry
- minimal_occlusion
- useful_metal_appearance
- gemstone_detail_applicable
- useful_lighting
- useful_background
- category_confidence_manual
- visual_quality
- design_diversity
- training_usefulness
- final_triage

Allowed values:

KEEP
REVIEW
REJECT

==================================================
2. IMPORTANT — DO NOT REQUIRE GEMSTONES
==================================================

The gemstone criterion is CONDITIONAL.

For jewellery without gemstones:

gemstone_detail_applicable = NOT_APPLICABLE

Do not reject a high-quality plain-metal jewellery item merely because it has no gemstone.

==================================================
3. NEAR-DUPLICATE HANDLING
==================================================

The 124 near-duplicate candidates must remain available for human review.

Do NOT automatically reject them.

However, the final training dataset should avoid redundant photographs of the same object/design.

Add a manual field:

design_redundancy:
- UNIQUE_DESIGN
- SAME_DESIGN_DIFFERENT_VIEW
- SAME_DESIGN_REDUNDANT
- UNKNOWN

If two images show the same jewellery object/design from slightly different angles, the curator should generally KEEP the strongest representation and REJECT redundant copies.

Do not delete the source files during this stage.

==================================================
4. CATEGORY NORMALIZATION
==================================================

Use only:

ring
earring
pendant
necklace
bracelet
bangle
brooch
other

Do not use combined labels.

Do not force ambiguous objects into a category.

==================================================
5. CATEGORY BALANCE
==================================================

Do NOT artificially duplicate data.

Do NOT oversample categories yet.

During human curation, report:

- candidates per category
- KEEP per category
- REVIEW per category
- REJECT per category

Pay special attention to:
- bangle underrepresentation
- other overrepresentation

The final dataset should be diverse, but natural.

==================================================
6. TRAINING-QUALITY CRITERIA
==================================================

Use the following evaluation criteria:

A. Jewellery clearly visible
B. Single primary jewellery object
C. Object sufficiently large
D. Useful geometry
E. Minimal occlusion
F. Useful metal/material appearance
G. Gemstone detail WHEN APPLICABLE
H. Useful lighting
I. Useful background
J. High visual sharpness
K. Design uniqueness/diversity
L. Training usefulness

Do not automatically reject museum-style neutral backgrounds.

Do not automatically reject historical jewellery.

==================================================
7. CONTACT SHEETS
==================================================

Generate a human-curation contact sheet that is easy to inspect.

For each candidate display:

- image
- candidate ID
- category
- relevance
- duplicate status
- current automated status

Generate:

datasets/curation/HUMAN_CURATION_MASTER_CONTACT_SHEET.png

Also generate:

datasets/curation/HUMAN_CURATION_NEAR_DUPLICATES.png

datasets/curation/HUMAN_CURATION_UNCERTAIN.png

Generate category sheets if practical.

==================================================
8. CURATION TABLE
==================================================

Create:

datasets/curation/HUMAN_CURATION.csv

The CSV should be easy to open in Excel/Google Sheets.

Freeze/header-friendly columns are not necessary in CSV, but keep the column order logical:

candidate_id
image_path
source
source_id
title
category
category_confidence
jewellery_relevance
duplicate_status
duplicate_of
dhash
ahash
sha256
license
width
height
jewellery_clearly_visible
single_primary_object
sufficient_object_size
useful_geometry
minimal_occlusion
useful_metal_appearance
gemstone_detail_applicable
useful_lighting
useful_background
visual_quality
design_diversity
design_redundancy
training_usefulness
final_triage
curator_notes

Leave manual fields blank rather than inventing decisions.

==================================================
9. CURATION SUMMARY
==================================================

Generate:

datasets/curation/HUMAN_CURATION_GUIDE.md

Explain exactly how a human should decide:

KEEP
REVIEW
REJECT

Also explain:

- how to handle near-duplicates
- how to handle multiple views of the same object
- how to handle historical jewellery
- how to handle jewellery without gemstones
- how to handle multi-piece displays
- how to handle uncertain categories

==================================================
10. SOURCE DIVERSITY WARNING
==================================================

Explicitly document that the current retained pool is dominated by CMA because The Met encountered WAF rate limiting.

Do NOT claim that the 226-image pool is already an ideal final appearance dataset.

Do NOT claim that museum photography perfectly represents modern jewellery product photography.

The human curation stage should assess photography/style suitability.

==================================================
11. FINAL REPORT
==================================================

Update/create:

datasets/curation/HUMAN_CURATION_README.md

Include:

- current candidate pool statistics
- category distribution
- duplicate statistics
- license status
- source distribution
- curation workflow
- final target: approximately 150–200 images
- explicit statement:

MANUAL CURATION REQUIRED — TRAINING NOT EXECUTED.

==================================================
12. TESTS
==================================================

Run the existing dataset pipeline tests.

Do not modify production code unnecessarily.

Do not modify tests merely to make them pass.

Report exact test results.

==================================================
13. STOP
==================================================

STOP after creating the human-curation artifacts.

Do NOT:
- select the final 150–200 automatically
- train anything
- run inference
- download additional images
- commit
- push

Wait for human curation/review.
