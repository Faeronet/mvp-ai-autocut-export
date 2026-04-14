from __future__ import annotations

import json
import os
from typing import Any, Dict

import cv2

from app.core.config import Settings
from app.inference.deterministic_zoning import Zone, deterministic_zones, last_resort_percent_zones
from app.inference.yolo_layout import YoloLayoutDetector
from app.postprocessing.overlay import draw_overlay


class LayoutService:
    def __init__(self, settings: Settings, detector: YoloLayoutDetector) -> None:
        self.settings = settings
        self.detector = detector

    def detect(self, image_path: str, profile: str, work_dir: str) -> Dict[str, Any]:
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError("cannot read image")
        h, w = img.shape[:2]
        max_side = self.settings.max_image_side
        scale = min(1.0, max_side / max(h, w))
        if scale < 1.0:
            img = cv2.resize(img, (int(w * scale), int(h * scale)))
        warnings: list[str] = []
        mode = "deterministic"
        zones, det_warnings = deterministic_zones(img)
        warnings.extend(det_warnings)
        # ML backend is additive secondary path, never the sole truth source.
        ml_zones = self.detector.predict(img)
        by_label: dict[str, Zone] = {z.label: z for z in zones}
        for mz in ml_zones:
            if mz.label == "unknown_region":
                continue
            if mz.label in by_label and mz.confidence > by_label[mz.label].confidence:
                by_label[mz.label] = mz
            elif mz.label not in by_label:
                by_label[mz.label] = mz
        zones = list(by_label.values())
        if not zones:
            mode = "last_resort"
            zones = last_resort_percent_zones(img)
            warnings.append("layout_last_resort_percent_fallback")

        os.makedirs(work_dir, exist_ok=True)
        overlay_path = os.path.join(work_dir, "layout_overlay.png")
        draw_overlay(img, zones, overlay_path)
        debug_dir = os.path.join(work_dir, "debug", "layout")
        os.makedirs(debug_dir, exist_ok=True)
        debug_overlay = os.path.join(debug_dir, "zones_overlay.png")
        draw_overlay(img, zones, debug_overlay)
        payload = {
            "zones": [
                {"label": z.label, "bbox_xyxy": list(z.bbox_xyxy), "confidence": z.confidence}
                for z in zones
            ],
            "overlay_path": overlay_path,
            "warnings": warnings,
            "mode": mode,
            "debug_artifacts": {"layout_overlay": debug_overlay},
        }
        with open(os.path.join(work_dir, "layout.json"), "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        return payload
