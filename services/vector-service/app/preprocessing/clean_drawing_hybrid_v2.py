from __future__ import annotations

import cv2
import numpy as np
from skimage.filters import threshold_sauvola


def preprocess(gray: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    den = cv2.fastNlMeansDenoising(gray, None, h=12, templateWindowSize=7, searchWindowSize=21)
    bg = cv2.GaussianBlur(den, (0, 0), 31)
    flat = cv2.divide(den, bg, scale=255)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(16, 16))
    enh = clahe.apply(flat)
    return enh, flat


def line_masks(fg: np.ndarray) -> np.ndarray:
    h1 = cv2.morphologyEx(fg, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (45, 1)))
    v1 = cv2.morphologyEx(fg, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (1, 45)))
    return ((h1 > 0) | (v1 > 0)).astype(np.uint8)


def strong_seed_mask(flat: np.ndarray, enh: np.ndarray) -> np.ndarray:
    bh7 = cv2.morphologyEx(flat, cv2.MORPH_BLACKHAT, cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7)))
    bh11 = cv2.morphologyEx(flat, cv2.MORPH_BLACKHAT, cv2.getStructuringElement(cv2.MORPH_RECT, (11, 11)))
    bh = np.maximum(bh7, bh11)

    seed = ((bh > 18) | (enh < 175)).astype(np.uint8)
    seed = cv2.morphologyEx(seed, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    return seed


def local_contrast(gray: np.ndarray, x: int, y: int, w: int, h: int, comp: np.ndarray) -> float:
    h_img, w_img = gray.shape
    pad = max(3, int(0.15 * max(w, h)))
    x0 = max(0, x - pad)
    y0 = max(0, y - pad)
    x1 = min(w_img, x + w + pad)
    y1 = min(h_img, y + h + pad)

    roi = gray[y0:y1, x0:x1]
    mask = np.zeros((y1 - y0, x1 - x0), dtype=np.uint8)
    mask[y - y0 : y - y0 + h, x - x0 : x - x0 + w] = comp.astype(np.uint8)

    dil = cv2.dilate(mask, np.ones((3, 3), np.uint8), iterations=2)
    ring = dil == 0
    local_bg = 255.0 if ring.sum() < 10 else float(np.median(roi[ring]))
    fg_mean = float(gray[y : y + h, x : x + w][comp].mean())
    return local_bg - fg_mean


def filter_components(candidate: np.ndarray, enh: np.ndarray, strong: np.ndarray, border_margin: int = 10) -> np.ndarray:
    h_img, w_img = candidate.shape
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(candidate, 8)
    out = np.zeros_like(candidate)
    line_like_mask = line_masks(candidate)

    for i in range(1, num_labels):
        x, y, w, h, area = stats[i]
        comp = labels[y : y + h, x : x + w] == i
        fill = area / float(max(1, w * h))
        overlap_strong = float(strong[y : y + h, x : x + w][comp].mean()) if area else 0.0
        overlap_line = float(line_like_mask[y : y + h, x : x + w][comp].mean()) if area else 0.0
        contrast = local_contrast(enh, x, y, w, h, comp)

        touches_border = x <= border_margin or y <= border_margin or x + w >= w_img - border_margin or y + h >= h_img - border_margin
        very_long = (w >= 100 and h <= 8) or (h >= 100 and w <= 8)
        elongated = (w >= 20 and h <= 4) or (h >= 20 and w <= 4)
        large_weak = max(w, h) >= 120 and fill < 0.04 and overlap_strong < 0.06

        keep = False
        if overlap_strong >= 0.22 and contrast >= 8:
            keep = True
        elif overlap_line >= 0.45 and contrast >= 7:
            keep = True
        elif very_long and contrast >= 7:
            keep = True
        elif elongated and contrast >= 9:
            keep = True
        elif area <= 12:
            keep = contrast >= 18 and overlap_strong >= 0.15
        elif area <= 40:
            keep = contrast >= 13 and (overlap_strong >= 0.12 or fill >= 0.20)
        elif area <= 200:
            keep = contrast >= 11 and (overlap_strong >= 0.08 or fill >= 0.08)
        else:
            keep = contrast >= 10 and (overlap_strong >= 0.05 or fill >= 0.04 or overlap_line >= 0.25)

        if touches_border and not very_long:
            keep = keep and (overlap_line >= 0.35 or overlap_strong >= 0.28 or contrast >= 18)
        if large_weak:
            keep = False
        if keep:
            out[labels == i] = 1

    final = out.copy()
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(out, 8)
    for i in range(1, num_labels):
        x, y, w, h, _ = stats[i]
        if x <= border_margin or y <= border_margin or x + w >= w_img - border_margin or y + h >= h_img - border_margin:
            comp = labels == i
            allowed = ((strong > 0) | (line_like_mask > 0)) & comp
            final[comp] = 0
            final[allowed] = 1
    final |= line_like_mask
    return final.astype(np.uint8)


def remove_giant_weak_smears(fg: np.ndarray) -> np.ndarray:
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(fg, 8)
    out = fg.copy()
    h_img, w_img = fg.shape
    for i in range(1, num_labels):
        _, _, w, h, area = stats[i]
        fill = area / float(max(1, w * h))
        if ((w > int(0.45 * w_img) and h < 20) or (h > int(0.45 * h_img) and w < 20)) and fill < 0.30:
            out[labels == i] = 0
        if w > 140 and h > 15 and h < 80 and fill < 0.12:
            out[labels == i] = 0
    return out


def clean_drawing(gray: np.ndarray) -> np.ndarray:
    enh, flat = preprocess(gray)
    thr = threshold_sauvola(enh, window_size=55, k=0.10)
    candidate = (enh <= thr).astype(np.uint8)
    strong = strong_seed_mask(flat, enh)
    fg = filter_components(candidate, enh, strong, border_margin=10)
    fg = remove_giant_weak_smears(fg)
    return ((1 - fg) * 255).astype(np.uint8)
