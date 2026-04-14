from pydantic import BaseModel, Field


class DetectRequest(BaseModel):
    image_path: str
    profile: str = Field(default="balanced")


class ZoneDTO(BaseModel):
    label: str
    bbox_xyxy: list[float]
    confidence: float


class DetectResponse(BaseModel):
    zones: list[ZoneDTO]
    overlay_path: str
    warnings: list[str] = Field(default_factory=list)
    mode: str = "deterministic"
    debug_artifacts: dict[str, str] = Field(default_factory=dict)
