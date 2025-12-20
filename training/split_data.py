#!/usr/bin/env python3
"""
Split dataset into train/val sets for YOLO training.
Usage: python3 split_data.py --ratio 0.8
"""

import os
import shutil
import random
import argparse
from pathlib import Path


def split_data(data_dir: str, train_ratio: float = 0.8, seed: int = 42):
    """Split images and labels into train/val sets."""
    random.seed(seed)

    data_path = Path(data_dir)
    images_train = data_path / "images" / "train"
    labels_train = data_path / "labels" / "train"
    images_val = data_path / "images" / "val"
    labels_val = data_path / "labels" / "val"

    # Create val directories
    images_val.mkdir(parents=True, exist_ok=True)
    labels_val.mkdir(parents=True, exist_ok=True)

    # Get all image files
    image_files = list(images_train.glob("*.jpg")) + list(images_train.glob("*.png"))

    if not image_files:
        print("No images found in", images_train)
        return

    # Shuffle and split
    random.shuffle(image_files)
    split_idx = int(len(image_files) * train_ratio)

    val_images = image_files[split_idx:]

    print(f"Total images: {len(image_files)}")
    print(f"Train: {split_idx}, Val: {len(val_images)}")

    # Move val files
    moved = 0
    for img_path in val_images:
        # Move image
        dst_img = images_val / img_path.name
        shutil.move(str(img_path), str(dst_img))

        # Move corresponding label
        label_name = img_path.stem + ".txt"
        src_label = labels_train / label_name
        dst_label = labels_val / label_name

        if src_label.exists():
            shutil.move(str(src_label), str(dst_label))
            moved += 1

    print(f"Moved {moved} image-label pairs to val set")
    print(f"Train images: {len(list(images_train.glob('*.jpg')))}")
    print(f"Val images: {len(list(images_val.glob('*.jpg')))}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Split dataset into train/val")
    parser.add_argument("--data", type=str, default="data", help="Data directory")
    parser.add_argument("--ratio", type=float, default=0.8, help="Train ratio (default: 0.8)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")

    args = parser.parse_args()

    script_dir = Path(__file__).parent.resolve()
    data_dir = script_dir / args.data

    split_data(str(data_dir), args.ratio, args.seed)
