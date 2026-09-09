# JewelMind Multi-Jewellery V2 Dataset

This dataset is engineered from the high-resolution **Jewelry-DWPose** paired dataset for multi-class jewellery instance segmentation in JewelMind.

---

## 📊 Dataset Statistics

- **Total Usable Unique Images:** 7,066
- **Total Segmentation Instances:** 11,484
- **Multi-Instance Images:** 3,425 (images containing 2+ jewellery items)
- **Discarded Non-Jewellery Images:** 571 (watch-only samples)
- **Data Leakage:** 0% (strict deterministic split enforced at unique target image level)

### Split Breakdown

| Split | Images | % Images | Total Instances | % Instances |
|---|:---:|:---:|:---:|:---:|
| **Train** | 4,925 | 69.7% | 7,991 | 69.6% |
| **Validation** | 1,446 | 20.5% | 2,357 | 20.5% |
| **Test** | 695 | 9.8% | 1,136 | 9.9% |
| **Total** | **7,066** | **100.0%** | **11,484** | **100.0%** |

---

## 🏷️ Category Taxonomy (8 JewelMind Categories)

| Class ID | Class Name | Instances in Dataset | Status |
|:---:|---|:---:|---|
| `0` | `ring` | 3,589 | Fully Populated |
| `1` | `earring` | 2,822 | Fully Populated |
| `2` | `pendant` | 0 | Pending Targeted Dataset Source |
| `3` | `necklace` | 2,366 | Fully Populated |
| `4` | `bracelet` | 2,707 | Fully Populated |
| `5` | `bangle` | 0 | Pending Targeted Dataset Source |
| `6` | `brooch` | 0 | Pending Targeted Dataset Source |
| `7` | `other_jewellery` | 0 | Fallback Class |

> **Completeness Notice:** DWPose is a foundation source dataset providing deep coverage for Rings, Earrings, Necklaces, and Bracelets. Targeted augmentation for Pendants, Bangles, and Brooches will be integrated from CC0 museum / synthetic sources.

---

## 📁 Directory Structure

```text
jewellery_v2/
├── train/
│   ├── images/      # 4,925 JPEG images
│   └── labels/      # 4,925 YOLO polygon label files (.txt)
├── val/
│   ├── images/      # 1,446 JPEG images
│   └── labels/      # 1,446 YOLO polygon label files (.txt)
├── test/
│   ├── images/      # 695 JPEG images
│   └── labels/      # 695 YOLO polygon label files (.txt)
├── conversion_stats.json # Machine-readable conversion metrics
└── README.md        # This specification
```
