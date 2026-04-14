from __future__ import annotations

import os
from typing import Any, Dict

import ezdxf


def export_dxf(intermediate: Dict[str, Any], output_path: str) -> None:
    doc = ezdxf.new(setup=True)
    for name in ("FRAME", "GEOMETRY", "TEXT", "TABLES", "DIMENSIONS", "DEBUG"):
        doc.layers.add(name, color=7)
    msp = doc.modelspace()
    geom = intermediate.get("geometry", {})
    for ln in geom.get("lines", []):
        msp.add_line(
            (ln.get("x1", 0), ln.get("y1", 0)),
            (ln.get("x2", 0), ln.get("y2", 0)),
            dxfattribs={"layer": ln.get("layer", "GEOMETRY")},
        )
    for c in geom.get("circles", []):
        msp.add_circle(
            (c.get("cx", 0), c.get("cy", 0)),
            radius=c.get("r", 1),
            dxfattribs={"layer": c.get("layer", "GEOMETRY")},
        )
    y = 0.0
    for t in intermediate.get("texts", []):
        txt = str(t.get("text", ""))
        if not txt:
            continue
        x1, y1, _, y2 = t.get("bbox_xyxy", [0, y, 100, y + 10])
        h = max(2.5, abs((y2 or 0) - (y1 or 0)) * 0.1)
        msp.add_text(
            txt,
            height=h,
            dxfattribs={"layer": "TEXT", "insert": (float(x1), float(y1))},
        )
        y += 12.0
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc.saveas(output_path)
