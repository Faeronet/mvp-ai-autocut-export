from pydantic import BaseModel, Field


class ROI(BaseModel):
    bbox_xyxy: list[float]
    semantic_role: str = "general_notes"


class RunRequest(BaseModel):
    image_path: str
    rois: list[ROI]
    profile: str = Field(default="balanced")


class OCRItem(BaseModel):
    raw_text: str
    normalized_text: str
    text: str
    bbox_xyxy: list[float]
    quad_xy: list[float] = Field(default_factory=list)
    angle_deg: float
    orientation_deg: int = 0
    confidence: float
    semantic_role: str
    review_required: bool


class RunResponse(BaseModel):
    items: list[OCRItem]


class PageUnderstandingRequest(BaseModel):
    image_path: str
    profile: str = Field(default="balanced")


class LayoutRegion(BaseModel):
    label: str
    bbox_xyxy: list[float]
    confidence: float
    source: str = "vlm"


class ReviewHint(BaseModel):
    kind: str
    reason: str
    bbox_xyxy: list[float]
    confidence: float = 0.0


class PageUnderstandingResponse(BaseModel):
    sheet_type: str = "mixed"
    regions: list[LayoutRegion] = Field(default_factory=list)
    orientation_hints: dict[str, int] = Field(default_factory=dict)
    review_hints: list[ReviewHint] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    model_version: str = ""
    confidence: float = 0.0
