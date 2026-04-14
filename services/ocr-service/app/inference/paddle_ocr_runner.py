"""PaddleOCR runner for ROI-oriented OCR."""
from __future__ import annotations

import os
from typing import Any, Dict, List, Tuple

import cv2
import numpy as np

class PaddleOCRRunner:
    def __init__(self, use_gpu: bool, cache_dir: str, lang: str = "ru", allow_offline_fallback: bool = True) -> None:
        self.active_lang = lang
        self.use_gpu = use_gpu
        self.lang = lang
        self.cache_dir = cache_dir
        from paddleocr import PaddleOCR

        det_en = os.path.join(cache_dir, ".paddleocr", "whl", "det", "en", "en_PP-OCRv3_det_infer")
        rec_en = os.path.join(cache_dir, ".paddleocr", "whl", "rec", "en", "en_PP-OCRv4_rec_infer")
        cls_shared = os.path.join(cache_dir, ".paddleocr", "whl", "cls", "ch_ppocr_mobile_v2.0_cls_infer")

        def _offline_kwargs() -> Dict[str, Any]:
            return {
                "det_model_dir": det_en,
                "rec_model_dir": rec_en,
                "cls_model_dir": cls_shared,
            }

        try:
            # Primary path (configured language).
            self._ocr = PaddleOCR(
                use_angle_cls=True,
                lang=lang,
                use_gpu=use_gpu,
                show_log=False,
                det_limit_side_len=2048,
            )
        except Exception:
            if not allow_offline_fallback:
                raise
            # Offline fallback (no network download): force prebootstrapped model dirs.
            self.active_lang = "en"
            self._ocr = PaddleOCR(
                use_angle_cls=True,
                lang="en",
                use_gpu=use_gpu,
                show_log=False,
                det_limit_side_len=2048,
                **_offline_kwargs(),
            )

    def run_roi(
        self, image_bgr: np.ndarray, bbox_xyxy: Tuple[float, float, float, float], semantic: str
    ) -> List[Dict[str, Any]]:
        x1, y1, x2, y2 = [int(v) for v in bbox_xyxy]
        h, w = image_bgr.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        crop = image_bgr[y1:y2, x1:x2]
        if crop.size == 0:
            return []
        out = self._ocr.ocr(crop, det=True, rec=True, cls=True)
        items: List[Dict[str, Any]] = []
        if not out or out[0] is None:
            return items
        for line in out[0]:
            box = line[0]
            info = line[1]
            if isinstance(info, (list, tuple)) and len(info) >= 2:
                txt, conf = info[0], float(info[1])
            else:
                txt, conf = str(info), 0.0
            xs = [p[0] for p in box]
            ys = [p[1] for p in box]
            lx1, ly1, lx2, ly2 = min(xs), min(ys), max(xs), max(ys)
            quad = [
                float(box[0][0] + x1),
                float(box[0][1] + y1),
                float(box[1][0] + x1),
                float(box[1][1] + y1),
                float(box[2][0] + x1),
                float(box[2][1] + y1),
                float(box[3][0] + x1),
                float(box[3][1] + y1),
            ]
            angle = _quad_angle_deg(quad)
            orientation = _orientation_bucket(angle)
            c = conf / 100.0 if conf > 1.0 else conf
            items.append(
                {
                    "raw_text": txt,
                    "bbox_xyxy": [lx1 + x1, ly1 + y1, lx2 + x1, ly2 + y1],
                    "quad_xy": quad,
                    "angle_deg": float(angle),
                    "orientation_deg": int(orientation),
                    "confidence": float(c),
                }
            )
        return items


def _quad_angle_deg(quad_xy: List[float]) -> float:
    # Use top edge direction as local text angle estimate.
    x1, y1, x2, y2 = quad_xy[0], quad_xy[1], quad_xy[2], quad_xy[3]
    angle = float(np.degrees(np.arctan2(y2 - y1, x2 - x1)))
    # Keep in [-180, 180)
    if angle >= 180.0:
        angle -= 360.0
    if angle < -180.0:
        angle += 360.0
    return angle


def _orientation_bucket(angle_deg: float) -> int:
    # Local ROI orientation stage: pick nearest right-angle orientation.
    candidates = [0, 90, 180, 270]
    angle_mod = angle_deg % 360.0
    return min(candidates, key=lambda c: min(abs(angle_mod - c), 360.0 - abs(angle_mod - c)))
