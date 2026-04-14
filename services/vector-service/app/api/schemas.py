from pydantic import BaseModel, Field


class PreprocessRequest(BaseModel):
    image_path: str
    output_dir: str
    profile: str = Field(default="balanced")
    save_debug: bool = False


class PreprocessResponse(BaseModel):
    preprocessed_path: str
    binary_path: str
    soft_path: str
    debug_artifacts: dict[str, str] = Field(default_factory=dict)
    image_meta: dict[str, float] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    preprocess_confidence: float = 0.0


class ExtractRequest(BaseModel):
    image_path: str
    profile: str = "balanced"


class LineDTO(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float
    layer: str
    confidence: float


class CircleDTO(BaseModel):
    cx: float
    cy: float
    r: float
    layer: str


class ExtractResponse(BaseModel):
    lines: list[LineDTO]
    circles: list[CircleDTO]
    tables: list
