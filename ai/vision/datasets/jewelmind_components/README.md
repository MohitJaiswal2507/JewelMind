# JewelMind-Specific Component Dataset Ingestion Roadmap

This directory is the repository intake for user-submitted, authenticated jewellery sketch blueprints and manual expert annotations.

---

## Ingestion Protocol

When adding new sketch blueprints for YOLO component segmentation:

1. **Image Placement**:
   Place high-contrast sketch images (`.png` or `.jpg`) in:
   `ai/vision/datasets/jewelmind_components/raw_images/`

2. **Annotation**:
   Generate or export normalized polygon annotations (`.txt`) matching the image name in:
   `ai/vision/datasets/jewelmind_components/raw_labels/`

3. **Schema**:
   ```text
   <class_id> <x1> <y1> <x2> <y2> ... <xn> <yn>
   ```
   Valid classes:
   - `0`: `gemstone`
   - `1`: `ring_shank`
   - `2`: `ring_head`
   - `3`: `prong`
   - `4`: `bezel`
   - `5`: `setting`
   - `6`: `shoulder`

4. **Review & Curation**:
   - Verify non-overlapping distinct component boundaries.
   - Run `python ai/vision/training/scripts/validate_dataset.py` to confirm zero degenerate polygons.
   - Run `python ai/vision/training/scripts/visualize_annotations.py` to visually inspect mask alignment.
