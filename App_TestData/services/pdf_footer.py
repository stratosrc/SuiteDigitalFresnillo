"""Institutional footer applied to every exported PDF page."""

from __future__ import annotations

import fitz

from App_TestData.services.pdf_fonts import fitz_font_kwargs


FOOTER_TEXT = (
    "© 2026 H. Ayuntamiento de Fresnillo, Zacatecas, México. Administración 2024-2027 "
    "Todos los derechos reservados."
)

FOOTER_FONT_SIZE = 5
FOOTER_HEIGHT = 24
FOOTER_MARGIN_X = 18
FOOTER_MARGIN_BOTTOM = 8
FOOTER_PADDING = 2


def add_institutional_footer(document: fitz.Document, start_page: int = 0) -> None:
    """Draw the institutional notice on pages added from ``start_page`` onward."""
    for page_number in range(start_page, document.page_count):
        page = document[page_number]
        footer_rect = fitz.Rect(
            FOOTER_MARGIN_X,
            max(0, page.rect.height - FOOTER_HEIGHT),
            page.rect.width - FOOTER_MARGIN_X,
            page.rect.height - FOOTER_MARGIN_BOTTOM,
        )
        text_rect = fitz.Rect(
            footer_rect.x0 + FOOTER_PADDING,
            footer_rect.y0 + FOOTER_PADDING,
            footer_rect.x1 - FOOTER_PADDING,
            footer_rect.y1 - FOOTER_PADDING,
        )
        page.insert_textbox(
            text_rect,
            FOOTER_TEXT,
            fontsize=FOOTER_FONT_SIZE,
            color=(0, 0, 0),
            align=fitz.TEXT_ALIGN_JUSTIFY,
            lineheight=1.05,
            overlay=True,
            **fitz_font_kwargs(),
        )
