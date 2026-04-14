from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import cv2
import numpy as np


@dataclass
class Zone:
    label: str
    bbox_xyxy: tuple[float, float, float, float]
    confidence: float


def _line_density(binary: np.ndarray, rect: tuple[int, int, int, int]) -> float:
    x1, y1, x2, y2 = rect
    roi = binary[y1:y2, x1:x2]
    if roi.size == 0:
        return 0.0
    return float(np.count_nonzero(roi) / roi.size)


def _find_frame(gray: np.ndarray) -> tuple[int, int, int, int]:
    h, w = gray.shape[:2]
    edges = cv2.Canny(gray, 70, 180)
    cnts, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        return (0, 0, w, h)
    best = max(cnts, key=cv2.contourArea)
    x, y, bw, bh = cv2.boundingRect(best)
    if bw * bh < 0.25 * w * h:
        return (0, 0, w, h)
    return (x, y, x + bw, y + bh)


def deterministic_zones(image_bgr: np.ndarray) -> tuple[list[Zone], list[str]]:
    h, w = image_bgr.shape[:2]
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    frame = _find_frame(gray)
    fx1, fy1, fx2, fy2 = frame
    bw = max(1, fx2 - fx1)
    bh = max(1, fy2 - fy1)
    bin_img = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 31, 7)

    # Soft positional priors constrained by signal density.
    title = (int(fx1 + 0.62 * bw), int(fy1 + 0.78 * bh), fx2, fy2)
    spec = (fx1, int(fy1 + 0.32 * bh), int(fx1 + 0.42 * bw), int(fy1 + 0.78 * bh))
    notes = (int(fx1 + 0.45 * bw), fy1, fx2, int(fy1 + 0.28 * bh))
    dims = (int(fx1 + 0.08 * bw), int(fy1 + 0.08 * bh), int(fx1 + 0.60 * bw), int(fy1 + 0.62 * bh))

    zones = [
        Zone("border_frame", (float(fx1), float(fy1), float(fx2), float(fy2)), 0.8),
        Zone("drawing_area", (float(fx1), float(fy1), float(fx2), float(fy2)), 0.75),
        Zone("title_block", tuple(float(v) for v in title), 0.55 + 0.35 * _line_density(bin_img, title)),
        Zone("specification_table", tuple(float(v) for v in spec), 0.5 + 0.4 * _line_density(bin_img, spec)),
        Zone("notes_block", tuple(float(v) for v in notes), 0.45 + 0.4 * _line_density(bin_img, notes)),
        Zone("dimension_cluster", tuple(float(v) for v in dims), 0.45 + 0.4 * _line_density(bin_img, dims)),
    ]
    warnings: list[str] = []
    if frame == (0, 0, w, h):
        warnings.append("weak_frame_detection")
    return zones, warnings


def last_resort_percent_zones(image_bgr: np.ndarray) -> list[Zone]:
    h, w = image_bgr.shape[:2]
    return [
        Zone("drawing_area", (0.0, 0.0, float(w), float(h)), 0.3),
        Zone("title_block", (float(w * 0.65), float(h * 0.82), float(w * 0.98), float(h * 0.98)), 0.25),
        Zone("specification_table", (float(w * 0.05), float(h * 0.35), float(w * 0.45), float(h * 0.75)), 0.25),
    ]
