import os

from fastapi import APIRouter, HTTPException, Request

from app.api.schemas import DetectRequest, DetectResponse, ZoneDTO

router = APIRouter()


@router.post("/v1/layout/detect", response_model=DetectResponse)
def detect(req: DetectRequest, request: Request) -> DetectResponse:
    svc = request.app.state.layout_service
    try:
        work = os.path.join(os.path.dirname(req.image_path), "_layout_work")
        data = svc.detect(req.image_path, req.profile, work)
        zones = [ZoneDTO(**z) for z in data["zones"]]
        return DetectResponse(
            zones=zones,
            overlay_path=data["overlay_path"],
            warnings=data.get("warnings", []),
            mode=data.get("mode", "deterministic"),
            debug_artifacts=data.get("debug_artifacts", {}),
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc
