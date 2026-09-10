JewelMind — Rendering Final Conditioning Generation
PHASE: phase-rendering-final-conditioning

You are working inside the JewelMind repository.

============================================================
1. PRIMARY OBJECTIVE
============================================================

We have completed the final curation of the new Rendering dataset.

The curated dataset is:

ai/rendering/datasets/rendering_final/

It contains approximately 10,685 accepted jewellery target images across the canonical JewelMind taxonomy:

0 = ring
1 = earring
2 = pendant
3 = necklace
4 = bracelet
5 = bangle
6 = brooch
7 = other_jewellery

The previous Rendering V2 dataset and models already exist and must remain untouched.

The purpose of THIS PHASE is ONLY:

    CURATED TARGET IMAGES
            ↓
    CONDITIONING GENERATION
            ↓
    TARGET + CONDITIONING PAIRS
            ↓
    TRAIN / VAL / TEST JSONL
            ↓
    VALIDATION + VISUAL QA
            ↓
    READY FOR MANUAL CONTROLNET TRAINING

This phase must NOT perform ControlNet training.

The actual GPU training will be performed manually by the project owner later on the RTX 4060.

============================================================
2. ABSOLUTE NO-TRAINING RULE
============================================================

IMPORTANT:

DO NOT TRAIN ANY MODEL IN THIS PHASE.

DO NOT:

- train ControlNet
- train LoRA
- train YOLO
- fine-tune Stable Diffusion
- run long GPU inference
- perform any optimization training
- start a training job automatically
- launch background training
- consume the RTX 4060 for training

You may use CPU/OpenCV/PIL/scikit-image/etc. for dataset preprocessing.

GPU use is not necessary for this phase.

If an existing utility appears to trigger model training, DO NOT execute it.

The owner will manually train the final ControlNet after this phase is reviewed.

============================================================
3. CRITICAL DATA PROTECTION RULES
============================================================

DO NOT MODIFY:

ai/rendering/datasets/rendering_final/

The curated target images are the source of truth.

Treat them as immutable.

DO NOT MODIFY:

ai/rendering/datasets/rendering_final_raw/

DO NOT MODIFY the old Rendering V2 dataset:

ai/rendering/datasets/rendering_v2/

DO NOT MODIFY:

ai/vision/datasets/jewellery_v2/

DO NOT MODIFY:

YOLO V1/V2 model files.

DO NOT MODIFY:

outputs/controlnet_jewellery_300/

DO NOT MODIFY:

outputs/rendering_v2_controlnet/

DO NOT MODIFY:

outputs/rendering_v2_controlnet_pilot/

DO NOT MODIFY:

outputs/appearance_lora/

DO NOT overwrite the existing production Rendering V1 ControlNet.

DO NOT overwrite the existing Rendering V2 300-step model.

DO NOT overwrite the existing Appearance LoRA.

This phase only creates new derived conditioning artifacts.

============================================================
4. WORKFLOW MUST BE JUPYTER NOTEBOOK BASED
============================================================

ALL DATASET WORK IN THIS PHASE MUST BE IMPLEMENTED THROUGH A JUPYTER NOTEBOOK.

Create:

ai/rendering/notebooks/Rendering_Final_Conditioning_Generation.ipynb

The notebook must be the primary reproducible workflow.

Do NOT create a Python-only workflow and merely mention that it could be run from Jupyter.

The actual preprocessing/generation logic must exist and be executable from the notebook.

Helper Python modules/scripts are allowed when useful, but the notebook must call them and document the complete workflow.

The notebook must be readable and organized into clear sections.

============================================================
5. BEFORE MODIFYING ANYTHING — INSPECT THE REPOSITORY
============================================================

First inspect the existing Rendering implementation.

Read and understand:

- existing Rendering V1 preprocessing
- existing ControlNet training dataset format
- existing Rendering V2 dataset preparation
- existing Rendering V2 conditioning/preprocessing code if present
- existing training scripts
- existing evaluation scripts
- existing dataset manifests
- existing category taxonomy
- existing image preprocessing conventions

Relevant locations include:

ai/rendering/

ai/rendering/datasets/

ai/rendering/training/

