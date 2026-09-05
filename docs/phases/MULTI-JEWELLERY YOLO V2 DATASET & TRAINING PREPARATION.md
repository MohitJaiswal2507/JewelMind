JewelMind — MULTI-JEWELLERY YOLO V2 DATASET & TRAINING PREPARATION
================================================================

ROLE
----
You are working on the JewelMind capstone project.

Your task in this phase is to upgrade the existing jewellery vision system from
a ring-component-only YOLO model into a MULTI-JEWELLERY vision system capable
of recognizing all jewellery categories currently supported by the JewelMind UI.

IMPORTANT:
You are preparing the complete codebase, dataset structure, configuration,
documentation, validation tooling, and training plan.

DO NOT START GPU TRAINING IN THIS PHASE.

The actual training will be performed manually by the developer on an RTX 4060
8GB laptop after reviewing your final report. The developer will provide your
report to another AI assistant, which will guide the training process
step-by-step.

================================================================
1. CURRENT PROJECT CONTEXT
================================================================

JewelMind currently has a YOLO11 instance-segmentation model.

Current production model:

runs/segment/runs/jewellery/yolo11m-seg-jewelmind-v1/weights/best.pt

Current model classes:

0: gemstone
1: ring_shank
2: ring_head
3: prong
4: bezel
5: setting
6: shoulder

Current dataset configuration:

ai/vision/training/configs/jewellery_components.yaml

Current dataset root:

ai/vision/datasets/sample

Current YAML:

path: ai/vision/datasets/sample

train: train/images
val: val/images
test: test/images

names:
  0: gemstone
  1: ring_shank
  2: ring_head
  3: prong
  4: bezel
  5: setting
  6: shoulder

Current YOLO training configuration from V1:

task: segment
model: yolo11m-seg.pt
epochs: 50
patience: 15
batch: 4
imgsz: 640
device: '0'
workers: 0
pretrained: true
optimizer: AdamW
seed: 0
deterministic: true
amp: true

The current model is known to detect ring-related components, but it cannot
recognize necklaces, earrings, bracelets, bangles, brooches, pendants, etc.
because those classes do not exist in the trained model.

================================================================
2. ACTUAL PRODUCT REQUIREMENT
================================================================

The JewelMind UI already supports these jewellery categories:

- Ring
- Earring
- Pendant
- Necklace
- Bracelet
- Bangle
- Brooch
- Other Jewellery

The AI vision system must eventually support all of these categories.

The goal is NOT to fake detection through frontend logic.

The goal is to train a real computer-vision model using properly annotated
training data.

The final system should be able to receive jewellery images/sketches and
identify/segment relevant jewellery structures.

================================================================
3. VERY IMPORTANT — PRESERVE V1
================================================================

DO NOT modify, overwrite, delete, or replace:

runs/segment/runs/jewellery/yolo11m-seg-jewelmind-v1/weights/best.pt

Treat the current V1 model as a protected baseline.

Do not modify its training artifacts.

Do not rename it.

Do not retrain over its output directory.

Do not make production inference depend on the new V2 model yet.

V2 must be developed separately.

We need the ability to compare:

YOLO V1
vs
YOLO V2

before deciding whether V2 should become production.

================================================================
4. CREATE A PROPER V2 TAXONOMY
================================================================

Design a sensible multi-jewellery taxonomy.

Do NOT blindly add dozens of classes without considering:

- annotation difficulty
- visual distinguishability
- class imbalance
- usefulness to JewelMind
- whether the class is appropriate for instance segmentation
- whether a class can realistically be annotated consistently
- whether the class overlaps with another class
- whether the model needs jewellery-level classes or component-level classes

The first-level jewellery categories must support:

- ring
- earring
- pendant
- necklace
- bracelet
- bangle
- brooch
- other_jewellery

The existing ring micro-components should not simply disappear.

Preserve the useful ring-component knowledge where technically appropriate:

- gemstone
- ring_shank
- ring_head
- prong
- bezel
- setting
- shoulder

For other jewellery types, propose a reasonable component taxonomy.

Potential examples to evaluate:

EARRING:
- earring_body
- earring_hook
- earring_post
- earring_clasp

NECKLACE:
- necklace_chain
- necklace_pendant
- necklace_clasp

PENDANT:
- pendant_body
- pendant_bail
- gemstone

BRACELET:
- bracelet_band
- bracelet_clasp
- bracelet_link

BANGLE:
- bangle_body

BROOCH:
- brooch_body
- brooch_pin
- brooch_clasp

Do not automatically use every suggested class.

