# JewelMind — Phase 6 Final Validation, Inference & Merge Readiness

You are working on the JewelMind project.

Phase 6 — Jewellery Component Detection using YOLO11 Instance Segmentation has already been implemented and trained.

The purpose of this task is to perform the FINAL VALIDATION of Phase 6 before it is merged into `main`.

============================================================
IMPORTANT OPERATING RULES
============================================================

1. DO NOT start another long training run.
2. DO NOT change the YOLO architecture unless a validation failure makes it necessary.
3. DO NOT replace the current trained model.
4. DO NOT create a new dataset.
5. DO NOT change the Phase 6 taxonomy unless a concrete implementation bug is discovered.
6. Use the existing trained checkpoint:
   `best.pt`
7. Prefer the existing training environment if it is already available.
8. Use the local RTX 4060 GPU for inference if CUDA is available.
9. Do not download unnecessary large models or datasets.
10. Do not commit `.pt`, `.pth`, `.onnx`, `.safetensors`, `.bin`, datasets, secrets, or `.env` files.
11. Do not modify unrelated Phase 7 or future AI functionality.
12. If something is already implemented correctly, reuse it rather than rewriting it.
13. If a command/path differs from the documentation, inspect the repository and use the actual existing path rather than inventing a new one.
14. Do not ask me to manually perform a step that you can safely perform yourself.
15. However, DO NOT perform the final Git merge into `main`. Stop after confirming that Phase 6 is merge-ready and provide the exact merge command for me.

============================================================
CURRENT PHASE 6 CONTEXT
============================================================

Project:
JewelMind

Project path:
C:\Users\usern\Desktop\JewelMind

Current training environment:
Conda environment:
`tgpu`

Expected Python:
3.10.x

GPU:
NVIDIA GeForce RTX 4060 Laptop GPU
8 GB VRAM

Current model:
YOLO11m-seg

Current model version:
`yolo11m-seg-jewelmind-v1`

Task:
Jewellery component instance segmentation.

Current 7-class taxonomy:

0 = gemstone
1 = ring_shank
2 = ring_head
3 = prong
4 = bezel
5 = setting
6 = shoulder

The current Phase 6 dataset is a SMALL SYNTHETIC BLUEPRINT DATASET intended primarily for pipeline validation and proof-of-concept, NOT as a production-quality jewellery segmentation dataset.

Current training result:

The actual YOLO11m training completed successfully.

The best checkpoint was selected at an early epoch.

Expected checkpoint names:

`best.pt`
`last.pt`

The model should be located somewhere under:

`runs/.../jewellery/yolo11m-seg-jewelmind-v1/weights/`

IMPORTANT:
The exact path printed by Ultralytics may contain nested `runs\segment\runs\...`.

DO NOT assume the path blindly.

First locate the actual checkpoint.

============================================================
PHASE 6 FINAL VALIDATION OBJECTIVE
============================================================

Perform these tasks in this exact order:

1. Locate and verify `best.pt`.
2. Run inference using `best.pt` on the Phase 6 TEST images.
3. Save prediction outputs.
4. Generate visual prediction previews.
5. Inspect the predictions programmatically and visually.
6. Determine whether predicted masks are sensible.
7. Verify the JewelMind `DetectionResult` output schema.
8. Run all relevant AI tests.
9. Fix ONLY genuine validation/integration bugs if discovered.
10. Update `docs/phases/PHASE_6_REPORT.md`.
11. Review Git diff.
12. Review Git status.
13. Verify no secrets/model binaries are staged or tracked.
14. Confirm Phase 6 is ready for merge.
15. STOP.
16. Do NOT merge yourself.

============================================================
STEP 1 — VERIFY CURRENT GIT STATE
============================================================

Before making changes:

Run:

git status

Then:

git branch --show-current

Then:

git log --oneline -5

Confirm that the current branch is the Phase 6 branch or the appropriate branch being used for Phase 6 work.

Do NOT switch branches automatically if doing so could risk uncommitted work.

If there are uncommitted changes, inspect them carefully before continuing.

Run:

git diff --stat

and:

git diff

Do not discard existing user work.

============================================================
STEP 2 — LOCATE THE TRAINED CHECKPOINT
============================================================