ai/rendering/evaluation/

ai/rendering/notebooks/

outputs/

Also inspect the final curation notebook and report:

ai/rendering/notebooks/Rendering_Final_Dataset_Curation.ipynb

PHASE_RENDERING_FINAL_DATASET_CURATION_REPORT.md

Use the existing repository conventions wherever they are correct.

Do not duplicate existing functionality unnecessarily.

============================================================
6. FINAL DATASET SOURCE OF TRUTH
============================================================

The target images must come ONLY from:

ai/rendering/datasets/rendering_final/

Do not go back to the raw datasets for this phase.

Do not download new datasets.

Do not scrape websites.

Do not call Hugging Face to download additional datasets.

Do not change the curated selection.

The curated dataset already passed:

- readability checks
- corruption checks
- resolution checks
- aspect-ratio checks
- blur checks
- human-dominance filtering
- category filtering
- exact duplicate checks
- near-duplicate grouping
- grouped train/val/test splitting

Preserve those decisions.

============================================================
7. EXPECTED DATASET STRUCTURE
============================================================

First inspect the actual structure instead of assuming it.

The intended target structure is approximately:

ai/rendering/datasets/rendering_final/

    images/
        ring/
        earring/
        pendant/
        necklace/
        bracelet/
        bangle/
        brooch/
        other_jewellery/

    train/
        images/

    val/
        images/

    test/
        images/

    dataset_manifest.csv
    category_statistics.csv
    rejection_log.csv
    duplicate_log.csv

The final report currently records approximately:

ring              510
earring           3774
pendant           547
necklace          1863
bracelet          1611
bangle            1068
brooch            43
other_jewellery   1269

TOTAL             10,685

Do NOT silently rebalance these counts in this phase.

Do NOT duplicate minority categories.

Do NOT synthesize images.

Do NOT delete additional accepted images unless a genuine corruption/integrity problem is discovered.

If actual counts differ from the report, investigate and report the discrepancy rather than silently changing the dataset.

============================================================
8. CONDITIONING OUTPUT DIRECTORY
============================================================

Create a NEW derived directory:

ai/rendering/datasets/rendering_final_conditioning/

Do not put generated conditioning images inside the immutable target dataset.

Use a clear structure such as:

ai/rendering/datasets/rendering_final_conditioning/

    train/
        target/
        lineart/
        canny/

    val/
        target/
        lineart/
        canny/

    test/
        target/
        lineart/
        canny/

    metadata/
        train.jsonl
        val.jsonl
        test.jsonl
        dataset_summary.json
        conditioning_statistics.csv

    visual_qa/
        train/
        val/
        test/

You may adjust the exact structure if the existing training code has a better compatible convention.

The important requirement is:

TARGET IMAGE
+
CONDITIONING IMAGE
+
CATEGORY
+
SPLIT
+
SOURCE/PATH METADATA

must remain deterministically paired.

============================================================
9. DO NOT MODIFY TARGET IMAGES
============================================================

The original target images in:

ai/rendering/datasets/rendering_final/

must never be edited in place.

If training requires 512×512 target images, create derived copies in the conditioning dataset.

Do not overwrite the originals.

Use a deterministic preprocessing policy.

Recommended target representation:

- RGB
- PNG
- 512×512
- deterministic resize/crop policy
- no random augmentation
- no random flip
- no color augmentation
- no destructive editing

The final training dataset must be reproducible.

============================================================
10. CONDITIONING STRATEGY
============================================================

The final Rendering model is intended to use ControlNet with jewellery structure as the main condition.

For this dataset, generate at least TWO conditioning representations:

A. LINEART
B. CANNY / STRUCTURAL EDGE MAP

The purpose is to compare them and determine which is best for the final ControlNet training pipeline.

Do NOT assume both must be used simultaneously during training.

The final training decision will happen later.

============================================================
11. LINEART GENERATION
============================================================

Generate a clean jewellery-oriented line representation from every target image.

Prefer existing JewelMind preprocessing conventions if they already work well.

If using OpenCV/PIL/scikit-image:

