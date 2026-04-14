#!/usr/bin/env python3
from __future__ import annotations

import argparse
import random
import shutil
from pathlib import Path


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".webp"}
CLASSES = ["drawing_area", "title_block", "specification_table", "notes_block", "dimension_cluster", "border_frame"]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Train YOLOv8 layout model for mcp_mvp on a remote GPU server.")
    p.add_argument("--repo-root", default=".", help="Path to repository root.")
    p.add_argument("--images-root", default="dataset", help="Dataset root with image folders (mix/worst/...).")
    p.add_argument(
        "--labels-root",
        required=True,
        help="Directory with YOLO txt labels (same basename as images).",
    )
    p.add_argument("--out-root", default="training/layout", help="Output root for prepared dataset and runs.")
    p.add_argument("--train-ratio", type=float, default=0.8, help="Train split ratio.")
    p.add_argument("--val-ratio", type=float, default=0.1, help="Val split ratio.")
    p.add_argument("--seed", type=int, default=42, help="Random seed for split.")
    p.add_argument("--imgsz", type=int, default=1280, help="YOLO image size.")
    p.add_argument("--epochs", type=int, default=100, help="Epochs.")
    p.add_argument("--batch", type=int, default=4, help="Batch size.")
    p.add_argument("--device", default="0", help="CUDA device index, e.g. 0.")
    p.add_argument("--model", default="yolov8n.pt", help="Base model checkpoint.")
    p.add_argument("--workers", type=int, default=4, help="Data loader workers.")
    p.add_argument("--project", default="training/layout/runs", help="Ultralytics project dir.")
    p.add_argument("--name", default="layout_yolov8n", help="Ultralytics run name.")
    p.add_argument("--patience", type=int, default=20, help="Early stopping patience.")
    p.add_argument("--optimizer", default="AdamW", help="SGD/Adam/AdamW/auto.")
    p.add_argument("--lr0", type=float, default=0.002, help="Initial learning rate.")
    p.add_argument("--lrf", type=float, default=0.01, help="Final LR ratio.")
    p.add_argument("--weight-decay", type=float, default=0.0005, help="Weight decay.")
    p.add_argument("--cos-lr", action="store_true", help="Use cosine LR scheduler.")
    p.add_argument("--mosaic", type=float, default=0.4, help="Mosaic augmentation probability.")
    p.add_argument("--mixup", type=float, default=0.0, help="MixUp probability.")
    p.add_argument("--close-mosaic", type=int, default=12, help="Disable mosaic in last N epochs.")
    p.add_argument("--degrees", type=float, default=0.0, help="Random rotation degrees.")
    p.add_argument("--translate", type=float, default=0.08, help="Random translate factor.")
    p.add_argument("--scale", type=float, default=0.35, help="Random scale factor.")
    p.add_argument("--fliplr", type=float, default=0.5, help="Horizontal flip probability.")
    p.add_argument("--hsv-s", type=float, default=0.4, help="HSV saturation augmentation.")
    p.add_argument("--hsv-v", type=float, default=0.2, help="HSV value augmentation.")
    p.add_argument(
        "--convert-cls-labels",
        action="store_true",
        help="Convert cls-only YOLO labels ('<class_id>') to detection full-image boxes.",
    )
    return p.parse_args()


def collect_images(images_root: Path) -> list[Path]:
    folders = ["mix", "worst", "handwritten", "dense_dims"]
    images: list[Path] = []
    for folder in folders:
        d = images_root / folder
        if not d.exists():
            continue
        for p in d.iterdir():
            if p.is_file() and p.suffix.lower() in IMAGE_EXTS:
                images.append(p)
    return sorted(images)


def detect_pre_split_mode(images_root: Path, labels_root: Path) -> bool:
    return (
        (images_root / "train").exists()
        and (images_root / "val").exists()
        and (labels_root / "train").exists()
        and (labels_root / "val").exists()
    )


def fail(msg: str) -> None:
    raise SystemExit(f"[train_layout_yolo] ERROR: {msg}")


def sanitize_labels_for_detection(labels_root: Path, convert_cls_labels: bool) -> tuple[int, int, int]:
    """
    Returns: (files_touched, lines_converted, lines_dropped)
    """
    touched = 0
    converted = 0
    dropped = 0
    for lbl in labels_root.rglob("*.txt"):
        raw = lbl.read_text(encoding="utf-8", errors="ignore").splitlines()
        out: list[str] = []
        file_changed = False
        for line in raw:
            s = line.strip()
            if not s:
                file_changed = True
                dropped += 1
                continue
            parts = s.split()
            if len(parts) == 1:
                if convert_cls_labels:
                    try:
                        cls = int(float(parts[0]))
                    except ValueError:
                        file_changed = True
                        dropped += 1
                        continue
                    out.append(f"{cls} 0.5 0.5 1.0 1.0")
                    file_changed = True
                    converted += 1
                else:
                    file_changed = True
                    dropped += 1
            elif len(parts) == 5:
                try:
                    cls = int(float(parts[0]))
                    xc, yc, w, h = [float(x) for x in parts[1:]]
                    if not (0 <= xc <= 1 and 0 <= yc <= 1 and 0 < w <= 1 and 0 < h <= 1):
                        file_changed = True
                        dropped += 1
                        continue
                    out.append(f"{cls} {xc:.6f} {yc:.6f} {w:.6f} {h:.6f}")
                except ValueError:
                    file_changed = True
                    dropped += 1
            else:
                file_changed = True
                dropped += 1
        if file_changed:
            touched += 1
            lbl.write_text("\n".join(out) + ("\n" if out else ""), encoding="utf-8")
    return touched, converted, dropped


def build_splits(images: list[Path], train_ratio: float, val_ratio: float, seed: int) -> tuple[list[Path], list[Path], list[Path]]:
    if not (0 < train_ratio < 1):
        fail("--train-ratio must be in (0,1)")
    if not (0 <= val_ratio < 1):
        fail("--val-ratio must be in [0,1)")
    if train_ratio + val_ratio >= 1:
        fail("train_ratio + val_ratio must be < 1")

    rnd = random.Random(seed)
    shuffled = images[:]
    rnd.shuffle(shuffled)
    n = len(shuffled)
    n_train = int(n * train_ratio)
    n_val = int(n * val_ratio)
    train = shuffled[:n_train]
    val = shuffled[n_train : n_train + n_val]
    test = shuffled[n_train + n_val :]
    return train, val, test


def stage_split(split_name: str, files: list[Path], labels_root: Path, stage_root: Path) -> int:
    img_out = stage_root / "images" / split_name
    lbl_out = stage_root / "labels" / split_name
    img_out.mkdir(parents=True, exist_ok=True)
    lbl_out.mkdir(parents=True, exist_ok=True)

    copied = 0
    for src in files:
        label_src = labels_root / f"{src.stem}.txt"
        if not label_src.exists():
            continue
        shutil.copy2(src, img_out / src.name)
        shutil.copy2(label_src, lbl_out / f"{src.stem}.txt")
        copied += 1
    return copied


def write_dataset_yaml(stage_root: Path) -> Path:
    y = stage_root / "dataset.yaml"
    y.write_text(
        "\n".join(
            [
                f"path: {stage_root.resolve()}",
                "train: images/train",
                "val: images/val",
                "test: images/test",
                f"nc: {len(CLASSES)}",
                "names:",
                *[f"  {i}: {name}" for i, name in enumerate(CLASSES)],
                "",
            ]
        ),
        encoding="utf-8",
    )
    return y


def count_split_samples(images_root: Path, labels_root: Path, split: str) -> int:
    img_dir = images_root / split
    lbl_dir = labels_root / split
    if not img_dir.exists() or not lbl_dir.exists():
        return 0
    cnt = 0
    for img in img_dir.iterdir():
        if not img.is_file() or img.suffix.lower() not in IMAGE_EXTS:
            continue
        label = lbl_dir / f"{img.stem}.txt"
        if label.exists():
            cnt += 1
    return cnt


def main() -> None:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    images_root = (repo_root / args.images_root).resolve()
    labels_root = Path(args.labels_root).resolve()
    out_root = (repo_root / args.out_root).resolve()

    if not images_root.exists():
        fail(f"images root not found: {images_root}")
    if not labels_root.exists():
        fail(f"labels root not found: {labels_root}")

    touched, conv, drop = sanitize_labels_for_detection(labels_root, convert_cls_labels=args.convert_cls_labels)
    if touched:
        print(
            f"[train_layout_yolo] label sanitization: files_touched={touched}, "
            f"converted_cls_lines={conv}, dropped_bad_lines={drop}"
        )

    if detect_pre_split_mode(images_root, labels_root):
        stage_root = images_root.parent
        data_yaml = write_dataset_yaml(stage_root)
        n_train = count_split_samples(images_root, labels_root, "train")
        n_val = count_split_samples(images_root, labels_root, "val")
        n_test = count_split_samples(images_root, labels_root, "test")
        n_total = n_train + n_val + n_test
        if n_total == 0:
            fail("pre-split dataset found, but no image/label pairs in train/val/test.")
        print("[train_layout_yolo] using pre-split dataset mode")
        print(f"[train_layout_yolo] dataset root: {stage_root}")
        print(f"[train_layout_yolo] samples train/val/test: {n_train}/{n_val}/{n_test} (total {n_total})")
        print(f"[train_layout_yolo] dataset yaml: {data_yaml}")
    else:
        images = collect_images(images_root)
        if not images:
            fail(f"no images found under {images_root}/mix|worst|handwritten|dense_dims")

        train, val, test = build_splits(images, args.train_ratio, args.val_ratio, args.seed)
        stage_root = out_root / "prepared_dataset"
        if stage_root.exists():
            shutil.rmtree(stage_root)
        stage_root.mkdir(parents=True, exist_ok=True)

        n_train = stage_split("train", train, labels_root, stage_root)
        n_val = stage_split("val", val, labels_root, stage_root)
        n_test = stage_split("test", test, labels_root, stage_root)
        n_total = n_train + n_val + n_test
        if n_total == 0:
            fail(
                "no matching labels were found. Expected YOLO txt files with same basename as images.\n"
                "Example: dataset/mix/sheet_001.jpg -> <labels-root>/sheet_001.txt"
            )

        data_yaml = write_dataset_yaml(stage_root)
        print(f"[train_layout_yolo] prepared dataset: {stage_root}")
        print(f"[train_layout_yolo] samples train/val/test: {n_train}/{n_val}/{n_test} (total {n_total})")
        print(f"[train_layout_yolo] dataset yaml: {data_yaml}")

    from ultralytics import YOLO  # noqa: WPS433

    model = YOLO(args.model)
    model.train(
        data=str(data_yaml),
        imgsz=args.imgsz,
        epochs=args.epochs,
        batch=args.batch,
        device=args.device,
        workers=args.workers,
        project=args.project,
        name=args.name,
        seed=args.seed,
        exist_ok=True,
        val=True,
        patience=args.patience,
        optimizer=args.optimizer,
        lr0=args.lr0,
        lrf=args.lrf,
        weight_decay=args.weight_decay,
        cos_lr=args.cos_lr,
        mosaic=args.mosaic,
        mixup=args.mixup,
        close_mosaic=args.close_mosaic,
        degrees=args.degrees,
        translate=args.translate,
        scale=args.scale,
        fliplr=args.fliplr,
        hsv_s=args.hsv_s,
        hsv_v=args.hsv_v,
    )

    print("[train_layout_yolo] training finished.")
    print(f"[train_layout_yolo] run artifacts: {Path(args.project) / args.name}")


if __name__ == "__main__":
    main()
