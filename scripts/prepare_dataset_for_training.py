#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import random
import shutil
from pathlib import Path

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".webp"}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Prepare mcp_mvp dataset for remote training.")
    p.add_argument("--dataset-root", default="dataset")
    p.add_argument("--out-root", default="training/layout/prepared_dataset")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--train-ratio", type=float, default=0.8)
    p.add_argument("--val-ratio", type=float, default=0.1)
    return p.parse_args()


def sha1(path: Path) -> str:
    return hashlib.sha1(path.read_bytes()).hexdigest()


def main() -> None:
    args = parse_args()
    root = Path(args.dataset_root).resolve()
    out = Path(args.out_root).resolve()
    folders = ["mix", "worst", "handwritten", "dense_dims"]

    all_images: list[Path] = []
    for folder in folders:
        d = root / folder
        if not d.exists():
            continue
        all_images.extend([p for p in d.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTS])
    if not all_images:
        raise SystemExit("No images found in dataset.")

    # Deduplicate by content hash.
    by_hash: dict[str, Path] = {}
    duplicates: list[tuple[str, str]] = []
    for p in sorted(all_images):
        h = sha1(p)
        if h in by_hash:
            duplicates.append((str(by_hash[h]), str(p)))
            continue
        by_hash[h] = p
    unique = sorted(by_hash.values())

    rnd = random.Random(args.seed)
    rnd.shuffle(unique)
    n = len(unique)
    n_train = int(n * args.train_ratio)
    n_val = int(n * args.val_ratio)
    train = unique[:n_train]
    val = unique[n_train : n_train + n_val]
    test = unique[n_train + n_val :]

    if out.exists():
        shutil.rmtree(out)
    (out / "images" / "train").mkdir(parents=True, exist_ok=True)
    (out / "images" / "val").mkdir(parents=True, exist_ok=True)
    (out / "images" / "test").mkdir(parents=True, exist_ok=True)
    (out / "labels" / "train").mkdir(parents=True, exist_ok=True)
    (out / "labels" / "val").mkdir(parents=True, exist_ok=True)
    (out / "labels" / "test").mkdir(parents=True, exist_ok=True)

    split_map = [("train", train), ("val", val), ("test", test)]
    rows: list[list[str]] = [["split", "image_path", "label_path", "status"]]
    for split, files in split_map:
        for src in files:
            dst = out / "images" / split / src.name
            shutil.copy2(src, dst)
            label = out / "labels" / split / f"{src.stem}.txt"
            label.write_text("", encoding="utf-8")
            rows.append([split, str(dst), str(label), "TODO_LABEL"])

    with (out / "annotation_manifest.csv").open("w", encoding="utf-8", newline="") as f:
        csv.writer(f).writerows(rows)

    with (out / "duplicates_removed.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["kept", "removed"])
        w.writerows(duplicates)

    summary = (
        f"source_images={len(all_images)}\n"
        f"unique_images={len(unique)}\n"
        f"duplicates_removed={len(duplicates)}\n"
        f"train={len(train)}\nval={len(val)}\ntest={len(test)}\n"
    )
    (out / "summary.txt").write_text(summary, encoding="utf-8")
    print(summary)
    print(f"Prepared dataset in: {out}")


if __name__ == "__main__":
    main()
