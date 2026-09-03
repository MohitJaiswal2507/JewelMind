# Phase 9: Structural Conditioning Preprocessing Technical Report

**Date:** September 3, 2026  
**Status:** Completed Investigation & Modular Component Implementation  
**Branch:** `phase-9-appearance-lora-training`  

---

## 1. Executive Summary

This investigation evaluates and implements the structural preprocessing pipeline required to extract clean, sketch-like conditioning maps from high-resolution fine jewellery photography. The objective is to establish a deterministic, high-fidelity pipeline for synthesizing paired (sketch $\rightarrow$ photo) datasets to train domain-specific ControlNet LineArt models.

Key findings:
- **Phase 6 YOLO11m-seg Evaluation:** The Phase 6 component segmentation model is **not viable** as an object-isolation mask generator for uncurated photographs. Detections were fragmented (confidences 0.10–0.28), missed major jewellery sub-structures (shanks, stones, or entire objects in 60% of test cases), and exhibited false-positive background inclusions on dark studio floors.
- **Structural Extraction Comparison:** Standalone Canny produced fragmented, discrete 1-pixel edges prone to reflection noise, while the existing `LineArtProcessor` retained raw luminance gradients and shading. Neural `LineartDetector` (from `controlnet_aux`), combined with **bilateral specular noise suppression and contrast floor thresholding**, provided the cleanest representation of outer silhouettes, gemstone facet edges, prongs, and shanks.
- **Implemented Solution:** A modular `StructuralConditioningProcessor` (`ai/rendering/preprocessing/structural.py`) was implemented and integrated with the conditioning factory. It preserves full aspect ratio via letterboxing, eliminates destructive cropping, and runs deterministically on RTX 4060 8GB VRAM with zero proprietary dependencies.

---

## 2. Existing Pipeline Audit

The existing preprocessing subsystem (`ai/rendering/preprocessing/`) was inspected:
1. **`ConditioningProcessor` (`base.py`)**:
   - Provides letterbox resizing (`letterbox_resize`) preserving aspect ratio with constant border padding.
   - Provides input normalization (`normalize_input`) handling EXIF orientation, RGBA/transparency flattening over neutral canvases, and dimension validation.
2. **`LineArtProcessor` (`lineart.py`)**:
   - Applies bilateral filter (`d=5, sigma=50`), background inversion, percentile normalization, and intensity thresholding.
   - *Limitation:* It is an intensity-inversion filter rather than a true contour/structural detector; metallic reflections and background gradients are preserved as unwanted strokes.
3. **`CannyProcessor` (`canny.py`)**:
   - Applies Gaussian blur (`5x5`) followed by OpenCV `Canny(low, high)`.
   - *Limitation:* Lacks continuous contour connectivity and cannot distinguish between geometric boundaries and specular sheen without severe threshold tuning.

---

## 3. Phase 6 Segmentation Model Audit

- **Checkpoint:** `runs/segment/runs/jewellery/yolo11m-seg-jewelmind-v1/weights/best.pt`
- **Architecture:** YOLO11m-seg (14.6M parameters, instance segmentation head).
- **Intended Taxonomy:** 7 component classes: `0: gemstone`, `1: ring_shank`, `2: ring_head`, `3: prong`, `4: bezel`, `5: setting`, `6: shoulder`.
- **Inference Harness:** `ai/vision/inference/detector.py` (`JewelleryComponentDetector`).
- **Limitation on General Photos:** The model was trained for component-level parsing rather than whole-object saliency. Consequently, the union of component masks fails to provide a contiguous jewellery silhouette.

---

## 4. Evaluation Methodology

A representative 5-image test subset was drawn from `datasets/appearance_lora/images/`.
Each image was evaluated across:
1. YOLO instance segmentation detection count, confidence scores, and mask area coverage at $\text{conf}=0.10$ and $\text{conf}=0.25$.
2. Isolated foreground generation via polygon union on white canvas.
3. Structural lineart generation via:
   - OpenCV Canny (100/200)
   - `LineArtProcessor`
   - `controlnet_aux.LineartDetector` (raw vs. bilateral pre-filtered vs. noise-floor enhanced).

Visual outputs were rendered to `outputs/evaluation/phase9_structural_conditioning/`.

---

## 5. Images Evaluated

