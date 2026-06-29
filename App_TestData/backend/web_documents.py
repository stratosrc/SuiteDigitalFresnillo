from __future__ import annotations

import base64
import shutil
from pathlib import Path
from uuid import uuid4

import fitz
from fastapi import HTTPException, UploadFile

from App_TestData.data.catalogue_data import build_catalogue_categories
from App_TestData.domain.document_state import RectangleData
from App_TestData.domain.redaction_editing import delete_selected_rectangle
from App_TestData.domain.redaction_numbering import assign_redaction_numbers
from App_TestData.services.redaction_exporter import RedactionPdfExporter

from Main_View.backend.config import RUNTIME_DIR
from Main_View.backend.runtime import cleanup_tree, session_dir


def upload_pdf_file(pdf: UploadFile) -> dict[str, object]:
    if not pdf.filename or not pdf.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Selecciona un archivo PDF.")
    session_path = _new_session_path()
    pdf_path = session_path / "source.pdf"
    with pdf_path.open("wb") as handle:
        shutil.copyfileobj(pdf.file, handle)
    return _read_pdf_session(session_path, pdf_path)


def upload_pdf_base64(filename: str, data: str) -> dict[str, object]:
    raw_data = data.split(",", 1)[1] if "," in data else data
    try:
        pdf_bytes = base64.b64decode(raw_data, validate=True)
    except ValueError as error:
        raise HTTPException(status_code=400, detail="El PDF del proyecto no tiene un formato valido.") from error

    session_path = _new_session_path()
    pdf_path = session_path / "source.pdf"
    pdf_path.write_bytes(pdf_bytes)
    payload = _read_pdf_session(session_path, pdf_path)
    payload["filename"] = filename
    return payload


def render_page_image(session_id: str, page_number: int) -> Path:
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
    return image_path


def normalize_rectangles(rectangles: list[dict]) -> list[RectangleData]:
    return assign_redaction_numbers(rectangles)


def remove_rectangle(rectangles: list[dict], selected_rect_id: str | int | None) -> list[RectangleData]:
    remaining_rectangles, *_ = delete_selected_rectangle(rectangles, selected_rect_id)
    return normalize_rectangles(remaining_rectangles)


def export_redacted_pdf(session_id: str, raw_rectangles: list[dict], committee_data: dict[str, str]) -> Path:
    session_path = session_dir(session_id)
    source_path = session_path / "source.pdf"
    output_path = session_path / "testado.pdf"
    rectangles = rectangles_for_export(raw_rectangles)
    RedactionPdfExporter(build_catalogue_categories()).export(
        str(source_path),
        str(output_path),
        rectangles,
        committee_data or None,
    )
    return output_path


def rectangles_for_export(raw_rectangles: list[dict]) -> list[RectangleData]:
    rectangles: list[RectangleData] = []
    for index, raw in enumerate(raw_rectangles, start=1):
        rectangles.append(
            {
                "id": index,
                "order": int(raw.get("order") or index),
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
                "rows": int(raw.get("rows") or 1),
                "paragraphs": int(raw.get("paragraphs") or 1),
                "object": str(raw.get("object") or ""),
                "articles": str(raw.get("articles") or ""),
                "law": str(raw.get("law") or ""),
                "label": str(raw.get("label") or f"#{index}"),
            }
        )
    return rectangles


def _new_session_path() -> Path:
    session_id = uuid4().hex
    session_path = RUNTIME_DIR / session_id
    session_path.mkdir(parents=True, exist_ok=True)
    return session_path


def _read_pdf_session(session_path: Path, pdf_path: Path) -> dict[str, object]:
    try:
        with fitz.open(pdf_path) as document:
            if document.page_count == 0:
                raise HTTPException(status_code=400, detail="El PDF no contiene paginas.")
            first_page = document[0]
            return {
                "session_id": session_path.name,
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
