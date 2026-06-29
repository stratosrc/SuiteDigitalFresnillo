from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import FileResponse

from ..config import INDEX_FILE

router = APIRouter()


@router.get("/")
def home() -> FileResponse:
    return FileResponse(INDEX_FILE)


@router.get("/testdata")
def testdata() -> FileResponse:
    return FileResponse(INDEX_FILE)


@router.get("/organigrama")
def organigrama() -> FileResponse:
    return FileResponse(INDEX_FILE)


@router.get("/directorio")
def directorio() -> FileResponse:
    return FileResponse(INDEX_FILE)


@router.get("/conversor-pdf")
def conversor_pdf() -> FileResponse:
    return FileResponse(INDEX_FILE)
