from typing import Any

from pydantic import BaseModel, Field


class RenderRequest(BaseModel):
    intermediate: dict[str, Any]
    output_dxf: str
    output_png: str
    profile: str = Field(default="balanced")


class RenderResponse(BaseModel):
    dxf_path: str
    png_path: str
    diagnostic_png_path: str = ""
