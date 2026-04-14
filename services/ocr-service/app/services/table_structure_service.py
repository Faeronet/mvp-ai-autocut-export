from __future__ import annotations

from typing import Any, Dict, List

import cv2
from app.inference.table_structure_engine import TableStructureEngine


class TableStructureService:
    def __init__(self, engine: TableStructureEngine) -> None:
        self.engine = engine

    def structure(self, image_path: str, rois: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
        if not rois:
            return self.engine.extract(image_path)
        img = cv2.imread(image_path)
        if img is None:
            return {"cells": [], "html": "", "warnings": ["cannot_read_image"], "partial": True}
        h, w = img.shape[:2]
        all_cells: List[Dict[str, Any]] = []
        warnings: List[str] = []
        partial = False
        for roi in rois:
            bbox = roi.get("bbox_xyxy", [0, 0, w, h])
            x1, y1, x2, y2 = [int(float(v)) for v in bbox]
            x1 = max(0, min(x1, w - 1))
            x2 = max(x1 + 1, min(x2, w))
            y1 = max(0, min(y1, h - 1))
            y2 = max(y1 + 1, min(y2, h))
            crop = img[y1:y2, x1:x2]
            out = self.engine.extract_image(crop)
            for cell in out.get("cells", []):
                if isinstance(cell, dict):
                    cell_copy = dict(cell)
                    if "bbox" in cell_copy and isinstance(cell_copy["bbox"], list) and len(cell_copy["bbox"]) >= 4:
                        cb = cell_copy["bbox"]
                        cell_copy["bbox"] = [float(cb[0]) + x1, float(cb[1]) + y1, float(cb[2]) + x1, float(cb[3]) + y1]
                    cell_copy["roi_bbox_xyxy"] = [x1, y1, x2, y2]
                    all_cells.append(cell_copy)
            warnings.extend(out.get("warnings", []))
            partial = partial or bool(out.get("partial", False))
        return {"cells": all_cells, "html": "", "warnings": sorted(set(warnings)), "partial": partial}
