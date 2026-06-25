"""Portable persistence for in-progress Test Data jobs."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
import shutil
import tempfile
from typing import Any
import zipfile

from App_TestData.domain.document_state import DocumentState, RectangleData


PROJECT_APP_ID = "testdata"
LEGACY_PROJECT_VERSION = 1
PROJECT_VERSION = 2
PROJECT_METADATA_NAME = "project.json"
EMBEDDED_PDF_NAME = "source.pdf"
_TRANSIENT_RECTANGLE_FIELDS = {"canvas_rect_id", "canvas_text_id", "rect"}


@dataclass(slots=True)
class LoadedProject:
    """Loaded metadata and its ready-to-open PDF source."""

    payload: dict[str, Any]
    pdf_path: Path
    _temporary_directory: tempfile.TemporaryDirectory[str] | None = None

    def close(self) -> None:
        """Delete an extracted embedded PDF, when one is in use."""
        if self._temporary_directory is not None:
            self._temporary_directory.cleanup()
            self._temporary_directory = None


def calculate_file_hash(file_path: str | Path) -> str:
    """Calculate a SHA-256 digest without loading the full file into memory."""
    digest = hashlib.sha256()
    with Path(file_path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def save_project(state: DocumentState, target_path: str | Path) -> Path:
    """Save project metadata and the original PDF in one portable `.td` file."""
    source_pdf = _require_source_pdf(state)
    target = Path(target_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = _build_payload(state, source_pdf)

    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            suffix=".td.tmp",
            prefix=f".{target.stem}-",
            dir=target.parent,
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)

        with zipfile.ZipFile(
            temporary_path,
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=6,
        ) as archive:
            archive.writestr(
                PROJECT_METADATA_NAME,
                json.dumps(payload, ensure_ascii=False, indent=2),
            )
            archive.write(source_pdf, EMBEDDED_PDF_NAME)

        temporary_path.replace(target)
    except (OSError, zipfile.BadZipFile):
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        raise
    return target


def load_project(source_path: str | Path) -> LoadedProject:
    """Load a portable container or a legacy JSON project."""
    source = Path(source_path)
    if zipfile.is_zipfile(source):
        return _load_portable_project(source)
    return _load_legacy_project(source)


def deserialize_rectangles(items: list[dict[str, Any]]) -> list[RectangleData]:
    """Restore rectangle dictionaries with empty canvas references."""
    rectangles: list[RectangleData] = []
    for item in items:
        rectangle = dict(item)
        rectangle["canvas_rect_id"] = None
        rectangle["canvas_text_id"] = None
        rectangles.append(rectangle)
    return rectangles


def _require_source_pdf(state: DocumentState) -> Path:
    if not state.current_pdf_path:
        raise ValueError("No hay un PDF cargado para guardar en el proyecto.")
    source_pdf = Path(state.current_pdf_path)
    if not source_pdf.is_file():
        raise FileNotFoundError(f"No se encontró el PDF original: {source_pdf}")
    return source_pdf


def _build_payload(state: DocumentState, source_pdf: Path) -> dict[str, Any]:
    return {
        "app": PROJECT_APP_ID,
        "version": PROJECT_VERSION,
        "pdf_name": source_pdf.name,
        "pdf_sha256": calculate_file_hash(source_pdf),
        "current_page": state.current_page,
        "current_zoom": state.current_zoom,
        "rectangles": [_serialize_rectangle(rectangle) for rectangle in state.censored_rectangles],
        "reserved_history": list(state.reserved_history),
        "confidential_history": list(state.confidential_history),
        "other_law_history": list(state.other_law_history),
        "committee_data": dict(state.committee_data),
    }


def _load_portable_project(source: Path) -> LoadedProject:
    temporary_directory: tempfile.TemporaryDirectory[str] | None = None
    try:
        with zipfile.ZipFile(source, mode="r") as archive:
            names = set(archive.namelist())
            missing = {PROJECT_METADATA_NAME, EMBEDDED_PDF_NAME} - names
            if missing:
                raise ValueError("El proyecto portátil está incompleto.")

            payload = json.loads(archive.read(PROJECT_METADATA_NAME).decode("utf-8"))
            _validate_payload(payload, expected_version=PROJECT_VERSION)

            temporary_directory = tempfile.TemporaryDirectory(prefix="testdata-project-")
            pdf_name = Path(str(payload.get("pdf_name") or EMBEDDED_PDF_NAME)).name
            extracted_pdf = Path(temporary_directory.name) / pdf_name
            with archive.open(EMBEDDED_PDF_NAME) as source_pdf, extracted_pdf.open("wb") as target_pdf:
                shutil.copyfileobj(source_pdf, target_pdf, length=1024 * 1024)

        expected_hash = str(payload.get("pdf_sha256", ""))
        if expected_hash and calculate_file_hash(extracted_pdf) != expected_hash:
            raise ValueError("El PDF incrustado está dañado o fue modificado.")
        return LoadedProject(payload, extracted_pdf, temporary_directory)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, zipfile.BadZipFile) as error:
        if temporary_directory is not None:
            temporary_directory.cleanup()
        raise ValueError("No se pudo leer el proyecto portátil de TestData.") from error
    except Exception:
        if temporary_directory is not None:
            temporary_directory.cleanup()
        raise


def _load_legacy_project(source: Path) -> LoadedProject:
    try:
        payload = json.loads(source.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("No se pudo leer el proyecto de TestData.") from error

    _validate_payload(payload, expected_version=LEGACY_PROJECT_VERSION)
    raw_pdf_path = payload.get("pdf_path")
    if not raw_pdf_path:
        raise FileNotFoundError("El proyecto anterior no contiene la ruta del PDF original.")
    pdf_path = Path(str(raw_pdf_path))
    if not pdf_path.is_file():
        raise FileNotFoundError(f"No se encontró el PDF original: {pdf_path}")

    expected_hash = str(payload.get("pdf_sha256", ""))
    payload["pdf_hash_matches"] = (
        not expected_hash or calculate_file_hash(pdf_path) == expected_hash
    )
    return LoadedProject(payload, pdf_path)


def _validate_payload(payload: Any, *, expected_version: int) -> None:
    if not isinstance(payload, dict):
        raise ValueError("El archivo no contiene un proyecto válido de TestData.")
    if payload.get("app", PROJECT_APP_ID) != PROJECT_APP_ID:
        raise ValueError("Este archivo no es un proyecto de TestData.")
    if payload.get("version") != expected_version:
        raise ValueError("Versión de proyecto no compatible.")


def _serialize_rectangle(rectangle: RectangleData) -> dict[str, Any]:
    return {
        key: value
        for key, value in rectangle.items()
        if key not in _TRANSIENT_RECTANGLE_FIELDS
    }


__all__ = [
    "LoadedProject",
    "calculate_file_hash",
    "deserialize_rectangles",
    "load_project",
    "save_project",
]
