# JewelMind — Pilot Deduplication & Met Query Strategy Fix Report

> **MANDATORY POLICY ENFORCEMENT**:  
> **PIPELINE TOOLING AUDIT & CORRECTION ONLY**  
> - Antigravity has NOT executed any model training.
> - No GPU inference was launched.
> - No large dataset acquisition or download was performed beyond the 20-candidate pilot.
> - All corrections have been validated through deterministic unit tests.

---

## 1. Executive Summary & Problems Identified in Pilot Review

The pilot acquisition run successfully validated end-to-end API harvesting, quality filtering, and manifest persistence, but exposed two significant operational weaknesses that required architectural correction before scaling:

1. **The Met Search Strategy Was Overly Broad**:
   - Querying `"gold"` or `"gold ring"` matched any artwork containing gold leaf, decorative gold trim, or gold alloy.
   - This accepted non-jewellery items into candidates: table clocks, porcelain vases, Japanese folding screens, and Inca effigies.
2. **Binary Deduplication Was Too Aggressive**:
   - A single hard threshold ($\text{Hamming Distance} \le 6$) caused false positives.
   - For example, `cma_130309` and `cma_132047` were materially distinct gold pendants, and `cma_115163` was a distinct Akan disk pendant, yet both were silently discarded because small structural features produced low 64-bit gradient differences.

---

## 2. Root Cause Analysis: Why Original dHash Produced False Positives

* **How dHash Operates**:
  Difference hash resizes an image to $9 \times 8$ grayscale and computes a 64-bit gradient boolean map:
  $$\text{bit}_{r, c} = (\text{pixel}_{r, c+1} > \text{pixel}_{r, c})$$
* **The Failure Mode on Studio Jewellery Photography**:
  - Fine jewellery product shots often feature a bright, centered piece against a uniform white or light grey canvas.
  - At $9 \times 8$ resolution, small objects (e.g. a round pendant vs. an oval medallion vs. an animal figurine) all collapse into similar low-frequency gradient profiles: light $\to$ dark central object $\to$ light.
  - The Hamming distance between two completely different pieces of jewellery on identical white studio backdrops can easily fall between **3 and 6 bits**.
* **The Architectural Flaw**:
  - Treating any distance $\le 6$ as an **automatic rejection** silently discarded valid, distinct training assets.
  - Perceptual hashing alone cannot capture high-frequency semantic distinctions like gemstone cuts or filigree patterns.

---

## 3. New Tiered Duplicate Decision Logic

We replaced the binary accept/reject mechanism with a **three-tier classification**:

| Tier Category | Threshold | Pipeline Action | Rationale |
| :--- | :--- | :--- | :--- |
| **`EXACT_DUPLICATE`** | $\text{Distance} \le 1$ | **Auto-Rejected** | Identical or near-zero pixel variation (identical file re-uploads or lossless re-compressions). Safe to discard automatically. |
| **`NEAR_DUPLICATE_REVIEW_REQUIRED`** | $1 < \text{Distance} \le 6$ | **PRESERVED ON DISK** (Marked for Operator Review) | Candidate exhibits visual similarity (e.g. slight angle shift or similar silhouette). **Never silently rejected**. Saved to disk, cataloged in manifest, and flagged for human decision. |
| **`DISTINCT`** | $\text{Distance} > 6$ | **Accepted** | Clear structural separation; accepted into training pool. |

Both 64-bit **dHash** and **aHash** signatures are retained in the machine-readable manifest (`pilot_manifest.jsonl`) alongside `duplicate_status`, `duplicate_distance`, and `duplicate_of`.

---

## 4. New Met Query & Relevance Strategy

### 4.1 Specific Targeted Jewellery Queries
Replaced broad generic terms (`gold`, `gold object`) with specific jewellery taxonomy:
- `"finger ring"`
- `"ring"`
- `"earrings"`
- `"gemstone pendant"`
- `"pendant"`
- `"necklace"`
- `"brooch"`
- `"bracelet"`
- `"bangle"`
- `"jewelry"`

### 4.2 Department-Scoped Filtering
The Met collection search is now scoped to departments known to house genuine jewellery:
- **Dept 12**: *European Sculpture and Decorative Arts* (master goldsmithing, rings, pendants)
- **Dept 1**: *American Decorative Arts*
- **Dept 13**: *Greek and Roman Art* (ancient gold rings, cameos, bezels)
- **Dept 10**: *Egyptian Art* (pectorals, amulets, signet rings)
- **Dept 14**: *Islamic Art* (filigree gold, enameled jewelry)
- **Dept 5**: *Arts of Africa, Oceania, and the Americas* (pre-Columbian and Akan goldwork)

### 4.3 Automated Non-Jewellery Pre-Filtering
Before downloading image bytes, `assess_jewellery_relevance()` inspects `classification`, `title`, and `medium`:
- **Exclusion Filters**:
  - Clocks, horology, watches, vases, vessels, ceramics, porcelain.
  - Screen paintings, textiles, costumes, sculptures, statues, effigies, figurines.
  - Arms, armor, swords, daggers, furniture, reliquaries, altars, chalices, snuffboxes.
- **Relevance Tracking in Manifest**:
  Every item now records:
  - `jewellery_relevance`: `"JEWELLERY_RELEVANT"`, `"JEWELLERY_UNCERTAIN"`, or `"NOT_JEWELLERY"`
  - `category_confidence`: `"HIGH"`, `"MEDIUM"`, or `"LOW"`
  - `department`, `classification`, `medium`, and `search_query`

This ensures that the report clearly separates **`TECHNICALLY_VALID`** (resolution, format) from **`JEWELLERY_RELEVANT`** (domain utility).

---

## 5. Automated Unit Test Verification

The updated test suite in [`tests/ai/test_dataset_pipeline.py`](file:///c:/Users/usern/Desktop/JewelMind/tests/ai/test_dataset_pipeline.py) specifically validates all fix criteria:

```
============================= test session starts =============================
platform win32 -- Python 3.10.19 (tgpu)
rootdir: C:\Users\usern\Desktop\JewelMind

tests/ai/test_rendering.py .......                                       [ 35%]
tests/ai/test_training_infra.py .....                                    [ 60%]
tests/ai/test_dataset_pipeline.py::test_image_filter_rejects_undersized_images PASSED [ 65%]
tests/ai/test_dataset_pipeline.py::test_image_filter_detects_corruption PASSED [ 70%]
tests/ai/test_dataset_pipeline.py::test_image_filter_accepts_valid_jewellery_image PASSED [ 75%]
tests/ai/test_dataset_pipeline.py::test_tiered_deduplication_exact_vs_review_vs_distinct PASSED [ 80%]
tests/ai/test_dataset_pipeline.py::test_near_duplicate_does_not_auto_reject PASSED [ 85%]
tests/ai/test_dataset_pipeline.py::test_met_targeted_query_construction PASSED [ 90%]
tests/ai/test_dataset_pipeline.py::test_jewellery_relevance_assessment PASSED [ 95%]
tests/ai/test_dataset_pipeline.py::test_metadata_preservation_in_manifest PASSED [100%]

======================== 20 passed, 1 warning in 7.01s ========================
```

---

## 6. Boundary & Compliance Confirmation

- **Zero Model Training**: Neither `train_lora.py` nor ControlNet training was started or scheduled.
- **Zero GPU Inference**: No diffusion models were loaded into VRAM.
- **Zero Dataset Scaling**: The dataset has NOT been scaled to 150–300 images yet. Only the 20 pilot candidates were processed.
- **Zero Git Operations**: No branches were merged, committed, or pushed.
