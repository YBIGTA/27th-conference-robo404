#!/usr/bin/env python3
"""
YOLO Fine-tuning Script

Usage:
    python train.py --model yolov8n.pt --epochs 100
    python train.py --model yolov8s.pt --epochs 50 --batch 8
    python train.py --resume weights/last.pt
"""

import argparse
from pathlib import Path
from ultralytics import YOLO


def parse_args():
    parser = argparse.ArgumentParser(description="YOLO Fine-tuning Script")

    # Model
    parser.add_argument(
        "--model",
        type=str,
        default="yolov8n.pt",
        help="Pretrained model name or path (default: yolov8n.pt)"
    )

    # Dataset
    parser.add_argument(
        "--data",
        type=str,
        default="data/dataset.yaml",
        help="Path to dataset.yaml (default: data/dataset.yaml)"
    )

    # Training hyperparameters
    parser.add_argument("--epochs", type=int, default=100, help="Number of epochs")
    parser.add_argument("--batch", type=int, default=16, help="Batch size")
    parser.add_argument("--imgsz", type=int, default=640, help="Image size")
    parser.add_argument("--lr0", type=float, default=0.01, help="Initial learning rate")
    parser.add_argument("--lrf", type=float, default=0.01, help="Final learning rate factor")

    # Device
    parser.add_argument(
        "--device",
        type=str,
        default="0",
        help="CUDA device (0, 1, ...) or 'cpu'"
    )

    # Output
    parser.add_argument(
        "--project",
        type=str,
        default="weights",
        help="Project directory for saving results"
    )
    parser.add_argument(
        "--name",
        type=str,
        default="train",
        help="Experiment name"
    )

    # Resume training
    parser.add_argument(
        "--resume",
        type=str,
        default=None,
        help="Resume training from checkpoint (path to last.pt)"
    )

    # Other options
    parser.add_argument("--patience", type=int, default=50, help="Early stopping patience")
    parser.add_argument("--workers", type=int, default=8, help="Number of data loader workers")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--exist-ok", action="store_true", help="Overwrite existing project/name")

    # Augmentation options
    parser.add_argument("--hsv_h", type=float, default=0.015, help="HSV-Hue augmentation")
    parser.add_argument("--hsv_s", type=float, default=0.7, help="HSV-Saturation augmentation")
    parser.add_argument("--hsv_v", type=float, default=0.4, help="HSV-Value augmentation")
    parser.add_argument("--degrees", type=float, default=0.0, help="Rotation augmentation (degrees)")
    parser.add_argument("--translate", type=float, default=0.1, help="Translation augmentation")
    parser.add_argument("--scale", type=float, default=0.5, help="Scale augmentation")
    parser.add_argument("--fliplr", type=float, default=0.5, help="Horizontal flip probability")
    parser.add_argument("--mosaic", type=float, default=1.0, help="Mosaic augmentation probability")

    return parser.parse_args()


def main():
    args = parse_args()

    # Set working directory to script location
    script_dir = Path(__file__).parent.resolve()

    # Resolve data path
    data_path = Path(args.data)
    if not data_path.is_absolute():
        data_path = script_dir / data_path

    # Check dataset exists
    if not data_path.exists():
        print(f"Error: Dataset config not found: {data_path}")
        print("Please create data/dataset.yaml with your dataset configuration.")
        return 1

    # Resume or load pretrained model
    if args.resume:
        print(f"Resuming training from: {args.resume}")
        model = YOLO(args.resume)
    else:
        print(f"Loading pretrained model: {args.model}")
        model = YOLO(args.model)

    # Start training
    print(f"\n{'='*50}")
    print("Starting YOLO Fine-tuning")
    print(f"{'='*50}")
    print(f"Model: {args.model}")
    print(f"Dataset: {data_path}")
    print(f"Epochs: {args.epochs}")
    print(f"Batch size: {args.batch}")
    print(f"Image size: {args.imgsz}")
    print(f"Device: {args.device}")
    print(f"{'='*50}\n")

    results = model.train(
        data=str(data_path),
        epochs=args.epochs,
        batch=args.batch,
        imgsz=args.imgsz,
        lr0=args.lr0,
        lrf=args.lrf,
        device=args.device,
        project=str(script_dir / args.project),
        name=args.name,
        patience=args.patience,
        workers=args.workers,
        seed=args.seed,
        exist_ok=args.exist_ok,
        verbose=True,
        plots=True,
        # Augmentation
        hsv_h=args.hsv_h,
        hsv_s=args.hsv_s,
        hsv_v=args.hsv_v,
        degrees=args.degrees,
        translate=args.translate,
        scale=args.scale,
        fliplr=args.fliplr,
        mosaic=args.mosaic,
    )

    print(f"\n{'='*50}")
    print("Training completed!")
    print(f"Results saved to: {script_dir / args.project / args.name}")
    print(f"{'='*50}")

    return 0


if __name__ == "__main__":
    exit(main())