- convert to grayscale
- denoise conservatively
- preserve jewellery boundaries
- extract structural edges
- suppress unnecessary texture where possible
- avoid creating excessive background edges
- preserve gemstone/prong/detail boundaries when visible
- keep the output deterministic

Do NOT produce artistic sketches.

Do NOT hallucinate geometry.

Do NOT use generative AI.

Do NOT use a model that requires downloading a large new checkpoint unless absolutely necessary.

The conditioning map must be derived from the target image itself.

The lineart image should emphasize:

- jewellery silhouette
- structural boundaries
- gemstone boundaries
- prongs/settings
- links/chain structure
- decorative details
- major internal geometry

while minimizing:

- skin
- faces
- hair
- clothing
- room backgrounds
- tables
- unrelated objects

============================================================
12. CANNY / EDGE CONDITIONING
============================================================

Generate a Canny or equivalent structural edge representation.

Use deterministic parameters.

Do not select parameters randomly.

Parameters should be configurable near the top of the notebook.

For example:

CANNY_LOW_THRESHOLD
CANNY_HIGH_THRESHOLD
BLUR_KERNEL
MORPHOLOGY_PARAMETERS

Choose reasonable defaults based on inspection of the dataset.

Do not blindly copy thresholds from the old Rendering V2 dataset if the new final dataset has different visual characteristics.

The notebook must print the chosen parameters.

============================================================
13. JEWELLERY-FIRST CONDITIONING
============================================================

This is extremely important.

The previous Rendering V2 300-step model showed evidence that it learned:

- jewellery
- hands
- people
- backgrounds
- environmental context

instead of purely learning jewellery product structure.

The new final dataset was specifically curated to reduce that problem.

Therefore, conditioning generation must prioritize jewellery structure.

Inspect whether the existing curation metadata contains:

- quality tier
- occupancy
- human/lifestyle score
- category
- source
- duplicate cluster
- product cluster

Use those fields where useful.

Do not create a perfect segmentation algorithm and pretend it is one.

If you implement jewellery occupancy/background suppression, clearly label it as a heuristic.

Never claim perfect jewellery isolation unless it has actually been verified.

============================================================
14. DO NOT OVERPROCESS CLEAN PRODUCT IMAGES
============================================================

For studio/product images:

do not aggressively erase backgrounds if doing so damages jewellery boundaries.

For contextual images:

do not allow huge amounts of background/human edges to dominate the conditioning image.

Use conservative processing.

The goal is:

"preserve useful jewellery geometry while reducing irrelevant scene information."

NOT:

"remove every pixel that is not jewellery."

============================================================
15. CATEGORY-AWARE PROCESSING
============================================================

The eight categories are:

ring
earring
pendant
necklace
bracelet
bangle
brooch
other_jewellery

Do not hard-code ring as the default.

Each metadata record must preserve the actual category.

Example:

{
    "image": "...",
    "conditioning": "...",
    "category": "bracelet",
    "split": "train"
}

Use the canonical category strings consistently.

============================================================
16. FILE NAMING
============================================================

Use deterministic filenames.

Avoid random UUIDs unless the original source filename is unsuitable.

The relationship between:

target
lineart
canny
metadata

must be obvious.

Example:

train/ring/abc123.png

could correspond to:

train/target/ring/abc123.png
train/lineart/ring/abc123.png
train/canny/ring/abc123.png

Choose a clean consistent naming scheme.

Avoid filename collisions.

If two source files have identical names, generate deterministic collision-safe names based on source-relative path or SHA-256.

============================================================
17. SHA-256 INTEGRITY
============================================================

Compute SHA-256 for source target images.

Record relevant hashes in metadata.

At minimum, record:

- source_relative_path
- source_sha256
- target_derived_path
- lineart_path
- canny_path
- category
- split

This allows us to verify pairing later.

Do not use hash values to replace the actual dataset files.

============================================================
18. JSONL METADATA
============================================================

Create:

ai/rendering/datasets/rendering_final_conditioning/metadata/train.jsonl

ai/rendering/datasets/rendering_final_conditioning/metadata/val.jsonl

ai/rendering/datasets/rendering_final_conditioning/metadata/test.jsonl

Each line must represent exactly one paired sample.

