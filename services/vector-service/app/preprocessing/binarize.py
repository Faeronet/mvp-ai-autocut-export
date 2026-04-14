from __future__ import annotations

import cv2
import numpy as np


def adaptive_binary(gray: np.ndarray) -> np.ndarray:
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    return cv2.adaptiveThreshold(
        blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 31, 10
    )


def soft_blur(gray: np.ndarray) -> np.ndarray:
    return cv2.bilateralFilter(gray, 5, 50, 50)
