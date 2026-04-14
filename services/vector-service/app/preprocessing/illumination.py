from __future__ import annotations

import cv2
import numpy as np


def normalize_background(gray: np.ndarray) -> np.ndarray:
    bg = cv2.medianBlur(gray, 31)
    norm = cv2.divide(gray, bg, scale=255)
    return cv2.normalize(norm, None, 0, 255, cv2.NORM_MINMAX)
