from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass
class FrameDetection:
    bbox_xyxy: tuple[int, int, int, int]
    confidence: float


def detect_page_frame(image_bgr: np.ndarray) -> FrameDetection:
    h, w = image_bgr.shape[:2]
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blur, 60, 180)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return FrameDetection((0, 0, w, h), 0.2)

    best = max(contours, key=cv2.contourArea)
    x, y, bw, bh = cv2.boundingRect(best)
    area_ratio = float((bw * bh) / max(1, w * h))
    if area_ratio < 0.25:
        return FrameDetection((0, 0, w, h), 0.25)

    pad_x = int(0.01 * w)
    pad_y = int(0.01 * h)
    x1 = max(0, x - pad_x)
    y1 = max(0, y - pad_y)
    x2 = min(w, x + bw + pad_x)
    y2 = min(h, y + bh + pad_y)
    conf = min(0.95, 0.5 + area_ratio * 0.5)
    return FrameDetection((x1, y1, x2, y2), conf)
