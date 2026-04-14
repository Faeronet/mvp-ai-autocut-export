"""Non-neural modules: sheet classifier, symbol detector, review (env-driven)."""
from __future__ import annotations

import os


def model_status_rows() -> list[dict]:
    return [
        {
            "model_name": "sheet_classifier",
            "installed": True,
            "loaded": True,
            "version": os.getenv("SHEET_CLASSIFIER_BACKEND", "rules"),
            "backend": os.getenv("SHEET_CLASSIFIER_BACKEND", "rules"),
            "device": "cpu",
            "last_error": None,
        },
        {
            "model_name": "symbol_detector",
            "installed": True,
            "loaded": True,
            "version": os.getenv("SYMBOL_DETECTION_BACKEND", "heuristic"),
            "backend": os.getenv("SYMBOL_DETECTION_BACKEND", "heuristic"),
            "device": "cpu",
            "last_error": None,
        },
        {
            "model_name": "low_confidence_review",
            "installed": True,
            "loaded": True,
            "version": os.getenv("REVIEW_BACKEND", "rules"),
            "backend": os.getenv("REVIEW_BACKEND", "rules"),
            "device": "cpu",
            "last_error": None,
        },
    ]
