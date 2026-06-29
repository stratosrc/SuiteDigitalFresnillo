from __future__ import annotations

import base64
import shutil
from uuid import uuid4

import fitz
from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse

from App_TestData.config.ui_strings import HELP_DIALOG
from App_TestData.data.catalogue_data import build_catalogue_categories
from App_TestData.domain.document_state import RectangleData
from App_TestData.services.redaction_exporter import RedactionPdfExporter

from ..config import RUNTIME_DIR
from ..runtime import cleanup_tree, session_dir
from ..schemas import PdfBase64Payload, RedactionPayload

router = APIRouter(prefix="/api/testdata")


@router.post("/upload")
def upload_pdf(pdf: UploadFile = File(...)) -> dict[str, object]:
    if not pdf.filename or not pdf.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Selecciona un archivo PDF.")
    session_id = uuid4().hex
    session_path = RUNTIME_DIR / session_id
    session_path.mkdir(parents=True, exist_ok=True)
    pdf_path = session_path / "source.pdf"
    with pdf_path.open("wb") as handle:
        shutil.copyfileobj(pdf.file, handle)
    try:
        with fitz.open(pdf_path) as document:
            if document.page_count == 0:
                raise HTTPException(status_code=400, detail="El PDF no contiene paginas.")
            first_page = document[0]
            return {
                "session_id": session_id,
                "page_count": document.page_count,
                "width": first_page.rect.width,
                "height": first_page.rect.height,
            }
    except HTTPException:
        cleanup_tree(session_path)
        raise
    except Exception as error:
        cleanup_tree(session_path)
        raise HTTPException(status_code=400, detail=f"No se pudo leer el PDF: {error}") from error


@router.post("/upload-base64")
def upload_pdf_base64(payload: PdfBase64Payload) -> dict[str, object]:
    raw_data = payload.data
    if "," in raw_data:
        raw_data = raw_data.split(",", 1)[1]
    try:
        pdf_bytes = base64.b64decode(raw_data, validate=True)
    except ValueError as error:
        raise HTTPException(status_code=400, detail="El PDF del proyecto no tiene un formato valido.") from error

    session_id = uuid4().hex
    session_path = RUNTIME_DIR / session_id
    session_path.mkdir(parents=True, exist_ok=True)
    pdf_path = session_path / "source.pdf"
    pdf_path.write_bytes(pdf_bytes)

    try:
        with fitz.open(pdf_path) as document:
            if document.page_count == 0:
                raise HTTPException(status_code=400, detail="El PDF no contiene paginas.")
            first_page = document[0]
            return {
                "session_id": session_id,
                "page_count": document.page_count,
                "width": first_page.rect.width,
                "height": first_page.rect.height,
                "filename": payload.filename,
            }
    except HTTPException:
        cleanup_tree(session_path)
        raise
    except Exception as error:
        cleanup_tree(session_path)
        raise HTTPException(status_code=400, detail=f"No se pudo leer el PDF del proyecto: {error}") from error


@router.get("/{session_id}/page/{page_number}.png")
def render_page(session_id: str, page_number: int) -> FileResponse:
    session_path = session_dir(session_id)
    pdf_path = session_path / "source.pdf"
    image_path = session_path / f"page-{page_number}.png"
    if not image_path.exists():
        with fitz.open(pdf_path) as document:
            if page_number < 1 or page_number > document.page_count:
                raise HTTPException(status_code=404, detail="Pagina no encontrada.")
            page = document[page_number - 1]
            pixmap = page.get_pixmap(matrix=fitz.Matrix(1.6, 1.6), colorspace=fitz.csRGB, alpha=False)
            pixmap.save(image_path)
    return FileResponse(image_path, media_type="image/png")


@router.post("/export")
def export_redacted_pdf(payload: RedactionPayload) -> FileResponse:
    session_path = session_dir(payload.session_id)
    source_path = session_path / "source.pdf"
    output_path = session_path / "testado.pdf"
    rectangles: list[RectangleData] = []
    for index, raw in enumerate(payload.rectangles, start=1):
        rectangles.append(
            {
                "id": index,
                "order": index,
                "page": int(raw.get("page", 0)),
                "x1": float(raw["x1"]),
                "y1": float(raw["y1"]),
                "x2": float(raw["x2"]),
                "y2": float(raw["y2"]),
                "classification": str(raw.get("classification") or "general"),
                "concept_id": int(raw.get("concept_id") or 1),
                "concept_name": str(raw.get("concept_name") or ""),
                "legal_basis": str(raw.get("legal_basis") or ""),
                "reason": str(raw.get("reason") or ""),
                "label": str(raw.get("label") or f"#{index}"),
            }
        )
    RedactionPdfExporter(build_catalogue_categories()).export(
        str(source_path),
        str(output_path),
        rectangles,
        payload.committee_data or None,
    )
    return FileResponse(output_path, media_type="application/pdf", filename="testado.pdf")


@router.get("/help")
def help_content() -> JSONResponse:
    return JSONResponse(HELP_DIALOG)
