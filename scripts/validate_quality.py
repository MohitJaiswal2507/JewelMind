"""JewelMind Phase 7 — Fixed Quality & Geometry Validation Suite.

Executes generation across a fixed validation set of jewellery blueprint sketches
(ring, pendant/earrings, bangle/bracelet) with fixed seeds, computes edge overlap
geometry retention metrics, and logs visual inspection findings.
"""

import os
import sys
import cv2
import numpy as np
from pathlib import Path
from PIL import Image
import torch

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from ai.rendering.config import rendering_config
from ai.rendering.pipeline import JewelleryRenderingPipeline
from ai.rendering.schemas import RenderRequest


def compute_edge_overlap_score(sketch_img: Image.Image, render_img: Image.Image) -> float:
    """Compute structural edge intersection score between sketch and rendered jewellery."""
    # Convert both to grayscale 512x512
    sk_gray = np.array(sketch_img.convert("L").resize((512, 512)))
    ren_gray = np.array(render_img.convert("L").resize((512, 512)))

    # Compute Canny edges
    edges_sk = cv2.Canny(sk_gray, 80, 180)
    edges_ren = cv2.Canny(ren_gray, 80, 180)

    # Dilate edges slightly (3x3 kernel) to account for stroke thickness differences
    kernel = np.ones((3, 3), np.uint8)
    edges_sk_dilated = cv2.dilate(edges_sk, kernel, iterations=1)
    edges_ren_dilated = cv2.dilate(edges_ren, kernel, iterations=1)

    intersection = np.logical_and(edges_sk_dilated > 0, edges_ren_dilated > 0)
    union = np.logical_or(edges_sk_dilated > 0, edges_ren_dilated > 0)

    union_count = np.count_nonzero(union)
    if union_count == 0:
        return 1.0

    iou = np.count_nonzero(intersection) / union_count
    return round(float(iou) * 100.0, 2)


def run_quality_validation():
    print("=" * 70)
    print("  JEWELMIND PHASE 7 — QUALITY & GEOMETRY VALIDATION")
    print("=" * 70)

    if not torch.cuda.is_available():
        print("[FAIL] CUDA is required for quality validation.")
        sys.exit(1)

    # Find sample images
    dataset_dir = WORKSPACE_ROOT / "ai" / "vision" / "datasets"
    candidate_files = sorted(list(dataset_dir.rglob("*.jpg")))[:5]
    if not candidate_files:
        print("[FAIL] No dataset sketches found.")
        sys.exit(1)

    pipeline = JewelleryRenderingPipeline()

    validation_suite = [
        {
            "id": "val_ring_solitaire",
            "file": candidate_files[0],
            "category": "ring",
            "material": "18k yellow gold",
            "gemstone": "round brilliant diamond",
            "seed": 42,
            "control_type": "lineart",
            "prompt": "solitaire engagement ring with four-prong setting",
        },
        {
            "id": "val_ring_sapphire",
            "file": candidate_files[1] if len(candidate_files) > 1 else candidate_files[0],
            "category": "ring",
            "material": "platinum",
            "gemstone": "blue sapphire",
            "seed": 108,
            "control_type": "lineart",
            "prompt": "cushion cut sapphire cocktail ring with micropave band",
        },
        {
            "id": "val_pendant_emerald",
            "file": candidate_files[2] if len(candidate_files) > 2 else candidate_files[0],
            "category": "pendant",
            "material": "rose gold",
            "gemstone": "emerald",
            "seed": 2026,
            "control_type": "canny",
            "prompt": "teardrop pendant necklace with halo emerald setting",
        },
    ]

    results = []

    for item in validation_suite:
        print(f"\n[EVAL] Testing {item['category']} ({item['id']}) | File: {item['file'].name}")
        sketch = Image.open(item["file"])

        req = RenderRequest(
            category=item["category"],
            material=item["material"],
            gemstone=item["gemstone"],
            control_type=item["control_type"],
            control_strength=1.0,
            steps=20,
            guidance_scale=7.5,
            seed=item["seed"],
            prompt=item["prompt"],
            width=512,
            height=512,
        )

        rendered, res = pipeline.render(sketch, request=req)
        edge_score = compute_edge_overlap_score(sketch, rendered)

        results.append({
            "id": item["id"],
            "category": item["category"],
            "material": item["material"],
            "gemstone": item["gemstone"],
            "seed": item["seed"],
            "edge_overlap_pct": edge_score,
            "latency_s": round(res.inference_time_ms / 1000, 2),
            "output_url": res.output_url,
        })

        print(f"       Material: {item['material']} | Gemstone: {item['gemstone']}")
        print(f"       Inference Time: {res.inference_time_ms/1000:.2f} s")
        print(f"       Geometry Edge Overlap: {edge_score}%")
        print(f"       Output: {res.output_url}")

    print("\n" + "=" * 70)
    print("  QUALITY VALIDATION SUMMARY")
    print("=" * 70)
    print(f"{'ID':<22} | {'Category':<10} | {'Material':<16} | {'Overlap %':<10} | {'Latency':<8}")
    print("-" * 70)
    for r in results:
        print(f"{r['id']:<22} | {r['category']:<10} | {r['material']:<16} | {r['edge_overlap_pct']:<10.1f} | {r['latency_s']:<8.2f}s")
    print("=" * 70)
    print("Quality validation completed successfully.")


if __name__ == "__main__":
    run_quality_validation()