Recommended schema:

{
  "id": "...",
  "category": "ring",
  "split": "train",
  "source_image": "...",
  "target_image": "...",
  "lineart_image": "...",
  "canny_image": "...",
  "source_sha256": "...",
  "width": 512,
  "height": 512
}

If the existing training script requires another schema, adapt it while preserving these concepts.

Do NOT invent metadata values.

============================================================
19. CAPTIONS / PROMPTS
============================================================

The final renderer will eventually be category-aware.

Prepare metadata that allows category-aware prompts.

However:

DO NOT train anything now.

Do not generate enormous amounts of LLM-generated captions.

If captions are needed, use deterministic templates based ONLY on verified category metadata.

For example:

"professional product photograph of a ring jewellery design"

"professional product photograph of an earring jewellery design"

etc.

Do not add unsupported material/gemstone claims unless the dataset metadata actually contains them.

If the existing training pipeline already expects prompts, make the prompt field available.

If it does not, do not unnecessarily add a complicated caption-generation system.

============================================================
20. TRAIN / VAL / TEST SPLITS
============================================================

The final curated dataset already has:

TRAIN
VAL
TEST

Do NOT randomly reshuffle the dataset.

Do NOT create a new split.

Do NOT move images between splits.

Do NOT break the duplicate-cluster grouping.

The existing split is part of the dataset's integrity.

The conditioning generation process must preserve the exact split.

Verify:

number of target images in train
=
number of lineart images in train
=
number of canny images in train
=
number of JSONL records in train

and similarly for validation/test.

============================================================
21. CROSS-SPLIT LEAKAGE CHECK
============================================================

Perform another integrity check after conditioning generation.

Verify:

- no source SHA appears in multiple splits
- no target file appears in multiple splits
- metadata records belong to exactly one split
- conditioning output corresponds to the correct target
- no accidental duplication happened during copying

If duplicate cluster information is available from the curation manifest, verify that clusters do not cross splits.

Report:

cross_split_sha_overlap = 0

or report the actual issue.

Never fabricate zero.

============================================================
22. IMAGE VALIDATION
============================================================

Validate every generated conditioning image.

Check:

- file exists
- file is readable
- file size > 0
- expected dimensions
- expected mode
- no NaN/invalid image data
- no completely blank image
- no completely saturated image
- reasonable edge density

For LineArt and Canny:

calculate useful statistics such as:

- nonzero pixel ratio
- mean intensity
- min/max
- edge density

Flag suspicious outputs.

Do NOT automatically delete suspicious samples without recording why.

============================================================
23. CONDITIONING QUALITY THRESHOLDS
============================================================

Make all quality thresholds configurable at the top of the notebook.

Do not scatter magic numbers throughout the code.

Examples:

MIN_NONZERO_RATIO
MAX_NONZERO_RATIO
MIN_EDGE_DENSITY
MAX_EDGE_DENSITY
MIN_IMAGE_SIZE
TARGET_SIZE

Do not blindly reject every unusual image.

The purpose of the thresholds is to detect likely preprocessing failures, not to remove legitimate jewellery designs.

============================================================
24. VISUAL QA IS REQUIRED
============================================================

This is NOT optional.

Create visual galleries showing:

A. original target
B. lineart
C. canny

side-by-side.

Create fixed-seed random samples.

Do not use random samples that change every notebook execution.

Use a fixed seed such as:

42

Create category-specific visual QA.

At minimum:

- ring
- earring
- pendant
- necklace
- bracelet
- bangle
- brooch
- other_jewellery

Show several examples per category.

Also create:

BEST / TYPICAL / WEAK

examples based on measurable conditioning statistics.

Do not claim "best" or "weakest" without defining the metric.

============================================================
25. PAY SPECIAL ATTENTION TO WEAK CATEGORIES
============================================================

The final curated dataset is highly uneven.

Especially inspect:

brooch = 43 images

versus:

earring = 3,774 images

Also inspect:

ring
bracelet
bangle
necklace

because these were problematic in the previous Rendering V2 model.

Do not artificially duplicate brooch samples.

Do not generate synthetic images.

Do not rebalance the dataset in this phase.