Evaluate whether each class is actually useful and realistically annotatable.

Document the final proposed taxonomy and explain why each class exists.

================================================================
5. IMPORTANT TAXONOMY DESIGN QUESTION
================================================================

Investigate whether the final V2 model should use:

A) jewellery category classes only

OR

B) a combined category + component taxonomy

OR

C) separate models/tasks for jewellery-category classification and
component segmentation.

Consider the practical limitations of a single YOLO segmentation model.

The final recommendation must be based on:

- JewelMind's current architecture
- existing V1 model
- frontend requirements
- backend AI API
- existing inference code
- dataset availability
- annotation complexity
- class imbalance
- future extensibility

Do not make an architectural change just because it sounds sophisticated.

Prefer the simplest robust solution.

================================================================
6. INSPECT THE EXISTING CODEBASE
================================================================

Before changing anything, inspect:

ai/
backend/
frontend/

Especially inspect:

- ai/vision/
- ai/vision/training/
- ai/vision/datasets/
- AI inference code
- YOLO service
- component detection service
- API endpoints
- frontend component-detection UI
- jewellery category definitions
- any category validation/mapping
- tests related to YOLO
- existing training scripts
- dataset preparation scripts
- class mappings

Determine exactly how the current model is loaded and how class names are
returned to the frontend.

Do not break existing API contracts unnecessarily.

================================================================
7. DATASET INVESTIGATION
================================================================

Inspect:

ai/vision/datasets/sample

Determine:

- number of train images
- number of validation images
- number of test images
- number of labels
- image formats
- label formats
- segmentation vs detection annotations
- image resolutions
- class distribution
- whether all labels correspond to existing images
- whether any labels are missing
- whether any images are missing labels
- whether duplicate images exist
- whether corrupt images exist
- whether labels contain invalid class IDs
- whether polygons are valid
- whether train/val/test leakage exists

Produce exact statistics.

Do not guess.

If possible, create a reusable dataset-audit script.

================================================================
8. DATASET DESIGN FOR V2
================================================================

Design the new dataset structure.

Prefer something similar to:

ai/vision/datasets/jewellery_v2/

    train/
        images/
        labels/

    val/
        images/
        labels/

    test/
        images/
        labels/

Create a V2 dataset YAML under:

ai/vision/training/configs/

For example:

jewellery_v2.yaml

Use the final taxonomy decided during this phase.

DO NOT populate the dataset with fabricated labels.

DO NOT generate fake annotations and present them as real training data.

If suitable real images are not currently available, clearly document that
the dataset still needs to be collected/annotated.

================================================================
9. DATA COLLECTION PLAN
================================================================

Because the developer has a ₹0 budget, design a training-data strategy that
does NOT depend on paid APIs or paid annotation services.

Investigate practical free/open approaches.

The report should recommend:

- what types of images are needed
- approximate minimum number per jewellery category
- preferred number for a stronger model
- how many images should be in train/val/test
- how to handle class imbalance
- how many examples should contain multiple components
- how to include product photographs
- how to include sketches where appropriate
- how to avoid data leakage
- how to maintain licensing/provenance information
- how to name files
- how to annotate consistently

Do not download a large dataset automatically.

Do not consume large amounts of disk space unnecessarily.

Do not start training.

================================================================
10. ANNOTATION GUIDELINES
================================================================

Create clear annotation rules.

For each class explain:

- what should be included
- what should not be included
- how to handle partially visible objects
- how to handle overlapping jewellery
- how to handle chains
- how to handle gemstones
- how to handle clasps
- how to handle thin structures
- how to handle shadows/reflections
- how to handle jewellery on human bodies
- how to handle jewellery photographed on plain backgrounds
- how to handle sketches
- how to handle multiple jewellery items in one image

For segmentation:

Explain how masks/polygons should be drawn.

Avoid ambiguous annotations.

================================================================
11. DATASET VALIDATION TOOLS
================================================================

Implement or improve scripts that can validate the V2 dataset BEFORE training.

The validator should detect:

- missing images
- missing labels
- corrupt images
- invalid YOLO segmentation syntax
- invalid polygon coordinates
- invalid class IDs
- empty labels where unexpected
- duplicate filenames
- duplicate images where detectable
- train/val/test leakage where detectable
- severe class imbalance
- unexpected classes

The validator should provide a clear summary.

Example:

Dataset:
  train: 1234 images
  val: 150 images
  test: 150 images

Classes:
  ring: 300
  earring: 250
  ...

Errors:
  missing labels: 0
  invalid polygons: 0
  unknown classes: 0

