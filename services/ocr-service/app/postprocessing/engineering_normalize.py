from __future__ import annotations

import re

_RULES = [
    (re.compile(r"\b0\s*([0-9]+)\b"), r"Ø\1"),
    (re.compile(r"\bГ0СТ\b", re.IGNORECASE), "ГОСТ"),
    (re.compile(r"\bM\s*([0-9]+)\b", re.IGNORECASE), r"M\1"),
    (re.compile(r"\bR\s*([0-9]+)\b", re.IGNORECASE), r"R\1"),
    (re.compile(r"\bH\s*([0-9]+)\b", re.IGNORECASE), r"H\1"),
    (re.compile(r"\bh\s*([0-9]+)\b"), r"h\1"),
    (re.compile(r"\bMM\b", re.IGNORECASE), "мм"),
    (re.compile(r"\bWT\b", re.IGNORECASE), "шт"),
]


def normalize_text(raw: str, confidence: float, semantic: str) -> tuple[str, bool]:
    text = re.sub(r"\s+", " ", raw.strip())
    review = confidence < 0.58 or len(text) == 0
    if semantic in {"dimension_text", "dimension", "title_block", "table"}:
        for pat, repl in _RULES:
            if confidence >= 0.7:
                text = pat.sub(repl, text)
    if semantic in {"dimension_text", "dimension"}:
        if not re.search(r"[0-9ØRМMHh]", text):
            review = True
    return text, review
