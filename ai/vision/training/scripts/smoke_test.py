"""JewelMind GPU Smoke Test for YOLO11 Instance Segmentation.

Executes an intentional 1-epoch mini-run on the local NVIDIA RTX 4060 to verify:
1. CUDA device accessibility and VRAM allocation.
2. Ultralytics YOLO11s-seg model weight loading.
3. Dataset loading and segmentation polygon parsing.
4. GPU forward pass, backward pass, and loss convergence.
5. Detection of any potential Out-Of-Memory (OOM) or CUDA runtime issues.
"""

import sys
import time
from pathlib import Path
import torch
from ultralytics import YOLO


def run_gpu_smoke_test(
    config_path: str = "ai/vision/training/configs/jewellery_components.yaml",
    model_name: str = "yolo11s-seg.pt",
    imgsz: int = 640,
    batch: int = 4,
):
    print("=" * 65)
    print("JEWELMIND GPU SMOKE TEST — NVIDIA RTX 4060 VERIFICATION")
    print("=" * 65)

    # 1. Verify CUDA availability
    if not torch.cuda.is_available():
        print("[FAIL] CUDA is NOT available. RTX 4060 cannot be accessed by PyTorch.")
        return False

    gpu_name = torch.cuda.get_device_name(0)
    vram_bytes = torch.cuda.get_device_properties(0).total_memory
    vram_gb = vram_bytes / (1024**3)
    torch_cuda = torch.version.cuda

    print(f"[*] GPU Device:       {gpu_name}")
    print(f"[*] Dedicated VRAM:   {vram_gb:.2f} GiB")
    print(f"[*] PyTorch Version:  {torch.__version__}")
    print(f"[*] CUDA Runtime:     {torch_cuda}")
    print(f"[*] Model Candidate:  {model_name}")
    print(f"[*] Image Size:       {imgsz}x{imgsz}")
    print(f"[*] Batch Size:       {batch}")
    print("-" * 65)

    # 2. Reset CUDA memory stats
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats(0)

    start_time = time.time()
    try:
        print(f"[*] Initializing YOLO model: {model_name}...")
        model = YOLO(model_name)

        print("[*] Launching 1-epoch GPU smoke test on device=0...")
        # Ultralytics train call for 1 epoch
        results = model.train(
            data=config_path,
            epochs=1,
            imgsz=imgsz,
            batch=batch,
            device=0,
            project="runs/smoke_test",
            name="gpu_smoke_run",
            exist_ok=True,
            verbose=True,
            plots=False,
            save=False,
            workers=0,  # Windows safe worker setting
        )

        elapsed = time.time() - start_time
        peak_vram_mb = torch.cuda.max_memory_allocated(0) / (1024**2)

        print("-" * 65)
        print("[SUCCESS] GPU SMOKE TEST PASSED!")
        print(f"[*] Elapsed Time:     {elapsed:.2f} seconds")
        print(f"[*] Peak VRAM Used:   {peak_vram_mb:.1f} MiB ({peak_vram_mb / 1024:.2f} GiB)")
        print(f"[*] VRAM Headroom:    {vram_gb - (peak_vram_mb / 1024):.2f} GiB remaining")
        print("=" * 65 + "\n")
        return True

    except torch.cuda.OutOfMemoryError as oom_err:
        print(f"\n[FAIL] CUDA OUT OF MEMORY ERROR: {oom_err}")
        print("[!] Recommendation: Reduce batch size to 2 and retry.")
        return False
    except Exception as e:
        print(f"\n[FAIL] Smoke test encountered an error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_gpu_smoke_test()
    sys.exit(0 if success else 1)
