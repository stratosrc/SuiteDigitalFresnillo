"""Font helpers shared by TestData PDF exporters."""

from __future__ import annotations

import os

import fitz

from components.styles.styles import SEGOE_UI_FONT_FILE


PDF_FONT_REGULAR = "SegoeUI"
_SEGOE_FITZ_FONT = None


def fitz_font_kwargs() -> dict[str, str]:
    if os.path.exists(SEGOE_UI_FONT_FILE):
        return {"fontname": PDF_FONT_REGULAR, "fontfile": SEGOE_UI_FONT_FILE}
    return {}


def fitz_text_width(text: str, fontsize: float) -> float:
    global _SEGOE_FITZ_FONT

    if os.path.exists(SEGOE_UI_FONT_FILE):
        if _SEGOE_FITZ_FONT is None:
            _SEGOE_FITZ_FONT = fitz.Font(fontfile=SEGOE_UI_FONT_FILE)
        return _SEGOE_FITZ_FONT.text_length(text, fontsize=fontsize)

    return max(len(text), 1) * fontsize * 0.52
