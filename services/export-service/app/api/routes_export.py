from fastapi import APIRouter, HTTPException, Request

from app.api.schemas import RenderRequest, RenderResponse

router = APIRouter()


@router.post("/v1/export/render", response_model=RenderResponse)
def render(req: RenderRequest, request: Request) -> RenderResponse:
    svc = request.app.state.export_service
    try:
        data = svc.render(req.intermediate, req.output_dxf, req.output_png, req.profile)
        return RenderResponse(**data)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc
