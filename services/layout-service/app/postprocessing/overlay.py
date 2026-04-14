from __future__ import annotations

from typing import List, Sequence, Tuple

import cv2
import numpy as np

from app.inference.deterministic_zoning import Zone


def draw_overlay(image_bgr: np.ndarray, zones: Sequence[Zone], out_path: str) -> None:
    canvas = image_bgr.copy()
    colors = [(0, 255, 0), (255, 0, 0), (0, 128, 255)]
    for i, z in enumerate(zones):
        x1, y1, x2, y2 = [int(v) for v in z.bbox_xyxy]
        cv2.rectangle(canvas, (x1, y1), (x2, y2), colors[i % len(colors)], 2)
        cv2.putText(canvas, z.label, (x1, max(0, y1 - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
    cv2.imwrite(out_path, canvas)