Warnings:
  class imbalance: ...

Do not hide errors.

================================================================
12. TRAINING CONFIGURATION
================================================================

Prepare the training configuration for manual execution.

Do NOT run training.

Do NOT invoke:

yolo segment train ...

Do not execute long-running GPU processes.

Do not automatically consume the RTX 4060.

Instead create/document the exact command that SHOULD be used later.

The final training configuration should be suitable for:

RTX 4060 Laptop GPU
8GB VRAM

Consider:

- YOLO11m-seg vs smaller model if necessary
- image size
- batch size
- AMP
- workers
- caching
- deterministic mode
- augmentation
- epochs
- patience
- pretrained weights
- checkpointing
- validation
- project/name paths

The final report must explain why the recommended settings were chosen.

================================================================
13. TRAINING SHOULD BE PHASED
================================================================

Do NOT recommend jumping immediately into a huge training run.

Design a staged training plan:

STAGE 0
Dataset validation.

STAGE 1
Small smoke-test training to confirm:

- dataset loads
- labels are valid
- GPU works
- model can train
- segmentation masks work
- no OOM

STAGE 2
Short baseline training.

STAGE 3
Full V2 training.

STAGE 4
Evaluation against V1.

STAGE 5
Manual visual testing.

STAGE 6
Production integration only after approval.

The final report must give exact recommended commands for each stage, but
DO NOT execute them.

================================================================
14. RTX 4060 CONSTRAINT
================================================================

The developer has:

NVIDIA RTX 4060 Laptop GPU
8GB VRAM

The training plan must be conservative with VRAM.

Avoid configurations likely to cause OOM.

If YOLO11m-seg at 640 with batch 4 is potentially too large for the expanded
dataset/configuration, explain whether to use:

- batch 2
- batch 1
- gradient accumulation if supported
- smaller model
- smaller image size

Do not silently change the model size.

Explain the tradeoff.

================================================================
15. EVALUATION PLAN
================================================================

Create a proper V2 evaluation plan.

Metrics should include appropriate YOLO metrics such as:

- box precision
- box recall
- box mAP50
- box mAP50-95
- mask precision
- mask recall
- mask mAP50
- mask mAP50-95

Also include per-class performance.

Do NOT judge the model only using overall mAP.

For JewelMind specifically evaluate:

- ring
- earring
- pendant
- necklace
- bracelet
- bangle
- brooch
- other_jewellery

And relevant component classes.

Create a manual visual evaluation checklist.

Important:

A model that gets high overall mAP but completely fails necklaces is NOT
acceptable.

================================================================
16. V1 VS V2 COMPARISON
================================================================

Design a fair comparison.

V1:

runs/segment/runs/jewellery/yolo11m-seg-jewelmind-v1/weights/best.pt

V2:

new separate output directory.

Compare:

- ring performance
- existing ring components
- new jewellery categories
- inference speed
- VRAM usage
- false positives
- false negatives
- segmentation quality

V2 must not be accepted simply because it detects new classes.

It must preserve acceptable ring performance.

================================================================
17. INFERENCE/API COMPATIBILITY
================================================================

Inspect the existing YOLO inference pipeline.

Determine what needs to change so V2 can eventually be loaded safely.

Do not switch production inference yet.

Prepare the code so that model selection can eventually be configured cleanly.

For example, prefer configuration such as:

JEWELRY_VISION_MODEL=v1

or

JEWELRY_VISION_MODEL=v2

if this fits the existing architecture.

Do not expose secrets.

Do not hard-code machine-specific absolute paths into production code.

Use existing configuration conventions.

================================================================
18. FRONTEND COMPATIBILITY
================================================================

The frontend already has jewellery category selection:

Ring
Earring
Pendant
Necklace
Bracelet
Bangle
Brooch
Other Jewellery

Inspect the current component detection UI.

Determine whether it needs changes to display:

- jewellery category
- detected components
- confidence
- segmentation masks
- multiple detected objects

Do not redesign the entire frontend in this phase.

Only make the minimum changes needed to support V2 data structures if
necessary.

Do not break the existing UI.

================================================================
19. BACKWARD COMPATIBILITY
================================================================

Existing functionality must remain intact.

Do not break:

- authentication
- designs
- sketch canvas
- sketch saving
- AI rendering
- ControlNet
- Appearance LoRA
- production management
- production optimization
- dashboard
- Studio
- existing YOLO V1 integration

This phase is ONLY for improving the jewellery vision system.

Do not modify the diffusion rendering pipeline unless absolutely required
for compatibility.

