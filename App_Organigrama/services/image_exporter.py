from pathlib import Path

import fitz


def export_pdf_as_image(pdf_path: str | Path, output_image_path: str | Path, dpi: int = 300) -> Path:
    source = Path(pdf_path)
    target = Path(output_image_path)
    if not source.exists():
        raise FileNotFoundError(f"No existe el PDF de origen: {source}")

    target.parent.mkdir(parents=True, exist_ok=True)
    zoom = dpi / 72
    matrix = fitz.Matrix(zoom, zoom)

    with fitz.open(source) as pdf_document:
        if pdf_document.page_count == 0:
            raise ValueError("El PDF no contiene páginas para exportar.")

        page = pdf_document[0]
        pixmap = page.get_pixmap(matrix=matrix, alpha=False)
        pixmap.save(target)

    return target
