# JewelMind — Validation Pilot Acquisition & Curation Report

> **VALIDATION PILOT SCOPE**: Fresh 20-candidate validation of corrected search taxonomy and tiered deduplication.  
> **MANDATORY BOUNDARY**: Zero model training executed. Zero diffusion inference run. These 16 retained images are for pipeline validation, NOT for training by themselves.

---

## 1. Executive Summary: Exact Stage-by-Stage Pipeline Reconciliation

Below is the complete, stage-by-stage accounting reconciling the 20 fetched candidates, the technical filter decisions, duplicate classification, relevance categorization, and manifest triage statuses.

### Pipeline Stage Flowchart & Cardinality Accounting
```
[TOTAL FETCHED: 20 Candidates] (Met: 10, CMA: 10)
   ├── Relevance at Ingestion: JEWELLERY_RELEVANT: 15, JEWELLERY_UNCERTAIN: 5, NOT_JEWELLERY: 0
   │
   ├── Technical Quality Filter ──────────────┐
   │                                          │
   ▼                                          ▼
[TECHNICALLY VALID: 16 Candidates]   [TECHNICALLY REJECTED: 4 Candidates]
   │  - Rings: 8                         - 1 Foreground Too Large (Subject 96.1%)
   │  - Other: 5                         - 1 Foreground Too Small (Subject 7.7%)
   │  - Pendants: 3                      - 1 Download Timeout (URL encoding)
   │  - Relevance: Relevant=12, Uncert=4 - 1 Excessive Background Clutter (std=89.9)
   │                                     (Relevance: 3 Relevant, 1 Uncertain)
   ├── Deduplication & Triage
   │
   ├── EXACT_DUPLICATE (SHA-256): 0
   ├── NEAR_DUPLICATE_REVIEW_REQUIRED (dHash/aHash dist <= 6): 4 (All preserved on disk)
   └── DISTINCT (dist > 6): 12
   │
   ▼
[FINAL STATUS IN MANIFEST: 16 Retained Candidates on Disk]
   ├── ACCEPTED: 9 Candidates (Distinct AND Jewellery Relevant)
   │     - Rings: 6, Pendants: 3
   └── REVIEW_REQUIRED: 7 Candidates (Preserved on Disk for Operator Triage)
         - 3 Near-Duplicate Review Required (Jewellery Relevant)
         - 1 Near-Duplicate Review Required (Jewellery Uncertain)
         - 3 Distinct (Jewellery Uncertain)
```

---

## 2. Quantitative Accounting Matrix

| Accounting Metric | Count | % of Fetched (20) | % of Valid (16) | Stage / Scope | Description |
| :--- | :---: | :---: | :---: | :--- | :--- |
| **`TOTAL_FETCHED`** | **20** | 100.0% | — | Ingestion (Batch Total) | Raw items retrieved via open-access APIs |
| **`TECHNICALLY_VALID`** | **16** | 80.0% | 100.0% | Filter Output | Passed min resolution ($\ge 512\times 512$), decode, & clutter limits |
| **`TECHNICALLY_REJECTED`** | **4** | 20.0% | — | Filter Discards | Failed technical bounds (foreground ratio, clutter, timeout) |
| **`JEWELLERY_RELEVANT` (Total Fetched)** | **15** | 75.0% | — | Ingestion Assessment | Confirmed jewellery terms across all 20 fetched candidates |
| **`JEWELLERY_RELEVANT` (Retained/Valid)** | **12** | 60.0% | 75.0% | Retained Pool (16) | Confirmed jewellery in the 16 retained images on disk |
| **`JEWELLERY_UNCERTAIN` (Total Fetched)** | **5** | 25.0% | — | Ingestion Assessment | General ornament/stone across all 20 fetched candidates |
| **`JEWELLERY_UNCERTAIN` (Retained/Valid)**| **4** | 20.0% | 25.0% | Retained Pool (16) | Uncertain items preserved on disk for manual operator triage |
| **`NOT_JEWELLERY`** | **0** | 0.0% | 0.0% | Ingestion Pre-Filter | Clocks, vases, screen paintings pre-filtered before download |
| **`EXACT_DUPLICATE` (SHA-256)** | **0** | 0.0% | 0.0% | Deduplication | Zero cryptographic byte duplicates detected in this batch |
| **`NEAR_DUPLICATE_REVIEW_REQUIRED`** | **4** | 20.0% | 25.0% | Deduplication | $1 < \text{Distance} \le 6$; **all 4 preserved on disk** |
| **`DISTINCT` (Retained/Valid)** | **12** | 60.0% | 75.0% | Deduplication | Structural separation $> 6$; all 12 preserved on disk |

### Reconciliation Sum Check
1. **Total Ingestion Check**: $\text{TECHNICALLY\_VALID (16)} + \text{TECHNICALLY\_REJECTED (4)} = \mathbf{20}$
2. **Relevance Ingestion Check**: $\text{RELEVANT (15)} + \text{UNCERTAIN (5)} + \text{NOT\_JEWELLERY (0)} = \mathbf{20}$
3. **Relevance Retained Check**: $\text{RELEVANT In Valid (12)} + \text{UNCERTAIN In Valid (4)} = \mathbf{16}$
4. **Relevance Rejected Check**: $\text{RELEVANT In Rejected (3)} + \text{UNCERTAIN In Rejected (1)} = \mathbf{4}$
5. **Deduplication Check (Valid 16)**: $\text{EXACT (0)} + \text{NEAR\_DUP (4)} + \text{DISTINCT (12)} = \mathbf{16}$
6. **Manifest Status Check (Valid 16)**: $\text{ACCEPTED (9)} + \text{REVIEW\_REQUIRED (7)} = \mathbf{16}$

