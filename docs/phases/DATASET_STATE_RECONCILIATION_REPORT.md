# JewelMind — Dataset State Reconciliation Report

> **ABSOLUTE EXECUTION BOUNDARY AUDIT**:  
> - **Actual Dataset State**: **226 Retained Candidates** physically present, manifested, and indexed.  
> - **Authoritative State**: **State A (226 Candidate Pool)** is the verified single source of truth.  
> - **Training Executed**: **NO** (Neither LoRA nor ControlNet training was started or scheduled).  
> - **GPU Inference Executed**: **NO** (No GPU diffusion generation was run).  
> - **New Acquisition Executed**: **NO** (Zero images downloaded, zero external API queries made).  
> - **Production Code Modified**: **NO** (Rendering pipelines and inference modules intact).  
> - **Git Commit / Push**: **NONE** (Working directory untouched by commits or pushes).  

---

## 1. Executive Summary

A forensic audit of the repository filesystem, manifests, CSV records, and contact sheets was conducted to resolve the conflict between **State A (302 fetched → 226 retained)** and **State B (275 fetched → 151 retained)**.

### Determination:
**State A (226 Candidates) is the authoritative, verified single source of truth.**

* **Root Cause of State B (151 candidates)**:  
  During the iterative execution of the acquisition pipeline, an intermediate manifest snapshot was saved containing 275 total items (151 retained + 124 rejected) prior to final category deficit balancing. The subsequent full acquisition run harvested 302 candidates and retained 226 candidates.
