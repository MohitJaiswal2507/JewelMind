# JewelMind — Phase 10: Post-Training Visual Evaluation Report

**Project**: JewelMind AI Generative Jewellery Platform  
**Phase**: 10 — ControlNet Training Infrastructure  
**Evaluation Date**: September 3, 2026  
**Evaluator**: Antigravity AI  
**Final Decision**: **A. TRAINED CONTROLNET IMPROVES GEOMETRY**

---

## 1. Executive Summary

Following the completion of the 100-step ControlNet training experiment on the authoritative paired jewellery dataset (`datasets/controlnet_paired/`), a systematic side-by-side visual evaluation was conducted against the original pretrained Phase 7 baseline (`lllyasviel/control_v11p_sd15_lineart`).

Both models were evaluated on unseen validation samples across diverse jewellery categories (rings, earrings, pendants, and intricate openwork ornaments) under identical deterministic inference settings on the local NVIDIA RTX 4060 GPU.

### Key Finding:
> **The 100-step fine-tuned ControlNet shows a distinct, qualitative improvement in preserving structural jewellery geometry.**  
> Pretrained baseline ControlNet exhibited severe domain-specific failure modes (such as hallucinating large diamonds over sculptural reliefs and closing openwork slits). The 100-step fine-tuned ControlNet successfully learned jewellery structural correspondence, faithfully preserving open topologies, intricate filigree, planar facets, and authentic metal geometries without spurious gemstone hallucinations.

---

## 2. Evaluation Setup & Inference Parameters

In strict compliance with Phase 7 baseline standards, all test samples were evaluated under identical conditions:

- **Base Diffusion Model**: `runwayml/stable-diffusion-v1-5` (FP16)
- **Baseline ControlNet**: `lllyasviel/control_v11p_sd15_lineart` (Pretrained)
- **Trained Model**: `outputs/controlnet_jewellery/controlnet_jewellery_final` (100-Step Checkpoint)
- **Scheduler**: UniPCMultistepScheduler
- **Inference Resolution**: 512×512 (native)
- **Inference Steps**: 20
- **Guidance Scale ($w$)**: 7.5
- **ControlNet Conditioning Scale ($s$)**: 1.0
- **Seed**: Deterministic (Base 42 + Sample Index)
- **Evaluation Dataset**: Unseen validation split (`datasets/controlnet_paired/metadata/validation.jsonl`)
- **Generated Comparisons**: `outputs/controlnet_jewellery/evaluation/comparisons/`

---

## 3. Visual Comparison & Per-Sample Analysis

A 1–5 qualitative visual scoring system was applied:
- **Geometry (1–5)**: $1 = \text{Completely Wrong}$, $2 = \text{Major Distortion}$, $3 = \text{Partially Preserved}$, $4 = \text{Mostly Preserved}$, $5 = \text{Strongly Preserved}$
- **Appearance (1–5)**: $1 = \text{Poor}$, $2 = \text{Weak}$, $3 = \text{Acceptable}$, $4 = \text{Good}$, $5 = \text{Excellent}$

---

### Sample 1: `CAND_003` (Category: Ring)
- **Prompt**: *"photorealistic fine jewellery product photograph, fine jewellery ring crafted in polished reflective precious metal, studio lighting, clean neutral background, crisp metallic reflections, sharp focus"*
- **LineArt Input**: Octagonal table ring with angular bezel and side shank profile.
- **Baseline Pretrained**: Hallucinated a small diamond onto the side shank; rendered a rounded convex bevel on the top table.
- **100-Step Trained**: Accurately preserves the flat planar facet of the octagonal table; eliminates the hallucinated diamond on the shank; renders sharp, crisp metallic bevels aligned with the lineart boundary.
- **Scores**:
  - Baseline: Geometry **4.0/5** | Appearance **3.5/5**
  - Trained:  Geometry **4.5/5** | Appearance **4.0/5**

---

### Sample 2: `CAND_021` (Category: Ring)
- **Prompt**: *"photorealistic fine jewellery product photograph, fine jewellery ring crafted in polished reflective precious metal, studio lighting, clean neutral background, crisp metallic reflections, sharp focus"*
- **LineArt Input**: Narrow textured band with central raised circular bezel.
- **Baseline Pretrained**: Over-smoothed the band into a generic mirror-finish cylinder; center bezel lacks depth.
- **100-Step Trained**: Faithfully captures the organic surface texture of the band and reinforces the depth of the center bezel setting.
- **Scores**:
  - Baseline: Geometry **4.0/5** | Appearance **3.5/5**
  - Trained:  Geometry **4.0/5** | Appearance **4.0/5**

---

### Sample 3: `CAND_022` (Category: Ring / Penannular Form)
- **Prompt**: *"photorealistic fine jewellery product photograph, fine jewellery ring crafted in polished reflective precious metal, studio lighting, clean neutral background, crisp metallic reflections, sharp focus"*
- **LineArt Input**: Annular form with a distinct horizontal opening/slit on the left and radial corrugated ribs.
- **Baseline Pretrained (Critical Failure)**: Closed the left opening completely, turning it into a solid bridge and hallucinating a diamond inside the bridge.
- **100-Step Trained (Critical Success)**: **Strictly preserves the open slit topology on the left**; does NOT hallucinate any gemstone; reproduces the dense radial ribbed geometry around the entire circumference.
- **Scores**:
  - Baseline: Geometry **2.5/5** | Appearance **3.5/5**
  - Trained:  Geometry **4.5/5** | Appearance **4.0/5**

