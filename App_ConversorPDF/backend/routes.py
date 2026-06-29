from __future__ import annotations

import shutil
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from App_ConversorPDF.services.converter import ConversionRequest, PdfConverter

from Main_View.backend.runtime import cleanup_tree, make_work_dir

router = APIRouter(prefix="/api/conversor")


@router.post("/convertir")
def convert_to_pdf(
    source_file: UploadFile = File(...),
    selection: str = Form(""),
) -> FileResponse:
    if not source_file.filename:
        raise HTTPException(status_code=400, detail="Selecciona un archivo.")
    work_dir = make_work_dir("suite-conversor-")
    source_path = work_dir / Path(source_file.filename).name
    output_path = work_dir / f"{source_path.stem}.pdf"
    try:
        with source_path.open("wb") as handle:
            shutil.copyfileobj(source_file.file, handle)
        result_path = PdfConverter().convert(
            ConversionRequest(
                source_path=source_path,
                target_path=output_path,
                sheet_name=selection.strip() or None,
            )
        )
    except Exception as error:
        cleanup_tree(work_dir)
        raise HTTPException(status_code=400, detail=str(error)) from error
    return FileResponse(
        result_path,
        media_type="application/pdf",
        filename=result_path.name,
        background=BackgroundTask(cleanup_tree, work_dir),
    )
