from __future__ import annotations

import os
from typing import Any, Dict, List

import cv2
import numpy as np

from app.core.config import Settings
from app.preprocessing.document_normalizer import normalize_document
from app.postprocessing.geometry_extract import extract_geometry


class VectorService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def preprocess(self, image_path: str, output_dir: str, profile: str, save_debug: bool) -> Dict[str, Any]:
        os.makedirs(output_dir, exist_ok=True)
        res = normalize_document(image_path=image_path, output_dir=output_dir, max_side=self.settings.max_image_side)
        return {
            "preprocessed_path": res.preprocessed_path,
            "binary_path": res.binary_path,
            "soft_path": res.soft_path,
            "debug_artifacts": res.debug_artifacts if save_debug else {},
            "image_meta": res.image_meta,
            "warnings": res.warnings,
            "preprocess_confidence": res.preprocess_confidence,
        }

    def extract(self, image_path: str, profile: str) -> Dict[str, Any]:
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError("cannot read image")
        geom = extract_geometry(img)
        return geom
