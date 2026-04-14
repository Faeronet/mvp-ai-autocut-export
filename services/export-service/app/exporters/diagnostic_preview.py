from __future__ import annotations

from typing import Any, Dict

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


def render_diagnostic_preview(intermediate: Dict[str, Any], output_path: str) -> None:
    fig, ax = plt.subplots(figsize=(8, 6), dpi=150)
    ax.set_facecolor("white")
    fig.patch.set_facecolor("white")
    ax.invert_yaxis()

    geom = intermediate.get("geometry", {})
    for ln in geom.get("lines", []):
        color = "tab:blue" if ln.get("layer") == "GEOMETRY" else "tab:orange"
        ax.plot([ln.get("x1", 0), ln.get("x2", 0)], [ln.get("y1", 0), ln.get("y2", 0)], color=color, linewidth=0.8)

    for z in intermediate.get("zones", []):
        x1, y1, x2, y2 = z.get("bbox_xyxy", [0, 0, 0, 0])
        ax.add_patch(Rectangle((x1, y1), x2 - x1, y2 - y1, fill=False, edgecolor="green", linewidth=1.0))
        ax.text(x1, y1, z.get("label", ""), fontsize=6, color="green")

    for t in intermediate.get("texts", []):
        x1, y1, x2, y2 = t.get("bbox_xyxy", [0, 0, 0, 0])
        color = "red" if t.get("review_required") else "black"
        ax.add_patch(Rectangle((x1, y1), x2 - x1, y2 - y1, fill=False, edgecolor=color, linewidth=0.8))
        ax.text(x1, y1, str(t.get("text", "")), fontsize=6, color=color)

    for tb in intermediate.get("tables", []):
        x1, y1, x2, y2 = tb.get("bbox_xyxy", [0, 0, 0, 0])
        ax.add_patch(Rectangle((x1, y1), x2 - x1, y2 - y1, fill=False, edgecolor="purple", linewidth=1.0))

    ax.set_aspect("equal", adjustable="box")
    ax.axis("off")
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)
