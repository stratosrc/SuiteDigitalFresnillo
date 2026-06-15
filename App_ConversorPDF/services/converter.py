from __future__ import annotations

import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageSequence

from App_ConversorPDF.config import IMAGE_EXTENSIONS


@dataclass(frozen=True, slots=True)
class ConversionRequest:
    source_path: Path
    target_path: Path
    sheet_name: str | None = None


class PdfConverter:
    def convert(self, request: ConversionRequest) -> Path:
        suffix = request.source_path.suffix.lower()
        if suffix in IMAGE_EXTENSIONS:
            return self._convert_image(request.source_path, request.target_path)
        return self._convert_office_document(request.source_path, request.target_path)

    def _convert_image(self, source_path: Path, target_path: Path) -> Path:
        with Image.open(source_path) as source:
            frames = []
            for frame in ImageSequence.Iterator(source):
                image = frame.convert("RGB")
                frames.append(image.copy())

        if not frames:
            raise ValueError("No se pudo leer la imagen.")

        target_path.parent.mkdir(parents=True, exist_ok=True)
        first, *rest = frames
        first.save(target_path, "PDF", save_all=bool(rest), append_images=rest)
        return target_path

    def _convert_office_document(self, source_path: Path, target_path: Path) -> Path:
        soffice_path = shutil.which("soffice") or shutil.which("libreoffice")
        if soffice_path is None:
            raise RuntimeError(
                "Para convertir documentos de Office se requiere LibreOffice instalado "
                "y disponible como 'soffice' o 'libreoffice'."
            )

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_output_dir = Path(temp_dir)
            completed = subprocess.run(
                [
                    soffice_path,
                    "--headless",
                    "--convert-to",
                    "pdf",
                    "--outdir",
                    str(temp_output_dir),
                    str(source_path),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            if completed.returncode != 0:
                message = (completed.stderr or completed.stdout or "Conversion fallida.").strip()
                raise RuntimeError(message)

            generated_path = temp_output_dir / f"{source_path.stem}.pdf"
            if not generated_path.exists():
                candidates = list(temp_output_dir.glob("*.pdf"))
                if not candidates:
                    raise RuntimeError("LibreOffice no genero ningun PDF.")
                generated_path = candidates[0]

            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(generated_path, target_path)
            return target_path
