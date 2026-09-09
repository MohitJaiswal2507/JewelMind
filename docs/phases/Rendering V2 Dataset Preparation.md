JewelMind — Rendering V2 Dataset Preparation
Academic Jupyter Notebook Phase

Create this Git branch:

phase-rendering-v2-dataset-preparation

============================================================
CORE OBJECTIVE
============================================================

Prepare the complete Rendering V2 training dataset for JewelMind
INSIDE ONE JUPYTER NOTEBOOK that is easy to demonstrate to
teachers/advisors.

The notebook must be an academic, presentation-friendly,
reproducible dataset engineering experiment.

Create:

ai/rendering/notebooks/Rendering_V2_Dataset_Preparation.ipynb

Also create:

ai/rendering/notebooks/outputs/rendering_v2_dataset/

And create a concise report:

PHASE_RENDERING_V2_DATASET_PREPARATION_REPORT.md

IMPORTANT:

THIS PHASE IS DATASET PREPARATION ONLY.

DO NOT:
- train ControlNet
- train LoRA
- start any diffusion training
- modify existing trained model weights
- modify Rendering V1 production code
- replace V1 models
- modify YOLO V2 weights
- delete existing datasets
- overwrite existing V1 datasets
- commit
- push
- merge

The notebook itself must perform the dataset preparation operations.

============================================================
1. NOTEBOOK DESIGN
============================================================

Make the notebook visually polished and easy for an undergraduate
student to explain to a teacher.

Use clear Markdown headings.

Every major section must contain:

1. What are we doing?
2. Why are we doing it?
3. What did we find?
4. What happens next?

Use simple academic language.

Do not make it look like a production engineering log.

The notebook should tell a clear story:

RAW DATA
   ↓
DATASET INSPECTION
   ↓
QUALITY FILTERING
   ↓
JEWELLERY EXTRACTION
   ↓
STRUCTURAL CONDITIONING
   ↓
CAPTION / METADATA CREATION
   ↓
DUPLICATE & LEAKAGE CHECK
   ↓
TRAIN / VAL / TEST SPLIT
   ↓
FINAL DATASET ANALYSIS
   ↓
TRAINING-READY DATASET

============================================================
2. ENVIRONMENT & PATH SETUP
============================================================

First notebook section:

# Rendering V2 Dataset Preparation

Include:

- Project name: JewelMind
- Phase name
- Objective
- Hardware
- Dataset goal
- Training is NOT performed in this notebook

Show environment information:

- Python version
- PyTorch version if available
- CUDA availability
- GPU name if available
- OpenCV version
- PIL/Pillow version

Use pathlib.

Automatically locate the repository root.

Do NOT hard-code a Windows username.

The notebook must work when opened from:

JewelMind/
or
JewelMind/ai/rendering/notebooks/

============================================================
3. EXISTING DATASET INVENTORY
============================================================

Inspect the actual repository and existing local datasets.

Known relevant sources:

A. Existing ControlNet V1 paired dataset
datasets/controlnet_paired/

B. Existing Appearance LoRA dataset
datasets/appearance_lora/

C. MET jewellery archive
ai/vision/datasets/raw/met_jewellery/

D. DWPose jewellery dataset
ai/vision/datasets/raw/jewelry-dwpose/

E. Existing YOLO V2 dataset
ai/vision/datasets/jewellery_v2/

Do not assume these paths exist.

Check each path.

Create a table:

Dataset
Path
Exists
Files/Records
Image Count
Image Types
Resolution Examples
Potential Use

Display the table in the notebook.

============================================================
4. LICENSING / DATA PROVENANCE
============================================================

Create a clear dataset provenance table.

Use only licensing information already established in the project
documentation or metadata.

Known information:

MET:
CC0 / Public Domain

DWPose:
MIT

Existing V1 datasets:
Project Internal

YOLO V2:
Project Curation

Do NOT invent licenses.

For every source explain:

- why it is allowed
- how it will be used
- whether it can be used for training
- whether it will be redistributed

Raw web scraping with unclear licensing must NOT be included.

============================================================
5. RAW DATA EXPLORATION
============================================================

Programmatically inspect available source images.

Calculate where possible:

- total images
- image width
- image height
- aspect ratio
- RGB/RGBA/grayscale
- file format
- file size
- corrupted files
- unreadable files

Create:

A. Resolution distribution chart
B. Aspect ratio distribution chart
C. Image format distribution chart

Use Matplotlib.

Do NOT use seaborn.

Do not specify chart colors manually.

============================================================
6. VISUAL DATASET EXPLORATION
============================================================

Create teacher-friendly image galleries.

