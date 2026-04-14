"""Weak GOST-style priors for table vs drawing split (not ML layout)."""

from __future__ import annotations

from typing import Tuple


def specification_table_bbox_xyxy(h: int, w: int) -> Tuple[int, int, int, int]:
    """
    Bottom-left specification / BOM band typical for Soviet/GOST title blocks.
    Explicit last-resort prior only — real zoning should come from layout-service later.
    """
    x1 = 0
    y1 = int(0.52 * h)
    x2 = int(0.42 * w)
    y2 = h
    return (x1, y1, min(x2, w), min(y2, h))


def clamp_box(
    x1: int, y1: int, x2: int, y2: int, w: int, h: int
) -> Tuple[int, int, int, int]:
    return (
        max(0, min(x1, w - 1)),
        max(0, min(y1, h - 1)),
        max(0, min(x2, w)),
        max(0, min(y2, h)),
    )
