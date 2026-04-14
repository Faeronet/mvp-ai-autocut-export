import logging

from fastapi import APIRouter, HTTPException, Request

from app.api.schemas import OCRItem, RunRequest, RunResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/v1/ocr/run", response_model=RunResponse)
def run_ocr(req: RunRequest, request: Request) -> RunResponse:
    svc = request.app.state.ocr_service
    try:
        data = svc.run(req.image_path, [r.model_dump() for r in req.rois], req.profile)
        items = [OCRItem(**it) for it in data["items"]]
        return RunResponse(items=items)
    except Exception as exc:  # noqa: BLE001
        logger.exception("ocr run failed image=%s rois=%d", req.image_path, len(req.rois))
        raise HTTPException(status_code=500, detail=str(exc)) from exc