Show representative samples from each available source.

For each gallery include:

- image
- source dataset
- category if known
- resolution
- format

Create:

raw_met_samples.png
raw_dwpose_samples.png
raw_v1_samples.png

If a source does not contain enough usable images, clearly state that.

Do not fabricate examples.

============================================================
7. CATEGORY ANALYSIS
============================================================

Use JewelMind's canonical taxonomy:

0 ring
1 earring
2 pendant
3 necklace
4 bracelet
5 bangle
6 brooch
7 other_jewellery

Analyze the actual available category information.

Create:

- category counts
- category percentages
- category distribution chart

Clearly distinguish:

KNOWN CATEGORY

from:

INFERRED CATEGORY

Do not silently infer categories.

If category inference is required from metadata/prompt/object title,
document the exact rule.

============================================================
8. DATA SOURCE SELECTION
============================================================

Based on actual inspection, select source images for Rendering V2.

Preferred strategy:

Existing V1 paired data:
Use as the "gold standard" paired subset.

MET:
Use as high-quality jewellery source images where appropriate.

DWPose:
Use clean jewellery crops/masks where appropriate.

Do NOT blindly combine every image.

Create a selection table:

Source
Candidates
Accepted
Rejected
Reason for rejection

Possible rejection reasons:

- corrupted
- extremely low resolution
- jewellery too small
- heavy occlusion
- excessive background clutter
- multiple unrelated objects
- insufficient structural visibility
- excessive blur
- duplicate
- unclear category
- unsuitable object
- poor mask
- human/body dominates image

============================================================
9. IMAGE QUALITY FILTERING
============================================================

Implement deterministic quality checks.

At minimum calculate:

- minimum width/height
- aspect ratio
- image readability
- grayscale variance / basic sharpness
- jewellery occupancy where mask exists
- background occupancy where mask exists

Do NOT use arbitrary hidden thresholds.

Display the thresholds in Markdown before applying them.

Example:

Minimum resolution:
512 px on shorter side

Minimum jewellery occupancy:
define only if a reliable mask exists

Sharpness:
use a documented Laplacian variance threshold

If a threshold needs tuning, analyze the distribution first.

Show:

Before filtering
After filtering
Rejected count
Rejection reasons

Create a rejection-reason bar chart.

============================================================
10. JEWELLERY EXTRACTION
============================================================

Where masks are available:

- use the provided mask
- isolate jewellery
- suppress background
- preserve original geometry

For DWPose:

Inspect the actual target/mask relationship.

Do not confuse:

mask

with:

DWPose human pose.

The jewellery mask is the relevant signal for extraction.

For sources without masks:

DO NOT invent segmentation masks blindly.

If an existing reliable segmentation source is available, use it.

Otherwise place the sample into:

manual_review / excluded

rather than creating fabricated masks.

============================================================
11. IMAGE STANDARDIZATION
============================================================

Prepare training targets at:

512x512

Use aspect-ratio-preserving resize and letterboxing.

Do NOT stretch jewellery.

Document:

- resize method
- padding policy
- color space
- output format

Recommended:

Target:
RGB PNG

Conditioning:
RGB PNG or grayscale/RGB according to actual ControlNet training
implementation.

All generated files must be deterministic.

============================================================
12. NEURAL LINEART CONDITIONING
============================================================

For every accepted target image where a valid source image exists:

generate the structural conditioning image.

Use the project's existing preferred approach:

Neural LineArt

with the established bilateral filtering strategy where applicable.

Existing project finding:

Bilateral filter:
d = 9
sigma = 75

But VERIFY that the implementation exists before using it.

The notebook must clearly explain:

Original Image
→ preprocessing
→ LineArt
→ final Conditioning Map

Create teacher-friendly visual comparisons.

For example:

Original | Extracted Jewellery | LineArt Conditioning

Generate:

lineart_examples.png

Do not overwrite existing V1 conditioning files.

Everything must go into the NEW Rendering V2 dataset.

============================================================
13. CONDITIONING QUALITY AUDIT
============================================================

Calculate edge density for each conditioning image.

Use the preparation specification:

too faint:
edge density < 0.015

too noisy:
edge density > 0.35

But FIRST display the actual edge-density distribution.

Then classify:

GOOD
TOO FAINT
TOO NOISY

Do not blindly delete everything outside the range.

Report:

- total
- good
- too faint
- too noisy

Show representative examples of each.

Create:

edge_density_distribution.png

and:

conditioning_quality_examples.png

============================================================
14. CATEGORY + METAL + GEMSTONE METADATA
============================================================

