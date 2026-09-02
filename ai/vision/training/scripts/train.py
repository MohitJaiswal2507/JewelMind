"""JewelMind YOLO11 Instance Segmentation Training Script.

Designed for local training on NVIDIA RTX 4060 GPU with:
- Checkpointing and uninterrupted resume from last.pt (Section 17A)
- Mixed-precision AMP acceleration
- Safe Windows multi-processing worker settings
- Comprehensive hyperparameters logging and results tracking
"""

import argparse
import sys
import time
from pathlib import Path
import torch
from ultralytics import YOLO


def train_jewelmind_yolo(
    model_name: str = "yolo11s-seg.pt",
    data_config: str = "ai/vision/training/configs/jewellery_components.yaml",
    epochs: int = 50,
    batch: int = 8,
    imgsz: int = 640,
    device: int = 0,
    project: str = "runs/jewellery",
    name: str = "yolo11s-seg-jewelmind-v1",
    resume: bool = False,
    resume_path: str = None,
    lr0: float = 0.001,
    patience: int = 15,
    save_period: int = 5,
    workers: int = 0,
):
    print("=" * 70)
    print("JEWELMIND YOLO11 SEGMENTATION TRAINING")
    print("Target Device: NVIDIA RTX 4060 GPU")
    print("=" * 70)

    # 1. Device Verification
    if torch.cuda.is_available():
        torch.cuda.set_device(device)
        gpu_name = torch.cuda.get_device_name(device)
        vram_gb = torch.cuda.get_device_properties(device).total_memory / (1024**3)
        print(f"[*] Active Device:    cuda:{device} ({gpu_name}, {vram_gb:.2f} GiB VRAM)")
    else:
        print("[!] Warning: CUDA is not available. Falling back to CPU.")
        device = "cpu"

    # 2. Checkpoint & Resume Handling (Section 17A)
    checkpoint_to_resume = None
    if resume:
        if resume_path:
            checkpoint_to_resume = Path(resume_path)
        else:
            checkpoint_to_resume = Path(project) / name / "weights" / "last.pt"

        if not checkpoint_to_resume.exists():
            print(f"[ERROR] Cannot resume: Checkpoint not found at {checkpoint_to_resume}")
            print("        Please provide a valid --resume_path or run a new training first.")
            sys.exit(1)

        print(f"[*] RESUMING TRAINING from checkpoint: {checkpoint_to_resume}")
        print("    Training will continue from the saved epoch without restarting from 0.")
        model = YOLO(str(checkpoint_to_resume))
        # Ultralytics resume call
        results = model.train(resume=True)
        return results

    # 3. Fresh Fine-Tuning Run
    print(f"[*] Initializing Base Model: {model_name}")
    print(f"[*] Dataset Config:          {data_config}")
    print(f"[*] Total Epochs:            {epochs}")
    print(f"[*] Batch Size:              {batch}")
    print(f"[*] Image Resolution:        {imgsz}x{imgsz}")
    print(f"[*] Initial Learning Rate:   {lr0}")
    print(f"[*] Early Stopping Patience: {patience}")
    print(f"[*] Checkpoint Interval:     every {save_period} epochs")
    print(f"[*] Project Run Directory:   {project}/{name}")
    print("-" * 70)

    model = YOLO(model_name)

    start_time = time.time()
    try:
        results = model.train(
            data=data_config,
            epochs=epochs,
            batch=batch,
            imgsz=imgsz,
            device=device,
            project=project,
            name=name,
            exist_ok=True,
            optimizer="AdamW",
            lr0=lr0,
            patience=patience,
            save=True,
            save_period=save_period,
            plots=True,
            val=True,
            workers=workers,
        )

        total_time_min = (time.time() - start_time) / 60.0
        print("-" * 70)
        print("[SUCCESS] TRAINING COMPLETED!")
        print(f"[*] Total Elapsed Time: {total_time_min:.2f} minutes")
        print(f"[*] Best Model Saved:   {project}/{name}/weights/best.pt")
        print(f"[*] Last Checkpoint:    {project}/{name}/weights/last.pt")
        print("=" * 70 + "\n")
        return results

    except torch.cuda.OutOfMemoryError as oom:
        print(f"\n[FAIL] CUDA OUT OF MEMORY: {oom}")
        print("[!] Quick Recovery Options for RTX 4060:")
        print("    1. Reduce batch size:  --batch 4 or --batch 2")
        print("    2. Reduce image size:  --imgsz 512")
        print("    3. Switch to small candidate: --model yolo11s-seg.pt")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FAIL] Training encountered an error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train YOLO11 on JewelMind jewellery components.")
    parser.add_argument("--model", default="yolo11s-seg.pt", help="Pretrained model weights (yolo11s-seg.pt or yolo11m-seg.pt)")
    parser.add_argument("--data", default="ai/vision/training/configs/jewellery_components.yaml", help="Path to dataset YAML config")
    parser.add_argument("--epochs", type=int, default=50, help="Total number of training epochs")
    parser.add_argument("--batch", type=int, default=8, help="Batch size (reduce to 4 or 2 if VRAM constrained)")
    parser.add_argument("--imgsz", type=int, default=640, help="Input image size")
    parser.add_argument("--device", type=int, default=0, help="CUDA GPU device index (0 for primary RTX 4060)")
    parser.add_argument("--project", default="runs/jewellery", help="Root directory for runs")
    parser.add_argument("--name", default="yolo11s-seg-jewelmind-v1", help="Experiment name")
    parser.add_argument("--resume", action="store_true", help="Resume interrupted training from last.pt")
    parser.add_argument("--resume_path", default=None, help="Explicit path to last.pt checkpoint to resume")
    parser.add_argument("--lr0", type=float, default=0.001, help="Initial learning rate")
    parser.add_argument("--patience", type=int, default=15, help="Early stopping patience epochs")
    parser.add_argument("--save_period", type=int, default=5, help="Save model checkpoint every N epochs")
    parser.add_argument("--workers", type=int, default=0, help="Dataloader workers (0 recommended for Windows)")
    args = parser.parse_args()

    train_jewelmind_yolo(
        model_name=args.model,
        data_config=args.data,
        epochs=args.epochs,
        batch=args.batch,
        imgsz=args.imgsz,
        device=args.device,
        project=args.project,
        name=args.name,
        resume=args.resume,
        resume_path=args.resume_path,
        lr0=args.lr0,
        patience=args.patience,
        save_period=args.save_period,
        workers=args.workers,
    )
