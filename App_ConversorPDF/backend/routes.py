from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from starlette.background import BackgroundTask

from App_ConversorPDF.services.converter import ConversionRequest, PdfConverter
from App_ConversorPDF.services.output_planner import build_output_plan
from App_ConversorPDF.services.pdf_merger import PdfMerger

from Main_View.backend.runtime import cleanup_tree, make_work_dir

router = APIRouter(prefix="/api/conversor")


class PlanItemRequest(BaseModel):
    id: str
    filename: str
    selection: str = ""
    split: bool = False


class PlanRequest(BaseModel):
    items: list[PlanItemRequest]


@dataclass(frozen=True, slots=True)
class StaticTextValue:
    value: str

    def get(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class StaticBooleanValue:
    value: bool

    def get(self) -> bool:
        return self.value


@dataclass(frozen=True, slots=True)
class WebPlanSourceItem:
    client_id: str
    path: Path
    sheet_var: StaticTextValue
    split_var: StaticBooleanValue

HELP_SECTIONS = [
    {
        "title": "1. MENU DE HERRAMIENTAS",
        "items": [
            "Convertir a PDF transforma imagenes, PDFs y documentos compatibles en archivos PDF.",
            "Unir PDFs permite ordenar varios PDFs y combinarlos en un solo archivo.",
            "El boton Nuevo limpia los archivos de la herramienta abierta.",
        ],
    },
    {
        "title": "2. CONVERTIR A PDF",
        "items": [
            "Carga archivos con clic o arrastrandolos al panel izquierdo.",
            "En PDFs y documentos puedes escribir paginas como 1, 2-4 o 1,3-5.",
            "En hojas de calculo, la seleccion corresponde a hojas o pestañas del libro.",
            "Deja la seleccion vacia para convertir todo el archivo.",
        ],
    },
    {
        "title": "3. UNIR PDFS",
        "items": [
            "Carga al menos dos archivos PDF.",
            "Arrastra los elementos para cambiar el orden.",
            "El PDF final se une de arriba hacia abajo.",
            "Usa Unir y guardar para descargar el resultado.",
        ],
    },
]


@router.get("/help")
def get_help() -> dict:
    return {"title": "Ayuda del Conversor", "heading": "Guia de uso", "sections": HELP_SECTIONS}


@router.post("/plan")
def get_output_plan(request: PlanRequest) -> dict:
    sources = [
        WebPlanSourceItem(
            client_id=item.id,
            path=Path(Path(item.filename).name),
            sheet_var=StaticTextValue(item.selection),
            split_var=StaticBooleanValue(item.split),
        )
        for item in request.items
        if item.filename
    ]
    outputs = []
    for index, planned in enumerate(build_output_plan(sources), start=1):
        outputs.append(
            {
                "id": f"{planned.source.client_id}-{index}",
                "sourceId": planned.source.client_id,
                "selection": planned.selection,
                "filename": planned.filename,
            }
        )
    return {"outputs": outputs}


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


@router.post("/unir")
def merge_pdfs(files: list[UploadFile] = File(...)) -> FileResponse:
    if len(files) < 2:
        raise HTTPException(status_code=400, detail="Selecciona al menos dos archivos PDF para unir.")

    work_dir = make_work_dir("suite-conversor-merge-")
    source_paths: list[Path] = []
    try:
        for index, uploaded_file in enumerate(files, start=1):
            if not uploaded_file.filename:
                raise ValueError("Todos los archivos deben tener nombre.")
            source_name = Path(uploaded_file.filename).name
            if Path(source_name).suffix.lower() != ".pdf":
                raise ValueError(f"El archivo no es un PDF: {source_name}")
            source_path = work_dir / f"{index:03d}-{source_name}"
            with source_path.open("wb") as handle:
                shutil.copyfileobj(uploaded_file.file, handle)
            source_paths.append(source_path)

        output_path = work_dir / "pdfs_unidos.pdf"
        result_path = PdfMerger().merge(source_paths, output_path)
    except Exception as error:
        cleanup_tree(work_dir)
        raise HTTPException(status_code=400, detail=str(error)) from error

    return FileResponse(
        result_path,
        media_type="application/pdf",
        filename=result_path.name,
        background=BackgroundTask(cleanup_tree, work_dir),
    )
