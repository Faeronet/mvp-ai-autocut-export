from __future__ import annotations

import os
import sys

from app.core.config import Settings
from app.ml_gpu_check import require_torch_cuda_if_layout_gpu
from app.inference.yolo_layout import YoloLayoutDetector
from app.model_registry.state import REGISTRY, ModelStatus
from app.services.layout_service import LayoutService


def load_layout_service(settings: Settings) -> LayoutService:
    os.makedirs(settings.model_cache_dir, exist_ok=True)
    require_torch_cuda_if_layout_gpu(settings.layout_use_gpu)
    det = YoloLayoutDetector(settings.layout_model_weights, settings.layout_use_gpu)
    err = det.last_error
    if det.is_ready:
        REGISTRY.set(
            ModelStatus(
                model_name=settings.layout_model_name,
                installed=True,
                loaded=True,
                version="yolov8n",
                backend=settings.layout_backend,
                device="gpu" if settings.layout_use_gpu else "cpu",
            )
        )
    else:
        REGISTRY.set(
            ModelStatus(
                model_name=settings.layout_model_name,
                installed=os.path.isfile(settings.layout_model_weights),
                loaded=False,
                version="",
                backend=settings.layout_backend,
                device="n/a",
                last_error=err or "weights_missing_or_load_failed",
            )
        )
        if settings.model_startup_strict:
            print("FATAL: YOLOv8n layout weights not available:", settings.layout_model_weights, file=sys.stderr)
            sys.exit(1)
    return LayoutService(settings, det)