Do not assume the checkpoint location.

Run an appropriate PowerShell search such as:

Get-ChildItem runs -Recurse -Filter best.pt | Select-Object FullName

Also search for the corresponding:

last.pt

Then identify the checkpoint belonging to:

`yolo11m-seg-jewelmind-v1`

Expected logical location:

`runs/.../jewellery/yolo11m-seg-jewelmind-v1/weights/best.pt`

Verify that:

- the file exists
- the file is not empty
- it belongs to the current Phase 6 model
- the corresponding `last.pt` exists if expected

Do not copy the model into Git.

============================================================
STEP 3 — VERIFY THE TEST DATASET
============================================================

Use the existing Phase 6 test split.

Expected dataset structure should contain approximately:

35 train images
10 validation images
5 test images

Do NOT regenerate the dataset unless the existing test split is missing or corrupted.

Locate the test images using the existing dataset configuration.

Verify:

- test images exist
- test labels exist
- labels correspond to the current 7-class taxonomy
- no obvious corruption exists

If an existing dataset validation script is available, use it.

For example:

python ai/vision/training/scripts/validate_dataset.py --config ai/vision/training/configs/jewellery_components.yaml

Record the result.

The validation should report:

0 errors
0 warnings

If the result differs, investigate before continuing.

============================================================
STEP 4 — RUN INFERENCE USING best.pt
============================================================

Use the existing JewelMind inference implementation if it exists.

First inspect:

`ai/vision/inference/`

and identify:

`predict_components.py`

Read the script before running it.

Determine its actual CLI arguments.

DO NOT invent arguments.

Run inference using:

- model = current `best.pt`
- source = Phase 6 TEST images
- device = CUDA GPU if available
- confidence threshold = use the existing project default unless there is a documented reason to use another value

The inference must run against the TEST split.

Do not train.

Do not fine-tune.

Do not modify the model.

Save inference outputs under an appropriate ignored runtime directory, for example:

`runs/...`

or the existing inference output directory used by the project.

Do NOT save generated model artifacts into source-control directories.

============================================================
STEP 5 — GENERATE VISUAL PREDICTIONS
============================================================

Generate prediction visualizations for the test images.

Each visualization should make it possible to inspect:

- original image
- predicted segmentation mask
- predicted bounding box if available
- class name
- confidence score

The 7 classes should be distinguishable.

At minimum inspect predictions for the test images.

If the existing inference script already produces visual overlays, reuse it.

If a visualization helper already exists, use it.

Do not create a large new visualization framework just for this validation.

============================================================
STEP 6 — VISUAL QUALITY CHECK
============================================================

This is an IMPORTANT step.

Do not judge the model only from numeric metrics.

Inspect the generated prediction images.

Evaluate whether predictions are geometrically sensible.

For each relevant class, check:

1. gemstone
   - Does the mask roughly cover the gemstone region?
   - Is it inside/around the expected stone location?

2. ring_shank
   - Does the mask follow the ring band/shank?
   - Is it reasonably aligned with the actual shank?

3. ring_head
   - Does the mask correspond to the ring head region?

4. prong
   - Do predictions appear around the gemstone/setting area?
   - Are there excessive false positives?

5. bezel
   - Does the mask correspond to the bezel structure?

6. setting
   - Does it identify the synthetic setting/gallery structure introduced during the dataset fix?
   - Is it distinct from bezel where possible?

7. shoulder
   - Does the mask cover the shoulder region between shank and head?

Check for:

- completely misplaced masks
- masks covering the entire image
- excessive duplicate detections
- predictions on empty background
- impossible geometry
- masks detached from the jewellery
- severe class confusion
- obviously nonsensical segmentation

IMPORTANT:

This dataset is only 50 synthetic images.

Therefore:

DO NOT claim that this model is production-ready.

The purpose of this validation is to prove that:

`dataset → trained model → inference → segmentation output → JewelMind structured result`

works correctly.

If the predictions are imperfect but the pipeline works, document that honestly.

If predictions are completely nonsensical, investigate the implementation before declaring Phase 6 complete.

============================================================
STEP 7 — VERIFY DetectionResult
============================================================