| Image | Dimensions | Jewellery Type / Scene Characteristics |
|---|---|---|
| **CAND_001.jpg** | $1122 \times 893$ | Solitaire diamond ring on dark studio gradient background |
| **CAND_002.jpg** | $900 \times 598$ | Multi-stone cluster ring with high specular reflection |
| **CAND_015.jpg** | $900 \times 605$ | Fine gemstone ring on low-contrast dark floor |
| **CAND_030.jpg** | $900 \times 774$ | Complex diamond band / eternity setting |
| **CAND_076.jpg** | $762 \times 900$ | Large bezel-set cocktail ring with dark shadowed backdrop |

---

## 6. YOLO Mask Results

| Image | Detections ($\text{conf} \ge 0.10$) | Detections ($\text{conf} \ge 0.25$) | Mask Area Coverage | Isolation Assessment |
|---|---|---|---|---|
| **CAND_001** | 2 (`ring_head` 0.25, `ring_shank` 0.10) | 1 (`ring_head` 0.25) | 27.2% | **Partial**: Captured head and upper shank; lower shank excluded. |
| **CAND_002** | 3 (`ring_head` 0.76, 0.40, 0.12) | 2 (`ring_head` 0.76, 0.40) | 21.6% | **Incomplete**: Head isolated; entire shank and side accents missing. |
| **CAND_015** | 1 (`ring_shank` 0.11) | 0 | 15.5% | **Failed**: Missed gemstone and head; partial shank fragment only. |
| **CAND_030** | 0 | 0 | 0.0% | **Total Miss**: 0 components detected across entire ring. |
| **CAND_076** | 5 (`bezel` 0.28, `gem` 0.20, `shank` 0.17, etc.) | 1 (`bezel` 0.28) | 96.0% | **False Positive**: Shadowed studio floor classified as bezel/gemstone. |

**Audit Conclusion:** YOLO mask union **must not be used** as a mandatory upstream gating filter for dataset generation.

---

## 7. Canny Results

- **Strengths:** Zero latency, deterministic, captures high-contrast outer contours.
- **Weaknesses:** Highly sensitive to specular highlights on polished gold/platinum; produces fragmented 1-pixel lines; misses subtle gemstone pavilion/crown facets and prong curves.

---

## 8. LineartDetector Results

- **Strengths:** Neural M-LSD architecture extracts continuous, coherent structural sketches with stroke hierarchy matching artist drawings. Gemstone facets, prongs, and shank curves are preserved with structural continuity.
- **Weaknesses:** Faint background gradient reflections can appear as low-intensity stray strokes if unaddressed.
- **Mitigation:** Adding bilateral pre-filtering (`d=9, sigma=75`) and a noise floor cutoff ($<35$) cleanly removes background noise while preserving primary geometry.

---

## 9. Existing LineArtProcessor Results

- **Strengths:** Fast execution, integrated with pipeline schemas.
- **Weaknesses:** Retains shading, specular gradients, and diffuse metallic reflections, making it unsuitable for training ControlNet on clean line sketches.

---

## 10. Recommended Pipeline

The recommended and implemented architecture is:

$$\text{Input Photo} \xrightarrow{\text{Normalize \& Letterbox (512}\times\text{512)}} \xrightarrow{\text{Bilateral Smoothing (d=9, }\sigma=75\text{)}} \xrightarrow{\text{Neural LineartDetector}} \xrightarrow{\text{Noise Floor Cutoff (<35)}} \xrightarrow{\text{Percentile Contrast Normalization}} \text{Conditioning Map}$$

```
Photograph (RGB)
   │
   ▼
[Letterbox Resize to 512x512] (Preserve Aspect Ratio, Black Padding)
   │
   ▼
[Bilateral Filter] (Suppress specular noise & surface reflections)
   │
   ▼
[LineartDetector] (Neural contour & structural line extraction)
   │
   ▼
[Noise Floor & Contrast Enhancer] (Zero < 35, Rescale p2-p98 to 0-255)
   │
   ▼
Clean 3-Channel ControlNet LineArt Map (White Strokes on Black Background)
```

---

## 11. Why this Pipeline is Appropriate for ControlNet

