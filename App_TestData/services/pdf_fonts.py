"""Font helpers shared by TestData PDF exporters."""

from __future__ import annotations

import fitz

from components.styles.styles import PYMUPDF_FONT_REGULAR


PDF_FONT_REGULAR = PYMUPDF_FONT_REGULAR
_FITZ_FONT = None


def fitz_font_kwargs() -> dict[str, str]:
    return {"fontname": PDF_FONT_REGULAR}


def fitz_text_width(text: str, fontsize: float) -> float:
    global _FITZ_FONT

    if _FITZ_FONT is None:
        _FITZ_FONT = fitz.Font(fontname=PDF_FONT_REGULAR)

    return _FITZ_FONT.text_length(text, fontsize=fontsize)
