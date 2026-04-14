from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List


def write_summary_md(path: Path, row: Dict[str, Any], archives: List[Path]) -> None:
    lines = [
        f"# Iteration {row['iteration']:03d}",
        "",
        f"- Profile: `{row['profile']}`",
        f"- Quality score: `{row['quality_score']:.4f}`",
        f"- Archives processed: `{len(archives)}`",
        f"- Page count: `{row.get('page_count', 0)}`",
        f"- Avg confidence: `{row.get('page_confidence_avg', 0):.4f}`",
        f"- Avg OCR conf: `{row.get('ocr_avg_conf_avg', 0):.4f}`",
        f"- Avg OCR junk ratio: `{row.get('ocr_junk_ratio_avg', 0):.4f}`",
        f"- Avg table fill: `{row.get('table_text_fill_ratio_avg', 0):.4f}`",
        f"- Avg frame leakage: `{row.get('frame_leakage_avg', 0):.4f}`",
        f"- Avg table leakage: `{row.get('table_leakage_avg', 0):.4f}`",
        f"- Avg line-density similarity: `{row.get('line_density_similarity_avg', 0):.4f}`",
        "",
        "## Root-cause notes",
        "",
        "- This iteration emphasizes end-to-end output quality (preview/JSON/geometry) over detector-only metrics.",
        "- High OCR junk ratio or high leakage indicates downstream degradation regardless of layout model mAP.",
        "- Inspect `side_by_side/` and per-archive metrics to identify failure hotspots.",
        "",
        "## Archives",
    ]
    lines.extend([f"- `{p.name}`" for p in archives])
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
