from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from App_Directorio.models import AreaReportData, DirectoryReportData, PersonReportRow
from App_Directorio.services.pdf_exporter import DirectoryPdfExporter

from Main_View.backend.runtime import cleanup_tree, make_work_dir

from .schemas import DirectoryPayload

router = APIRouter(prefix="/api/directorio")


@router.post("/pdf")
def create_pdf(payload: DirectoryPayload) -> FileResponse:
    work_dir = make_work_dir("suite-directorio-")
    output_path = work_dir / "directorio.pdf"
    areas = [
        AreaReportData(
            name=area.name.strip() or "Area",
            personnel=[
                PersonReportRow(
                    rank=person.rank.strip(),
                    name=person.name.strip(),
                    position=person.position.strip(),
                    email=person.email.strip(),
                    start_date=person.start_date.strip(),
                )
                for person in area.personnel
                if any((person.rank, person.name, person.position, person.email, person.start_date))
            ],
        )
        for area in payload.areas
    ]
    if not areas:
        areas = [AreaReportData(name="Area", personnel=[])]
    DirectoryPdfExporter().export(
        DirectoryReportData(title=payload.title.strip() or "Directorio", period=payload.period.strip(), areas=areas),
        output_path,
    )
    return FileResponse(
        output_path,
        media_type="application/pdf",
        filename="directorio.pdf",
        background=BackgroundTask(cleanup_tree, work_dir),
    )
