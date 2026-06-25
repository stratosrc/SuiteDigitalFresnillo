"""PDF merge service."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path

import fitz

from components.shared.atomic_output import OutputCancelled, write_atomic_output


class PdfMerger:
    def merge(
        self,
        source_paths: Sequence[Path],
        target_path: Path,
        cancel_check: Callable[[], bool] | None = None,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> Path:
        sources = [Path(path) for path in source_paths]
        if len(sources) < 2:
            raise ValueError("Selecciona al menos dos archivos PDF para unir.")

        for source in sources:
            if not source.is_file():
                raise FileNotFoundError(f"El archivo no existe: {source}")
            if source.suffix.lower() != ".pdf":
                raise ValueError(f"El archivo no es un PDF: {source.name}")

        target = target_path if target_path.suffix.lower() == ".pdf" else target_path.with_suffix(".pdf")
        return write_atomic_output(
            target,
            lambda temporary: self._write_merged_pdf(
                sources,
                temporary,
                cancel_check,
                progress_callback,
            ),
            should_commit=lambda: cancel_check is None or not cancel_check(),
        )

    @staticmethod
    def _write_merged_pdf(
        sources: Sequence[Path],
        target_path: Path,
        cancel_check: Callable[[], bool] | None,
        progress_callback: Callable[[int, int], None] | None,
    ) -> None:
        output = fitz.open()
        try:
            for index, source_path in enumerate(sources, start=1):
                if cancel_check is not None and cancel_check():
                    raise OutputCancelled("La unión fue cancelada.")
                if progress_callback is not None:
                    progress_callback(index, len(sources))
                try:
                    with fitz.open(source_path) as source:
                        if len(source) == 0:
                            raise ValueError(f"El PDF no contiene páginas: {source_path.name}")
                        output.insert_pdf(source)
                except fitz.FileDataError as error:
                    raise ValueError(f"No se pudo leer el PDF: {source_path.name}") from error

            if len(output) == 0:
                raise ValueError("Los archivos seleccionados no contienen páginas.")
            output.save(target_path)
        finally:
            output.close()


__all__ = ["PdfMerger"]