Just report the distribution and conditioning quality.

============================================================
26. HUMAN / BACKGROUND EDGE AUDIT
============================================================

Sample conditioning outputs from:

- Tier A
- Tier B
- Tier C

where the metadata supports these tiers.

Inspect whether the conditioning is dominated by:

- hands
- arms
- faces
- hair
- clothing
- models
- tables
- room backgrounds

versus:

- jewellery geometry

Report observations.

This is one of the most important checks because the previous V2 model learned unwanted context.

============================================================
27. CATEGORY DISTRIBUTION REPORT
============================================================

Generate a table showing:

category
target_count
lineart_count
canny_count
train_count
val_count
test_count
failed_count

All should reconcile.

Also generate a bar chart for category counts.

Use matplotlib.

Do not use seaborn.

Do not specify custom colors.

============================================================
28. CONDITIONING STATISTICS
============================================================

Generate statistics for LineArt and Canny:

- total images
- mean edge density
- median edge density
- min edge density
- max edge density
- percentile values
- number of suspiciously faint images
- number of suspiciously noisy images
- number of blank images

Break down by category.

Do not delete based only on these statistics.

Use them for QA and diagnosis.

============================================================
29. OUTPUT MANIFEST
============================================================

Create:

ai/rendering/datasets/rendering_final_conditioning/metadata/
dataset_summary.json

It should contain:

- generation date/time
- source dataset path
- total samples
- train count
- val count
- test count
- category counts
- target size
- lineart parameters
- canny parameters
- validation results
- failed sample count
- source dataset report reference
- preprocessing version

Do not include fake model metrics.

============================================================
30. REPRODUCIBILITY
============================================================

The notebook must be rerunnable.

It should:

- create directories safely
- avoid corrupting previous outputs
- detect existing generated files
- optionally skip already-valid outputs
- regenerate only missing/invalid outputs
- never silently mix outputs from different parameter configurations

If parameters change, make the output version identifiable.

For example:

rendering_final_conditioning_v1/

or include a preprocessing version in metadata.

Do not create confusing duplicate datasets.

============================================================
31. SAFE RESUME
============================================================

Because the dataset contains approximately 10,685 images, the notebook should be able to resume.

Do not force the user to regenerate all conditioning images if the notebook stops midway.

For every sample:

1. check whether output exists
2. validate it
3. skip if valid
4. regenerate if missing/invalid

Print progress.

Do not hide failures.

============================================================
32. NO LARGE MODEL DOWNLOADS
============================================================

Do not download:

- SDXL
- Flux
- ControlNet checkpoints
- YOLO models
- segmentation models
- SAM
- other large AI models

unless an already-existing local JewelMind dependency is explicitly required and already present.

This phase should be primarily deterministic image processing.

Do not add unnecessary dependencies.

Prefer packages already used by JewelMind.

If a new dependency is truly required, document it in the notebook and report.

============================================================
33. DO NOT USE THE V2 961-SAMPLE DATASET
============================================================

This is critical.

Do NOT accidentally use:

ai/rendering/datasets/rendering_v2/

The new final dataset is:

ai/rendering/datasets/rendering_final/

The new conditioning output is:

ai/rendering/datasets/rendering_final_conditioning/

The old V2 dataset must remain untouched.

============================================================
34. DO NOT TRAIN FROM THE NOTEBOOK
============================================================

The notebook must end at:

"READY FOR MANUAL CONTROLNET TRAINING"

It must NOT call:

train_rendering_v2.py

or any ControlNet training command.

Do not start a training process.

Do not run a GPU training smoke test.

Do not create fabricated training results.

============================================================
35. TRAINING PREPARATION INFORMATION
============================================================

At the end of the notebook/report, document what the future training phase will consume.

Expected future inputs:

train.jsonl
val.jsonl
test.jsonl

target images

lineart conditioning

possibly Canny conditioning depending on final experiment design.

The future ControlNet training will use the local SD1.5 + LineArt ControlNet strategy already established in JewelMind.

Existing local model resources must not be modified.

The future training will be manually executed by the owner on:

NVIDIA RTX 4060 Laptop GPU
8GB VRAM

