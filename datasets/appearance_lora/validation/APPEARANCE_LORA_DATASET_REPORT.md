# JewelMind — Appearance-LoRA Dataset Quality Report

> **PHASE 8 DATASET VALIDATION REPORT**  
> **Prepared**: 2026-09-02 21:00:06 UTC  
> **Source Curation**: `datasets/curation/HUMAN_CURATION_FINAL.csv`  
> **Training Executed**: **NO**  
> **Inference Executed**: **NO**  

---

## 1. Dataset Summary

* **Source Candidate Pool**: 226 candidates
* **Authoritative Curated KEEP**: **164 images** (100.0% openable and verified)
* **Authoritative Curated REJECT**: **62 candidates** (excluded from dataset)
* **Pending REVIEW**: **0** (fully resolved curation)
* **Training Split**: **147 images** (89.6%)
* **Validation Split**: **17 images** (10.4%)

---

## 2. Image Validation & Integrity

* **Total Images Processed**: 164
* **Readable & Validated**: **164 (100.0%)**
* **Corrupted / Unreadable**: **0**
* **Unsupported Formats**: **0** (All JPEG/RGB)
* **Zero-Byte Files**: **0**
* **Cryptographic SHA-256 Byte Collisions in KEEP**: **0** (All 164 files are byte-distinct)
* **Cross-Split Leakage**: **0** (Near-duplicate clusters grouped together; zero SHA overlap between train and validation)

---

## 3. Category Distribution

| Canonical Category | Total KEEP | % of Pool | Train Split | Val Split |
| :--- | ---:| ---:| ---:| ---:|
| **`ring`** | 29 | 17.7% | 26 | 3 |
| **`earring`** | 26 | 15.9% | 23 | 3 |
| **`pendant`** | 50 | 30.5% | 45 | 5 |
| **`necklace`** | 22 | 13.4% | 20 | 2 |
| **`bracelet`** | 14 | 8.5% | 13 | 1 |
| **`bangle`** | 3 | 1.8% | 3 | 0 |
| **`brooch`** | 17 | 10.4% | 14 | 3 |
| **`other`** | 3 | 1.8% | 3 | 0 |
| **Total** | **164** | **100.0%** | **147** | **17** |

---

## 4. Resolution & Aspect Ratio Distribution

* **Widths**: Min = 513 px | Max = 1263 px | Median = 838 px
* **Heights**: Min = 513 px | Max = 900 px | Median = 893 px
* **Aspect Ratios (W/H)**: Min = 0.620 | Max = 1.846 | Median = 1.016
* **Aspect Ratio Preservation**: Original silhouettes and jewel geometry are 100% preserved. No destructive center-cropping was applied to raw images.

---

## 5. Caption Validation

* **Total Captions Generated**: 164 individual `.txt` files + `metadata.jsonl`
* **Missing Captions**: **0**
* **Empty Captions**: **0**
* **Unverifiable / Hallucinated Claims**: **0** (Strictly grounded in observable category, metal reflections, and verified metadata)
* **Average Caption Length**: ~20 words / 130 characters (ideal for CLIP text encoder without truncation)

---

## 6. Duplicate & Leakage Validation

* **Cryptographic SHA-256 Check**: 164 unique hashes.
* **Near-Duplicate Cluster Preservation**: Items linked by perceptual similarity (`duplicate_of`) were partitioned as atomic units, ensuring that multi-angle views of the same object remain entirely within either the `train` split or the `validation` split.
* **Train / Val Overlap**: Exactly **0 bytes / 0 images** overlap.

---

## 7. License Traceability

* **100% Public Domain**: All 164 images originate from the Cleveland Museum of Art Open Access Collection under **CC0 1.0 Universal**.
* Fully legal for ₹0 budget fine-tuning and commercial deployment.
