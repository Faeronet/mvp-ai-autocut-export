"""Startup: load PaddleOCR + table engine; populate registry; optional strict exit."""
from __future__ import annotations

import os
import sys

from app.core.config import Settings
from app.ml_gpu_check import require_paddle_cuda_if_configured
from app.inference.paddle_ocr_runner import PaddleOCRRunner
from app.inference.table_structure_engine import TableStructureEngine
from app.inference.vl_parser import Qwen25VLParser
from app.model_registry.state import REGISTRY, ModelStatus
from app.services.ocr_service import OCRService
from app.services.page_understanding_service import PageUnderstandingService
from app.services.table_structure_service import TableStructureService


def load_services(settings: Settings) -> tuple[OCRService, TableStructureService, PageUnderstandingService]:
    cache = settings.model_cache_dir
    os.makedirs(cache, exist_ok=True)
    require_paddle_cuda_if_configured(settings.ocr_use_gpu, settings.table_use_gpu)

    paddle_err = None
    runner = None
    try:
        runner = PaddleOCRRunner(use_gpu=settings.ocr_use_gpu, cache_dir=cache, lang=settings.ocr_lang)
        if runner.active_lang != settings.ocr_lang:
            print(
                f"WARN: requested OCR_LANG={settings.ocr_lang} unavailable offline; fallback to {runner.active_lang}",
                file=sys.stderr,
            )
        REGISTRY.set(
            ModelStatus(
                model_name="paddleocr_ppocrv4",
                installed=True,
                loaded=True,
                version=f"PP-OCRv4:{runner.active_lang}",
                backend=settings.ocr_backend,
                device="gpu" if settings.ocr_use_gpu else "cpu",
            )
        )
    except Exception as exc:  # noqa: BLE001
        paddle_err = str(exc)
        REGISTRY.set(
            ModelStatus(
                model_name="paddleocr_ppocrv4",
                installed=False,
                loaded=False,
                version="",
                backend=settings.ocr_backend,
                device="n/a",
                last_error=paddle_err,
            )
        )
        if settings.model_startup_strict:
            print("FATAL: PaddleOCR load failed:", paddle_err, file=sys.stderr)
            sys.exit(1)

    tbl_err = None
    table_engine = TableStructureEngine(use_gpu=settings.table_use_gpu, cache_dir=cache)
    if not table_engine.is_ready:
        tbl_err = table_engine.last_error
        REGISTRY.set(
            ModelStatus(
                model_name="ppstructure_table",
                installed=False,
                loaded=False,
                version="",
                backend=settings.table_backend,
                device="n/a",
                last_error=tbl_err,
            )
        )
        if settings.model_startup_strict:
            print("FATAL: PP-Structure table engine failed:", tbl_err, file=sys.stderr)
            sys.exit(1)
    else:
        REGISTRY.set(
            ModelStatus(
                model_name="ppstructure_table",
                installed=True,
                loaded=True,
                version=settings.table_model_name,
                backend=settings.table_backend,
                device="gpu" if settings.table_use_gpu else "cpu",
            )
        )

    if runner is None:
        raise RuntimeError("OCR runner not initialized")

    vl_parser = Qwen25VLParser(
        enabled=settings.vlm_enabled,
        backend=settings.vlm_backend,
        device=settings.vlm_device,
        use_fp16=settings.vlm_use_fp16,
        max_batch=settings.vlm_max_batch,
        model_id=settings.vlm_model_id,
        max_new_tokens=settings.vlm_max_new_tokens,
        quantization=settings.vlm_quantization,
        use_flash_attention=settings.vlm_use_flash_attention,
    )
    if vl_parser.is_ready:
        REGISTRY.set(
            ModelStatus(
                model_name="qwen2_5_vl_3b",
                installed=True,
                loaded=True,
                version=vl_parser.model_version,
                backend=settings.vlm_backend,
                device=settings.vlm_device,
            )
        )
    else:
        REGISTRY.set(
            ModelStatus(
                model_name="qwen2_5_vl_3b",
                installed=False,
                loaded=False,
                version=vl_parser.model_version,
                backend=settings.vlm_backend,
                device=settings.vlm_device,
                last_error=vl_parser.last_error,
            )
        )

    ocr_svc = OCRService(settings, runner)
    table_svc = TableStructureService(table_engine)
    page_understanding_svc = PageUnderstandingService(vl_parser)
    return ocr_svc, table_svc, page_understanding_svc