Inspect the existing JewelMind inference/result implementation.

The architecture expects a stable structured result similar to:

{
  "model_version": "...",
  "image_size": {
    "width": ...,
    "height": ...
  },
  "inference_time_ms": ...,
  "device_used": "...",
  "total_detections": ...,
  "detections": [
    {
      "class_id": ...,
      "class_name": "...",
      "confidence": ...,
      "bbox": ...,
      "mask": ...,
      "normalized_mask": ...,
      "area": ...
    }
  ]
}

Do NOT blindly rewrite the schema.

Inspect the actual project implementation and verify that inference produces the intended fields.

Verify:

- model_version is present
- image_size is present
- inference_time_ms is present
- device_used is present
- total_detections is present
- detections is an array/list
- class_id is present
- class_name is present
- confidence is numeric
- bbox is present
- mask information is present when segmentation exists
- normalized mask information is present if implemented
- area is present if implemented

Verify that class IDs map correctly:

0 → gemstone
1 → ring_shank
2 → ring_head
3 → prong
4 → bezel
5 → setting
6 → shoulder

Do not introduce breaking schema changes.

============================================================
STEP 8 — VERIFY GPU INFERENCE
============================================================

Confirm that inference actually uses CUDA if the environment supports it.

Use the existing environment.

You may verify with:

python -c "import torch; print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"

Expected:

CUDA = True

GPU:

NVIDIA GeForce RTX 4060 Laptop GPU

Do not switch to CPU unless CUDA is unavailable.

Record the actual device in the validation report.

============================================================
STEP 9 — RUN AI TESTS
============================================================

Run the relevant AI tests.

Start with:

pytest tests/ai -v

If the repository has more specific Phase 6 tests, run those too.

Look for tests related to:

- dataset validation
- inference
- YOLO component detection
- DetectionResult
- schema validation
- model loading
- GPU/device selection

Do not skip failing tests.

If tests fail:

1. identify whether the failure is caused by this Phase 6 implementation
2. fix only the relevant bug
3. rerun the failed test
4. rerun the complete AI test suite

Do NOT weaken or delete tests just to make them pass.

============================================================
STEP 10 — CHECK INFERENCE SCRIPT QUALITY
============================================================

Inspect:

`ai/vision/inference/predict_components.py`

Verify that it:

- loads the configured YOLO11 segmentation model
- uses the expected class mapping
- supports the current checkpoint
- produces segmentation output
- does not hard-code a developer-specific absolute path
- does not require secrets
- handles missing model files cleanly
- does not crash on normal test input
- keeps model loading separate from future web/API logic where appropriate

If obvious implementation issues are found, fix them.

Do not redesign the entire AI architecture.

============================================================
STEP 11 — CHECK MODEL ARTIFACT GIT SAFETY
============================================================

Model weights must NOT be committed.

Run:

git status

Then:

git ls-files "*.pt"

Then:

git ls-files "*.pth"

Then:

git ls-files "*.onnx"

Then:

git ls-files "*.safetensors"

Also check:

git ls-files ".env"

and:

git status --ignored

Confirm that model files and secrets are ignored appropriately.

If `.gitignore` is missing required patterns, make the minimal safe update.

Expected ignored model types include:

*.pt
*.pth
*.onnx
*.safetensors
*.bin

Do NOT ignore source code or documentation accidentally.

Do NOT add datasets to Git unless the existing project explicitly requires a tiny source dataset and it is already intended to be versioned.

============================================================
STEP 12 — UPDATE PHASE_6_REPORT.md
============================================================

Update:

`docs/phases/PHASE_6_REPORT.md`

Do not create a completely unrelated report.

Preserve the existing report structure where possible.

Add a clearly labeled section:

## Final Validation

Document:

### Model

- Model: YOLO11m-seg
- Version: yolo11m-seg-jewelmind-v1
- Task: instance segmentation
- Checkpoint: best.pt
- Checkpoint path
- GPU used
- CUDA status

### Dataset

Document:

- train images
- validation images
- test images
- total images
- total masks
- 7 classes
- synthetic dataset limitation

### Inference

Document:

- test split used
- inference completed successfully
- number of test images processed
- output location
- whether GPU inference was used

