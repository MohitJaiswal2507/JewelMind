# JewelMind Vision Datasets Research & Roadmap

This document outlines the dataset research, licensing audit, component taxonomy, and multi-stage data architecture for JewelMind's YOLO11 instance segmentation pipeline.

---

## 1. Multi-Tier Dataset Strategy

Jewellery component detection operates across three complementary tiers:

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                      Tier 1: Public Bootstrap Data                      │
│   (Macro jewellery recognition: rings, earrings, bracelets, necklaces)   │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ Transfer weights
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     Tier 2: Component-Level Data                        │
│ (Micro component segmentation: gemstones, shanks, prongs, bezels, heads)│
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ Domain adaptation
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                  Tier 3: JewelMind Blueprint Sketches                   │
│   (User freehand canvas & CAD sketches with manufacturing annotations)  │
└─────────────────────────────────────────────────────────────────────────┘
```

> [!NOTE]
> Public datasets containing broad classes (e.g. `ring`, `bracelet`) provide macro-level object localization. Fine-grained manufacturing blueprint understanding requires Tier 2 and Tier 3 annotations with polygon masks.

---

## 2. Public Dataset Research & License Audit

| Dataset Name | Source / URL | License | Image Count | Classes | Annotation Type | Relevance to JewelMind | Limitations |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Roboflow Jewelry Detection** | [Roboflow Universe](https://universe.roboflow.com/roboflow-100/jewelry-detection) | CC BY 4.0 | ~6,900 | `ring`, `earring`, `necklace`, `bracelet`, `pendant` | Bounding Box | Bootstrap macro jewellery localization | Does not provide instance masks or micro-components |
| **Roboflow Gemstone Segmentation** | [Roboflow Universe](https://universe.roboflow.com/gemstones-seg) | CC BY 4.0 | ~1,200 | `gemstone`, `facet`, `table` | Polygon Segmentation | Component-level gemstone detection & facet contours | Limited to isolated loose gemstones, not full rings |
| **Kaggle Jewelry Products Dataset** | Kaggle Open Data | CC0: Public Domain | ~3,500 | Product catalogue categories | Image Classification | Style and texture reference | No localization or segmentation masks |
| **JewelMind Synthetic & Studio Blueprints** | JewelMind In-House | Proprietary / Internal | Scalable | `gemstone`, `ring_shank`, `ring_head`, `prong`, `bezel`, `setting`, `shoulder` | Polygon Segmentation | **Primary target**: Direct alignment with sketch studio canvas | Requires ongoing expansion through user submissions |

---

## 3. Evidence-Based Component Taxonomy

JewelMind defines a 7-class micro-component taxonomy grounded in physical jewellery manufacturing:

| Class ID | Class Name | Physical Description | Visual Distinctiveness | Manufacturing Relevance |
| :---: | :--- | :--- | :--- | :--- |
| `0` | **`gemstone`** | Central or accent stones (diamonds, emeralds, sapphires) | High contrast, faceted or cabochon contours | Cost driver, stone setting labor |
| `1` | **`ring_shank`** | The circular metal band circling the finger | Long curved band with continuous contour | Metal weight calculation, sizing, casting |
| `2` | **`ring_head`** | Top assembly structure supporting stones | Upper cluster platform | Assembly solder joints, head casting |
| `3` | **`prong`** | Slender metallic claws securing stones | Small pointed or rounded vertical tabs | Casting precision, stone security, finishing |
| `4` | **`bezel`** | Continuous metal rim wrapping the stone circumference | Solid border hugging stone boundary | Metal volume, secure mount setting |
| `5` | **`setting`** | Basket, gallery mount, or channel housing stones | Structural framework below stones | Casting complexity, stone setting style |
| `6` | **`shoulder`** | Upper shank transitions tapering into head/mount | Tapering lateral metal transitions | Aesthetic curvature, accent stone seating |

---

## 4. Directory Structure

```text
ai/vision/datasets/
├── raw/                      # Downloaded source archives (gitignored)
├── processed/                # Normalized YOLO segmentation datasets (gitignored)
│   ├── train/
│   │   ├── images/
│   │   └── labels/
│   ├── val/
│   │   ├── images/
│   │   └── labels/
│   └── test/
│       ├── images/
│       └── labels/
├── sample/                   # Synthetic benchmark/smoke dataset (normalized)
│   ├── train/
│   ├── val/
│   └── test/
├── jewelmind_components/     # Ingested user sketch blueprints & annotations
│   └── README.md
├── previews/                 # Visual inspection outputs with polygon overlays
└── README.md
```

---

## 5. YOLO Segmentation Label Format

Annotations follow the standard Ultralytics YOLO segmentation polygon format:
```text
<class_id> <x1> <y1> <x2> <y2> <x3> <y3> ... <xn> <yn>
```
- All coordinates $x_i, y_i$ are normalized to $[0.0, 1.0]$ relative to image width and height.
- Minimum 3 coordinate pairs ($n \ge 3$) forming a closed polygon contour.
- Matching image and label share the same basename (e.g., `ring_001.jpg` and `ring_001.txt`).