Do NOT train it now.

============================================================
36. FUTURE TRAINING STRATEGY — DOCUMENT ONLY
============================================================

Do NOT execute this.

Document the intended future experimental sequence:

Stage 0:
conditioning validation — THIS PHASE

Stage 1:
small manual ControlNet smoke test

Stage 2:
manual pilot training

Stage 3:
manual 300-step candidate

Stage 4:
evaluate

Stage 5:
if improving, consider 500+ steps

Training must be decided based on validation quality, not simply number of steps.

Do not claim future results.

============================================================
37. COMPARISON WITH EXISTING V2
============================================================

At the end of the report, explicitly document that:

Existing Rendering V2 300-step model:

outputs/rendering_v2_controlnet/controlnet_rendering_v2_final

is a BASELINE.

It is not being overwritten.

The new final dataset is being prepared specifically to address the previous model's weaknesses:

- contextual/human contamination
- weak bracelet rendering
- weak bangle rendering
- inconsistent ring fidelity
- excessive scene learning
- insufficient product-style concentration

Do not claim the new dataset solves these problems yet.

It has only been curated and conditioned.

Actual improvement can only be established after training and evaluation.

============================================================
38. PROTECTION AUDIT
============================================================

Before processing:

record baseline hashes/counts for protected artifacts.

After processing:

verify they remain unchanged.

At minimum verify:

ai/rendering/datasets/rendering_final/
ai/rendering/datasets/rendering_final_raw/
ai/rendering/datasets/rendering_v2/
ai/vision/datasets/jewellery_v2/
outputs/controlnet_jewellery_300/
outputs/rendering_v2_controlnet/
outputs/rendering_v2_controlnet_pilot/
outputs/appearance_lora/

The target dataset itself must also remain unchanged.

Report any unexpected modification immediately.

============================================================
39. NOTEBOOK SECTION STRUCTURE
============================================================

Create a clear notebook with sections similar to:

1. Title / Objective

2. Environment Verification

3. Project Path Configuration

4. Protected Artifact Inventory

5. Final Dataset Inventory

6. Dataset Manifest Loading

7. Category Distribution

8. Split Verification

9. Conditioning Configuration

10. LineArt Generation Functions

11. Canny Generation Functions

12. Test Generation on Small Fixed Samples

13. Visual QA of Test Samples

14. Full Conditioning Generation

15. Conditioning Integrity Validation

16. Pairing Validation

17. Cross-Split Leakage Validation

18. Category-Level Statistics

19. Human/Background Conditioning Audit

20. Visual Galleries

21. Final Dataset Summary

22. Protection Audit

23. Readiness Checklist

24. Conclusion

The notebook should be clean enough that another developer can understand exactly how the final conditioning dataset was generated.

============================================================
40. SMALL TEST BEFORE FULL GENERATION
============================================================

DO NOT immediately process all 10,685 images.

First process a small deterministic test set.

For example:

- 2–5 images per category

using seed 42.

Inspect:

target
lineart
canny

and verify:

- images readable
- correct size
- useful jewellery structure
- no blank outputs
- no obviously broken preprocessing
- filenames map correctly

Only after the test generation passes should the notebook proceed to the full dataset generation.

The notebook can contain a clear variable such as:

RUN_FULL_GENERATION = False

for initial testing.

Make it easy for the owner to switch to:

RUN_FULL_GENERATION = True

after QA.

Do NOT run a full GPU training process.

============================================================
41. FULL GENERATION
============================================================

After test QA passes, generate conditioning for all accepted samples.

Expected approximate total:

10,685 target images

Therefore expected approximately:

10,685 LineArt images
10,685 Canny images

unless actual dataset inventory proves otherwise.

Do not fabricate counts.

Print progress such as:

[1234/10685] ring/xxxxx.jpg

At the end print:

targets processed
lineart generated
canny generated
skipped valid
failed
missing

============================================================
42. FAILURE HANDLING
============================================================

If an image fails:

- record the source path
- record the error
- continue processing other images
- do not silently ignore it

Create a failure log such as:

conditioning_failures.csv

with:

source_path
category
split
error
timestamp

At the end, report the exact failure count.

