"""JewelMind YOLO11s-seg vs YOLO11m-seg Model Benchmark on NVIDIA RTX 4060.

Runs a controlled short-run comparative experiment between:
- YOLO11s-seg (Small, 10.1M params, fast, low VRAM)
- YOLO11m-seg (Medium, 22.4M params, higher capacity, higher VRAM)

Measures:
- Parameter count and GFLOPs
- Peak VRAM usage on RTX 4060 (MiB)
- Training throughput / epoch duration
- Inference latency per image (ms)
- Validation Box & Mask precision, recall, mAP50, mAP50-95
"""

import argparse
import json
import time
from pathlib import Path
import torch
from ultralytics import YOLO


def benchmark_model_candidate(
    model_name: str,
    config_path: str = "ai/vision/training/configs/jewellery_components.yaml",
    epochs: int = 2,
    batch: int = 4,
    imgsz: int = 640,
) -> dict:
    print(f"\n{'='*70}")
    print(f"BENCHMARKING CANDIDATE: {model_name} (Epochs: {epochs}, Batch: {batch}, Imgsz: {imgsz})")
    print(f"{'='*70}")

    if torch.cuda.is_available():
        torch.cuda.set_device(0)
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats(0)

    model = YOLO(model_name)


    # Measure inference latency on dummy/test input
    dummy_input = torch.rand((1, 3, imgsz, imgsz), device="cuda" if torch.cuda.is_available() else "cpu")
    # Warmup
    for _ in range(5):
        _ = model(dummy_input, verbose=False)

    latencies = []
    for _ in range(20):
        t0 = time.perf_counter()
        _ = model(dummy_input, verbose=False)
        torch.cuda.synchronize()
        latencies.append((time.perf_counter() - t0) * 1000.0)
    avg_inference_ms = sum(latencies) / len(latencies)

    # Train short run
    t_start = time.time()
    results = model.train(
        data=config_path,
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        device=0,
        project="runs/benchmark",
        name=f"bench_{Path(model_name).stem}",
        exist_ok=True,
        verbose=False,
        save=True,
        workers=0,
    )
    total_train_sec = time.time() - t_start
    peak_vram_mb = torch.cuda.max_memory_allocated(0) / (1024**2)

    # Extract metrics from validation
    val_results = model.val(data=config_path, device=0, verbose=False)

    metrics = {
        "model_name": model_name,
        "parameters": sum(p.numel() for p in model.model.parameters()),
        "peak_vram_mb": round(peak_vram_mb, 1),
        "peak_vram_gb": round(peak_vram_mb / 1024, 2),
        "avg_inference_ms": round(avg_inference_ms, 2),
        "total_train_sec": round(total_train_sec, 2),
        "sec_per_epoch": round(total_train_sec / epochs, 2),
        "box_p": round(float(val_results.box.p[0]) if len(val_results.box.p) else 0.0, 4),
        "box_r": round(float(val_results.box.r[0]) if len(val_results.box.r) else 0.0, 4),
        "box_map50": round(float(val_results.box.map50), 4),
        "box_map50_95": round(float(val_results.box.map), 4),
        "mask_p": round(float(val_results.seg.p[0]) if len(val_results.seg.p) else 0.0, 4),
        "mask_r": round(float(val_results.seg.r[0]) if len(val_results.seg.r) else 0.0, 4),
        "mask_map50": round(float(val_results.seg.map50), 4),
        "mask_map50_95": round(float(val_results.seg.map), 4),
    }

    print(f"[*] {model_name} Results:")
    print(f"    - Parameters:     {metrics['parameters']:,}")
    print(f"    - Peak VRAM:       {metrics['peak_vram_mb']} MiB ({metrics['peak_vram_gb']} GiB)")
    print(f"    - Inference Speed: {metrics['avg_inference_ms']} ms/image")
    print(f"    - Train Speed:     {metrics['sec_per_epoch']} s/epoch")
    print(f"    - Mask mAP50:      {metrics['mask_map50']:.4f}")
    print(f"    - Mask mAP50-95:   {metrics['mask_map50_95']:.4f}")

    return metrics


def run_benchmark(
    config_path: str = "ai/vision/training/configs/jewellery_components.yaml",
    output_json: str = "ai/vision/training/benchmark_results.json",
    epochs: int = 2,
    batch: int = 4,
):
    print("=" * 70)
    print("JEWELMIND YOLO11 BENCHMARK: YOLO11s-seg vs YOLO11m-seg")
    print("Target Hardware: NVIDIA RTX 4060 Laptop GPU (8GB VRAM)")
    print("=" * 70)

    candidates = ["yolo11s-seg.pt", "yolo11m-seg.pt"]
    results = {}

    for cand in candidates:
        try:
            results[cand] = benchmark_model_candidate(cand, config_path, epochs=epochs, batch=batch)
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"[!] Benchmark failed for {cand}: {str(e)}")
            results[cand] = {"error": str(e)}


    # Print Comparative Table
    print("\n" + "=" * 85)
    print("BENCHMARK COMPARATIVE RESULTS")
    print("=" * 85)
    print(f"{'Metric':<25} | {'YOLO11s-seg':<25} | {'YOLO11m-seg':<25}")
    print("-" * 85)

    s = results.get("yolo11s-seg.pt", {})
    m = results.get("yolo11m-seg.pt", {})

    def fmt(d, key, suffix=""):
        val = d.get(key, "N/A")
        return f"{val}{suffix}"

    print(f"{'Parameters':<25} | {fmt(s, 'parameters'):<25} | {fmt(m, 'parameters'):<25}")
    print(f"{'Peak VRAM (MiB / GiB)':<25} | {s.get('peak_vram_mb','N/A')} MiB ({s.get('peak_vram_gb','N/A')} GiB) | {m.get('peak_vram_mb','N/A')} MiB ({m.get('peak_vram_gb','N/A')} GiB)")
    print(f"{'Inference Latency':<25} | {fmt(s, 'avg_inference_ms', ' ms'):<25} | {fmt(m, 'avg_inference_ms', ' ms'):<25}")
    print(f"{'Epoch Duration':<25} | {fmt(s, 'sec_per_epoch', ' s'):<25} | {fmt(m, 'sec_per_epoch', ' s'):<25}")
    print(f"{'Mask mAP50':<25} | {fmt(s, 'mask_map50'):<25} | {fmt(m, 'mask_map50'):<25}")
    print(f"{'Mask mAP50-95':<25} | {fmt(s, 'mask_map50_95'):<25} | {fmt(m, 'mask_map50_95'):<25}")
    print(f"{'Box mAP50':<25} | {fmt(s, 'box_map50'):<25} | {fmt(m, 'box_map50'):<25}")
    print("=" * 85 + "\n")

    # Save to disk
    out_file = Path(output_json)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"[SUCCESS] Benchmark report saved to {out_file}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="ai/vision/training/configs/jewellery_components.yaml")
    parser.add_argument("--epochs", type=int, default=2)
    parser.add_argument("--batch", type=int, default=4)
    parser.add_argument("--output", default="ai/vision/training/benchmark_results.json")
    args = parser.parse_args()

    run_benchmark(args.config, args.output, epochs=args.epochs, batch=args.batch)
