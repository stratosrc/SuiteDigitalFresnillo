"""Committee cover page for TestData PDF export."""

from __future__ import annotations

import fitz

from App_TestData.domain.document_state import CommitteeData, RectangleData
from App_TestData.services.pdf_fonts import fitz_font_kwargs
from App_TestData.services.summary_pages import apply_watermark


class CommitteeCoverWriter:
    def append(
        self,
        document: fitz.Document,
        committee_data: CommitteeData,
        ordered_rectangles: list[RectangleData],
    ) -> None:
        page = document.new_page()
        apply_watermark(page)
        margin_x = 36
        y_position = 40
        left_width = 190
        right_width = page.rect.width - (margin_x * 2) - left_width
        x_left = margin_x
        x_right = margin_x + left_width

        reserved_items = self._joined_reason_items(ordered_rectangles, "reserved")
        confidential_items = self._joined_reason_items(ordered_rectangles, "confidential")
        suppressed_text = (
            f"Datos reservados: {reserved_items}\n"
            f"Datos confidenciales: {confidential_items}"
        )

        rows = [
            ("Fecha de clasificacion", committee_data.get("date", ""), 34),
            ("Area", committee_data.get("department", ""), 34),
            ("Documentos", committee_data.get("document", ""), 44),
            ("Partes o secciones que se suprimen. Confidencial y/o reservada", suppressed_text, 86),
            ("Fundamento Legal confidencial", committee_data.get("confidential_legal_basis", ""), 58),
            ("Fundamento legal reservada", committee_data.get("reserved_legal_basis", ""), 58),
            ("Periodo de reserva", committee_data.get("reservation_period", ""), 38),
            ("Firma del titular de area y de quien clasifica", committee_data.get("area_owner_name", ""), 58),
            ("Sello de la dependencia", "", 120),
        ]

        page.insert_text(
            (margin_x, y_position),
            "Comite de Transparencia del Estado de Zacatecas",
            fontsize=14,
            color=(0, 0, 0),
            **fitz_font_kwargs(),
        )
        y_position += 28

        for label, value, height in rows:
            left_rect = fitz.Rect(x_left, y_position, x_right, y_position + height)
            right_rect = fitz.Rect(x_right, y_position, x_right + right_width, y_position + height)
            page.draw_rect(left_rect, color=(0, 0, 0), width=0.7)
            page.draw_rect(right_rect, color=(0, 0, 0), width=0.7)
            self._write_table_cell(page, left_rect, label)
            if value:
                self._write_table_cell(page, right_rect, value)
            y_position += height

    def _write_table_cell(self, page, rect, text):
        inner_rect = fitz.Rect(rect.x0 + 5, rect.y0 + 6, rect.x1 - 5, rect.y1 - 5)
        page.insert_textbox(inner_rect, text, fontsize=9, color=(0, 0, 0), align=0, **fitz_font_kwargs())

    def _joined_reason_items(self, ordered_rectangles, classification):
        items = [
            rect_data.get("reason", "").strip()
            for rect_data in ordered_rectangles
            if rect_data.get("classification") == classification and rect_data.get("reason", "").strip()
        ]
        return ", ".join(items)
