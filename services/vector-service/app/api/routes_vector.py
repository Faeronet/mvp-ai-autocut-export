from fastapi import APIRouter, HTTPException, Request

from app.api.schemas import (
    CircleDTO,
    ExtractRequest,
    ExtractResponse,
    LineDTO,
    PreprocessRequest,
    PreprocessResponse,
)

router = APIRouter()


@router.post("/v1/vector/preprocess", response_model=PreprocessResponse)
def preprocess(req: PreprocessRequest, request: Request) -> PreprocessResponse:
    svc = request.app.state.vector_service
    try:
        data = svc.preprocess(req.image_path, req.output_dir, req.profile, req.save_debug)
        return PreprocessResponse(**data)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/v1/vector/extract", response_model=ExtractResponse)
def extract(req: ExtractRequest, request: Request) -> ExtractResponse:
    svc = request.app.state.vector_service
    try:
        data = svc.extract(req.image_path, req.profile)
        lines = [LineDTO(**ln) for ln in data["lines"]]
        circles = [CircleDTO(**c) for c in data["circles"]]
        return ExtractResponse(lines=lines, circles=circles, tables=data["tables"])
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc
