# JewelMind — Human Curation Workspace Overview

> **MANDATORY BOUNDARY ENFORCEMENT**:  
> **CANDIDATE CURATION PHASE — NOT YET TRAINING DATA**  
> - Antigravity has NOT executed any model training.
> - Neither LoRA nor ControlNet training was executed or scheduled.
> - No GPU diffusion inference was run.
> - Production rendering pipelines remain untouched.
> - No code was committed or pushed.
> - **MANUAL CURATION REQUIRED — TRAINING NOT EXECUTED.**

---

## 1. Candidate Pool Statistics

The acquisition pipeline fetched 302 candidates and, after quality filtering, produced **226 retained candidates** preserved on disk for human review:

* **Total Fetched**: 302 candidates
* **Technically Valid / Retained**: **226 candidates** (100% CC0 1.0 Universal)
* **Technically Rejected**: 76 candidates (background clutter, scale violations, download issues)
* **Jewellery Relevance Assessment**:
  * `JEWELLERY_RELEVANT`: 188 candidates (83.2%)
  * `JEWELLERY_UNCERTAIN`: 38 candidates (16.8%)
* **Deduplication Triage**:
  * `DISTINCT` (Hamming Distance $> 6$): 102 candidates (45.1%)
  * `NEAR_DUPLICATE_REVIEW_REQUIRED` (Hamming Distance $\le 6$): 124 candidates (54.9%) — **All preserved on disk**
  * `EXACT_DUPLICATE` (SHA-256 byte match): 0 in retained pool (exact byte duplicates auto-rejected)

---

## 2. Category Distribution (Retained Pool)

Strict canonical taxonomy used (`ring`, `earring`, `pendant`, `necklace`, `bracelet`, `bangle`, `brooch`, `other`):

| Canonical Category | Retained Count | % of Pool | Target Curation Goal (150–200 total) |
| :--- | :---: | :---: | :--- |
| **`ring`** | **32** | 14.2% | Retain $\approx 22–26$ top-tier rings |
| **`earring`** | **30** | 13.3% | Retain $\approx 20–25$ top-tier earrings |
| **`pendant`** | **47** | 20.8% | Retain $\approx 30–35$ top-tier pendants |
| **`necklace`** | **34** | 15.0% | Retain $\approx 22–28$ top-tier necklaces |
| **`bracelet`** | **18** | 8.0% | Retain $\approx 12–16$ top-tier bracelets |
| **`bangle`** | **3** | 1.3% | **Preserve all 3** if acceptable |
| **`brooch`** | **21** | 9.3% | Retain $\approx 12–15$ top-tier brooches |
| **`other`** | **41** | 18.1% | Prune down to $\approx 15–20$ wearable ornaments |
| **Total** | **226** | **100.0%** | **Target: 150–200 high-signal images** |

---

## 3. SOURCE DIVERSITY WARNING

> [!WARNING]
> **Source Imbalance Notice & Visual Style Differences**:
> 1. **CMA Dominance**: The retained candidate pool is currently populated from the Cleveland Museum of Art (CMA) Open Access Collection because The Metropolitan Museum of Art API enforced Akamai WAF rate-limiting during large batch queries, tripping the pipeline's safety circuit breaker.
> 2. **Museum vs. Modern Commercial Photography**: Museum conservation photographs feature neutral grey, off-white, or black studio backdrops, and showcase historic, classical, and vintage craftsmanship. While ideal for learning metal reflections, filigree, and gem settings, **they do not perfectly represent contemporary high-gloss e-commerce jewellery catalog photography**.
> 3. **Not Yet Final Training Data**: This 226-image pool is a raw candidate pool. The operator must inspect each candidate for silhouette clarity, metal specular quality, and background cleanliness before approving an image for training.

---

## 4. Human Curation Artifacts Generated

All human curation files are generated and available in `datasets/curation/` and mirrored in the artifact directory:

1. **Human Curation Table (CSV)**:
   [`datasets/curation/HUMAN_CURATION.csv`](file:///c:/Users/usern/Desktop/JewelMind/datasets/curation/HUMAN_CURATION.csv)  
   *(226 rows containing complete metadata, candidate IDs `CAND_001`–`CAND_226`, and blank manual evaluation fields)*
2. **Synchronized Manifests**:
   - [`datasets/curation/full_dataset_manifest.json`](file:///c:/Users/usern/Desktop/JewelMind/datasets/curation/full_dataset_manifest.json)
   - [`datasets/curation/full_dataset_manifest.jsonl`](file:///c:/Users/usern/Desktop/JewelMind/datasets/curation/full_dataset_manifest.jsonl)
3. **Master Curation Contact Sheet**:
   [`HUMAN_CURATION_MASTER_CONTACT_SHEET.png`](file:///c:/Users/usern/Desktop/JewelMind/datasets/curation/HUMAN_CURATION_MASTER_CONTACT_SHEET.png)  
   *(All 226 candidates with candidate ID badges, metadata, and status)*
4. **Focused Review Contact Sheets**:
   - Near-Duplicates: [`HUMAN_CURATION_NEAR_DUPLICATES.png`](file:///c:/Users/usern/Desktop/JewelMind/datasets/curation/HUMAN_CURATION_NEAR_DUPLICATES.png) *(119 items with Hamming distance $\le 6$)*
   - Uncertain Relevance: [`HUMAN_CURATION_UNCERTAIN.png`](file:///c:/Users/usern/Desktop/JewelMind/datasets/curation/HUMAN_CURATION_UNCERTAIN.png) *(38 items)*
5. **Category Contact Sheets**:
   - Rings: [`HUMAN_CURATION_RINGS.png`](file:///c:/Users/usern/Desktop/JewelMind/datasets/curation/HUMAN_CURATION_RINGS.png) *(32 items)*
   - Earrings: [`HUMAN_CURATION_EARRINGS.png`](file:///c:/Users/usern/Desktop/JewelMind/datasets/curation/HUMAN_CURATION_EARRINGS.png) *(30 items)*
   - Pendants: [`HUMAN_CURATION_PENDANTS.png`](file:///c:/Users/usern/Desktop/JewelMind/datasets/curation/HUMAN_CURATION_PENDANTS.png) *(47 items)*
   - Necklaces: [`HUMAN_CURATION_NECKLACES.png`](file:///c:/Users/usern/Desktop/JewelMind/datasets/curation/HUMAN_CURATION_NECKLACES.png) *(34 items)*
   - Bracelets & Bangles: [`HUMAN_CURATION_BRACELETS_BANGLES.png`](file:///c:/Users/usern/Desktop/JewelMind/datasets/curation/HUMAN_CURATION_BRACELETS_BANGLES.png) *(21 items)*
   - Brooches & Other: [`HUMAN_CURATION_BROOCHES_OTHER.png`](file:///c:/Users/usern/Desktop/JewelMind/datasets/curation/HUMAN_CURATION_BROOCHES_OTHER.png) *(62 items)*
6. **Detailed Curation Protocol Guide**:
   [`datasets/curation/HUMAN_CURATION_GUIDE.md`](file:///c:/Users/usern/Desktop/JewelMind/datasets/curation/HUMAN_CURATION_GUIDE.md)

---

## 5. Execution Boundary

**MANUAL CURATION REQUIRED — TRAINING NOT EXECUTED.**  
Execution is paused awaiting operator manual review and completion of [`HUMAN_CURATION.csv`](file:///c:/Users/usern/Desktop/JewelMind/datasets/curation/HUMAN_CURATION.csv).