Create structured metadata for every accepted pair.

Required fields:

sample_id
source_dataset
source_id
category
category_id
metal
gemstone
image_width
image_height
edge_density
sha256
phash if available
conditioning_path
target_path

Optional:

style
caption
background
mask_available
quality_score

Use JSONL.

Example:

{
  "sample_id": "...",
  "category": "ring",
  "category_id": 0,
  "metal": "18K Yellow Gold",
  "gemstone": "Diamond",
  ...
}

IMPORTANT:

Do not invent metal or gemstone labels.

If they are unavailable:

use null / unknown

or derive them only from explicit metadata/prompt using a documented rule.

Never hallucinate metadata.

============================================================
15. CAPTION GENERATION
============================================================

Create deterministic captions.

Example structure:

"a photorealistic [category] in [metal] with [gemstone],
professional jewellery product photography"

BUT only include metal/gemstone when actually known.

If unknown:

omit the attribute.

Do not create false labels.

Show 10 real caption examples in the notebook.

============================================================
16. DUPLICATE DETECTION
============================================================

Implement:

SHA-256 exact duplicate detection.

Also use perceptual hashing if available.

Detect:

- exact duplicates
- near duplicates

Do NOT automatically remove legitimate variants without analysis.

Create:

duplicate_groups.csv

and display examples of detected duplicates.

============================================================
17. TRAIN / VALIDATION / TEST SPLIT
============================================================

Create a deterministic split.

Target approximately:

70% train
15% validation
15% test

OR use another ratio only if the actual dataset size/category balance
requires it.

The split must be:

- deterministic
- reproducible
- category-aware
- leakage-safe

IMPORTANT:

Split at source-image identity level.

If multiple records derive from the same original image,
they MUST remain in the same split.

Do not let:

source image A
and its crop/mask variants

appear in different splits.

This is critical.

Document the random seed.

============================================================
18. CATEGORY BALANCING
============================================================

Analyze the resulting split.

Do NOT blindly oversample.

Show:

Before balancing
After balancing

For each of 8 categories:

ring
earring
pendant
necklace
bracelet
bangle
brooch
other_jewellery

Determine whether sufficient data exists.

Do not fabricate missing categories.

If some categories remain small, document:

"Limited-data category"

instead of artificially generating data.

============================================================
19. FINAL DATASET STRUCTURE
============================================================

Create:

ai/rendering/datasets/rendering_v2/

Use:

rendering_v2/
├── train/
│   ├── conditioning/
│   ├── target/
│   └── metadata.jsonl
│
├── val/
│   ├── conditioning/
│   ├── target/
│   └── metadata.jsonl
│
├── test/
│   ├── conditioning/
│   ├── target/
│   └── metadata.jsonl
│
├── manifests/
│   ├── train.jsonl
│   ├── val.jsonl
│   ├── test.jsonl
│   └── DATASET_MANIFEST.json
│
└── reports/

IMPORTANT:

Do not overwrite:

datasets/controlnet_paired/

Do not overwrite:

datasets/appearance_lora/

Do not overwrite any V1 dataset.

============================================================
20. FINAL DATASET VALIDATION
============================================================

Run a complete audit.

Verify:

- every conditioning image exists
- every target image exists
- dimensions are correct
- RGB/RGBA policy is correct
- metadata is valid
- category IDs are valid
- no duplicate SHA-256 across splits
- no duplicate pHash across splits
- source identities do not cross splits
- polygons/masks are not required for final dataset unless explicitly used
- no broken images
- no empty conditioning images
- no empty target images

Produce a final validation table:

Check
Result
Status

Use:

PASS
WARNING
FAIL

The notebook should end with:

DATASET READY FOR TRAINING

only if all critical checks pass.

============================================================
21. FINAL DATASET STATISTICS
============================================================

Create final charts:

1. Final class distribution
2. Train/Val/Test distribution
3. Resolution distribution
4. Edge density distribution
5. Source contribution
6. Rejection reasons
7. Category balance

Save all figures under:

ai/rendering/notebooks/outputs/rendering_v2_dataset/

============================================================
22. FINAL VISUAL GALLERIES
============================================================

Create polished galleries for teacher presentation.

At minimum:

01_raw_vs_processed.png

02_lineart_conditioning_examples.png

03_category_examples.png

04_train_examples.png

05_validation_examples.png

06_test_examples.png

07_rejected_examples.png

08_dataset_pipeline_overview.png

The pipeline overview should visually communicate:

Raw Image
↓
Quality Filter
↓
Jewellery Extraction
↓
Resize / Normalize
↓
Neural LineArt
↓
Metadata
↓
Leakage Check
↓
Train / Val / Test

============================================================
23. DATASET SUMMARY
============================================================

End notebook with a concise academic summary.

Include:

- total source candidates
- accepted images/pairs
- rejected images
- rejection rate
- final train count
- final validation count
- final test count
- total categories
- category distribution
- duplicate count
- leakage count
- conditioning quality
- dataset storage location

Then state:

"Rendering V2 dataset preparation is complete."

OR

"Rendering V2 dataset preparation requires additional curation."

Do NOT claim ready if critical checks fail.

============================================================
24. TRAINING READINESS CHECK
============================================================

The notebook must explicitly state:

TRAINING PERFORMED:
NO

MODEL WEIGHTS MODIFIED:
NO

CONTROLNET TRAINING:
NOT PERFORMED

LORA TRAINING:
NOT PERFORMED

PRODUCTION V1 MODIFIED:
NO

YOLO V2 MODIFIED:
NO

DATASET STATUS:
READY / NOT READY

============================================================
25. REPORT GENERATION
============================================================

Generate:

PHASE_RENDERING_V2_DATASET_PREPARATION_REPORT.md

The report must summarize the actual notebook results.

Include:

1. Objective
2. Data sources
3. Licensing/provenance
4. Filtering
5. Processing
6. LineArt generation
7. Metadata
8. Duplicate detection
9. Leakage prevention
10. Final dataset size
11. Category distribution
12. Visual quality findings
13. Validation results
14. Training readiness
15. Limitations
16. Recommended next step

Do not put fake or estimated counts in the report.

Use actual notebook results.

============================================================
26. IMPORTANT TECHNICAL CONSTRAINTS
============================================================

Use:

- Python
- pandas
- numpy
- PIL
- OpenCV
- matplotlib
- pathlib
- hashlib
- json

Use existing project packages where available.

Do NOT use seaborn.

Do NOT manually specify chart colors.

Do not download large external datasets.

Do not call external APIs unless absolutely necessary.

Do not require internet access for notebook execution if local
datasets are already sufficient.

============================================================
27. REPRODUCIBILITY
============================================================

Set deterministic seeds where relevant.

Record:

- Python version
- package versions
- random seed
- dataset source paths
- processing parameters
- thresholds
- split ratio

Create:

DATASET_MANIFEST.json

containing:

- generation timestamp
- dataset version
- source datasets
- counts
- hashes
- split information
- preprocessing configuration
- quality thresholds

============================================================
28. NOTEBOOK EXECUTION
============================================================

After building the notebook:

RUN THE ENTIRE NOTEBOOK.

Do not leave empty cells.

Every code cell must execute successfully.

Verify:

- zero errors
- all tables rendered
- all charts rendered
- all image galleries rendered
- final dataset exists
- metadata files exist
- manifest exists

If a processing step fails:

FIX THE NOTEBOOK.

Do not silently skip the step.

============================================================
29. GIT SAFETY
============================================================

At the end run:

git status
git diff --stat

DO NOT:

git add
git commit
git push
git merge

The final report must state:

Current branch:
phase-rendering-v2-dataset-preparation

GPU training performed:
NO

Production V1 modified:
NO

Existing V1 datasets modified:
NO

YOLO V2 weights modified:
NO

============================================================
30. FINAL ANTIGRAVITY REPORT
============================================================

When finished, report:

1. Notebook created
2. Notebook executed successfully
3. Total cells
4. Errors
5. Source datasets inspected
6. Final dataset size
7. Train/Val/Test counts
8. Category counts
9. Duplicate count
10. Leakage count
11. Rejected count
12. Conditioning quality statistics
13. Final dataset location
14. Report location
15. Files created
16. Files modified
17. Files intentionally untouched
18. Whether dataset is ready for ControlNet V2 training
19. Exact next manual action

============================================================
FINAL RULE
============================================================

This notebook is the authoritative record of Rendering V2 dataset
preparation.

Do not hide processing behind undocumented scripts.

The teacher should be able to open the notebook and understand:

WHERE THE DATA CAME FROM
→ WHY IT WAS SELECTED
→ HOW IT WAS CLEANED
→ HOW IT WAS TRANSFORMED
→ HOW LINEART CONDITIONING WAS CREATED
→ HOW DUPLICATES WERE REMOVED
→ HOW DATA LEAKAGE WAS PREVENTED
→ HOW TRAIN/VAL/TEST WERE CREATED
→ WHAT THE FINAL DATASET LOOKS LIKE
→ WHY IT IS READY FOR TRAINING

NO MODEL TRAINING IN THIS PHASE.