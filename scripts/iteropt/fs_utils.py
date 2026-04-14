from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def ensure_iter_dirs(iter_dir: Path) -> None:
    for rel in (
        "",
        "side_by_side",
        "previews",
        "diagnostics",
        "reports",
        "logs",
        "artifacts",
    ):
        (iter_dir / rel).mkdir(parents=True, exist_ok=True)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_simple_yaml(path: Path, payload: dict[str, Any]) -> None:
    lines: list[str] = []
    for k, v in payload.items():
        if isinstance(v, (int, float)):
            lines.append(f"{k}: {v}")
        else:
            s = str(v).replace("\n", " ")
            lines.append(f'{k}: "{s}"')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