1. **Format Alignment:** Produces high-contrast white strokes on black backgrounds, exactly matching the ControlNet v1.1 LineArt conditioning specification (`lllyasviel/control_v11p_sd15_lineart`).
2. **Stroke Continuity:** Continuous contours prevent ControlNet from generating disconnected or hallucinated metal fragments.
3. **Geometry Retention:** Retains critical domain details (gemstone facets, prongs, bezels, shank thickness) while discarding photographic color and diffuse reflections.
4. **Aspect Ratio Integrity:** Aspect ratio is strictly preserved with letterboxing; no distortive stretching or center cropping occurs.

---

## 12. Known Limitations

- **Complex Pave Setting Textures:** Extremely dense micro-pave clusters ($<10$ px per stone) may merge into textured line clusters rather than individual stones.
- **Low Contrast Platinum-on-White:** Photographs with pure white metal directly on overexposed pure white backgrounds require adequate edge contrast.
- **Neural Dependency:** Requires `controlnet_aux` LineArt weights (automatically cached locally from HuggingFace). If offline, the processor gracefully falls back to adaptive Canny.

---

## 13. ControlNet Training Readiness Assessment

- **Dataset Preprocessing Readiness:** **READY**. The paired conditioning generator can process appearance photos into sketch-image pairs deterministically.
- **Training Infra Readiness:** **PENDING Phase 10 execution** (requires script for ControlNet dataset formatting and training loop).

---

## 14. What Needs to Happen Before Training

1. Execute batch conditioning generation across selected high-quality jewellery photos to create `(sketch_conditioning, target_photo, caption)` triplets.
2. Filter/validate paired dataset for edge density and visual fidelity.
3. Setup ControlNet training script with gradient checkpointing and mixed precision for 8GB VRAM constraint.

---

## 15. Exact Commands for the Next Phase

To run batch paired conditioning generation on the appearance dataset:
```bash
# Example command using the new processor
python -c "
from PIL import Image
from pathlib import Path
from ai.rendering.preprocessing.structural import StructuralConditioningProcessor

proc = StructuralConditioningProcessor(512, 512, device='cuda')
for img_path in sorted(Path('datasets/appearance_lora/images').glob('*.jpg'))[:10]:
    cond, meta = proc.process(Image.open(img_path))
    out_path = Path('outputs/paired_conditioning') / f'{img_path.stem}_cond.png'
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cond.save(out_path)
    print(f'Saved: {out_path} (density={meta.edge_density})')
"
```

---

## 16. GPU / Memory Considerations (RTX 4060 8GB)

- **Conditioning Preprocessing:** `LineartDetector` consumes $\approx 1.1\text{ GB}$ VRAM during batch inference at $512\times 512$, running smoothly on the RTX 4060.
- **ControlNet Training Considerations:**
  - Base SD 1.5 + ControlNet in fp16 with AdamW optimizer requires $\approx 7.2\text{ GB}$ VRAM at batch size 1 with gradient accumulation.
  - Must enable `xformers` / `sdpa` attention and `gradient_checkpointing=True`.

---

## 17. Files Changed

1. `ai/rendering/preprocessing/structural.py` *(New)*: Implementation of `StructuralConditioningProcessor`.
2. `ai/rendering/preprocessing/__init__.py` *(Modified)*: Registered `StructuralConditioningProcessor` in the factory.
3. `tests/ai/test_structural_preprocessing.py` *(New)*: Comprehensive test suite for structural preprocessing.
4. `docs/PHASE_9_STRUCTURAL_PREPROCESSING_REPORT.md` *(New)*: Comprehensive technical investigation report.

---

## 18. Tests Executed and Results

```bash
python -m pytest tests/ai/test_structural_preprocessing.py -v
```
- `test_structural_processor_output_dimensions_and_aspect_ratio`: **PASSED**
- `test_structural_processor_deterministic_output`: **PASSED**
- `test_structural_processor_invalid_image_handling`: **PASSED**
- `test_factory_registration`: **PASSED**
- `test_empty_canvas_edge_density`: **PASSED**
- `test_neural_lineart_on_eval_image`: **PASSED**
- **Result:** `6 passed in 4.64s`

Full repository test suite:
```bash
python -m pytest tests/
```
- **Result:** `63 passed in 13.80s` (0 failures, 0 regressions)

---

## 19. Statement of Non-Execution

- **NO model training** was initiated or executed.
- **NO ControlNet training** was performed.
- **NO LoRA retraining** was performed.
- **NO dataset files or trained checkpoints** were modified or deleted.
- **NO git commit or push** was performed.
