from __future__ import annotations

import json
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
import shutil

import fitz
from PIL import Image, ImageSequence

from App_ConversorPDF.config import IMAGE_EXTENSIONS, PDF_EXTENSIONS, SHEET_EXTENSIONS
from App_ConversorPDF.services.libreoffice import require_soffice_path
from App_ConversorPDF.services.process_control import run_cancellable_process
from App_ConversorPDF.services.spreadsheet_exporter import SpreadsheetPdfExporter
from components.shared.atomic_output import write_atomic_output


LIBREOFFICE_TIMEOUT_SECONDS = 180


@dataclass(frozen=True, slots=True)
class ConversionRequest:
    source_path: Path
    target_path: Path
    sheet_name: str | None = None


class PdfConverter:
    def __init__(self) -> None:
        self._spreadsheet_exporter = SpreadsheetPdfExporter()

    def convert(self, request: ConversionRequest, cancel_check=None) -> Path:
        self._validate_source(request.source_path)
        suffix = request.source_path.suffix.lower()
        target_path = self._prepare_target_path(request.target_path)
        return write_atomic_output(
            target_path,
            lambda temporary: self._convert_to_path(
                request,
                suffix,
                temporary,
                cancel_check,
            ),
            should_commit=lambda: cancel_check is None or not cancel_check(),
        )

    def _convert_to_path(
        self,
        request: ConversionRequest,
        suffix: str,
        target_path: Path,
        cancel_check=None,
    ) -> None:
        if suffix in IMAGE_EXTENSIONS:
            self._convert_image(request.source_path, target_path)
        elif suffix in PDF_EXTENSIONS:
            self._convert_pdf(request.source_path, target_path, request.sheet_name)
        elif suffix in SHEET_EXTENSIONS:
            self._convert_spreadsheet(
                request.source_path,
                target_path,
                request.sheet_name,
                cancel_check,
            )
        else:
            self._convert_office_document(
                request.source_path,
                target_path,
                request.sheet_name,
                cancel_check,
            )

    def _convert_spreadsheet(
        self,
        source_path: Path,
        target_path: Path,
        sheet_selection: str | None,
        cancel_check=None,
    ) -> Path:
        self._ensure_output_dir(target_path.parent)
        if cancel_check is None:
            return self._spreadsheet_exporter.export(
                source_path,
                target_path,
                sheet_selection,
            )
        return self._spreadsheet_exporter.export(
            source_path,
            target_path,
            sheet_selection,
            cancel_check=cancel_check,
        )

    def _convert_image(self, source_path: Path, target_path: Path) -> Path:
        try:
            with Image.open(source_path) as source:
                frames = []
                for frame in ImageSequence.Iterator(source):
                    image = frame.convert("RGB")
                    frames.append(image.copy())
        except PermissionError as error:
            raise PermissionError(f"No se pudo leer la imagen por permisos: {source_path}") from error

        if not frames:
            raise ValueError("No se pudo leer la imagen.")

        self._ensure_output_dir(target_path.parent)
        first, *rest = frames
        try:
            first.save(target_path, "PDF", save_all=bool(rest), append_images=rest)
        except PermissionError as error:
            raise PermissionError(f"No se pudo guardar el PDF por permisos: {target_path}") from error
        return target_path

    def _convert_pdf(self, source_path: Path, target_path: Path, page_range: str | None) -> Path:
        self._ensure_output_dir(target_path.parent)
        try:
            with fitz.open(source_path) as source_document:
                if len(source_document) == 0:
                    raise ValueError("El PDF no contiene paginas.")

                selected_pages = self._parse_pdf_page_range(page_range, len(source_document))
                output_document = fitz.open()
                try:
                    for page_index in selected_pages:
                        output_document.insert_pdf(source_document, from_page=page_index, to_page=page_index)
                    output_document.save(target_path)
                finally:
                    output_document.close()
        except fitz.FileDataError as error:
            raise ValueError(f"No se pudo leer el PDF: {source_path}") from error
        except PermissionError as error:
            raise PermissionError(f"No se pudo leer o guardar el PDF por permisos: {source_path}") from error
        return target_path

    def _convert_office_document(
        self,
        source_path: Path,
        target_path: Path,
        page_range: str | None,
        cancel_check=None,
    ) -> Path:
        soffice_path = require_soffice_path()
        self._ensure_output_dir(target_path.parent)

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            temp_output_dir = temp_root / "out"
            temp_profile_dir = temp_root / "profile"
            temp_output_dir.mkdir(parents=True, exist_ok=True)
            temp_profile_dir.mkdir(parents=True, exist_ok=True)

            command = [
                str(soffice_path),
                "--headless",
                "--nologo",
                "--nodefault",
                "--nolockcheck",
                "--nofirststartwizard",
                f"-env:UserInstallation={temp_profile_dir.as_uri()}",
                "--convert-to",
                self._pdf_filter_arg(source_path.suffix.lower(), page_range),
                "--outdir",
                str(temp_output_dir),
                str(source_path),
            ]
            completed = self._run_libreoffice(command, cancel_check)

            generated_path = temp_output_dir / f"{source_path.stem}.pdf"
            if not generated_path.exists():
                candidates = list(temp_output_dir.glob("*.pdf"))
                if not candidates:
                    details = self._format_process_output(completed.stdout, completed.stderr)
                    raise RuntimeError("LibreOffice termino, pero no genero ningun PDF." + details)
                generated_path = candidates[0]

            try:
                shutil.copyfile(generated_path, target_path)
            except PermissionError as error:
                raise PermissionError(f"No se pudo guardar el PDF por permisos: {target_path}") from error
            return target_path

    def _pdf_filter_arg(self, suffix: str, page_range: str | None) -> str:
        filter_name = self._pdf_filter_name(suffix)
        if page_range is None or not page_range.strip():
            return f"pdf:{filter_name}"

        options = {
            "PageRange": {
                "type": "string",
                "value": page_range.strip(),
            }
        }
        return f"pdf:{filter_name}:{json.dumps(options, separators=(',', ':'))}"

    def _pdf_filter_name(self, suffix: str) -> str:
        if suffix in {".doc", ".docx", ".rtf", ".odt"}:
            return "writer_pdf_Export"
        if suffix in {".ppt", ".pptx", ".odp"}:
            return "impress_pdf_Export"
        return "writer_pdf_Export"

    def _parse_pdf_page_range(self, raw_range: str | None, total_pages: int) -> list[int]:
        if raw_range is None or not raw_range.strip():
            return list(range(total_pages))

        selected_pages: list[int] = []
        parts = [part.strip() for part in raw_range.replace(";", ",").split(",")]
        for part in parts:
            if not part:
                continue
            if "-" not in part:
                selected_pages.append(self._parse_pdf_page_number(part, total_pages))
                continue

            start, end, *extra = [value.strip() for value in part.split("-")]
            if extra:
                raise ValueError(f"Rango de paginas invalido: {part}")
            start_number = self._parse_pdf_page_number(start, total_pages)
            end_number = self._parse_pdf_page_number(end, total_pages)
            if start_number > end_number:
                raise ValueError(f"Rango de paginas invalido: {part}")
            selected_pages.extend(range(start_number, end_number + 1))

        if not selected_pages:
            return list(range(total_pages))
        return selected_pages

    def _parse_pdf_page_number(self, raw_value: str, total_pages: int) -> int:
        if not raw_value.isdigit():
            raise ValueError(f"Pagina invalida: {raw_value}")
        page_number = int(raw_value)
        if page_number < 1 or page_number > total_pages:
            raise ValueError(f"La pagina {page_number} esta fuera del rango 1-{total_pages}.")
        return page_number - 1

    def _run_libreoffice(
        self,
        command: list[str],
        cancel_check=None,
    ) -> subprocess.CompletedProcess[str]:
        completed = run_cancellable_process(
            command,
            timeout_seconds=LIBREOFFICE_TIMEOUT_SECONDS,
            cancel_check=cancel_check,
        )
        if completed.returncode != 0:
            details = self._format_process_output(completed.stdout, completed.stderr)
            raise RuntimeError(f"LibreOffice fallo con codigo {completed.returncode}." + details)
        return completed

    def _validate_source(self, source_path: Path) -> None:
        if not source_path.exists():
            raise FileNotFoundError(f"El archivo de entrada no existe: {source_path}")
        if not source_path.is_file():
            raise ValueError(f"La ruta de entrada no es un archivo: {source_path}")

    def _prepare_target_path(self, target_path: Path) -> Path:
        if target_path.suffix.lower() != ".pdf":
            target_path = target_path.with_suffix(".pdf")
        self._ensure_output_dir(target_path.parent)
        return self._unique_pdf_path(target_path)

    def _ensure_output_dir(self, output_dir: Path) -> None:
        if output_dir.exists() and not output_dir.is_dir():
            raise NotADirectoryError(f"La carpeta de salida no es valida: {output_dir}")
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError as error:
            raise PermissionError(f"No se pudo crear o escribir en la carpeta de salida: {output_dir}") from error

    def _unique_pdf_path(self, target_path: Path) -> Path:
        if not target_path.exists():
            return target_path

        stem = target_path.stem
        suffix = target_path.suffix
        parent = target_path.parent
        counter = 1
        while True:
            candidate = parent / f"{stem} ({counter}){suffix}"
            if not candidate.exists():
                return candidate
            counter += 1

    def _format_process_output(self, stdout: str | None, stderr: str | None) -> str:
        parts = []
        if stderr and stderr.strip():
            parts.append(f"Error: {stderr.strip()}")
        if stdout and stdout.strip():
            parts.append(f"Salida: {stdout.strip()}")
        if not parts:
            return " LibreOffice no devolvio detalles adicionales."
        return " " + " ".join(parts)
