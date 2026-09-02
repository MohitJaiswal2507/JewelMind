# JewelMind — Pilot Dataset Acquisition & Curation Report

> **PILOT RUN SCOPE**: This is a pipeline validation pilot (**~20 candidates**).
> **TRAINING NOTICE**: These 13 accepted images are **NOT suitable for training by themselves** (150–200 images are required for appearance LoRA). This run validates source harvesting, quality filtering, perceptual deduplication, and license metadata handling.

---

## 1. Executive Summary

* **Total Candidates Fetched**: `20`
* **Accepted Candidates**: `13` (65.0%)
* **Rejected Candidates**: `7` (35.0%)
* **Perceptual Near-Duplicates Detected**: `5`
* **Unresolved License Cases**: `0`

---

## 2. Rejection Reasons Breakdown

| Rejection Category | Count | Description |
| :--- | :--- | :--- |
| `NEAR_DUPLICATE` | 5 | Candidate failed automated quality/aspect criteria |
| `EXCESSIVE_BACKGROUND_CLUTTER` | 2 | Candidate failed automated quality/aspect criteria |

---

## 3. Source & Topology Distribution

### Source Distribution
| Source Repository | Total Fetched | Accepted |
| :--- | :--- | :--- |
| `MET` | 10 | 9 |
| `CMA` | 10 | 4 |

### Accepted Jewellery Category Distribution
| Category | Accepted Count | Percentage of Accepted |
| :--- | :--- | :--- |
| `other` | 9 | 69.2% |
| `pendant` | 4 | 30.8% |

---

## 4. License & Commercial Compliance Distribution

| License Tag | Status | Count |
| :--- | :--- | :--- |
| CC0 1.0 Universal (Public Domain) (VERIFIED_CC0) | Active | 10 |
| CC0 1.0 Universal (VERIFIED_CC0) | Active | 10 |

### Unresolved License Cases
*Zero unresolved license cases. All accepted assets have verified CC0 1.0 Universal public domain dedication.*

---

## 5. Duplicate & Near-Duplicate Log

* **Configured Hamming Distance Threshold**: `6`
- Candidate `cma_692270` matched existing `cma_692272` with Hamming distance `3` (Threshold: `6`).
- Candidate `cma_692273` matched existing `cma_692272` with Hamming distance `3` (Threshold: `6`).
- Candidate `cma_692269` matched existing `cma_692272` with Hamming distance `3` (Threshold: `6`).
- Candidate `cma_115163` matched existing `met_309960` with Hamming distance `6` (Threshold: `6`).
- Candidate `cma_130309` matched existing `cma_132047` with Hamming distance `4` (Threshold: `6`).

---

## 6. Accepted Assets Manifest (Sample)

| Local Filename | Category | Dimensions | Perceptual dHash | License Status |
| :--- | :--- | :--- | :--- | :--- |
| `met_207968_other.jpg` | `other` | `2792x3894` | `5070f0f00f2b3332` | `VERIFIED_CC0` |
| `met_454738_other.jpg` | `other` | `3791x3791` | `00303026060f0700` | `VERIFIED_CC0` |
| `met_194067_other.jpg` | `other` | `2620x3013` | `0e0f0f272b130f0c` | `VERIFIED_CC0` |
| `met_205427_other.jpg` | `other` | `3180x4000` | `e032333333331313` | `VERIFIED_CC0` |
| `met_193674_other.jpg` | `other` | `2942x4000` | `108c0c0e06061714` | `VERIFIED_CC0` |
| `met_53429_other.jpg` | `other` | `4000x1903` | `64ce9b8786ce5645` | `VERIFIED_CC0` |
| `met_309943_other.jpg` | `other` | `3053x4000` | `cccc8c8ccccc8ccc` | `VERIFIED_CC0` |
| `met_309944_other.jpg` | `other` | `2771x4000` | `cc8c9e9c96cf0f8d` | `VERIFIED_CC0` |
| `met_309960_other.jpg` | `other` | `3053x4000` | `204426861c169744` | `VERIFIED_CC0` |
| `cma_692272_pendant.jpg` | `pendant` | `726x900` | `0e22b296941c0c0c` | `VERIFIED_CC0` |

*(Showing up to 10 of 13 accepted pilot assets. Complete catalog in `pilot_manifest.jsonl`).*

---

## 7. Next Steps for Full Dataset Scaling

1. **Expand Search Terms**: Broaden query taxonomy to include specific cuts (marquise, cushion, emerald cut) and gemstone varieties (sapphire, ruby, emerald).
2. **Target 150–200 Images**: Once approved, run batch scaling targeting 180 curated images across Met and CMA collections.
3. **Synthetic LineArt Inversion**: Run `LineArtProcessor` on the finalized 180 clean images to produce the paired conditioning dataset for ControlNet.
