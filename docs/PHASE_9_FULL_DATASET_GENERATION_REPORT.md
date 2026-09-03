# Phase 9: Full Paired ControlNet Dataset Generation Report

**Date:** September 3, 2026  
**Status:** Completed & Verified  
**Branch:** `phase-9-appearance-lora-training`  

---

## 1. Executive Summary

Full structural conditioning generation has been completed across all 164 authoritative fine jewellery images from the Phase 8 appearance dataset. Using the validated `StructuralConditioningProcessor`, each high-resolution photograph was processed into a 512×512 clean structural lineart conditioning map without destructive cropping or distortion.

The dataset has been exported in standard paired format to `datasets/controlnet_paired/`, partitioned into strictly separated training (147 pairs) and validation (17 pairs) splits with zero SHA-256 hash leakage.

---

## 2. Dataset Specifications

| Metric | Specification / Result |
|---|---|
| **Source Dataset** | `datasets/appearance_lora/images/` (Authoritative Phase 8) |
| **Total Source Images** | 164 images |
| **Total Processed** | 164 pairs (100% complete) |
| **Training Pairs** | 147 pairs |
| **Validation Pairs** | 17 pairs |
| **Missing / Failed** | 0 |
| **Corrupted Images** | 0 |
| **Conditioning Dimensions** | Exactly $512 \times 512$ px (164/164) |
| **Conditioning Color Mode** | RGB (3-channel) (164/164) |
| **SHA-256 Train/Val Overlap** | **0** (Strict disjoint separation) |

---

## 3. Preprocessing Configuration

The conditioning maps were synthesized using `ai/rendering/preprocessing/structural.py` with the following parameters:

```python
StructuralConditioningProcessor(
    target_width=512,
    target_height=512,
    device="cuda",          # RTX 4060 8GB
    noise_floor=35,         # Suppresses background floor reflections & smudges
    bilateral_d=9,          # Specular reflection smoothing diameter
    bilateral_sigma=75.0,   # Color & coordinate smoothing space
    coarse=False,           # Detailed facet & prong stroke extraction
    use_neural_lineart=True # M-LSD LineartDetector
)
```

---

## 4. Directory Structure

```
datasets/controlnet_paired/
├── images/                   # 164 original high-res jewellery photos
│   ├── CAND_001.jpg
│   └── ... (164 files)
├── conditioning/             # 164 512x512 neural structural lineart maps
│   ├── CAND_001.png
│   └── ... (164 files)
└── metadata/
    ├── train.jsonl           # 147 training records (source, target, prompt, category)
    ├── validation.jsonl      # 17 validation records
    ├── dataset_metadata.json # Full JSON records with edge densities & SHA hashes
    └── dataset_summary.json  # Aggregate statistics & QA flags
```

---

## 5. Statistical Quality Analysis

### Edge Density Metrics
- **Minimum Edge Density:** `0.0100` (`CAND_030`)
- **Maximum Edge Density:** `0.2102` (`CAND_213`)
- **Mean Edge Density:** `0.0570`
- **Median Edge Density:** `0.0473`

The edge density distribution reflects high structural consistency across jewellery categories (rings, pendants, earrings, bracelets, brooches).

---

## 6. QA Review & Flagged Samples

Per quality control guidelines, outlier samples were flagged for audit without automated deletion:

### A. Low Edge Density (< 0.01)
- **Count:** `0` samples. All 164 conditioning maps contain sufficient active structural lines.

### B. High Edge Density (> 0.15)
- **Count:** `4` samples (`2.4%` of dataset):
  1. `CAND_074` (density: `0.1530`, validation) - Intricate multi-tier gemstone chandelier necklace.
  2. `CAND_166` (density: `0.1679`, validation) - Detailed Victorian filigree openwork brooch.
  3. `CAND_185` (density: `0.1546`, train) - Complex multi-gemstone floral pendant.
  4. `CAND_213` (density: `0.2102`, train) - High-density pavé cocktail ring with ornate halo.
- **Audit Finding:** High density is legitimate geometric complexity (filigree, dense pavé, multi-stone clusters); these samples provide valuable training signal for complex settings.

### C. Border Background Activity (> 0.10)
- **Count:** `17` samples (`10.4%` of dataset):
  - `CAND_074`, `CAND_085`, `CAND_087`, `CAND_091`, `CAND_097`, `CAND_118`, `CAND_125`, `CAND_166`, `CAND_169`, `CAND_170`, `CAND_180`, `CAND_185`, `CAND_188`, `CAND_191`, `CAND_063`, etc.
- **Audit Finding:** Primarily caused by wide jewelry pieces extending close to the canvas boundary or studio shadow gradations. The core jewellery silhouette remains sharp and continuous.

---

## 7. Test Verification

```bash
# Structural Preprocessing Test Suite
python -m pytest tests/ai/test_structural_preprocessing.py -v
# Result: 6 passed in 5.15s

# Paired Dataset Integrity Test Suite
python -m pytest tests/ai/test_controlnet_paired_dataset.py -v
# Result: 3 passed in 0.08s
```

All 9 automated unit and integrity tests passed with 100% success rate.

---

## 8. Final Readiness Assessment

- **Dataset Quality:** **100% READY**
- **Train/Val Partitions:** Strictly verified with 0 SHA-256 leakage (147 train / 17 val).
- **Format Compatibility:** Standard `(conditioning_512x512.png, image.jpg, prompt)` format ready for Diffusers `ControlNetModel` training pipelines.
- **Training Guardrail:** No training has been executed. No checkpoints or model weights were modified.
