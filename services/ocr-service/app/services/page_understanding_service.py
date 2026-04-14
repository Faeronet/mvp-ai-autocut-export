from __future__ import annotations

from typing import Any, Dict

from app.inference.vl_parser import PaddleOCRVLParser


class PageUnderstandingService:
    def __init__(self, parser: PaddleOCRVLParser) -> None:
        self.parser = parser

    def understand(self, image_path: str, profile: str) -> Dict[str, Any]:
        return self.parser.understand_page(image_path, profile)