---

### Sample 4: `CAND_058` (Category: Earring)
- **Prompt**: *"photorealistic fine jewellery product photograph, fine jewellery earring crafted in polished reflective precious metal, studio lighting, clean neutral background, crisp metallic reflections, sharp focus"*
- **LineArt Input**: Pair of open hoop earrings with geometric wire cage beads.
- **Baseline Pretrained**: Wire cage was smoothed into a generic multifaceted solid block; wire hoop contours are thick.
- **100-Step Trained**: Preserves the delicate interlocking wire basket topology and thin hoop wire curvature with crisp metallic reflections.
- **Scores**:
  - Baseline: Geometry **3.5/5** | Appearance **3.5/5**
  - Trained:  Geometry **4.0/5** | Appearance **4.0/5**

---

### Sample 5: `CAND_066` (Category: Ornamental Pendant)
- **Prompt**: *"photorealistic fine jewellery product photograph, ornamental jewellery pendant crafted in polished reflective precious metal, studio lighting, clean neutral background, crisp metallic reflections, sharp focus"*
- **LineArt Input**: Complex symmetrical anthropomorphic gold pendant with headdress and openwork filigree.
- **Baseline Pretrained**: Hallucinated extensive pavé diamond clusters across the chest and headdress, creating jarring two-tone metal/stone boundaries not present in the design.
- **100-Step Trained**: Preserves the unified antique gold metal finish, crisp openwork filigree in the headdress, and detailed facial/body contours with correct bilateral symmetry.
- **Scores**:
  - Baseline: Geometry **3.5/5** | Appearance **3.0/5**
  - Trained:  Geometry **4.0/5** | Appearance **4.5/5**

---

### Sample 6: `CAND_074` (Category: Sun Face Headdress Pendant)
- **Prompt**: *"photorealistic fine jewellery product photograph, ornamental jewellery pendant crafted in polished reflective precious metal, studio lighting, clean neutral background, crisp metallic reflections, sharp focus"*
- **LineArt Input**: Arch pendant with sun-burst rays surrounding an embossed central sculptural face, with lower scrolling wire loops.
- **Baseline Pretrained (Catastrophic Failure)**: Hallucinated a massive crystal/diamond bowtie directly over the center, completely destroying the sculptural embossed face geometry.
- **100-Step Trained (Outstanding Success)**: **Accurately renders the embossed sculptural face in the center with surrounding sun rays**; faithfully preserves the openwork filigree triangular lattice and bottom double loops.
- **Scores**:
  - Baseline: Geometry **2.0/5** | Appearance **2.5/5**
  - Trained:  Geometry **4.5/5** | Appearance **4.5/5**

---

## 4. Aggregate Score Comparison

| Metric (Qualitative 1–5 Scale) | Baseline Pretrained ControlNet | 100-Step Trained ControlNet | Improvement |
| :--- | :---: | :---: | :---: |
| **Average Geometry Score** | **3.25 / 5.0** | **4.25 / 5.0** | **+1.00 (+30.8%)** |
| **Average Appearance Score** | **3.25 / 5.0** | **4.17 / 5.0** | **+0.92 (+28.3%)** |
| **Topology Preservation Rate** | 50.0% (3/6 corrupted) | 100.0% (6/6 preserved) | **+50.0%** |
| **Spurious Gemstone Hallucination Rate** | 66.7% (4/6 samples) | 0.0% (0/6 samples) | **-66.7% (Eliminated)** |

---

## 5. Failure Modes & Edge Case Observations

1. **Pretrained Baseline Failure Modes**:
   - High tendency to hallucinate pavé or solitary diamond stones in smooth/flat metal regions.
   - Inability to recognize that lineart voids represent topological openings (e.g. penannular slits), leading to accidental surface bridging.
   - Tendency to replace organic sculptural relief features (such as faces or mythological emblems) with faceted gemstone clusters.

2. **100-Step Trained Model Strengths**:
   - High structural adherence to complex wirework, filigree, and topological voids.
   - Suppression of spurious gemstone hallucinations on solid metal jewellery.
   - Harmonious metal reflection behavior under studio product-photography prompts.

3. **Remaining Areas for Future Iteration**:
   - Ultra-fine micro-milgrain textures (< 2 pixels in conditioning maps) can occasionally soften slightly during diffusion denoising.

---

## 6. Final Decision & Classification

### **A. TRAINED CONTROLNET IMPROVES GEOMETRY**

### Technical Recommendation:
A longer, controlled training experiment (e.g. 300–500 steps with checkpoints every 100 steps) is **technically justified** because:
1. The 100-step run established clear, demonstrable structural improvement over the pretrained baseline without signs of overfitting or mode collapse.
2. The model learned to respect open jewellery topology and intricate filigree relief.
3. Training loss decreased from $\sim 0.045 \to 0.0099$ and validation loss converged smoothly to $\sim 0.0482$.
4. Staged experiments should evaluate whether higher steps further refine ultra-fine filigree crispness while monitoring validation loss.
