"""JewelMind Dataset Preparation & Synthetic Blueprint Generator.

Generates reproducible jewellery blueprint sketch datasets with ground-truth
YOLO instance segmentation polygon masks for local GPU benchmarking, smoke testing,
and pipeline verification.
"""

import math
import os
import random
from pathlib import Path
import cv2
import numpy as np


CLASS_MAP = {
    0: "gemstone",
    1: "ring_shank",
    2: "ring_head",
    3: "prong",
    4: "bezel",
    5: "setting",
    6: "shoulder",
}


def draw_ellipse_polygon(center, axes, angle_deg, num_points=32):
    """Generate normalized polygon vertices for an ellipse."""
    cx, cy = center
    rx, ry = axes
    angle_rad = math.radians(angle_deg)
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)

    points = []
    for i in range(num_points):
        theta = 2.0 * math.pi * i / num_points
        dx = rx * math.cos(theta)
        dy = ry * math.sin(theta)
        x = cx + dx * cos_a - dy * sin_a
        y = cy + dx * sin_a + dy * cos_a
        points.append((x, y))
    return points


def draw_shank_polygon(cx, cy, outer_r, inner_r, num_points=40):
    """Generate polygon vertices for a circular ring shank band."""
    points = []
    # Outer arc
    for i in range(num_points):
        theta = 2.0 * math.pi * i / num_points
        points.append((cx + outer_r * math.cos(theta), cy + outer_r * math.sin(theta)))
    # Return outer contour
    return points


