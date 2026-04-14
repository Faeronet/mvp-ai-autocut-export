from pydantic import BaseModel, Field

from fastapi import APIRouter, HTTPException, Request

router = APIRouter()


class TableStructureRequest(BaseModel):
    image_path: str
    profile: str = Field(default="balanced")
    rois: list[dict] = Field(default_factory=list)


@router.post("/v1/table/structure")
def table_structure(req: TableStructureRequest, request: Request) -> dict:
    svc = request.app.state.table_service
    try:
        return svc.structure(req.image_path, req.rois)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc
