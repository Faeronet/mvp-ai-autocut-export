from __future__ import annotations

import subprocess
import zipfile
from pathlib import Path
from typing import List


def discover_archives(test_metr_dir: Path) -> List[Path]:
    items = sorted(test_metr_dir.glob("*.rar")) + sorted(test_metr_dir.glob("*.zip")) + sorted(
        test_metr_dir.glob("*.7z")
    )
    return sorted({p.resolve() for p in items}, key=lambda p: p.name)


def _run_extract(cmd: list[str]) -> bool:
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False


def extract_images_for_comparison(archive_path: Path, target_dir: Path) -> List[Path]:
    target_dir.mkdir(parents=True, exist_ok=True)
    suffix = archive_path.suffix.lower()
    ok = False
    if suffix == ".zip":
        ok = _run_extract(["unzip", "-o", str(archive_path), "-d", str(target_dir)])
    elif suffix == ".rar":
        ok = _run_extract(["unar", "-o", str(target_dir), str(archive_path)]) or _run_extract(
            ["unrar", "x", "-o+", str(archive_path), f"{target_dir}/"]
        )
    elif suffix == ".7z":
        ok = _run_extract(["7z", "x", "-y", f"-o{target_dir}", str(archive_path)])
    if not ok:
        return []
    exts = ("*.png", "*.jpg", "*.jpeg", "*.tif", "*.tiff", "*.bmp", "*.webp")
    out: List[Path] = []
    for ext in exts:
        out.extend(target_dir.rglob(ext))
    return sorted(out)


def build_zip_from_images(images: List[Path], root_dir: Path, out_zip: Path) -> Path | None:
    if not images:
        return None
    out_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for img in images:
            try:
                rel = img.relative_to(root_dir)
            except ValueError:
                rel = Path(img.name)
            zf.write(img, arcname=str(rel))
    return out_zip
