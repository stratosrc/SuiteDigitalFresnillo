"""Redaction PDF export orchestration."""

from __future__ import annotations

from copy import deepcopy
from typing import Mapping
from collections.abc import Callable

import fitz

from App_TestData.domain.document_state import CommitteeData, RectangleData
from App_TestData.domain.redaction_editing import iter_rectangles_in_order
from App_TestData.services.committee_cover import CommitteeCoverWriter
from App_TestData.services.pdf_fonts import fitz_font_kwargs, fitz_text_width
from App_TestData.services.pdf_footer import add_institutional_footer
from App_TestData.services.summary_pages import SummaryPagesWriter
from components.shared.atomic_output import write_atomic_output


class RedactionPdfExporter:
    def __init__(self, concept_categories: Mapping[int, str]) -> None:
        self.summary_writer = SummaryPagesWriter(concept_categories)
        self.committee_writer = CommitteeCoverWriter()

    def export(
        self,
        source: bytes | str,
        output_path: str,
        rectangles: list[RectangleData],
        committee_data: CommitteeData | None = None,
        cancel_check: Callable[[], bool] | None = None,
    ) -> None:
        write_atomic_output(
            output_path,
            lambda temporary: self._write_pdf(
                source,
                str(temporary),
                rectangles,
                committee_data,
            ),
            should_commit=(
                (lambda: not cancel_check())
                if cancel_check is not None
                else None
            ),
        )

    def _write_pdf(
        self,
        source: bytes | str,
        output_path: str,
        rectangles: list[RectangleData],
        committee_data: CommitteeData | None,
    ) -> None:
        output_document = (
            fitz.open(stream=source, filetype="pdf")
            if isinstance(source, bytes)
            else fitz.open(source)
        )
        ordered_rectangles = deepcopy(iter_rectangles_in_order(rectangles))

        try:
            original_page_count = output_document.page_count
            self._assign_final_numbers(ordered_rectangles)
            self._apply_redactions(output_document, ordered_rectangles)
            self._draw_rectangle_labels(output_document, ordered_rectangles)
            self.summary_writer.append(output_document, ordered_rectangles)
            if committee_data:
                self.committee_writer.append(output_document, committee_data, ordered_rectangles)
            add_institutional_footer(output_document, start_page=original_page_count)
            output_document.save(output_path, garbage=4, deflate=True)
        finally:
            output_document.close()

    def _apply_redactions(self, document, ordered_rectangles):
        for rect_data in ordered_rectangles:
            page = document[rect_data["page"]]
            rect = fitz.Rect(rect_data["x1"], rect_data["y1"], rect_data["x2"], rect_data["y2"]) & page.rect
            if rect.is_empty or rect.is_infinite:
                continue
            rect_data["rect"] = rect
            page.add_redact_annot(
                rect,
                text="",
                fontsize=10,
                align=fitz.TEXT_ALIGN_CENTER,
                fill=(1, 1, 1),
                cross_out=False,
            )

        for page in document:
            page.apply_redactions()

        for rect_data in ordered_rectangles:
            if "rect" not in rect_data:
                continue
            page = document[rect_data["page"]]
            page.draw_rect(rect_data["rect"], color=(0, 0, 0), width=1)

    def _draw_rectangle_labels(self, document, ordered_rectangles):
        for rect_data in ordered_rectangles:
            if "rect" not in rect_data:
                continue
            page = document[rect_data["page"]]
            label_text = rect_data.get("final_number", rect_data.get("label", ""))
            font_size = 10
            text_width = fitz_text_width(label_text, font_size)
            start_x = ((rect_data["x1"] + rect_data["x2"]) / 2) - (text_width / 2)
            center_y = (rect_data["y1"] + rect_data["y2"]) / 2
            background = fitz.Rect(start_x - 2, center_y - 6, start_x + text_width + 2, center_y + 6)
            page.draw_rect(background, color=(1, 1, 1), fill=(1, 1, 1), width=0)
            page.insert_textbox(
                background,
                label_text,
                fontsize=font_size,
                align=fitz.TEXT_ALIGN_CENTER,
                rotate=page.rotation,
                color=(0, 0, 0),
                **fitz_font_kwargs(),
            )

    def _assign_final_numbers(self, ordered_rectangles):
        concept_counters = {}
        reserved_counter = 0
        confidential_counter = 0
        other_law_counter = 0

        for rect_data in ordered_rectangles:
            classification = rect_data.get("classification", "general")
            if classification == "reserved":
                reserved_counter += 1
                rect_data["final_number"] = f"#Reservada.{reserved_counter}"
            elif classification == "confidential":
                confidential_counter += 1
                rect_data["final_number"] = f"#Confidencial.{confidential_counter}"
            elif classification == "other_law":
                other_law_counter += 1
                rect_data["final_number"] = f"Otra.{other_law_counter}"
            else:
                concept_id = rect_data["concept_id"]
                concept_counters[concept_id] = concept_counters.get(concept_id, 0) + 1
                rect_data["final_number"] = f"#{concept_id}.{concept_counters[concept_id]}"
