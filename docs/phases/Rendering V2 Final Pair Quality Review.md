JewelMind — Rendering V2 Final Pair Quality Review

Continue on the CURRENT branch:

phase-rendering-v2-dataset-preparation

IMPORTANT:
Do NOT create another branch.
Do NOT train any model.
Do NOT modify ControlNet V1.
Do NOT modify Appearance LoRA V1.
Do NOT modify YOLO V2 weights.
Do NOT start GPU training.
Do NOT download any new datasets.
Do NOT commit or push.

============================================================
OBJECTIVE
============================================================

The Rendering V2 dataset preparation notebook has already been
completed successfully.

Current reported dataset:

Total pairs: 961

Train: 664
Validation: 152
Test: 145

All images:
512x512

All critical integrity checks:
PASS

Before approving this dataset for ControlNet V2 training, add a
FINAL VISUAL QUALITY REVIEW section to:

ai/rendering/notebooks/Rendering_V2_Dataset_Preparation.ipynb

The purpose is to verify that the generated:

TARGET IMAGE ↔ LINEART CONDITIONING

pairs are visually meaningful for ControlNet training.

This is NOT another dataset-generation phase.

This is a visual quality gate.

============================================================
1. NOTEBOOK SECTION
============================================================

Add a prominent Markdown heading:

# Final Rendering V2 Pair Quality Review

Explain:

"The dataset passed structural integrity checks. This section
performs a visual audit to verify that the LineArt conditioning
maps actually preserve useful jewellery geometry and do not
primarily represent background noise."

Then explain why this matters:

A dataset can have:
- correct file counts
- valid metadata
- zero duplicates
- zero leakage

and still produce poor ControlNet training if the conditioning
images do not preserve useful jewellery structure.

============================================================
2. FIXED RANDOM SAMPLING
============================================================

Use a deterministic random seed.

For example:

SEED = 42

The same notebook execution must produce the same samples.

Do NOT simply display the first N images.

============================================================
3. ALL 8 CATEGORIES MUST BE REPRESENTED
============================================================

Canonical categories:

0 ring
1 earring
2 pendant
3 necklace
4 bracelet
5 bangle
6 brooch
7 other_jewellery

Select at least:

3 representative pairs per category

Therefore minimum:

8 × 3 = 24 pairs

Prefer 4 per category if practical:

8 × 4 = 32 pairs

Use the final canonical dataset.

============================================================
4. REQUIRED VISUALIZATION
============================================================

Create a clean teacher-friendly gallery.

For every selected pair show:

LEFT:
Target Photograph

RIGHT:
LineArt Conditioning

Under each pair display:

Category
Sample ID
Source
Edge Density

Example:

--------------------------------------------------
Target Image       | LineArt Conditioning
Ring               | Ring
Sample: rv2_0042   | Edge density: 0.084
--------------------------------------------------

Do NOT make the images too small.

Create:

ai/rendering/notebooks/outputs/rendering_v2_dataset/
final_pair_quality_review.png

============================================================
5. LOW-COUNT CATEGORY REVIEW
============================================================

Explicitly review:

ring
earring
necklace
bracelet
bangle
pendant
brooch
other_jewellery

Pay particular attention to:

ring
earring
necklace

because they have relatively fewer samples.

Also inspect:

bangle
pendant

because their distributions differ substantially from
brooch/other_jewellery.

============================================================
6. BEST / NORMAL / WORST PAIRS
============================================================

Do NOT judge only manually.

Use the existing measurable conditioning statistics to identify:

A. Strong examples
B. Typical examples
C. Weak examples

For example:

Strong:
edge density comfortably inside valid range

Weak:
very faint jewellery structure
or
background-heavy lineart
or
fragmented structure

Select:

5 strong examples
5 typical examples
5 weak examples

Create:

final_pair_quality_examples.png

with:

Target | Conditioning | Category | Edge Density | Quality Group

============================================================
7. CONDITIONING QUALITY ANALYSIS
============================================================

Calculate per-category statistics:

category
sample_count
mean_edge_density
median_edge_density
min_edge_density
max_edge_density

Display as a pandas table.

Also calculate:

percentage of samples with:

0.015 <= edge_density <= 0.35

for each category.

Create a chart:

final_conditioning_quality_by_category.png

============================================================
8. BACKGROUND DOMINANCE CHECK
============================================================

Where possible, estimate whether the LineArt is dominated by
background structure.

Use the existing masks when available.

Do NOT invent segmentation masks.

If a reliable jewellery mask exists:

calculate approximately:

jewellery edge density
background edge density

Then compare them.

If no reliable mask exists for a sample:

mark the metric as:

N/A

Do NOT fabricate the value.

Explain this limitation clearly.

============================================================
9. STRUCTURAL FIDELITY CHECK
============================================================

For the selected visual samples, inspect whether the LineArt
preserves important jewellery structure.

Look specifically for:

- ring circular geometry
- earring body
- necklace chain
- pendant outline
- bracelet shape
- bangle circular structure
- brooch structure
- other jewellery silhouette

