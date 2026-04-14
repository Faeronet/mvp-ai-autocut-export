"""YOLOv8n baseline + rule-based zone labels (custom weights supported via env)."""
from __future__ import annotations

import os
from typing import List

import numpy as np
from numpy.typing import NDArray

from app.inference.class_mapping import map_yolo_class
from app.inference.deterministic_zoning import Zone


class YoloLayoutDetector:
    def __init__(self, weights_path: str, use_gpu: bool) -> None:
        self.weights_path = weights_path
        self.use_gpu = use_gpu
        self._model = None
        self._last_error: str | None = None
        if os.path.isfile(weights_path):
            try:
                from ultralytics import YOLO

                self._model = YOLO(weights_path)
            except Exception as exc:  # noqa: BLE001
                self._last_error = str(exc)

    @property
    def is_ready(self) -> bool:
        return self._model is not None

    @property
    def last_error(self) -> str | None:
        return self._last_error

    def predict(self, image_bgr: NDArray[np.uint8]) -> List[Zone]:
        zones: List[Zone] = []
        if self._model is None:
            return zones
        try:
            dev = 0 if self.use_gpu else "cpu"
            res = self._model.predict(image_bgr, device=dev, verbose=False)
            if not res:
                return zones
            r0 = res[0]
            names = getattr(r0, "names", {}) or {}
            if r0.boxes is None or not len(r0.boxes):
                return zones
            for b in r0.boxes:
                xyxy = b.xyxy[0].cpu().numpy().tolist()
                x1, y1, x2, y2 = [float(v) for v in xyxy]
                conf = float(b.conf[0].item()) if b.conf is not None else 0.5
                cls_id = int(b.cls[0].item()) if b.cls is not None else -1
                cls_name = str(names.get(cls_id, "")).strip() if isinstance(names, dict) else ""
                zones.append(Zone(map_yolo_class(cls_id, cls_name), (x1, y1, x2, y2), conf))
        except Exception as exc:  # noqa: BLE001
            self._last_error = str(exc)
        return zones
