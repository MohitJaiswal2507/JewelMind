# JewelMind — Dataset State Reconciliation Prompt

## ROLE

You are Antigravity working on the JewelMind project.

Your task in this phase is **DATASET STATE RECONCILIATION ONLY**.

There are conflicting reports describing different dataset states:

- One report says **302 fetched → 226 retained**
- Another report says **275 fetched → 151 retained**

Before any human curation or training begins, determine which dataset state is actually present on disk and establish ONE mathematically verified source of truth.

---

# 🚨 ABSOLUTE EXECUTION BOUNDARY

During this task:

### DO NOT:
- Acquire or download any new dataset images.
- Retry museum APIs or external acquisition.
- Start LoRA training.
- Start ControlNet training.
- Start Stable Diffusion training.
- Run GPU diffusion inference.
- Run rendering experiments.
- Modify production rendering code.
- Modify Phase 7 inference behavior.
- Modify model architecture.
- Generate synthetic training images.
- Create a new dataset.
- Delete candidate images merely to "clean things up".
- Commit or push changes.

### YOU MAY:
- Inspect the existing repository and filesystem.
- Inspect existing dataset manifests.
- Inspect existing CSV files.
- Inspect existing image files.
- Compute file counts, hashes, dimensions, and metadata.
- Reconcile manifests against files on disk.
- Inspect existing reports.
- Run safe read-only validation scripts.
- Create/update a reconciliation report.
- Create small diagnostic scripts if necessary, but do not alter production behavior.

**This phase ends with a report only.**

---

# 1. PRIMARY QUESTION

Determine:

> **What is the actual current dataset state on disk, and which dataset should be treated as the single source of truth for the upcoming human curation phase?**

Do not assume that either 151 or 226 is correct.

Verify from the actual filesystem and manifests.

---

# 2. INSPECT THESE AREAS

Inspect all existing dataset/curation-related files, especially:

```text
datasets/
datasets/curation/
datasets/curation/full_candidates/
datasets/curation/HUMAN_CURATION.csv
datasets/curation/full_dataset_manifest.json
datasets/curation/full_dataset_manifest.jsonl
```

Also search the repository for:

```text
CAND_001
CAND_226
302
275
226
151
FULL_DATASET_ACQUISITION_REPORT
HUMAN_CURATION
```

Find all relevant dataset manifests, acquisition reports, CSVs, JSON/JSONL files, image directories, and generated contact sheets.

Do not rely on filenames alone.

---

# 3. RECONCILE THE TWO CONFLICTING STATES

Previous reports contain these conflicting claims.

## State A

```text
TOTAL FETCHED: 302
TECHNICALLY VALID: 226
TECHNICALLY REJECTED: 76

JEWELLERY_RELEVANT: 188
JEWELLERY_UNCERTAIN: 38

DISTINCT: 102
NEAR_DUPLICATE_REVIEW_REQUIRED: 124
EXACT SHA-256 DUPLICATES: 0
```

## State B

```text
TOTAL FETCHED: 275
TECHNICALLY VALID: 151
TECHNICALLY REJECTED: 124

JEWELLERY_RELEVANT: 122
JEWELLERY_UNCERTAIN: 29

DISTINCT: 82
NEAR_DUPLICATE_REVIEW_REQUIRED: 69
EXACT SHA-256 DUPLICATES: 0
```

Determine whether:

1. State B is a newer replacement dataset.
2. State B is a partial/regenerated batch.
3. State A remains the actual current dataset.
4. Both datasets exist simultaneously.
5. One report was generated from stale/intermediate files.
6. The 151 candidates are a subset of the 226 candidates.
7. The 151 candidates are a completely different acquisition batch.
8. The 226 candidates were overwritten or replaced.
9. The manifests and contact sheets correspond to different dataset states.

Do not speculate. Use filesystem evidence.

---

# 4. PHYSICAL FILE ACCOUNTING

Count the actual image files currently present.

Report:

```text
Total image files physically present:
JPEG:
JPG:
PNG:
WEBP:
Other:
```

Then identify which directories contain them.

For every relevant candidate directory, calculate:

```text
directory
file_count
```

Do not delete or move anything.

---

# 5. MANIFEST ACCOUNTING

For every existing manifest:

```text
full_dataset_manifest.json
full_dataset_manifest.jsonl
other relevant manifests
```

report:

```text
manifest filename
candidate count
candidate ID range
duplicate candidate IDs
missing candidate IDs
image paths referenced
missing image paths
paths pointing to nonexistent files
files not represented in manifest
```

If the manifest contains 226 candidates, verify all 226 actually exist.

If it contains 151 candidates, verify all 151 actually exist.

---

# 6. HUMAN_CURATION.CSV ACCOUNTING

Inspect:

```text
datasets/curation/HUMAN_CURATION.csv
```

Report:

```text
row count excluding header
candidate ID count
minimum candidate ID
maximum candidate ID
duplicate candidate IDs
missing IDs
blank/manual-curation fields
existing final_triage values
```

Determine whether it is:

```text
226-row workspace
151-row workspace
other
```

Do NOT overwrite the CSV.

---

# 7. CONTACT SHEET CONSISTENCY

Inspect the existing contact sheets and their generation metadata/scripts if available.

Important files may include:

```text
HUMAN_CURATION_MASTER_CONTACT_SHEET.png
HUMAN_CURATION_NEAR_DUPLICATES.png
HUMAN_CURATION_UNCERTAIN.png

HUMAN_CURATION_RINGS.png
HUMAN_CURATION_EARRINGS.png
HUMAN_CURATION_PENDANTS.png
HUMAN_CURATION_NECKLACES.png
HUMAN_CURATION_BRACELETS_BANGLES.png
HUMAN_CURATION_BROOCHES_OTHER.png
```

Determine:

- How many candidates are represented?
- Which candidate IDs are represented?
- Do they match `HUMAN_CURATION.csv`?
- Do they match `full_dataset_manifest.json/jsonl`?
- Are contact sheets stale relative to the current filesystem?

If exact candidate counts cannot be extracted reliably from the image alone, inspect the generator scripts/metadata rather than guessing.

---

# 8. SHA-256 VERIFICATION

For every currently retained candidate image that belongs to the disputed dataset state:

Calculate SHA-256.

Determine:

```text
actual unique image count
exact byte duplicates
duplicate groups
```

Compare these against existing manifest metadata.

If the report says:

```text
EXACT_DUPLICATE = 0
```

verify that independently.

Do not delete duplicates.

---

# 9. PERCEPTUAL HASH / NEAR-DUPLICATE VERIFICATION

Inspect the existing dHash/aHash metadata and/or safely recompute it if needed.

Determine:

```text
DISTINCT count
NEAR_DUPLICATE count
```

and compare against both reported states:

```text
226-state:
DISTINCT = 102
NEAR_DUPLICATE = 124

151-state:
DISTINCT = 82
NEAR_DUPLICATE = 69
```

Important:

**Do NOT reject or delete near-duplicates.**

This phase is only reconciliation.

---

# 10. CATEGORY RECONCILIATION

Use the canonical taxonomy:

```text
ring
earring
pendant
necklace
bracelet
bangle
brooch
other
```

For each actual dataset state, calculate category counts.

Do not use compound categories such as:

```text
ring/earring
bracelet/bangle
```

unless the original metadata genuinely cannot be resolved. If ambiguous, report it instead of silently changing it.

Compare actual category counts against the previous reports.

---

# 11. SOURCE AND LICENSE RECONCILIATION

Determine actual source distribution from the metadata.

Report:

```text
CMA count
Met count
Other source count
Unknown source count
```

Also verify license metadata.

Do NOT make new external API calls or download anything.

Report:

```text
CC0 count
Public Domain count
Other license count
Unknown/unverified count
```

Do not make legal conclusions beyond what the stored metadata/source information supports.

---

# 12. DETERMINE THE SINGLE SOURCE OF TRUTH