### Visual Validation

Document the observed result honestly.

For example:

- shank predictions are visually coherent
- setting predictions are present
- some classes remain weak
- false positives/false negatives observed if any

Do NOT fabricate positive results.

### DetectionResult Validation

Document that the structured JewelMind output was verified.

Mention the fields actually verified.

### Automated Tests

Document:

- exact test command
- number passed
- number failed
- number skipped if relevant

### Limitations

Explicitly state:

The current model is a Phase 6 proof-of-concept trained on a small synthetic dataset. Its metrics and visual predictions must not be interpreted as production-level jewellery component detection performance.

A real production model will require a substantially larger, diverse, properly annotated real-jewellery/sketch dataset.

### Checkpointing

Document:

- `best.pt` = best validation checkpoint
- `last.pt` = latest checkpoint used for resume
- model binaries are excluded from Git

### Merge Readiness

At the end add:

## Phase 6 Merge Readiness

Include a checklist:

- [ ] Dataset validation passed
- [ ] best.pt located
- [ ] Test inference completed
- [ ] Prediction visualizations generated
- [ ] Prediction masks visually inspected
- [ ] DetectionResult verified
- [ ] AI tests passed
- [ ] No secrets tracked
- [ ] No model binaries tracked
- [ ] Git diff reviewed
- [ ] Git status clean or intentionally documented
- [ ] Phase 6 ready to merge into main

Only mark an item checked if it was actually verified.

============================================================
STEP 13 — RUN FINAL TESTS AGAIN
============================================================

After any code changes and after updating the report:

Run:

pytest tests/ai -v

If the project has a normal test suite that is reasonably quick, also run the relevant broader tests.

Then verify the build if applicable.

Do not start any long training job.

============================================================
STEP 14 — FINAL GIT REVIEW
============================================================

Run:

git status

Then:

git diff --stat

Then:

git diff

Then:

git ls-files "*.pt"

Then:

git ls-files "*.pth"

Then:

git ls-files "*.onnx"

Then:

git ls-files "*.safetensors"

Then:

git ls-files ".env"

Check that:

- no model weights are tracked
- no secrets are tracked
- no unexpected files are modified
- no generated runtime artifacts are accidentally staged
- only Phase 6 related files are changed
- report is updated
- inference implementation is correct
- tests are present and passing

If unrelated files were modified accidentally, do NOT silently delete user work.

Report them clearly.

============================================================
STEP 15 — DO NOT MERGE
============================================================

DO NOT execute:

git checkout main

DO NOT execute:

git merge phase-6-sketch-...

DO NOT push to main.

The final merge must be performed manually by me after I review your report.

============================================================
FINAL RESPONSE TO ME
============================================================

When all validation work is complete, give me a concise but detailed final summary with exactly these sections:

# Phase 6 Final Validation Complete

## 1. Inference
- checkpoint used
- number of test images
- GPU/CPU
- inference result

## 2. Visual Prediction Check
- whether masks are sensible
- strongest classes
- weakest classes
- important limitations

## 3. DetectionResult
- verified or failed
- important fields verified

## 4. Tests
- command
- passed
- failed
- skipped

## 5. Report
- confirm `docs/phases/PHASE_6_REPORT.md` updated

## 6. Git Safety
- model binaries tracked? YES/NO
- `.env` tracked? YES/NO
- unexpected files? YES/NO

## 7. Merge Readiness

Clearly state one of:

`PHASE 6 READY TO MERGE`

OR

`PHASE 6 NOT READY TO MERGE`

If NOT READY, explain exactly what is blocking the merge.

## 8. Exact Merge Command

If everything passes, provide the exact Git commands I should run manually to merge the Phase 6 branch into `main`.

Do NOT execute those merge commands yourself.

============================================================
CRITICAL FINAL RULE
============================================================

This is a VALIDATION phase only.

DO NOT:

- start another 50 epoch training run
- start another benchmark
- change YOLO model architecture
- download large datasets
- begin Phase 7
- implement ControlNet
- implement diffusion
- implement XGBoost
- implement OR-Tools
- merge into main

Only validate, document, fix genuine Phase 6 issues, and stop at merge readiness.