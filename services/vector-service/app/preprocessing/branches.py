from __future__ import annotations

import cv2
import numpy as np


def make_ocr_branch(gray: np.ndarray) -> np.ndarray:
    den = cv2.bilateralFilter(gray, 7, 40, 40)
    return cv2.fastNlMeansDenoising(den, h=4, templateWindowSize=7, searchWindowSize=21)


def make_geometry_branch(gray: np.ndarray) -> np.ndarray:
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enh = clahe.apply(gray)
    bin_img = cv2.adaptiveThreshold(
        enh,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        31,
        7,
    )
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    return cv2.morphologyEx(bin_img, cv2.MORPH_OPEN, kernel, iterations=1)
