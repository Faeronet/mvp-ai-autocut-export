from __future__ import annotations

from typing import Any, Dict

import matplotlib.pyplot as plt


def render_clean_preview(intermediate: Dict[str, Any], output_path: str) -> None:
    fig, ax = plt.subplots(figsize=(8, 6), dpi=150)
    ax.set_facecolor("white")
    fig.patch.set_facecolor("white")
    ax.invert_yaxis()
    geom = intermediate.get("geometry", {})
    for ln in geom.get("lines", []):
        if ln.get("layer") == "DEBUG":
            continue
        ax.plot([ln.get("x1", 0), ln.get("x2", 0)], [ln.get("y1", 0), ln.get("y2", 0)], color="black", linewidth=0.9)
    for t in intermediate.get("texts", []):
        if t.get("review_required"):
            continue
        x1, y1, _, _ = t.get("bbox_xyxy", [0, 0, 0, 0])
        ax.text(x1, y1, str(t.get("text", "")), fontsize=6, color="black")
    ax.set_aspect("equal", adjustable="box")
    ax.axis("off")
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)
