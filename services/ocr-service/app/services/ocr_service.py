from __future__ import annotations

import logging
from typing import Any, Dict, List

import cv2

from app.core.config import Settings

logger = logging.getLogger(__name__)
from app.inference.ocr_router import resolve_mode
from app.inference.paddle_ocr_runner import PaddleOCRRunner
from app.postprocessing.engineering_normalize import normalize_text


class OCRService:
    def __init__(self, settings: Settings, runner: PaddleOCRRunner) -> None:
        self.settings = settings
        self.runner = runner

    def run(self, image_path: str, rois: List[Dict[str, Any]], profile: str) -> Dict[str, Any]:
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError("cannot read image")
        items: List[Dict[str, Any]] = []
        for i, roi in enumerate(rois):
            bbox = tuple(roi["bbox_xyxy"])  # type: ignore[assignment]
            sem = str(roi.get("semantic_role", "generic"))
            mode = resolve_mode(sem)
            try:
                parts = self.runner.run_roi(img, bbox, sem)
            except Exception as exc:  # noqa: BLE001
                logger.exception("ocr roi %d failed semantic=%s bbox=%s", i, sem, bbox)
                raise RuntimeError(f"ocr_roi[{i}] semantic={sem}: {exc}") from exc
            for part in parts:
                raw = part["raw_text"]
                conf = float(part.get("confidence", 0.0))
                norm, review = normalize_text(raw, conf, mode.semantic_role)
                if conf < mode.min_confidence:
                    review = True
                items.append(
                    {
                        "raw_text": raw,
                        "normalized_text": norm,
                        "text": norm,
                        "bbox_xyxy": part["bbox_xyxy"],
                        "quad_xy": part.get("quad_xy", []),
                        "angle_deg": float(part.get("angle_deg", 0.0)),
                        "orientation_deg": int(part.get("orientation_deg", 0)),
                        "confidence": conf,
                        "semantic_role": mode.semantic_role,
                        "review_required": review,
                    }
                )
        return {"items": items}
