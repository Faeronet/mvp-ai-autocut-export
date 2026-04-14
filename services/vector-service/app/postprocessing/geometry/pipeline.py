"""
Hierarchical baseline geometry: frame strips + table crop + drawing area (table masked out).

Not global HoughLinesP on the full sheet as primary logic.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

import cv2
import numpy as np

from app.postprocessing.geometry.line_extract import (
    classify_frame_table_geom,
    create_lsd,
    lsd_segments,
    masked_edges_fallback,
    segments_to_dicts,
)
from app.postprocessing.geometry.merge import merge_line_segments
from app.postprocessing.geometry.regions import clamp_box, specification_table_bbox_xyxy


def _frame_ring_mask(h: int, w: int, band: int) -> np.ndarray:
    m = np.zeros((h, w), dtype=np.uint8)
    m[:band, :] = 255
    m[-band:, :] = 255
    m[:, :band] = 255
    m[:, -band:] = 255
    return m


def extract_geometry(image_bgr: np.ndarray) -> Dict[str, Any]:
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape[:2]
    table_bbox = clamp_box(*specification_table_bbox_xyxy(h, w), w, h)
    tx1, ty1, tx2, ty2 = table_bbox
    frame_band = max(12, min(h, w) // 80)

    lsd = create_lsd()
    all_segments: List[Dict[str, Any]] = []

    # 1) Frame: line segments only in a border ring (local context).
    ring = _frame_ring_mask(h, w, frame_band)
    frame_gray = cv2.bitwise_and(gray, gray, mask=ring)
    if lsd:
        for x1, y1, x2, y2 in lsd_segments(frame_gray, lsd):
            all_segments.extend(
                segments_to_dicts([(x1, y1, x2, y2)], "FRAME", 0.72)
            )
    else:
        for x1, y1, x2, y2 in masked_edges_fallback(gray, ring):
            all_segments.extend(
                segments_to_dicts([(x1, y1, x2, y2)], "FRAME", 0.65)
            )

    # 2) Table: local LSD on crop only.
    if tx2 > tx1 + 16 and ty2 > ty1 + 16:
        tcrop = gray[ty1:ty2, tx1:tx2]
        if lsd:
            for x1, y1, x2, y2 in lsd_segments(tcrop, lsd, min_len=8.0):
                all_segments.extend(
                    segments_to_dicts(
                        [(x1 + tx1, y1 + ty1, x2 + tx1, y2 + ty1)], "TABLE", 0.66
                    )
                )
        else:
            mask_t = np.ones(tcrop.shape[:2], dtype=np.uint8) * 255
            for x1, y1, x2, y2 in masked_edges_fallback(tcrop, mask_t):
                all_segments.extend(
                    segments_to_dicts(
                        [(x1 + tx1, y1 + ty1, x2 + tx1, y2 + ty1)], "TABLE", 0.6
                    )
                )

    # 3) Drawing: suppress table interior so grid/text edges do not dominate "geometry".
    work_draw = gray.copy()
    pad = min(h, w) // 120
    tpad1 = max(0, ty1 - pad)
    tpad2 = min(h, ty2 + pad)
    tpadx1 = max(0, tx1 - pad)
    tpadx2 = min(w, tx2 + pad)
    cv2.rectangle(work_draw, (tpadx1, tpad1), (tpadx2, tpad2), 255, thickness=-1)

    if lsd:
        raw = lsd_segments(work_draw, lsd, min_len=14.0)
    else:
        mask_d = np.ones((h, w), dtype=np.uint8) * 255
        cv2.rectangle(mask_d, (tpadx1, tpad1), (tpadx2, tpad2), 0, thickness=-1)
        raw = masked_edges_fallback(gray, mask_d)

    for x1, y1, x2, y2 in raw:
        layer = classify_frame_table_geom(
            x1, y1, x2, y2, h, w, table_bbox, frame_band
        )
        if layer == "TABLE":
            continue
        conf = 0.58 if layer == "GEOMETRY" else 0.7
        all_segments.append(
            {
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2,
                "layer": layer,
                "confidence": conf,
            }
        )

    merged = merge_line_segments(all_segments, tol=1.0)
    return {
        "lines": merged,
        "circles": [],
        "tables": [{"bbox_xyxy": [tx1, ty1, tx2, ty2]}],
    }
