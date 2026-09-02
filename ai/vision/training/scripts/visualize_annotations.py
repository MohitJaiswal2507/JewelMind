"""JewelMind Ground-Truth Annotation Visualizer.

Renders translucent colored segmentation masks, bounding contours,
and class labels onto original blueprint images to enable visual verification
prior to any training run.
"""

import argparse
from pathlib import Path
import cv2
import numpy as np
import yaml


CLASS_COLORS = {
    0: (230, 180, 0),     # gemstone: bright cyan/gold
    1: (0, 140, 255),     # ring_shank: deep orange
    2: (0, 200, 200),     # ring_head: yellow
    3: (255, 0, 255),     # prong: magenta
    4: (0, 220, 0),       # bezel: green
    5: (180, 0, 180),     # setting: purple
    6: (255, 100, 100),   # shoulder: light blue
}


def visualize_dataset_samples(
    config_path: str = "ai/vision/training/configs/jewellery_components.yaml",
    split: str = "train",
    num_samples: int = 5,
    output_dir: str = "ai/vision/datasets/previews",
):
    """Render and save visual inspection previews with overlaid ground-truth masks."""
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    base_path = Path(config.get("path", "ai/vision/datasets/sample"))
    names = config.get("names", {})
    img_dir = base_path / split / "images"
    lbl_dir = base_path / split / "labels"

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    img_files = sorted(list(img_dir.glob("*.jpg")) + list(img_dir.glob("*.png")))[:num_samples]
    if not img_files:
        print(f"[!] No images found in {img_dir}")
        return

    print(f"[*] Generating {len(img_files)} visual previews from split '{split}' into '{out_path}'...")

    for img_path in img_files:
        img = cv2.imread(str(img_path))
        if img is None:
            continue
        h, w = img.shape[:2]
        overlay = img.copy()

        lbl_path = lbl_dir / f"{img_path.stem}.txt"
        if not lbl_path.exists():
            continue

        with open(lbl_path, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]

        for line in lines:
            tokens = line.split()
            cls_id = int(tokens[0])
            coords = [float(c) for c in tokens[1:]]

            # Denormalize polygon coordinates
            pts = []
            for i in range(0, len(coords), 2):
                px = int(round(coords[i] * w))
                py = int(round(coords[i + 1] * h))
                pts.append((px, py))

            pts_arr = np.array(pts, dtype=np.int32)
            color = CLASS_COLORS.get(cls_id, (128, 128, 128))

            # Draw filled translucent polygon mask
            cv2.fillPoly(overlay, [pts_arr], color)
            # Draw crisp contour boundary
            cv2.polylines(img, [pts_arr], True, color, 2, cv2.LINE_AA)

            # Draw label tag at centroid or first point
            cx = int(np.mean([p[0] for p in pts]))
            cy = int(np.mean([p[1] for p in pts]))
            label_text = f"{names.get(cls_id, f'cls_{cls_id}')}"

            # Tag background
            (tw, th), _ = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)
            cv2.rectangle(img, (cx - 2, cy - th - 4), (cx + tw + 2, cy + 2), (20, 20, 20), -1)
            cv2.putText(img, label_text, (cx, cy - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1, cv2.LINE_AA)

        # Blend overlay with original image (alpha 0.4)
        alpha = 0.35
        blended = cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0)

        # Save output preview
        out_file = out_path / f"preview_{img_path.stem}.png"
        cv2.imwrite(str(out_file), blended)
        print(f"  [+] Saved preview: {out_file.name}")

    print(f"[SUCCESS] Visual previews saved in {out_path}.\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Visualize ground-truth dataset annotations.")
    parser.add_argument("--config", default="ai/vision/training/configs/jewellery_components.yaml")
    parser.add_argument("--split", default="train")
    parser.add_argument("--samples", type=int, default=5)
    parser.add_argument("--output", default="ai/vision/datasets/previews")
    args = parser.parse_args()

    visualize_dataset_samples(args.config, args.split, args.samples, args.output)