---

## 3. Category Distribution Reconciliation

### 3.1 Retained Candidates on Disk (16 Items)
| Jewellery Category | Retained Count | % of Retained (16) | Examples |
| :--- | :---: | :---: | :--- |
| **`Ring`** | 8 | 50.0% | `met_256193` (Hermes ring), `cma_152815` (Nike ring), `met_573599` (Archer's ring) |
| **`Other`** | 5 | 31.25% | `cma_161779` (Belt buckle), `met_449311` (Seal stone), `met_464148` (Virgin medallion) |
| **`Pendant`** | 3 | 18.75% | `cma_154807` (Pendant), `cma_129226` (Face in crescent), `cma_157568` (Octagonal) |
| **Total Retained** | **16** | **100.0%** | All 16 images physically exist on disk in `validation_pilot_images/` |

### 3.2 Rejected Candidates (4 Items)
| Category | Rejected Count | Rejection Reason |
| :--- | :---: | :--- |
| **`Pendant`** | 1 | `met_451270`: Subject occupies 96.1% of canvas (`FOREGROUND_TOO_LARGE`) |
| **`Ring`** | 1 | `met_244899`: Subject occupies 7.7% of canvas (`FOREGROUND_TOO_SMALL`) |
| **`Other`** | 1 | `met_551786`: Download URL unicode encoding error (`DOWNLOAD_FAILED_OR_TIMEOUT`) |
| **`Other`** | 1 | `cma_117824`: Corner variance std=89.9 > 65.0 (`EXCESSIVE_BACKGROUND_CLUTTER`) |
| **Total Rejected** | **4** | **100.0%** |

### 3.3 Total Ingested Across Categories
- `Ring`: 8 retained + 1 rejected = **9**
- `Other`: 5 retained + 2 rejected = **7**
- `Pendant`: 3 retained + 1 rejected = **4**
- **Total**: 9 + 7 + 4 = **20 (100.0%)**

---

## 4. Manifest Status Reconciliation: `ACCEPTED` (9) vs `REVIEW_REQUIRED` (7)

Every one of the 16 retained images is assigned a triage status in the manifest:

### 4.1 `ACCEPTED` (9 Candidates)
Candidates that are both **`DISTINCT`** (distance > 6) and **`JEWELLERY_RELEVANT`** (high/medium category confidence):
1. `met_256193` — Gold finger ring engraved with Hermes (`ring`, Distinct, Valid)
2. `met_453048` — Ring (`ring`, Distinct, Valid)
3. `cma_154807` — Pendant (`pendant`, Distinct, Valid)
4. `cma_129226` — Pendant: Face in Crescent (`pendant`, Distinct, Valid)
5. `cma_95589` — Earring (`ring/earring`, Distinct, Valid)
6. `cma_157568` — Octagonal Pendant (`pendant`, Distinct, Valid)
7. `cma_94782` — Earring with Four-Armed Vishnu (`ring/earring`, Distinct, Valid)
8. `cma_152815` — Finger Ring with Figure of Nike (`ring`, Distinct, Valid)
9. `cma_94777` — Earring with Vishnu Riding Garuda (`ring/earring`, Distinct, Valid)

### 4.2 `REVIEW_REQUIRED` (7 Candidates Preserved on Disk)
Candidates preserved on disk that require human operator verification:
1. **`met_573599`** (*Archer's ring*): `JEWELLERY_RELEVANT`, `NEAR_DUPLICATE_REVIEW_REQUIRED` (Distance 4 of `met_256193`).
2. **`cma_161779`** (*Belt Buckle*): `JEWELLERY_RELEVANT`, `NEAR_DUPLICATE_REVIEW_REQUIRED` (Distance 4 of `cma_157568`).
3. **`cma_94781`** (*Earring with Vishnu Riding Garuda*): `JEWELLERY_RELEVANT`, `NEAR_DUPLICATE_REVIEW_REQUIRED` (Distance 2 of `cma_94782` — counterpart of pair).
4. **`met_449311`** (*Seal Stone*): `JEWELLERY_UNCERTAIN`, `NEAR_DUPLICATE_REVIEW_REQUIRED` (Distance 4 of `met_256193`).
5. **`met_464148`** (*Virgin and Child*): `JEWELLERY_UNCERTAIN`, `DISTINCT`.
6. **`met_853449`** (*Portrait of Sor Juana*): `JEWELLERY_UNCERTAIN`, `DISTINCT`.
7. **`met_189425`** (*The Louis XV Room*): `JEWELLERY_UNCERTAIN`, `DISTINCT`.

---

## 5. Visual Artifacts Verification

Both contact sheets are synchronized with the 16 retained images:
* **Accepted Contact Sheet** ([`VALIDATION_PILOT_ACCEPTED_CONTACT_SHEET.png`](file:///c:/Users/usern/Desktop/JewelMind/datasets/curation/VALIDATION_PILOT_ACCEPTED_CONTACT_SHEET.png)): Displays the 9 `ACCEPTED` candidates.
* **Review Contact Sheet** ([`VALIDATION_PILOT_REVIEW_CONTACT_SHEET.png`](file:///c:/Users/usern/Desktop/JewelMind/datasets/curation/VALIDATION_PILOT_REVIEW_CONTACT_SHEET.png)): Displays the 7 `REVIEW_REQUIRED` candidates (near-duplicates and uncertain relevance items).

---

## 6. Confirmation of Guardrails
- Model training: NOT EXECUTED.
- GPU inference: NOT EXECUTED.
- Scaling to 150–300: NOT EXECUTED.
- No code committed or pushed.
- All numbers mathematically reconciled and synchronized with `validation_pilot_manifest.json` and `jsonl`.
