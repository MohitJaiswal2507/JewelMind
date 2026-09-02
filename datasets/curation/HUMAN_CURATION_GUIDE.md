# JewelMind — Human Curation Protocol & Operational Guide

> **MANDATORY BOUNDARY ENFORCEMENT**:  
> **HUMAN OPERATOR CURATION ONLY — TRAINING NOT EXECUTED**  
> Antigravity has not executed any model training, LoRA training, ControlNet training, or GPU diffusion inference. Production rendering code has not been modified, and no git commits or pushes have occurred. This guide defines the operator decision framework to down-select the 226 candidate pool to the final **150–200 image appearance LoRA training dataset**.

---

## 1. Executive Overview & Mission

The goal of this curation phase is to curate a training-grade dataset for the **JewelMind Jewellery Appearance LoRA (Stable Diffusion 1.5)**.

* **Input Candidate Pool**: 226 technically valid, decodable, high-resolution CC0 images.
* **Target Training Pool**: **150–200 high-signal, clean, diverse jewellery images**.
* **Review Tool**: Open [`datasets/curation/HUMAN_CURATION.csv`](file:///c:/Users/usern/Desktop/JewelMind/datasets/curation/HUMAN_CURATION.csv) in Excel, LibreOffice, or Google Sheets. Inspect corresponding visual contact sheets in [`datasets/curation/`](file:///c:/Users/usern/Desktop/JewelMind/datasets/curation/).

---

## 2. Decision Framework (`final_triage`)

For each candidate (`CAND_001` through `CAND_226`), assign one of three triage outcomes:

### A. `KEEP`
Assign when the image satisfies all core appearance-training requirements:
1. **Jewellery is the indisputable primary subject** (wearable jewellery, not a decorative figurine or vase).
2. **Single primary piece** clearly in focus.
3. **Sufficient object scale** (occupies $\ge 20\%$ of frame; not a speck).
4. **Useful geometry** (crisp outer contours, prongs, bezels, shank, or links suitable for edge/lineart conditioning).
5. **Useful metal/material appearance** (specular reflections on gold, platinum, or silver are clearly rendered).
6. **Low background entropy** (clean studio neutral, white, light grey, or dark museum mount; minimal distracting shadows or display props).

### B. `REVIEW`
Assign when an image has high potential but exhibits minor ambiguities:
1. **Near-duplicate / multiple views of a single design**: If two angles of the same piece are both excellent, flag one for secondary comparison before deciding which angle best trains the UNet.
2. **Minor mounting props**: Light transparent suspension thread, subtle museum pin, or neutral ring stand that can be safely cropped or masked.
3. **Uncertain category**: An ornate pectoral or armlet that could function as either a necklace, pendant, or bracelet.
4. **Borderline resolution or lighting**: Slight underexposure that is still salvageable for diffusion training.

### C. `REJECT`
Assign when an image degrades training signal:
1. **Multi-piece group clutter**: Piles of unsorted coins, trays of loose beads, or chaotic group displays with no distinct primary subject.
2. **Extreme occlusion**: Mannequin fingers, heavy velvet clamp stands, or mounting brackets that obstruct $> 25\%$ of the jewellery silhouette.
3. **Heavy historical erosion**: Tarnished, corroded, broken, or heavily pitted metal lacking usable specular reflection properties.
4. **Redundant design angles**: Duplicate views of an already accepted design (`SAME_DESIGN_REDUNDANT`).
5. **Non-wearable artefacts**: Architectural fragments, chalices, wall hangings, or figurines misclassified as jewellery.

---

## 3. Near-Duplicate & Design Redundancy Triage

The candidate pool contains **124 near-duplicate candidates** flagged by perceptual hashing (dHash/aHash Hamming distance $\le 6$).

> **CRITICAL RULE**: Do **NOT** automatically reject near-duplicates. Automated hashing flags visual similarity, not worthlessness. However, the final appearance training dataset must avoid redundant photographs of identical designs.

### Use the `design_redundancy` Column:

| Value | Definition | Action |
| :--- | :--- | :--- |
| **`UNIQUE_DESIGN`** | Distinct design motif despite low perceptual distance to another item. | Eligible for **`KEEP`**. |
| **`SAME_DESIGN_DIFFERENT_VIEW`** | Different perspective, angle, or lighting of an existing piece. | Inspect both; select the stronger angle for **`KEEP`**, mark alternate as **`REVIEW`** or **`REJECT`**. |
| **`SAME_DESIGN_REDUNDANT`** | Nearly identical framing, resolution, or duplicate angle offering zero new signal. | Mark **`REJECT`** to preserve dataset diversity. |
| **`UNKNOWN`** | Ambiguous provenance or unconfirmed similarity. | Mark **`REVIEW`**. |

*Consult the dedicated visual contact sheet:*  
[`HUMAN_CURATION_NEAR_DUPLICATES.png`](file:///c:/Users/usern/Desktop/JewelMind/datasets/curation/HUMAN_CURATION_NEAR_DUPLICATES.png)

---

## 4. Gemstone Handling: Explicitly CONDITIONAL

> **IMPORTANT**: **DO NOT REQUIRE GEMSTONES.**  
> Stable Diffusion appearance LoRA must learn both **plain metal jewellery** (signet rings, gold bangles, platinum bands, curb chains) and **gemstone-set jewellery** (solitaires, halo rings, pavé pendants).

* For plain-metal or engraved jewellery:
  * Set `gemstone_detail_applicable = NOT_APPLICABLE`.
  * **DO NOT REJECT** a piece merely because it lacks gemstones.
* For gemstone-set jewellery:
  * Set `gemstone_detail_applicable = YES`.
  * Verify facet sharpness, color clarity, and lack of excessive motion blur or blown-out white flash reflection.

---

## 5. Historical vs. Modern Studio Photography

Because candidates originate from open-access museum archives (Cleveland Museum of Art):
1. **Neutral Museum Photography is Acceptable**: Neutral grey, off-white, gradient, or black studio backdrops commonly used by museum conservators are high-quality and low-entropy. Do not reject an image simply because the background is not pure `#FFFFFF`.
2. **Historical Craftsmanship is Valuable**: Classical Roman, Greek, Renaissance, Byzantine, and Victorian jewellery provide exquisite gold filigree, granulation, and bezel settings. Accept historical pieces provided the metal reflection and silhouette geometry are intact.
3. **Reject Severe Corrosion**: Only reject historical items if the metal has oxidized into unrecognisable crust or severe pitting that would teach the model bad texture artefacts.

---

## 6. Multi-Piece Displays & Cropping

* **Single Primary Object**: Diffusion LoRA learns best when there is one clear focal subject.
* **Pairs of Earrings**: A matched pair of earrings photographed side-by-side on neutral background is **ACCEPTABLE** (`single_primary_object = YES` for matched pairs).
* **Trays / Collections**: Composite photos containing multiple unrelated rings, necklaces, or loose gems must be marked `REJECT` or flagged for cropping in `curator_notes`.

---

## 7. Category Balancing Guidelines

Monitor category distribution in [`HUMAN_CURATION.csv`](file:///c:/Users/usern/Desktop/JewelMind/datasets/curation/HUMAN_CURATION.csv):

| Canonical Category | Retained Pool | Target Curation Objective |
| :--- | :---: | :--- |
| **`ring`** | 32 | Aim to **KEEP $\ge 22$** high-quality rings (solitaires, signet rings, bands). |
| **`earring`** | 30 | Aim to **KEEP $\ge 20$** earrings (drops, hoops, studs). |
| **`pendant`** | 47 | Aim to **KEEP $\ge 30$** pendants (gemstone lockets, medallions, solitaires). |
| **`necklace`** | 34 | Aim to **KEEP $\ge 22$** necklaces (chokers, chains, collar pieces). |
| **`bracelet`** | 18 | Aim to **KEEP $\ge 12$** bracelets (chain links, cuffs, tennis bracelets). |
| **`bangle`** | 3 | **PRESERVE ALL 3** if valid (bangles are rare; avoid unnecessary rejection). |
| **`brooch`** | 21 | Aim to **KEEP $\approx 12–15$** brooches (pins, clips, filigree badges). |
| **`other`** | 41 | Prune aggressively: reject decorative figurines, keep only genuine wearable items ($\approx 15–20$). |
| **Total Target** | **226** | **Target Final Curated Dataset: 150–200 Images** |

---

## 8. Step-by-Step Operator Workflow

1. Open [`datasets/curation/HUMAN_CURATION.csv`](file:///c:/Users/usern/Desktop/JewelMind/datasets/curation/HUMAN_CURATION.csv) in a spreadsheet editor.
2. Open [`HUMAN_CURATION_MASTER_CONTACT_SHEET.png`](file:///c:/Users/usern/Desktop/JewelMind/datasets/curation/HUMAN_CURATION_MASTER_CONTACT_SHEET.png) or the individual category sheets in an image viewer.
3. For row $i$ (`CAND_001` to `CAND_226`):
   - Check image against the 12 criteria (columns Q through AB).
   - For `design_redundancy`, assign `UNIQUE_DESIGN`, `SAME_DESIGN_DIFFERENT_VIEW`, or `SAME_DESIGN_REDUNDANT`.
   - Set `final_triage` to `KEEP`, `REVIEW`, or `REJECT`.
   - Add optional notes in `curator_notes`.
4. Save the completed `HUMAN_CURATION.csv`.
5. Report the final counts (`KEEP`, `REVIEW`, `REJECT` per category).
