"""Paddle PP-Structure table backend (SLANet-class) with graceful degradation."""
from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional

import cv2
import numpy as np


class TableStructureEngine:
    def __init__(self, use_gpu: bool, cache_dir: str) -> None:
        self.use_gpu = use_gpu
        self._engine: Any = None
        self._last_error: Optional[str] = None
        self._init_engine()

    def _init_engine(self) -> None:
        try:
            from paddleocr import PPStructure

            try:
                self._engine = PPStructure(
                    show_log=False,
                    use_gpu=self.use_gpu,
                    lang="en",
                    table=True,
                    layout=False,
                    ocr=True,
                )
            except TypeError:
                self._engine = PPStructure(show_log=False, use_gpu=self.use_gpu, lang="en")
        except Exception as exc:  # noqa: BLE001
            self._last_error = str(exc)
            self._engine = None

    @property
    def is_ready(self) -> bool:
        return self._engine is not None

    @property
    def last_error(self) -> str | None:
        return self._last_error

    def extract(self, image_path: str) -> Dict[str, Any]:
        img = cv2.imread(image_path)
        if img is None:
            return {"cells": [], "html": "", "warnings": ["cannot_read_image"], "partial": True}
        return self.extract_image(img)

    def extract_image(self, img: np.ndarray) -> Dict[str, Any]:
        warnings: List[str] = []
        if self._engine is None:
            warnings.append("table_structure_unavailable:" + (self._last_error or "unknown"))
            return {"cells": [], "html": "", "warnings": warnings, "partial": True}
        try:
            res = self._engine(img)
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"table_infer_failed:{exc}")
            return {"cells": [], "html": "", "warnings": warnings, "partial": True}
        cells: List[Dict[str, Any]] = []
        if isinstance(res, list):
            for r in res:
                if isinstance(r, dict):
                    row = _to_python(r)
                    cells.extend(_extract_cells(row))
                else:
                    cells.append({"raw": str(_to_python(r)), "text": str(_to_python(r)).strip()})
        else:
            py = _to_python(res)
            if isinstance(py, dict):
                cells.extend(_extract_cells(py))
            else:
                cells.append({"raw": str(py), "text": str(py).strip()})
        if not cells:
            warnings.append("table_cells_empty_after_parse")
        return {"cells": cells, "html": "", "warnings": warnings, "partial": bool(warnings)}


def _to_python(value: Any) -> Any:
    """Normalize numpy-heavy PP-Structure output for FastAPI JSON serialization."""
    if isinstance(value, dict):
        return {str(k): _to_python(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_python(v) for v in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    return value


def _extract_cells(node: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    PP-Structure outputs heterogeneous records:
    - table entry can contain `res` with OCR cell fragments
    - keys differ by PaddleOCR version.
    Build a normalized list with explicit `text` whenever possible.
    """
    out: List[Dict[str, Any]] = []
    res = node.get("res")
    if isinstance(res, list):
        for item in res:
            if not isinstance(item, dict):
                txt = str(item).strip()
                out.append({"text": txt, "raw": item})
                continue
            txt = _cell_text(item)
            row: Dict[str, Any] = {"text": txt}
            if "bbox" in item:
                row["bbox"] = item["bbox"]
            if "text_region" in item:
                row["bbox"] = item["text_region"]
            row["raw"] = item
            out.append(row)
    txt_node = _cell_text(node)
    if txt_node or (not out and any(k in node for k in ("bbox", "text_region", "res", "html"))):
        row = {"text": txt_node, "raw": node}
        if "bbox" in node:
            row["bbox"] = node["bbox"]
        if "text_region" in node:
            row["bbox"] = node["text_region"]
        out.append(row)
    return out


def _cell_text(item: Dict[str, Any]) -> str:
    direct = item.get("text")
    if isinstance(direct, str) and direct.strip():
        return direct.strip()
    # Paddle often emits nested OCR under "res" entries with "text"
    nested = item.get("res")
    if isinstance(nested, list):
        texts = [str(v.get("text", "")).strip() for v in nested if isinstance(v, dict)]
        texts = [t for t in texts if t]
        if texts:
            return " ".join(texts)
    # Table html fallback
    html = item.get("html")
    if isinstance(html, str) and html.strip():
        plain = re.sub(r"<[^>]+>", " ", html)
        plain = re.sub(r"\\s+", " ", plain).strip()
        if plain:
            return plain
    return ""