def generate_blueprint_image(img_size=640, design_id=0):
    """Render a synthetic high-contrast jewellery ring sketch blueprint
    and compute exact normalized polygon masks for components.
    """
    rng = random.Random(design_id * 10007 + 42)
    img = np.full((img_size, img_size, 3), 242 + rng.randint(0, 8), dtype=np.uint8)

    # Unique design geometry
    offset_y = rng.randint(-15, 15)
    radius_var = rng.randint(-12, 12)

    cx = img_size // 2 + rng.randint(-8, 8)
    cy = int(img_size * 0.58) + offset_y

    shank_outer_r = int(img_size * 0.28) + radius_var
    shank_inner_r = int(img_size * 0.21) + radius_var - rng.randint(0, 4)



    labels = []  # tuples: (class_id, [(norm_x, norm_y), ...])

    # 1. Ring Shank (band)
    # Shank ring outer contour
    shank_pts = draw_shank_polygon(cx, cy, shank_outer_r, shank_inner_r, num_points=36)
    # Draw sketch strokes on canvas
    cv2.circle(img, (cx, cy), shank_outer_r, (40, 40, 40), 3, cv2.LINE_AA)
    cv2.circle(img, (cx, cy), shank_inner_r, (40, 40, 40), 3, cv2.LINE_AA)

    # Crosshatch/contour lines for hand-drawn feel
    for angle in range(-45, 225, 30):
        rad = math.radians(angle)
        x1 = int(cx + shank_inner_r * math.cos(rad))
        y1 = int(cy + shank_inner_r * math.sin(rad))
        x2 = int(cx + shank_outer_r * math.cos(rad))
        y2 = int(cy + shank_outer_r * math.sin(rad))
        cv2.line(img, (x1, y1), (x2, y2), (180, 180, 180), 1, cv2.LINE_AA)

    norm_shank_pts = [(x / img_size, y / img_size) for (x, y) in shank_pts]
    labels.append((1, norm_shank_pts))  # 1: ring_shank

    # 2. Ring Shoulders (left and right tapers into head)
    shoulder_y = cy - int(shank_outer_r * 0.75)
    shoulder_w = int(img_size * 0.08)
    shoulder_h = int(img_size * 0.05)

    left_shoulder_pts = [
        (cx - shank_outer_r, shoulder_y),
        (cx - shank_outer_r + shoulder_w, shoulder_y - shoulder_h),
        (cx - shank_inner_r, shoulder_y + shoulder_h),
        (cx - shank_inner_r - shoulder_w // 2, shoulder_y + shoulder_h * 2),
    ]
    cv2.polylines(img, [np.array(left_shoulder_pts, dtype=np.int32)], True, (35, 35, 35), 2, cv2.LINE_AA)
    labels.append((6, [(x / img_size, y / img_size) for x, y in left_shoulder_pts]))  # 6: shoulder

    right_shoulder_pts = [
        (cx + shank_outer_r, shoulder_y),
        (cx + shank_outer_r - shoulder_w, shoulder_y - shoulder_h),
        (cx + shank_inner_r, shoulder_y + shoulder_h),
        (cx + shank_inner_r + shoulder_w // 2, shoulder_y + shoulder_h * 2),
    ]
    cv2.polylines(img, [np.array(right_shoulder_pts, dtype=np.int32)], True, (35, 35, 35), 2, cv2.LINE_AA)
    labels.append((6, [(x / img_size, y / img_size) for x, y in right_shoulder_pts]))  # 6: shoulder

    # 3. Ring Head / Mount Basket
    head_cy = cy - shank_outer_r - int(img_size * 0.04)
    head_w = int(img_size * 0.16)
    head_h = int(img_size * 0.09)

    head_pts = [
        (cx - head_w, head_cy + head_h // 2),
        (cx - head_w // 2, head_cy - head_h // 2),
        (cx + head_w // 2, head_cy - head_h // 2),
        (cx + head_w, head_cy + head_h // 2),
        (cx, head_cy + head_h),
    ]
    cv2.fillConvexPoly(img, np.array(head_pts, dtype=np.int32), (220, 220, 220), cv2.LINE_AA)
    cv2.polylines(img, [np.array(head_pts, dtype=np.int32)], True, (30, 30, 30), 2, cv2.LINE_AA)
    labels.append((2, [(x / img_size, y / img_size) for x, y in head_pts]))  # 2: ring_head

    # 4. Bezel / Stone Setting
    bezel_cy = head_cy - int(img_size * 0.02)
    bezel_r = int(img_size * 0.09)
    bezel_pts = draw_ellipse_polygon((cx, bezel_cy), (bezel_r, int(bezel_r * 0.9)), 0, num_points=24)
    cv2.circle(img, (cx, bezel_cy), bezel_r, (40, 40, 40), 2, cv2.LINE_AA)
    labels.append((4, [(x / img_size, y / img_size) for x, y in bezel_pts]))  # 4: bezel

    # 5. Center Gemstone
    gem_r = int(bezel_r * 0.8)
    gem_pts = draw_ellipse_polygon((cx, bezel_cy), (gem_r, int(gem_r * 0.88)), 0, num_points=20)
    # Fill with blueprint gemstone facet lines
    cv2.circle(img, (cx, bezel_cy), gem_r, (25, 25, 25), 2, cv2.LINE_AA)
    # Brilliant cut star facets
    for i in range(8):
        rad = math.radians(i * 45)
        fx = int(cx + gem_r * math.cos(rad))
        fy = int(bezel_cy + gem_r * math.sin(rad))
        cv2.line(img, (cx, bezel_cy), (fx, fy), (80, 80, 80), 1, cv2.LINE_AA)
    labels.append((0, [(x / img_size, y / img_size) for x, y in gem_pts]))  # 0: gemstone

    # 6. Prongs (4 claws securing center stone)
    prong_offsets = [(-gem_r, -int(gem_r * 0.7)), (gem_r, -int(gem_r * 0.7)),
                     (-gem_r, int(gem_r * 0.7)), (gem_r, int(gem_r * 0.7))]
    for px_off, py_off in prong_offsets:
        pcx = cx + px_off
        pcy = bezel_cy + py_off
        pr_w, pr_h = int(img_size * 0.018), int(img_size * 0.025)
        p_pts = [
            (pcx - pr_w, pcy - pr_h),
            (pcx + pr_w, pcy - pr_h),
            (pcx + pr_w, pcy + pr_h),
            (pcx - pr_w, pcy + pr_h),
        ]
        cv2.fillConvexPoly(img, np.array(p_pts, dtype=np.int32), (60, 60, 60), cv2.LINE_AA)
        labels.append((3, [(x / img_size, y / img_size) for x, y in p_pts]))  # 3: prong

    # Subtle blueprint grid lines
    grid_spacing = 64
    for gx in range(0, img_size, grid_spacing):
        cv2.line(img, (gx, 0), (gx, img_size), (235, 235, 235), 1)
    for gy in range(0, img_size, grid_spacing):
        cv2.line(img, (0, gy), (img_size, gy), (235, 235, 235), 1)

    return img, labels


def prepare_benchmark_dataset(base_dir="ai/vision/datasets/sample", num_train=35, num_val=10, num_test=5, seed=42):
    """Build train/val/test splits with balanced synthetic blueprint sketches."""
    random.seed(seed)
    np.random.seed(seed)

    base_path = Path(base_dir)

    splits = {
        "train": num_train,
        "val": num_val,
        "test": num_test,
    }

    split_offset = {"train": 0, "val": 100, "test": 200}

    for split_name, count in splits.items():
        img_dir = base_path / split_name / "images"
        lbl_dir = base_path / split_name / "labels"
        img_dir.mkdir(parents=True, exist_ok=True)
        lbl_dir.mkdir(parents=True, exist_ok=True)

        for i in range(count):
            global_id = split_offset[split_name] + i
            img_id = f"ring_{split_name}_{i:03d}"
            img, labels = generate_blueprint_image(img_size=640, design_id=global_id)


            img_file = img_dir / f"{img_id}.jpg"
            lbl_file = lbl_dir / f"{img_id}.txt"

            cv2.imwrite(str(img_file), img, [cv2.IMWRITE_JPEG_QUALITY, 95])

            with open(lbl_file, "w", encoding="utf-8") as f:
                for class_id, pts in labels:
                    # Clip points strictly in [0, 1]
                    poly_str = " ".join(f"{max(0.0, min(1.0, x)):.6f} {max(0.0, min(1.0, y)):.6f}" for x, y in pts)
                    f.write(f"{class_id} {poly_str}\n")

    print(f"[SUCCESS] Dataset created at {base_path}: {num_train} train, {num_val} val, {num_test} test.")


if __name__ == "__main__":
    prepare_benchmark_dataset()
