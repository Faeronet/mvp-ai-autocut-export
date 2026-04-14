from __future__ import annotations

from typing import Any, Dict, List


def merge_line_segments(lines: List[Dict[str, Any]], tol: float = 1.0) -> List[Dict[str, Any]]:
    seen: set[tuple[float, ...]] = set()
    merged: List[Dict[str, Any]] = []
    for ln in lines:
        key = tuple(round(ln[k] / tol) * tol for k in ("x1", "y1", "x2", "y2"))
        rkey = (key[2], key[3], key[0], key[1])
        if key in seen or rkey in seen:
            continue
        seen.add(key)
        merged.append(ln)
    return merged
