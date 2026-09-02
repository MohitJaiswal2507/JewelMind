"""JewelMind Dataset Preparation Utility for Jewellery LoRA Fine-Tuning.

Processes raw photographs/renderings into 512x512 normalized images with rich
descriptive jewellery captions and creates train/val splits with metadata.jsonl.
"""

import argparse
import json
import os
import random
import shutil
from pathlib import Path
from PIL import Image, ImageOps

DEFAULT_CATEGORIES = ["ring", "necklace", "pendant", "earrings", "bracelet", "bangle"]
DEFAULT_METALS = ["18k yellow gold", "white gold", "rose gold", "platinum"]
DEFAULT_STONES = ["diamond", "blue sapphire", "emerald", "ruby"]


def process_image(img_path: Path, output_path: Path, resolution: int = 512):
    """Normalize EXIF, transparency, center-crop or pad to target resolution."""
    with Image.open(img_path) as img:
        img = ImageOps.exif_transpose(img)
        if img.mode != "RGB":
            # Composite over pure white canvas
            canvas = Image.new("RGB", img.size, (255, 255, 255))
            if "A" in img.mode:
                canvas.paste(img, mask=img.split()[-1])
            else:
                canvas.paste(img.convert("RGB"))
            img = canvas

        # Letterbox/pad or crop
        w, h = img.size
        scale = min(resolution / w, resolution / h)
        new_w, new_h = max(1, int(round(w * scale))), max(1, int(round(h * scale)))
        resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

        final_img = Image.new("RGB", (resolution, resolution), (255, 255, 255))
        paste_x = (resolution - new_w) // 2
        paste_y = (resolution - new_h) // 2
        final_img.paste(resized, (paste_x, paste_y))
        final_img.save(output_path, format="JPEG", quality=95)


def generate_jewellery_caption(filename: str) -> str:
    """Derive descriptive training caption based on filename keywords or defaults."""
    name_lower = filename.lower()
    
    # Identify category
    category = "jewellery piece"
    for cat in DEFAULT_CATEGORIES:
        if cat in name_lower:
            category = cat
            break

    # Identify metal
    metal = "18k yellow gold"
    for m in DEFAULT_METALS:
        if m.replace(" ", "") in name_lower.replace("_", "").replace("-", ""):
            metal = m
            break

    # Identify gemstone
    stone = "round brilliant diamond"
    for s in DEFAULT_STONES:
        if s in name_lower:
            stone = s
            break

    caption = (
        f"photorealistic fine jewellery product photograph, luxury {category}, "
        f"crafted in polished {metal}, embellished with {stone}, "
        f"studio lighting, crisp reflective surface, sharp focus, master artisan craftsmanship"
    )
    return caption


def main():
    parser = argparse.ArgumentParser(description="Prepare jewellery dataset for LoRA fine-tuning.")
    parser.add_argument("--source", type=str, required=True, help="Path to raw source images directory")
    parser.add_argument("--output", type=str, default="datasets/jewellery_lora", help="Output directory")
    parser.add_argument("--resolution", type=int, default=512, help="Target image resolution")
    parser.add_argument("--val_ratio", type=float, default=0.1, help="Validation set fraction (default: 0.1)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for split")
    args = parser.parse_args()

    random.seed(args.seed)
    source_dir = Path(args.source)
    output_dir = Path(args.output)

    if not source_dir.exists():
        print(f"[ERROR] Source directory does not exist: {source_dir}")
        return

    train_dir = output_dir / "train"
    val_dir = output_dir / "val"
    train_dir.mkdir(parents=True, exist_ok=True)
    val_dir.mkdir(parents=True, exist_ok=True)

    # Find valid images
    valid_extensions = {".jpg", ".jpeg", ".png", ".webp"}
    raw_images = [p for p in source_dir.rglob("*") if p.suffix.lower() in valid_extensions]
    print(f"[INFO] Found {len(raw_images)} candidate images in {source_dir}")

    if not raw_images:
        print("[WARNING] No valid image files found.")
        return

    random.shuffle(raw_images)
    n_val = max(1, int(len(raw_images) * args.val_ratio)) if len(raw_images) > 5 else 0
    val_images = raw_images[:n_val]
    train_images = raw_images[n_val:]

    def process_split(split_images, target_folder, split_name):
        metadata_lines = []
        for idx, img_path in enumerate(split_images):
            out_filename = f"{split_name}_{idx:04d}.jpg"
            out_path = target_folder / out_filename
            try:
                process_image(img_path, out_path, resolution=args.resolution)
                caption = generate_jewellery_caption(img_path.name)
                metadata_lines.append({
                    "file_name": out_filename,
                    "text": caption,
                    "source_name": img_path.name,
                })
            except Exception as e:
                print(f"[WARN] Skipping corrupted image {img_path}: {e}")

        # Write metadata.jsonl
        meta_file = target_folder / "metadata.jsonl"
        with open(meta_file, "w", encoding="utf-8") as f:
            for item in metadata_lines:
                f.write(json.dumps(item) + "\n")
        print(f"[INFO] Processed {len(metadata_lines)} images for {split_name} -> {target_folder}")

    process_split(train_images, train_dir, "train")
    if val_images:
        process_split(val_images, val_dir, "val")

    print("[SUCCESS] Dataset preparation complete.")


if __name__ == "__main__":
    main()
