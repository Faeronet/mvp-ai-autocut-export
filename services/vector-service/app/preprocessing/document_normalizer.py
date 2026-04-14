from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from app.preprocessing.branches import make_geometry_branch, make_ocr_branch
from app.preprocessing.frame_detect import detect_page_frame
from app.preprocessing.illumination import normalize_background


@dataclass
class NormalizeResult:
    preprocessed_path: str
    binary_path: str
    soft_path: str
    debug_artifacts: dict[str, str]
    image_meta: dict[str, float]
    warnings: list[str]
    preprocess_confidence: float


def _line_based_angle(gray: np.ndarray) -> tuple[float, float]:
    edges = cv2.Canny(gray, 50, 150)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=120, minLineLength=120, maxLineGap=8)
    if lines is None or len(lines) < 5:
        return 0.0, 0.2

    angles = []
    for ln in lines[:, 0]:
        x1, y1, x2, y2 = [float(v) for v in ln]
        dx, dy = x2 - x1, y2 - y1
        if abs(dx) + abs(dy) < 5:
            continue
        a = np.degrees(np.arctan2(dy, dx))
        if a > 45:
            a -= 90
        if a < -45:
            a += 90
        angles.append(a)
    if len(angles) < 5:
        return 0.0, 0.25
    median = float(np.median(angles))
    spread = float(np.std(angles))
    conf = max(0.1, min(0.95, 1.0 - min(1.0, spread / 10.0)))
    if abs(median) < 0.2 or abs(median) > 12:
        return 0.0, max(0.2, conf - 0.3)
    return median, conf


def normalize_document(image_path: str, output_dir: str, max_side: int) -> NormalizeResult:
    out = Path(output_dir)
    debug_dir = out / "debug" / "preprocess"
    debug_dir.mkdir(parents=True, exist_ok=True)

    image = cv2.imread(image_path)
    if image is None:
        raise ValueError("cannot read image")

    raw_path = debug_dir / "raw.png"
    cv2.imwrite(str(raw_path), image)
    h0, w0 = image.shape[:2]

    scale = min(1.0, max_side / max(1, h0, w0))
    if scale < 1.0:
        image = cv2.resize(image, (int(w0 * scale), int(h0 * scale)), interpolation=cv2.INTER_AREA)

    frame = detect_page_frame(image)
    x1, y1, x2, y2 = frame.bbox_xyxy
    cropped = image[y1:y2, x1:x2]
    if cropped.size == 0:
        cropped = image

    cropped_path = debug_dir / "cropped.png"
    cv2.imwrite(str(cropped_path), cropped)

    gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
    angle, deskew_conf = _line_based_angle(gray)
    if abs(angle) > 0.01:
        hh, ww = gray.shape[:2]
        m = cv2.getRotationMatrix2D((ww / 2, hh / 2), angle, 1.0)
        gray = cv2.warpAffine(gray, m, (ww, hh), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)

    deskewed_path = debug_dir / "deskewed.png"
    cv2.imwrite(str(deskewed_path), gray)

    normalized = normalize_background(gray)
    normalized_path = debug_dir / "normalized.png"
    cv2.imwrite(str(normalized_path), normalized)

    ocr_branch = make_ocr_branch(normalized)
    geom_branch = make_geometry_branch(normalized)
    soft_path = out / "soft.png"
    bin_path = out / "binary.png"
    pre_path = out / "preprocessed.png"
    cv2.imwrite(str(soft_path), ocr_branch)
    cv2.imwrite(str(bin_path), geom_branch)
    cv2.imwrite(str(pre_path), normalized)

    ocr_path = debug_dir / "ocr_branch.png"
    geom_path = debug_dir / "geom_branch.png"
    cv2.imwrite(str(ocr_path), ocr_branch)
    cv2.imwrite(str(geom_path), geom_branch)

    warnings: list[str] = []
    if frame.confidence < 0.4:
        warnings.append("weak_frame_detection")
    if deskew_conf < 0.35:
        warnings.append("weak_deskew_signal")

    preprocess_conf = max(0.2, min(0.95, 0.5 * frame.confidence + 0.5 * deskew_conf))
    return NormalizeResult(
        preprocessed_path=str(pre_path),
        binary_path=str(bin_path),
        soft_path=str(soft_path),
        debug_artifacts={
            "raw": str(raw_path),
            "cropped": str(cropped_path),
            "deskewed": str(deskewed_path),
            "normalized": str(normalized_path),
            "ocr_branch": str(ocr_path),
            "geom_branch": str(geom_path),
        },
        image_meta={"width_px": float(normalized.shape[1]), "height_px": float(normalized.shape[0]), "deskew_angle_deg": angle},
        warnings=warnings,
        preprocess_confidence=preprocess_conf,
    )
