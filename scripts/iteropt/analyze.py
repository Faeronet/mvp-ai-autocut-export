from __future__ import annotations

import json
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import cv2
import numpy as np


@dataclass
class PageMetrics:
    page_id: str
    layout_zone_count: int
    title_block_coverage: float
    spec_table_coverage: float
    ocr_avg_conf: float
    ocr_junk_ratio: float
    table_cell_count: int
    table_text_fill_ratio: float
    geom_line_count: int
    geom_frame_leakage: float
    geom_table_leakage: float
    review_density: float
    page_confidence: float


def _bbox_area(box: List[float]) -> float:
    x1, y1, x2, y2 = box
    return max(0.0, x2 - x1) * max(0.0, y2 - y1)


def _zones_by_label(zones: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for z in zones:
        lbl = str(z.get("label", ""))
        if lbl and lbl not in out:
            out[lbl] = z
    return out


def _text_junk_ratio(texts: List[Dict[str, Any]]) -> float:
    if not texts:
        return 1.0
    bad = 0
    for t in texts:
        raw = str(t.get("normalized_text") or t.get("text") or "")
        if len(raw.strip()) <= 1:
            bad += 1
            continue
        letters = sum(ch.isalpha() for ch in raw)
        digits = sum(ch.isdigit() for ch in raw)
        if letters + digits == 0:
            bad += 1
    return bad / float(len(texts))


def _line_density_similarity(src_img: np.ndarray, preview_img: np.ndarray) -> float:
    src_g = cv2.cvtColor(src_img, cv2.COLOR_BGR2GRAY)
    prev_g = cv2.cvtColor(preview_img, cv2.COLOR_BGR2GRAY)
    src_edges = cv2.Canny(src_g, 70, 180)
    prev_edges = cv2.Canny(prev_g, 70, 180)
    src_d = float(np.count_nonzero(src_edges)) / src_edges.size
    prev_d = float(np.count_nonzero(prev_edges)) / prev_edges.size
    if src_d <= 1e-9:
        return 0.0
    return max(0.0, 1.0 - abs(src_d - prev_d) / src_d)


def collect_metrics_from_result_zip(
    result_zip: Path,
    extracted_dir: Path,
    src_images: List[Path],
    side_by_side_dir: Path,
) -> Dict[str, Any]:
    extracted_dir.mkdir(parents=True, exist_ok=True)
    side_by_side_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(result_zip, "r") as zf:
        zf.extractall(extracted_dir)
    manifest_path = extracted_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}

    page_metrics: List[PageMetrics] = []
    line_similarity_scores: List[float] = []
    warnings_union: set[str] = set()

    pages = manifest.get("pages", [])
    for i, page in enumerate(pages):
        page_id = str(page.get("page_id", f"idx_{i}"))
        json_rel = page.get("json", "")
        preview_rel = page.get("png", "")
        inter = {}
        if json_rel:
            p = extracted_dir / json_rel
            if p.exists():
                inter = json.loads(p.read_text(encoding="utf-8"))
        zones = inter.get("zones", [])
        texts = inter.get("texts", [])
        tables = inter.get("tables", [])
        geom = inter.get("geometry", {})
        warnings = inter.get("warnings", [])
        for w in warnings:
            warnings_union.add(str(w))
        review_items = inter.get("review_required_items", [])
        image_meta = inter.get("image_meta", {})
        width = float(image_meta.get("width_px", inter.get("meta", {}).get("width_px", 1)) or 1)
        height = float(image_meta.get("height_px", inter.get("meta", {}).get("height_px", 1)) or 1)
        page_area = max(1.0, width * height)
        zbl = _zones_by_label(zones)
        title_cov = _bbox_area(zbl.get("title_block", {}).get("bbox_xyxy", [0, 0, 0, 0])) / page_area
        spec_cov = _bbox_area(zbl.get("specification_table", {}).get("bbox_xyxy", [0, 0, 0, 0])) / page_area

        ocr_conf = [float(t.get("confidence", 0.0)) for t in texts]
        ocr_avg = float(np.mean(ocr_conf)) if ocr_conf else 0.0
        junk_ratio = _text_junk_ratio(texts)
        table_cells = sum(len(t.get("cells", [])) for t in tables if isinstance(t, dict))
        non_empty_cells = 0
        for t in tables:
            for c in t.get("cells", []):
                if str(c.get("text", "")).strip():
                    non_empty_cells += 1
        fill_ratio = (non_empty_cells / table_cells) if table_cells else 0.0
        lines = geom.get("lines", []) if isinstance(geom, dict) else []
        line_count = len(lines)
        frame_leak = (sum(1 for ln in lines if ln.get("layer") == "FRAME") / line_count) if line_count else 0.0
        table_leak = (sum(1 for ln in lines if ln.get("layer") == "TABLE") / line_count) if line_count else 0.0
        review_density = len(review_items) / max(1, len(texts) + len(lines))
        page_conf = float(inter.get("confidence", 0.0))

        pm = PageMetrics(
            page_id=page_id,
            layout_zone_count=len(zones),
            title_block_coverage=title_cov,
            spec_table_coverage=spec_cov,
            ocr_avg_conf=ocr_avg,
            ocr_junk_ratio=junk_ratio,
            table_cell_count=table_cells,
            table_text_fill_ratio=fill_ratio,
            geom_line_count=line_count,
            geom_frame_leakage=frame_leak,
            geom_table_leakage=table_leak,
            review_density=review_density,
            page_confidence=page_conf,
        )
        page_metrics.append(pm)

        if i < len(src_images) and preview_rel:
            src = cv2.imread(str(src_images[i]))
            prev = cv2.imread(str(extracted_dir / preview_rel))
            if src is not None and prev is not None:
                h = min(src.shape[0], prev.shape[0])
                ws = int(src.shape[1] * (h / src.shape[0]))
                wp = int(prev.shape[1] * (h / prev.shape[0]))
                src_r = cv2.resize(src, (ws, h))
                prev_r = cv2.resize(prev, (wp, h))
                canvas = np.concatenate([src_r, prev_r], axis=1)
                out = side_by_side_dir / f"{page_id}.png"
                cv2.imwrite(str(out), canvas)
                line_similarity_scores.append(_line_density_similarity(src_r, prev_r))

    if not page_metrics:
        return {"page_count": 0, "warnings": ["no_pages_in_manifest"]}

    agg = {
        "page_count": len(page_metrics),
        "layout_zone_count_avg": float(np.mean([p.layout_zone_count for p in page_metrics])),
        "title_block_coverage_avg": float(np.mean([p.title_block_coverage for p in page_metrics])),
        "spec_table_coverage_avg": float(np.mean([p.spec_table_coverage for p in page_metrics])),
        "ocr_avg_conf_avg": float(np.mean([p.ocr_avg_conf for p in page_metrics])),
        "ocr_junk_ratio_avg": float(np.mean([p.ocr_junk_ratio for p in page_metrics])),
        "table_cell_count_avg": float(np.mean([p.table_cell_count for p in page_metrics])),
        "table_text_fill_ratio_avg": float(np.mean([p.table_text_fill_ratio for p in page_metrics])),
        "geom_line_count_avg": float(np.mean([p.geom_line_count for p in page_metrics])),
        "frame_leakage_avg": float(np.mean([p.geom_frame_leakage for p in page_metrics])),
        "table_leakage_avg": float(np.mean([p.geom_table_leakage for p in page_metrics])),
        "review_density_avg": float(np.mean([p.review_density for p in page_metrics])),
        "page_confidence_avg": float(np.mean([p.page_confidence for p in page_metrics])),
        "line_density_similarity_avg": float(np.mean(line_similarity_scores)) if line_similarity_scores else 0.0,
        "warnings_union": sorted(warnings_union),
        "pages": [p.__dict__ for p in page_metrics],
    }
    return agg


def quality_score(metrics: Dict[str, Any]) -> float:
    if not metrics or metrics.get("page_count", 0) == 0:
        return 0.0
    conf = float(metrics.get("page_confidence_avg", 0.0))
    ocr = float(metrics.get("ocr_avg_conf_avg", 0.0))
    table = float(metrics.get("table_text_fill_ratio_avg", 0.0))
    sim = float(metrics.get("line_density_similarity_avg", 0.0))
    leaks = float(metrics.get("frame_leakage_avg", 1.0)) + float(metrics.get("table_leakage_avg", 1.0))
    junk = float(metrics.get("ocr_junk_ratio_avg", 1.0))
    review = float(metrics.get("review_density_avg", 1.0))
    score = 0.28 * conf + 0.2 * ocr + 0.16 * table + 0.16 * sim + 0.2 * max(0.0, 1.0 - 0.5 * leaks - 0.5 * junk - 0.4 * review)
    return max(0.0, min(1.0, score))
