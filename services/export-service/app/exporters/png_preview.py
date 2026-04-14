from __future__ import annotations

from typing import Any, Dict

import matplotlib.pyplot as plt


def render_preview(intermediate: Dict[str, Any], output_path: str) -> None:
    fig, ax = plt.subplots(figsize=(8, 6), dpi=150)
    ax.set_facecolor("white")
    fig.patch.set_facecolor("white")
    ax.invert_yaxis()
    geom = intermediate.get("geometry", {})
    for ln in geom.get("lines", []):
        ax.plot([ln.get("x1", 0), ln.get("x2", 0)], [ln.get("y1", 0), ln.get("y2", 0)], color="black", linewidth=0.8)
    for c in geom.get("circles", []):
        circ = plt.Circle((c.get("cx", 0), c.get("cy", 0)), c.get("r", 1), fill=False, edgecolor="blue")
        ax.add_patch(circ)
    for t in intermediate.get("texts", []):
        x1, y1, _, _ = t.get("bbox_xyxy", [0, 0, 0, 0])
        ax.text(x1, y1, str(t.get("text", "")), fontsize=6, color="black")
    ax.set_aspect("equal", adjustable="box")
    ax.axis("off")
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)
