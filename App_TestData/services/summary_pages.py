"""Legal summary pages for TestData PDF export."""

from __future__ import annotations

import os
from typing import Mapping

import fitz

from App_TestData.config.settings import (
    PDF_SUMMARY_PAGE_LINE_HEIGHT,
    PDF_SUMMARY_PAGE_MARGIN_X,
    PDF_SUMMARY_PAGE_TITLE_HEIGHT,
    PDF_WATERMARK_LOGO_PATH,
)
from App_TestData.domain.document_state import RectangleData
from App_TestData.services.pdf_fonts import fitz_font_kwargs, fitz_text_width


class SummaryPagesWriter:
    def __init__(self, concept_categories: Mapping[int, str]) -> None:
        self._concept_categories = concept_categories

    def append(self, document: fitz.Document, ordered_rectangles: list[RectangleData]) -> None:
        margin_x = PDF_SUMMARY_PAGE_MARGIN_X
        y_position = 50
        max_y = 750
        line_height = PDF_SUMMARY_PAGE_LINE_HEIGHT
        title_height = PDF_SUMMARY_PAGE_TITLE_HEIGHT

        page = self._create_page(document, margin_x, y_position)
        y_position += title_height

        for rect_data in ordered_rectangles:
            summary_label = rect_data.get("final_number", rect_data.get("label", ""))
            line = self.build_summary_line(summary_label, rect_data)
            required_height = self._measure_line_height(page, line, margin_x, line_height)
            if y_position + required_height > max_y:
                page = self._create_page(document, margin_x, 50, continuation=True)
                y_position = 50 + title_height

            y_position = self._write_line(page, line, margin_x, y_position, required_height)

    def build_summary_line(self, summary_label, rect_data):
        classification = rect_data.get("classification", "general")
        if classification == "reserved":
            return self._build_reserved_summary_line(summary_label, rect_data)
        if classification == "confidential":
            return self._build_confidential_summary_line(summary_label, rect_data)
        if classification == "other_law":
            return self._build_other_law_summary_line(summary_label, rect_data)

        concept_name = rect_data.get("concept_name", rect_data.get("label", ""))
        rows = rect_data.get("rows", 1)
        paragraphs = rect_data.get("paragraphs", 1)
        article_reference = self._legal_reference_for_concept(rect_data.get("concept_id"))

        return (
            f"{summary_label} {concept_name} eliminado por ser un dato personal de conformidad con "
            f"el {article_reference} de la Ley de proteccion de datos personales en posesion de sujetos obligados "
            f"del Estado de Zacatecas ({paragraphs} parrafo{'s' if paragraphs != 1 else ''} "
            f"{rows} renglon{'es' if rows != 1 else ''})."
        )

    def _create_page(self, document, margin_x, y_position, continuation=False):
        page = document.new_page()
        apply_watermark(page)
        title = (
            "Fundamentos de la Ley de Transparencia y Acceso a la Informacion Publica \n"
            "del Estado de Zacatecas (continuacion)"
            if continuation
            else "Fundamentos de la Ley de Transparencia y Acceso a la Informacion Publica \n"
            "del Estado de Zacatecas"
        )
        page.insert_text(
            (margin_x, y_position),
            title,
            fontsize=16,
            color=(0, 0, 0),
            **fitz_font_kwargs(),
        )
        return page

    def _measure_line_height(self, page, line, margin_x, line_height):
        page_width = page.rect.width
        available_width = page_width - (margin_x * 2)
        words = line.split()
        lines = 1
        current_line = ""
        for word in words:
            candidate = f"{current_line} {word}".strip()
            if current_line and fitz_text_width(candidate, 10) > available_width:
                lines += 1
                current_line = word
            else:
                current_line = candidate
        return max(line_height, lines * 13) + 10

    def _write_line(self, page, line, margin_x, y_position, paragraph_height):
        page_width = page.rect.width
        available_width = page_width - (margin_x * 2)
        text_rect = fitz.Rect(margin_x, y_position, margin_x + available_width, y_position + paragraph_height)
        page.insert_textbox(text_rect, line, fontsize=10, color=(0, 0, 0), align=0, **fitz_font_kwargs())
        return y_position + paragraph_height

    def _build_reserved_summary_line(self, summary_label, rect_data):
        return (
            f"{summary_label}: El {rect_data.get('reason', '')}, {rect_data.get('paragraphs', 1)} parrafos y "
            f"{rect_data.get('rows', 1)} renglones por ser considerado como informacion reservada "
            f"de conformidad con los articulos 99, 100 y 101 de la Ley de Transparencia y Acceso "
            f"a la Informacion Publica del Estado de Zacatecas y los lineamientos generales en "
            f"materia de clasificacion y desclasificacion de la informacion, asi como para la "
            f"elaboracion de versiones publicas {rect_data.get('legal_basis', '')}."
        )

    def _build_confidential_summary_line(self, summary_label, rect_data):
        return (
            f"{summary_label}: {rect_data.get('reason', '')}, {rect_data.get('paragraphs', 1)} parrafos y "
            f"{rect_data.get('rows', 1)} renglones por ser considerado como informacion confidencial "
            f"de conformidad con los articulos 102, 103, 104, 105 y 106 de la Ley de Transparencia "
            f"y Acceso a la Informacion Publica del Estado de Zacatecas y con {rect_data.get('legal_basis', '')}."
        )

    def _build_other_law_summary_line(self, summary_label, rect_data):
        return (
            f"{summary_label}: Eliminado {rect_data.get('object', '')} en base a "
            f"{rect_data.get('articles', '')} de la {rect_data.get('law', '')} "
            f"({rect_data.get('paragraphs', 1)} parrafo"
            f"{'s' if rect_data.get('paragraphs', 1) != 1 else ''} "
            f"{rect_data.get('rows', 1)} renglon"
            f"{'es' if rect_data.get('rows', 1) != 1 else ''})."
        )

    def _legal_reference_for_concept(self, concept_id):
        category = self._concept_categories.get(concept_id, "normal")
        if category == "sensitive":
            return "articulo 3, seccion X, inciso a"
        if category == "biometric":
            return "articulo 3, seccion X, inciso b"
        return "articulo 3, seccion X"


def apply_watermark(page):
    if not os.path.exists(PDF_WATERMARK_LOGO_PATH):
        return

    page_width = page.rect.width
    page_height = page.rect.height
    watermark_width = 788
    watermark_height = 1050
    reportlab_x = (page_width / 2) - 200
    reportlab_y = (page_height / 2) - 800
    x0 = reportlab_x
    y0 = page_height - reportlab_y - watermark_height
    watermark_rect = fitz.Rect(x0, y0, x0 + watermark_width, y0 + watermark_height)
    page.insert_image(watermark_rect, filename=PDF_WATERMARK_LOGO_PATH, overlay=False)
