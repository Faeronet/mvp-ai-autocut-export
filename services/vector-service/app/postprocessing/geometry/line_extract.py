from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np


def _segment_length(x1: float, y1: float, x2: float, y2: float) -> float:
    return float(np.hypot(x2 - x1, y2 - y1))


def _midpoint(x1: float, y1: float, x2: float, y2: float) -> Tuple[float, float]:
    return (x1 + x2) * 0.5, (y1 + y2) * 0.5


def create_lsd() -> Optional[Any]:
    try:
        refine = getattr(cv2, "LSD_REFINE_STD", 1)
        return cv2.createLineSegmentDetector(refine)
    except Exception:
        return None


def lsd_segments(gray: np.ndarray, lsd: Any, min_len: float = 12.0) -> List[Tuple[float, float, float, float]]:
    if lsd is None:
        return []
    lines, _, _, _ = lsd.detect(gray)
    if lines is None or lines.size == 0:
        return []
    out: List[Tuple[float, float, float, float]] = []
    for seg in lines.reshape(-1, 4):
        x1, y1, x2, y2 = float(seg[0]), float(seg[1]), float(seg[2]), float(seg[3])
        if _segment_length(x1, y1, x2, y2) >= min_len:
            out.append((x1, y1, x2, y2))
    return out


def classify_frame_table_geom(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    h: int,
    w: int,
    table_xyxy: Tuple[int, int, int, int],
    frame_band: int,
) -> str:
    mx, my = _midpoint(x1, y1, x2, y2)
    tx1, ty1, tx2, ty2 = table_xyxy
    if tx1 <= mx <= tx2 and ty1 <= my <= ty2:
        return "TABLE"
    # Border-aligned segments (frame / format линии)
    near_l = mx < frame_band
    near_r = mx > w - frame_band
    near_t = my < frame_band
    near_b = my > h - frame_band
    if near_l or near_r or near_t or near_b:
        return "FRAME"
    return "GEOMETRY"


def masked_edges_fallback(gray: np.ndarray, mask: np.ndarray) -> List[Tuple[float, float, float, float]]:
    """HoughLinesP only on masked edges — not used as primary; last resort if LSD missing."""
    edges = cv2.Canny(gray, 60, 160)
    edges = cv2.bitwise_and(edges, edges, mask=mask)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=80, minLineLength=30, maxLineGap=6)
    out: List[Tuple[float, float, float, float]] = []
    if lines is None:
        return out
    for ln in lines:
        x1, y1, x2, y2 = ln[0]
        out.append((float(x1), float(y1), float(x2), float(y2)))
    return out


def segments_to_dicts(
    segments: List[Tuple[float, float, float, float]],
    layer: str,
    confidence: float,
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for x1, y1, x2, y2 in segments:
        rows.append(
            {
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2,
                "layer": layer,
                "confidence": confidence,
            }
        )
    return rows