If failure rate is significant, stop and report instead of declaring success.

============================================================
43. FINAL READINESS CHECK
============================================================

The phase can only be marked READY if:

[ ] Notebook exists

[ ] Notebook runs without errors

[ ] Final dataset source remains unchanged

[ ] Raw datasets remain unchanged

[ ] Existing models remain unchanged

[ ] All expected categories are represented

[ ] Train/val/test splits are preserved

[ ] Target images are valid

[ ] LineArt outputs are valid

[ ] Canny outputs are valid

[ ] Target ↔ conditioning pairing is verified

[ ] JSONL records match generated files

[ ] No cross-split SHA leakage

[ ] No missing conditioning files

[ ] No blank/broken conditioning outputs

[ ] Visual QA completed

[ ] Weak categories inspected

[ ] Human/background contamination audited

[ ] Category statistics generated

[ ] Conditioning parameters documented

[ ] Protection audit passes

[ ] No training performed

============================================================
44. REQUIRED REPORT
============================================================

Create:

PHASE_RENDERING_FINAL_CONDITIONING_REPORT.md

The report must contain:

1. Executive summary

2. Objective

3. Source dataset

4. Dataset inventory

5. Category distribution

6. Train/val/test distribution

7. Conditioning methodology

8. LineArt parameters

9. Canny parameters

10. Output directory structure

11. Generated counts

12. Failed counts

13. Conditioning statistics

14. Visual QA findings

15. Human/background contamination findings

16. Weak-category findings

17. Pairing verification

18. Cross-split leakage verification

19. Protection audit

20. Reproducibility information

21. Limitations

22. Future ControlNet training plan

23. Final readiness decision

The final decision must be one of:

READY FOR MANUAL CONTROLNET TRAINING

or

NOT READY — list the exact blocking issues.

Do not say the model is improved because no model has been trained.

============================================================
45. GIT RULES
============================================================

Work only on:

phase-rendering-final-conditioning

Do not commit to main.

Do not merge anything.

Do not push unless explicitly instructed.

At the end, provide:

git status

and a concise list of:

- files created
- files modified
- files deleted
- protected files verified unchanged

DO NOT COMMIT.

============================================================
46. EXPECTED DELIVERABLES
============================================================

At minimum create:

ai/rendering/notebooks/
Rendering_Final_Conditioning_Generation.ipynb

ai/rendering/datasets/rendering_final_conditioning/

    train/
    val/
    test/
    metadata/
    visual_qa/

PHASE_RENDERING_FINAL_CONDITIONING_REPORT.md

Potentially:

conditioning_failures.csv

dataset_summary.json

conditioning_statistics.csv

depending on implementation.

============================================================
47. IMPORTANT QUALITY PRINCIPLE
============================================================

Do NOT optimize for dataset size.

Optimize for:

1. jewellery structural clarity
2. clean conditioning
3. target-conditioning correspondence
4. product-style representation
5. category coverage
6. reproducibility
7. absence of leakage
8. minimal human/background interference

A smaller verified dataset is better than a huge broken conditioning dataset.

However, do not remove valid samples merely to make the dataset smaller.

============================================================
48. STOP CONDITION
============================================================

After completing the notebook, generation, validation, visual QA, and report:

STOP.

Do not start ControlNet training.

Do not modify the training configuration yet unless it is strictly necessary to describe how the generated dataset will be consumed.

Do not commit.

Do not push.

Wait for the project owner to review the report and visual conditioning galleries.

============================================================
49. FINAL RESPONSE FORMAT
============================================================

When finished, report:

A. What was implemented

B. Notebook path

C. Output dataset path

D. Number of target images

E. Number of LineArt images

F. Number of Canny images

G. Train/Val/Test counts

H. Category counts

I. Failed samples

J. Pairing validation result

K. Leakage validation result

L. Visual QA result

M. Protection audit result

N. Any warnings or limitations

O. Exact next step

The exact next step should be:

MANUAL CONTROLNET TRAINING PREPARATION / REVIEW

and NOT automatic training.

Again:

DO NOT TRAIN ANY MODEL.

The owner will manually perform the GPU training after reviewing this phase.