================================================================
20. TESTING
================================================================

Add/update tests for:

- taxonomy
- dataset config
- class mapping
- dataset validation
- model loading
- inference result parsing
- unknown class handling
- multi-class output
- API compatibility

Do not require GPU training to pass the standard test suite.

GPU-dependent tests should be clearly marked or separated.

Run:

- backend tests
- AI tests
- frontend typecheck/build

Do not claim tests passed unless actually run.

================================================================
21. CODE QUALITY
================================================================

Follow existing JewelMind conventions.

Use:

- Python
- FastAPI
- existing project structure
- existing configuration patterns

Avoid unnecessary dependencies.

Do not introduce paid services.

Do not introduce external cloud GPU requirements.

Do not expose secrets.

Do not commit model weights.

Ensure large datasets and model artifacts are gitignored.

Inspect and update .gitignore if necessary.

================================================================
22. GIT SAFETY
================================================================

Create/use a dedicated branch:

phase-multi-jewellery-yolo-v2

DO NOT work directly on main.

DO NOT merge into main.

DO NOT commit until the implementation and report are complete.

At the end, provide:

- files changed
- files added
- files removed
- tests run
- test results
- dataset statistics
- taxonomy
- training configuration
- exact future training commands
- known limitations
- recommended next steps

The developer will review your work before committing/merging.

================================================================
23. NO TRAINING RULE — EXTREMELY IMPORTANT
================================================================

DO NOT train YOLO.

DO NOT run a long GPU process.

DO NOT download huge datasets automatically.

DO NOT generate hundreds/thousands of images automatically.

DO NOT spend hours on model training.

DO NOT replace the existing V1 weights.

Your job in this phase is:

PREPARE → VALIDATE → DOCUMENT → STOP.

The developer will perform training manually later.

================================================================
24. REQUIRED FINAL REPORT
================================================================

Create a comprehensive report:

PHASE_MULTI_JEWELLERY_YOLO_V2_REPORT.md

The report MUST contain these sections:

1. Executive Summary

2. Current V1 Model Analysis

3. Current V1 Taxonomy

4. Current Dataset Analysis

5. Proposed V2 Taxonomy

6. Taxonomy Design Rationale

7. Dataset Architecture

8. Dataset Collection Strategy

9. Annotation Guidelines

10. Dataset Validation Strategy

11. Training Configuration

12. RTX 4060 VRAM Considerations

13. Staged Training Plan

14. Exact Training Commands
    - Smoke test
    - Baseline
    - Full training
    - Resume training
    - Validation
    - Inference

15. V1 vs V2 Evaluation Plan

16. Manual Visual QA Checklist

17. API Integration Plan

18. Frontend Compatibility

19. Testing Results

20. Files Changed

21. Git Changes

22. Known Limitations

23. Risks

24. Recommended Next Steps

25. EXACT MANUAL TRAINING PROCEDURE FOR DEVELOPER

The final section is extremely important.

Write it so that another AI assistant can read this report and guide the
developer through training one command at a time.

Include:

- environment to activate
- exact working directory
- dependencies required
- dataset validation command
- dataset statistics command
- smoke-test command
- baseline training command
- full training command
- resume command
- validation command
- inference command
- where weights will be generated
- how to verify CUDA
- how to monitor VRAM
- how to recognize OOM
- what to do if OOM occurs
- what files must NOT be deleted
- what outputs should be reported back after each stage

DO NOT execute those training commands yourself.

================================================================
26. REPORT MUST DISTINGUISH FACTS FROM RECOMMENDATIONS
================================================================

Use these labels where appropriate:

CONFIRMED:
Facts actually observed in the repository.

RECOMMENDED:
Your engineering recommendation.

REQUIRES MANUAL ACTION:
Something the developer must perform.

NOT VERIFIED:
Something that could not be confirmed.

Do not invent dataset counts or model performance numbers.

================================================================
27. FINAL OUTPUT FORMAT
================================================================

At the end of your work, provide a concise completion summary:

PHASE STATUS:
READY FOR MANUAL TRAINING

DATASET:
...

TAXONOMY:
...

TRAINING:
NOT RUN

V1:
PROTECTED

V2:
PREPARED

TESTS:
...

REPORT:
PHASE_MULTI_JEWELLERY_YOLO_V2_REPORT.md

NEXT ACTION:
Developer reviews the report and provides it to the AI assistant for
step-by-step manual training guidance.

STOP AFTER PREPARATION.

DO NOT TRAIN.
DO NOT MERGE.
DO NOT REPLACE V1.