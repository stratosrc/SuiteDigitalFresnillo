from __future__ import annotations

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import FileResponse, JSONResponse

from App_TestData.config.ui_strings import HELP_DIALOG

from .schemas import DeleteRectanglePayload, PdfBase64Payload, RedactionPayload
from .web_documents import (
    export_redacted_pdf,
    normalize_rectangles,
    remove_rectangle,
    render_page_image,
    upload_pdf_base64,
    upload_pdf_file,
)

router = APIRouter(prefix="/api/testdata")


@router.post("/upload")
def upload_pdf(pdf: UploadFile = File(...)) -> dict[str, object]:
    return upload_pdf_file(pdf)


@router.post("/upload-base64")
def upload_project_pdf(payload: PdfBase64Payload) -> dict[str, object]:
    return upload_pdf_base64(payload.filename, payload.data)


@router.get("/{session_id}/page/{page_number}.png")
def render_page(session_id: str, page_number: int) -> FileResponse:
    return FileResponse(render_page_image(session_id, page_number), media_type="image/png")


@router.post("/export")
def export_pdf(payload: RedactionPayload) -> FileResponse:
    output_path = export_redacted_pdf(payload.session_id, payload.rectangles, payload.committee_data)
    return FileResponse(output_path, media_type="application/pdf", filename="testado.pdf")


@router.post("/rectangles/normalize")
def normalize_rectangle_payload(payload: RedactionPayload) -> dict[str, object]:
    return {"rectangles": normalize_rectangles(payload.rectangles)}


@router.post("/rectangles/delete")
def delete_rectangle_payload(payload: DeleteRectanglePayload) -> dict[str, object]:
    return {"rectangles": remove_rectangle(payload.rectangles, payload.selected_rect_id)}


@router.get("/help")
def help_content() -> JSONResponse:
    return JSONResponse(HELP_DIALOG)