Create a simple rubric:

GOOD
PARTIAL
WEAK

This does NOT need to be an automated AI score.

It can be a documented visual audit of the selected fixed samples.

IMPORTANT:

Do not pretend that this subjective visual rubric is an objective
model accuracy metric.

Clearly label it:

"Visual Quality Audit"

============================================================
10. HUMAN / BACKGROUND CONTAMINATION
============================================================

Check whether conditioning maps contain excessive:

- hands
- fingers
- faces
- clothing
- skin
- display stands
- unrelated objects
- background textures

Create representative examples if found.

Report:

Low contamination
Moderate contamination
High contamination

based only on the reviewed sample set.

Do not claim this percentage represents the entire dataset unless
the entire dataset was actually evaluated.

============================================================
11. CATEGORY-SPECIFIC FINDINGS
============================================================

Create a table:

| Category | Samples Reviewed | Conditioning Quality | Main Observation |
|----------|------------------|----------------------|------------------|

For each category write a short factual observation.

Examples of acceptable observations:

"Most reviewed samples preserve the outer silhouette."

"Several samples contain weak chain edges."

"Small objects produce sparse conditioning."

Do NOT invent observations.

============================================================
12. FINAL QUALITY SCORECARD
============================================================

Create a final scorecard:

| Quality Gate | Result | Status |
|--------------|--------|--------|
| Target readable | ... | PASS/WARN |
| Conditioning readable | ... | PASS/WARN |
| Jewellery geometry preserved | ... | PASS/WARN |
| Background contamination acceptable | ... | PASS/WARN |
| All 8 categories represented | ... | PASS/WARN |
| Low-count categories reviewed | ... | PASS/WARN |
| Edge density within target range | ... | PASS/WARN |
| Train/Val/Test leakage | ... | PASS |
| Duplicate leakage | ... | PASS |

IMPORTANT:

Do not mark a quality gate PASS unless the notebook actually
evaluated it.

============================================================
13. FINAL TRAINING DECISION
============================================================

At the end create a clear Markdown section:

# Rendering V2 Dataset Training Decision

The notebook must choose one:

READY FOR CONTROLNET V2 TRAINING

or

REQUIRES ADDITIONAL DATASET CURATION

Use the actual evidence.

Do NOT automatically write READY.

If the dataset is visually acceptable, state:

"The Rendering V2 dataset passes structural integrity and visual
conditioning quality review and is suitable for the next
ControlNet V2 training phase."

If significant problems exist, state exactly what needs fixing.

============================================================
14. TEACHER PRESENTATION SUMMARY
============================================================

Add a final concise section:

## What This Dataset Preparation Achieved

Explain in simple undergraduate language:

1. We collected legitimate jewellery images from approved sources.
2. We removed low-quality and unsuitable images.
3. Images were standardized to 512×512.
4. Jewellery structure was converted into LineArt conditioning.
5. Duplicate images were removed.
6. Train/validation/test leakage was prevented.
7. Eight jewellery categories were represented.
8. The final pairs were visually inspected.
9. The resulting dataset can be used for ControlNet V2 training
   if the final quality gate passes.

Also explicitly state:

"Training has NOT been performed yet."

============================================================
15. RE-RUN THE ENTIRE NOTEBOOK
============================================================

After modifying the notebook:

RUN EVERY CELL FROM TOP TO BOTTOM.

Verify:

- 0 errors
- all tables render
- all visualizations render
- final_pair_quality_review.png exists
- final_pair_quality_examples.png exists
- final_conditioning_quality_by_category.png exists
- final decision is shown
- previous dataset remains unchanged

============================================================
16. UPDATE THE REPORT
============================================================

Update:

PHASE_RENDERING_V2_DATASET_PREPARATION_REPORT.md

Add a new section:

## Final Pair Quality Review

Include:

- number of pairs visually reviewed
- random seed
- categories reviewed
- edge-density statistics
- background contamination findings
- structural fidelity findings
- best/typical/weak examples
- final training decision

Use ONLY actual notebook results.

Do not fabricate measurements.

============================================================
17. FINAL ANTIGRAVITY RESPONSE
============================================================

When finished report:

1. Notebook updated
2. Notebook executed successfully
3. Total cells
4. Errors
5. Number of visual pairs reviewed
6. Categories reviewed
7. Strong/typical/weak examples
8. Conditioning quality findings
9. Background contamination findings
10. Final training decision
11. Output image paths
12. Report updated
13. Git status
14. Whether any existing V1/V2 models were modified

DO NOT COMMIT.
DO NOT PUSH.

============================================================
FINAL SAFETY RULE
============================================================

This phase is ONLY a final visual dataset quality gate.

NO:
- ControlNet training
- LoRA training
- diffusion training
- model replacement
- production integration
- YOLO retraining
- external dataset downloads

The only goal is to determine whether the existing
961-pair Rendering V2 dataset is visually good enough
to proceed to ControlNet V2 training.