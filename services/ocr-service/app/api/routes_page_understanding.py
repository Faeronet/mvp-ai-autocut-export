import logging

from fastapi import APIRouter, HTTPException, Request

from app.api.schemas import (
    LayoutRegion,
    PageUnderstandingRequest,
    PageUnderstandingResponse,
    ReviewHint,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/v1/page/understand", response_model=PageUnderstandingResponse)
def understand_page(req: PageUnderstandingRequest, request: Request) -> PageUnderstandingResponse:
    svc = request.app.state.page_understanding_service
    try:
        out = svc.understand(req.image_path, req.profile)
        return PageUnderstandingResponse(
            sheet_type=out.get("sheet_type", "mixed"),
            regions=[LayoutRegion(**r) for r in out.get("regions", [])],
            orientation_hints=out.get("orientation_hints", {}),
            review_hints=[ReviewHint(**h) for h in out.get("review_hints", [])],
            warnings=out.get("warnings", []),
            model_version=out.get("model_version", ""),
            confidence=float(out.get("confidence", 0.0)),
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("page understanding failed image=%s", req.image_path)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