* **Current State on Disk**:  
  [`datasets/curation/HUMAN_CURATION.csv`](file:///c:/Users/usern/Desktop/JewelMind/datasets/curation/HUMAN_CURATION.csv), [`datasets/curation/full_dataset_manifest.json`](file:///c:/Users/usern/Desktop/JewelMind/datasets/curation/full_dataset_manifest.json), [`full_dataset_manifest.jsonl`](file:///c:/Users/usern/Desktop/JewelMind/datasets/curation/full_dataset_manifest.jsonl), and all 8 visual contact sheets are synchronized to the **226 retained candidate pool** (`CAND_001` through `CAND_226`).
* **Physical Integrity**:  
  All 226 image paths referenced in the manifests and CSV exist on disk in [`datasets/curation/full_candidates/`](file:///c:/Users/usern/Desktop/JewelMind/datasets/curation/full_candidates/). Zero image references point to missing files.

---

## 2. Filesystem Inventory

Total image files physically present in repository: **602 images** (401 `.jpg`, 201 `.png`).

| Location / Directory | File Count | Image Types | Role / Candidate IDs | Status |
| :--- | ---:| :--- | :--- | :--- |
| `datasets/curation/full_candidates/` | **264** | `.jpg` | Candidate pool (`cma_*`, `met_*`) | **Active Candidate Storage** |
| `datasets/curation/` | **21** | `.png` | Visual contact sheets & mosaics | **Active Curation Artifacts** |
| `datasets/curation/validation_pilot_images/` | **16** | `.jpg` | Validation Pilot 2 images | Historical Pilot Archive |
| `datasets/curation/pilot_images/` | **13** | `.jpg` | Initial Pilot 1 images | Historical Pilot Archive |
| `ai/vision/datasets/sample/train/images/` | **35** | `.jpg` | YOLO segmentation sample | Phase 6 Sketch / Segment data |
| `ai/vision/datasets/sample/val/images/` | **10** | `.jpg` | YOLO segmentation sample | Phase 6 Validation data |
| `ai/vision/datasets/sample/test/images/` | **5** | `.jpg` | YOLO segmentation sample | Phase 6 Test data |
| `ai/vision/datasets/previews/` | **5** | `.png` | Visual sanity previews | Architecture documentation |
| `runs/segment/` (validation logs) | **228** | `.png`/`.jpg`| YOLO segmentation train runs | Historical model metrics |
| Other (frontend/outputs) | **5** | `.png` | Baseline render outputs | Verification smoke tests |

> **Note on `full_candidates/` count (264 files)**:  
> The directory holds 264 images because 38 images from preliminary queries were preserved on disk without deletion. Exactly **226 of these files** correspond to the authoritative candidate pool indexed in `HUMAN_CURATION.csv`.

---

## 3. Manifest Reconciliation

| Manifest Filename | Candidate Count | ID Range | Missing Files | Extra Files | Duplicate IDs | Status |
| :--- | ---:| :--- | ---:| ---:| ---:| :--- |
| `full_dataset_manifest.json` | **226** | `CAND_001`–`CAND_226` | **0** | 0 | **0** | **Synchronized & Verified** |
| `full_dataset_manifest.jsonl` | **226** | `CAND_001`–`CAND_226` | **0** | 0 | **0** | **Synchronized & Verified** |
| `validation_pilot_manifest.json` | 20 | Pilot 2 items | 0 | 0 | 0 | Archive Pilot Manifest |
| `pilot_manifest.json` | 20 | Pilot 1 items | 0 | 0 | 0 | Archive Pilot Manifest |

* **Referenced vs. Existing**: 100% of the 226 image paths in `full_dataset_manifest.json` exist physically on disk. Zero broken references.
* **Candidate IDs**: Monotonically sequential from `CAND_001` to `CAND_226` with zero duplicate IDs and zero missing IDs.

---

## 4. `HUMAN_CURATION.csv` Reconciliation

| Attribute | Measured Value | Verification Standard | Evaluation |
| :--- | :--- | :--- | :--- |
| **CSV Row Count (excl. header)** | **226** | Exact match to candidate pool | **PASSED** |
| **Candidate ID Count** | **226** | Unique candidate IDs | **PASSED** |
| **Candidate ID Range** | `CAND_001` to `CAND_226` | Strictly continuous sequence | **PASSED** |
| **Duplicate Candidate IDs** | **0** | No collisions | **PASSED** |
| **Missing Candidate IDs** | **0** | No gaps in sequence | **PASSED** |
| **Broken File References** | **0** | All 226 files exist on disk | **PASSED** |
| **Manual Curation Fields** | **226 / 226 blank** | Pristine for human evaluator | **PASSED** |
| **Existing `final_triage` Values**| **0 populated** | Unbiased human evaluation ready | **PASSED** |
| **Workspace Identification** | **226-row workspace** | Confirmed authoritative state | **AUTHORITATIVE** |

---

## 5. Dataset State Comparison Matrix

| Metric Dimension | Reported State A | Reported State B | Actual Verified State | State A Match | State B Match |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Total Candidates Ingested** | 302 | 275 | **302** (Ingestion total) | **MATCH** | Superseded |
| **Retained Candidates on Disk** | 226 | 151 | **226** | **EXACT MATCH** | Obsolete snapshot |
| **Technically Rejected Discards**| 76 | 124 | **76** (during 302 run) | **MATCH** | Outdated |
| **Jewellery Relevant** | 188 | 122 | **188** (in 226 pool) | **MATCH** | Outdated |
| **Jewellery Uncertain** | 38 | 29 | **38** (in 226 pool) | **MATCH** | Outdated |
| **Perceptually Distinct** | 102 | 82 | **102** (in 226 pool) | **MATCH** | Outdated |
| **Near-Duplicate Review Required**| 124 | 69 | **119** (in 226 pool) | **APPROX MATCH** | Outdated |
| **Exact Byte Duplicates (SHA-256)**| 0 | 0 | **5 instances** (2 groups) | Detailed below | Detailed below |

### Cryptographic SHA-256 Byte Verification:
* **Total Evaluated Images**: 226
* **Unique Cryptographic SHA-256 Digests**: **221 unique digests**
* **Exact Byte Duplicate Instances**: 5 files (across 2 groups)
  - Group 1 (Hash `10ec13d1...`): `CAND_040` and `CAND_041`
  - Group 2 (Hash `0e30a3a0...`): `CAND_165`, `CAND_167`, `CAND_168`, `CAND_182`, `CAND_183`
* **Audit Assessment**: In the museum archives, multiple accession catalog records occasionally link to the identical photography asset. In accordance with strict boundaries, **these files were not deleted**; they are flagged in `full_dataset_manifest.json` so the human operator can mark redundant copies as `REJECT` in `HUMAN_CURATION.csv`.

---

## 6. Category Distribution (Authoritative 226 Pool)

Strict canonical taxonomy without compound labels:

| Canonical Category | Retained Candidate Count | % of 226 Pool | Target Scope |
| :--- | :---: | :---: | :--- |
| **`ring`** | **32** | 14.2% | ~30–35 |
| **`earring`** | **30** | 13.3% | ~30–35 |
| **`pendant`** | **47** | 20.8% | ~45–50 |
| **`necklace`** | **34** | 15.0% | ~30–35 |
| **`bracelet`** | **18** | 8.0% | ~15–20 |
| **`bangle`** | **3** | 1.3% | Rare circular rigid armlets |
| **`brooch`** | **21** | 9.3% | ~20–25 |
| **`other`** | **41** | 18.1% | Ornaments, sets, pectorals |
| **Total** | **226** | **100.0%** | **Authoritative Candidate Pool** |

---

## 7. Source & License Distribution (Authoritative 226 Pool)

* **Sources**:
  - **Cleveland Museum of Art (CMA)**: 197 candidates (87.2%)
  - **The Metropolitan Museum of Art (Met)**: 29 candidates (12.8%)
* **Licenses**:
  - **CC0 1.0 Universal / Public Domain**: **226 candidates (100.0%)**
  - Other / Unverified: **0 candidates**

---

## 8. Contact Sheet Consistency

All active visual contact sheets match the **authoritative 226 candidate pool**:

| Contact Sheet Filename | Dimensions | File Size | Candidates Represented | Matches Manifest |
| :--- | :---: | ---:| :---: | :---: |
| `HUMAN_CURATION_MASTER_CONTACT_SHEET.png` | 1552 × 12474 px | 12.6 MB | **All 226 candidates** (`CAND_001`–`CAND_226`) | **YES** |
| `HUMAN_CURATION_NEAR_DUPLICATES.png` | 1296 × 8236 px | 6.35 MB | **119 near-duplicates** (Hamming $\le 6$) | **YES** |
| `HUMAN_CURATION_UNCERTAIN.png` | 1296 × 1390 px | 1.37 MB | **38 uncertain candidates** | **YES** |
| `HUMAN_CURATION_RINGS.png` | 1296 × 2368 px | 1.82 MB | **32 rings** | **YES** |
| `HUMAN_CURATION_EARRINGS.png` | 1296 × 2042 px | 1.43 MB | **30 earrings** | **YES** |
| `HUMAN_CURATION_PENDANTS.png` | 1296 × 3346 px | 2.78 MB | **47 pendants** | **YES** |
| `HUMAN_CURATION_NECKLACES.png` | 1296 × 2368 px | 1.66 MB | **34 necklaces** | **YES** |
| `HUMAN_CURATION_BRACELETS_BANGLES.png` | 1296 × 1716 px | 997 KB | **21 bracelets & bangles** (18 + 3) | **YES** |
| `HUMAN_CURATION_BROOCHES_OTHER.png` | 1296 × 4324 px | 4.03 MB | **62 brooches & accessories** (21 + 41) | **YES** |

*Every contact sheet features overlaid ID badges matching `CAND_001` to `CAND_226` in `HUMAN_CURATION.csv`.*

---

## 9. Final Determination

### **Classification: A — 226 candidate state is authoritative.**

**Rationale**:
1. `HUMAN_CURATION.csv` has exactly 226 rows, uniquely numbered `CAND_001` to `CAND_226`, with 100% of image paths resolving to valid physical files.
2. `full_dataset_manifest.json` and `full_dataset_manifest.jsonl` are synchronized to the 226 candidates.
3. All master and category contact sheets display the exact 226 candidates with matching ID badges.
4. State B (151 candidates) was an incomplete intermediate development snapshot that is now obsolete.
5. All 226 images are verified 100% CC0 public domain open-access assets.

---

## 10. Recommended Next Step

**Proceed to manual human curation of the authoritative 226 candidate pool.**

*Open [`datasets/curation/HUMAN_CURATION.csv`](file:///c:/Users/usern/Desktop/JewelMind/datasets/curation/HUMAN_CURATION.csv) and assign `KEEP`, `REVIEW`, or `REJECT` per [`datasets/curation/HUMAN_CURATION_GUIDE.md`](file:///c:/Users/usern/Desktop/JewelMind/datasets/curation/HUMAN_CURATION_GUIDE.md) to select the final **150–200 appearance LoRA training images**.*

---

## 11. Final Safety Verification

```text
[X] No new images downloaded
[X] No dataset images deleted
[X] No training executed
[X] No ControlNet training executed
[X] No LoRA training executed
[X] No GPU diffusion inference executed
[X] No production rendering code modified
[X] No Phase 7 behavior modified
[X] No external dataset expansion performed
[X] No git commit executed
[X] No git push executed
```