After all checks, classify the situation as exactly one of:

```text
A = 226 candidate state is authoritative
B = 151 candidate state is authoritative
C = both states exist and must remain separately identified
D = dataset state is corrupted/incomplete and requires controlled regeneration
```

Explain the evidence.

The recommendation must be based on actual files, not report wording.

---

# 13. IMPORTANT: DO NOT AUTOMATICALLY CHOOSE 150–200 YET

Even if the authoritative state is 151 candidates:

**DO NOT declare them final training data.**

Even if the authoritative state is 226 candidates:

**DO NOT declare them final training data.**

Human visual curation is still required.

The appearance-LoRA target remains:

```text
150–200 high-signal jewellery images
```

But selection must happen only after the dataset state is reconciled.

---

# 14. DO NOT MODIFY THE TRAINING PIPELINE

The existing JewelMind rendering/training architecture must remain untouched.

Do not change:

```text
Stable Diffusion 1.5
ControlNet
LoRA trainer
render API
model manager
preprocessing
GPU configuration
Phase 7 rendering pipeline
```

No training.

No inference.

No GPU work.

---

# 15. OUTPUT REPORT

Create:

```text
DATASET_STATE_RECONCILIATION_REPORT.md
```

The report must contain:

## Executive Summary

State clearly:

```text
Actual dataset state:
Authoritative state:
Reason:
Training executed: NO
Inference executed: NO
New acquisition executed: NO
Production code modified: NO
```

## Filesystem Inventory

Table containing:

| Location | File Count | Candidate IDs | Status |
|---|---:|---|---|

## Manifest Reconciliation

| Manifest | Candidates | Missing Files | Extra Files | Duplicate IDs | Status |
|---|---:|---:|---:|---:|---|

## CSV Reconciliation

| CSV | Rows | ID Range | Duplicate IDs | Missing IDs | Status |
|---|---:|---|---:|---:|---|

## Dataset State Comparison

| Metric | Reported 226 State | Reported 151 State | Actual | Match |
|---|---:|---:|---:|---|

Include:

- fetched
- technically valid
- rejected
- relevant
- uncertain
- distinct
- near duplicates
- exact duplicates

## Category Distribution

Use:

```text
ring
earring
pendant
necklace
bracelet
bangle
brooch
other
```

## Source Distribution

## License Distribution

## Contact Sheet Consistency

Explicitly state whether contact sheets match the authoritative manifest.

## Final Determination

Choose:

```text
A / B / C / D
```

and explain why.

## Recommended Next Step

Give exactly one recommended next step.

If reconciliation is successful:

> Proceed to manual human curation of the authoritative candidate pool.

If reconciliation fails:

> Resolve the dataset-state inconsistency before human curation.

---

# 16. FINAL SAFETY CHECK

Before finishing, verify:

```text
[ ] No new images downloaded
[ ] No dataset images deleted
[ ] No training executed
[ ] No ControlNet training executed
[ ] No LoRA training executed
[ ] No GPU diffusion inference executed
[ ] No production rendering code modified
[ ] No Phase 7 behavior modified
[ ] No external dataset expansion performed
[ ] No git commit
[ ] No git push
```

---

# 17. FINAL RESPONSE FORMAT

After completing the inspection, respond with:

```text
DATASET RECONCILIATION COMPLETE

Actual filesystem state:
Authoritative candidate pool:
Reason:

Key counts:
- ...
- ...
- ...

Conflicts found:
- ...

Files created:
- DATASET_STATE_RECONCILIATION_REPORT.md

Training: NOT EXECUTED
Inference: NOT EXECUTED
Acquisition: NOT EXECUTED
Production changes: NONE
Git commit/push: NONE
```

Do not claim anything that was not verified from the actual repository/filesystem.

## STOP CONDITION

Once `DATASET_STATE_RECONCILIATION_REPORT.md` is created and the state is mathematically reconciled:

**STOP.**

Do not continue into human curation.
Do not continue into dataset preparation.
Do not continue into LoRA training.
Do not continue into ControlNet training.
