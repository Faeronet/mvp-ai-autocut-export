from __future__ import annotations

import re

ENGINEERING_FIXES = [
    (re.compile(r"\b0\s*12\b"), "Ø12"),
    (re.compile(r"\bR\s*1\s*0\b"), "R10"),
    (re.compile(r"\bM1\s*2\b"), "M12"),
]


def normalize_text(raw: str, confidence: float, semantic: str) -> tuple[str, bool]:
    text = raw.strip()
    review = confidence < 0.55
    if review:
        return text, True
    for pat, repl in ENGINEERING_FIXES:
        if pat.search(text) and confidence > 0.75 and semantic in ("dimension", "title_block"):
            text = pat.sub(repl, text)
    return text, False
