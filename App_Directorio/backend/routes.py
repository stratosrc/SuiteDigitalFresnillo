from __future__ import annotations

from fastapi import APIRouter, Body, HTTPException
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from App_Directorio.models import AreaReportData, DirectoryReportData, PersonReportRow
from App_Directorio.services.pdf_exporter import DirectoryPdfExporter
from App_Directorio.services.persistence import DirectoryPersistenceManager

from Main_View.backend.runtime import cleanup_tree, make_work_dir

from .schemas import DirectoryPayload

router = APIRouter(prefix="/api/directorio")


HELP_SECTIONS = [
    {
        "title": "1. ARCHIVO Y PROYECTO",
        "items": [
            "Para generar el reporte se va a Archivo y Exportar PDF.",
            "Para guardar el proyecto editable se va a Archivo y Guardar proyecto; se crea un archivo .dir.",
            "Para continuar un proyecto anterior se va a Archivo y Cargar proyecto.",
            "Para empezar un nuevo proyecto se va a Archivo y Nuevo.",
        ],
    },
    {
        "title": "2. DATOS GENERALES",
        "items": [
            "En Unidad Administrativa va el nombre del area administrativa correspondiente al directorio.",
            "En Periodo va el periodo correspondiente.",
            "En el nombre del area va la subdivision del area administrativa.",
        ],
    },
    {
        "title": "3. DATOS DEL COLABORADOR",
        "items": [
            "En Rango / Clave / Nivel va el codigo correspondiente del colaborador.",
            "En Nombre va el nombre del colaborador.",
            "En Cargo va el cargo del colaborador.",
            "En Correo electronico puede escribir solamente la primera parte; al salir del campo se agregara @fresnillo.gob.mx.",
            "En Fecha de Alta va la fecha en la que comenzo a ejercer su cargo el colaborador.",
        ],
    },
    {
        "title": "4. AREAS Y ORDEN",
        "items": [
            "El boton + Agregar Area permite crear una subdivision nueva.",
            "El icono verde + agrega una fila adicional de colaborador dentro de un area.",
            "El icono - elimina una fila de colaborador.",
            "El icono x elimina un area completa.",
            "Los numeros a la izquierda de areas y colaboradores se pueden editar para cambiar su posicion.",
            "La flecha situada a la izquierda del colaborador permite transferirlo a otra area.",
        ],
    },
    {
        "title": "ATAJOS DE TECLADO",
        "items": [
            "Ctrl+N: Crear un proyecto nuevo.",
            "Ctrl+O: Cargar un proyecto existente.",
            "Ctrl+S: Guardar el proyecto actual.",
            "Tab y Shift+Tab: Recorrer los campos y botones del formulario.",
        ],
    },
]


def _directory_to_dict(data: DirectoryReportData) -> dict:
    return {
        "title": data.title,
        "period": data.period,
        "areas": [
            {
                "name": area.name,
                "personnel": [
                    {
                        "rank": person.rank,
                        "name": person.name,
                        "position": person.position,
                        "email": person.email,
                        "start_date": person.start_date,
                    }
                    for person in area.personnel
                ],
            }
            for area in data.areas
        ],
    }


@router.get("/help")
def get_help() -> dict:
    return {"title": "Ayuda de Directorio", "sections": HELP_SECTIONS}


@router.post("/project/normalize")
def normalize_project(payload: dict = Body(...)) -> dict:
    try:
        if payload.get("app") == "directorio":
            raw_directory = payload.get("directory")
        else:
            raw_directory = payload.get("directory", payload)
        if not isinstance(raw_directory, dict):
            raise ValueError("El archivo seleccionado no parece ser un proyecto de Directorio.")
        data = DirectoryPersistenceManager().from_dict(raw_directory)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return {"directory": _directory_to_dict(data)}


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
