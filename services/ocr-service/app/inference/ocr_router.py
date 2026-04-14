from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OCRMode:
    semantic_role: str
    min_confidence: float
    allow_cls: bool


_ALIASES = {
    "title_block": "title_block",
    "specification_table": "table",
    "table": "table",
    "dimension": "dimension_text",
    "dimension_text": "dimension_text",
    "notes": "notes",
    "general_notes": "notes",
    "callout": "callout",
    "generic": "generic",
}

_MODES = {
    "title_block": OCRMode("title_block", 0.5, True),
    "table": OCRMode("table", 0.45, True),
    "dimension_text": OCRMode("dimension_text", 0.42, True),
    "notes": OCRMode("notes", 0.5, True),
    "callout": OCRMode("callout", 0.45, True),
    "generic": OCRMode("generic", 0.5, True),
}


def resolve_mode(semantic: str) -> OCRMode:
    key = _ALIASES.get(semantic, "generic")
    return _MODES[key]
