#!/usr/bin/env python3
"""Bootstrap mandatory model weights into MODEL_CACHE_DIR without importing Paddle/torch.

Importing paddle/ultralytics in a minimal image can SIGSEGV (exit 139). This script only
uses the stdlib and mirrors paddleocr.ppocr.utils.network.maybe_download layout.
"""
from __future__ import annotations

import json
import os
import sys
import tarfile
import time
import urllib.error
import urllib.request
from pathlib import Path

# PaddleOCR 2.7.3 MODEL_URLS — PP-OCRv4 lang=en + PP-StructureV2 table/layout (en)
_PADDLE_TARS: list[tuple[str, str]] = [
    (
        "https://paddleocr.bj.bcebos.com/PP-OCRv3/english/en_PP-OCRv3_det_infer.tar",
        ".paddleocr/whl/det/en/en_PP-OCRv3_det_infer",
    ),
    (
        "https://paddleocr.bj.bcebos.com/PP-OCRv4/english/en_PP-OCRv4_rec_infer.tar",
        ".paddleocr/whl/rec/en/en_PP-OCRv4_rec_infer",
    ),
    (
        "https://paddleocr.bj.bcebos.com/dygraph_v2.0/ch/ch_ppocr_mobile_v2.0_cls_infer.tar",
        ".paddleocr/whl/cls/ch_ppocr_mobile_v2.0_cls_infer",
    ),
    (
        "https://paddleocr.bj.bcebos.com/ppstructure/models/slanet/en_ppstructure_mobile_v2.0_SLANet_infer.tar",
        ".paddleocr/whl/table/en_ppstructure_mobile_v2.0_SLANet_infer",
    ),
    (
        "https://paddleocr.bj.bcebos.com/ppstructure/models/layout/picodet_lcnet_x1_0_fgd_layout_infer.tar",
        ".paddleocr/whl/layout/picodet_lcnet_x1_0_fgd_layout_infer",
    ),
]

_YOLO_URL = "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8n.pt"

_FETCH_ATTEMPTS = 6
_FETCH_TIMEOUT_S = 600


def log(msg: str) -> None:
    print(f"[bootstrap-models] {msg}", flush=True)


def env_bool(key: str, default: bool) -> bool:
    v = os.environ.get(key, "").strip().lower()
    if v == "":
        return default
    return v in ("1", "true", "yes")


def _fetch_url_bytes(url: str) -> bytes:
    """HTTP GET with retries (handles transient DNS / network in Docker)."""
    last: BaseException | None = None
    for attempt in range(_FETCH_ATTEMPTS):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "mcp-mvp-bootstrap/1"})
            with urllib.request.urlopen(req, timeout=_FETCH_TIMEOUT_S) as resp:
                return resp.read()
        except (urllib.error.URLError, OSError) as exc:
            last = exc
            if attempt == _FETCH_ATTEMPTS - 1:
                break
            wait = min(45, 2**attempt)
            log(f"fetch attempt {attempt + 1}/{_FETCH_ATTEMPTS} failed ({exc}); retry in {wait}s")
            time.sleep(wait)
    assert last is not None
    raise last


def _maybe_download_infer_dir(model_dir: Path, url: str) -> None:
    """Match paddleocr ppocr.utils.network.maybe_download (inference pdmodel/pdiparams)."""
    tar_suffixes = (".pdiparams", ".pdiparams.info", ".pdmodel")
    if (model_dir / "inference.pdiparams").exists() and (model_dir / "inference.pdmodel").exists():
        return
    assert url.endswith(".tar"), "only .tar supported"
    model_dir.mkdir(parents=True, exist_ok=True)
    tmp_path = model_dir / url.split("/")[-1]
    log(f"download {url} -> {tmp_path}")
    tmp_path.write_bytes(_fetch_url_bytes(url))
    with tarfile.open(tmp_path, "r") as tar_obj:
        for member in tar_obj.getmembers():
            filename = None
            for suf in tar_suffixes:
                if member.name.endswith(suf):
                    filename = "inference" + suf
                    break
            if filename is None:
                continue
            file = tar_obj.extractfile(member)
            if file is None:
                continue
            (model_dir / filename).write_bytes(file.read())
    tmp_path.unlink(missing_ok=True)


def _download_yolo(layout_pt: Path) -> None:
    if layout_pt.exists() and layout_pt.stat().st_size > 1000:
        return
    layout_pt.parent.mkdir(parents=True, exist_ok=True)
    log(f"download {_YOLO_URL} -> {layout_pt}")
    layout_pt.write_bytes(_fetch_url_bytes(_YOLO_URL))


def _write_status(cache: Path, state: str, ok: bool, errors: list[str] | None = None) -> None:
    payload = {
        "state": state,
        "ok": ok,
        "ts": time.time(),
        "errors": errors or [],
    }
    (cache / "bootstrap_status.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> int:
    cache = Path(os.environ.get("MODEL_CACHE_DIR", "/models_cache"))
    auto = env_bool("MODEL_AUTO_DOWNLOAD", True)
    strict = env_bool("MODEL_STARTUP_STRICT", True)
    # PaddleOCR resolves ~/.paddleocr; in containers HOME should be MODEL_CACHE_DIR.
    os.environ.setdefault("HOME", str(cache))

    if not auto:
        log("MODEL_AUTO_DOWNLOAD=false — skipping downloads")
        cache.mkdir(parents=True, exist_ok=True)
        _write_status(cache, "skipped", ok=True)
        return 0

    cache.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []

    for url, rel in _PADDLE_TARS:
        try:
            _maybe_download_infer_dir(cache / rel, url)
            log(f"ok {rel}")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{rel}:{exc}")
            log(f"ERROR {rel}: {exc}")

    layout_pt = cache / "layout" / "yolov8n_layout.pt"
    try:
        _download_yolo(layout_pt)
        log(f"ok {layout_pt}")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"yolov8n:{exc}")
        log(f"ERROR YOLOv8n: {exc}")

    # Marker for manifest / ops (PP-Structure pack lives under .paddleocr/whl/table)
    pp_dir = cache / "ppstructure"
    pp_dir.mkdir(parents=True, exist_ok=True)
    (pp_dir / ".bootstrap_ok").write_text("ppstructure weights under .paddleocr/whl/table+layout\n", encoding="utf-8")

    ok = len(errors) == 0
    if not ok and strict:
        _write_status(cache, "failed", ok=False, errors=errors)
        return 1
    _write_status(cache, "ready" if ok else "partial", ok=ok, errors=errors or None)
    return 0


if __name__ == "__main__":
    sys.exit(main())
