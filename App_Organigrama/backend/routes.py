from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from App_Organigrama.exporters.pdf import PdfOrgChartExporter
from App_Organigrama.rendering.engine import RenderingEngine
from App_Organigrama.routing.manhattan_router import ManhattanRouter
from App_Organigrama.services.persistence import PersistenceManager

from Main_View.backend.runtime import cleanup_tree, make_work_dir

from .schemas import OrgPayload

router = APIRouter(prefix="/api/organigrama")


@router.post("/pdf")
def create_pdf(payload: OrgPayload) -> FileResponse:
    work_dir = make_work_dir("suite-organigrama-")
    output_path = work_dir / "organigrama.pdf"
    try:
        document = PersistenceManager().from_dict(payload.document)
        engine = RenderingEngine()
        PdfOrgChartExporter(engine, ManhattanRouter(engine)).export(document, output_path)
    except Exception as error:
        cleanup_tree(work_dir)
        raise HTTPException(status_code=400, detail=str(error)) from error
    return FileResponse(
        output_path,
        media_type="application/pdf",
        filename="organigrama.pdf",
        background=BackgroundTask(cleanup_tree, work_dir),
    )
