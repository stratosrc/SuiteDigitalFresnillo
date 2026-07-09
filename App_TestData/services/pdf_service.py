"""PDF loading, rendering, and export helpers."""

from __future__ import annotations

import os
import logging
from collections.abc import Callable
from typing import Mapping, Optional, Protocol, TypedDict

import fitz
from PIL import Image, ImageTk

from App_TestData.config.ui_strings import PDF_MANAGER_MESSAGES
from App_TestData.config.settings import (
    CANVAS_DEFAULT_WIDTH,
    CANVAS_MIN_WIDTH,
    CANVAS_PADDING,
)
from App_TestData.domain.document_state import (
    CommitteeData,
    DocumentState,
    RectangleData,
)
from App_TestData.services.redaction_exporter import RedactionPdfExporter
from App_TestData.utils.zoom import get_auto_zoom


LOGGER = logging.getLogger(__name__)


class DrawnRectangle(TypedDict, total=False):
    """Canvas item identifiers returned after drawing a rectangle."""

    canvas_rect_id: int
    canvas_text_id: int


class PdfUiCallbacks(Protocol):
    """Callbacks used by the PDF manager to communicate with the UI layer."""

    def request_pdf_file_path(self) -> Optional[str]:
        """Ask the UI for a PDF path."""

    def clear_document_view(self) -> None:
        """Clear all rendered document artifacts from the UI."""

    def set_status(self, message: str) -> None:
        """Update the user-visible status text."""

    def show_error(self, title: str, message: str) -> None:
        """Show an error message."""

    def get_canvas_width(self) -> int:
        """Return the current PDF canvas width."""

    def draw_page_image(self, image: ImageTk.PhotoImage, width: int, height: int) -> None:
        """Draw a rendered PDF page."""

    def update_page_controls(self, current_page: int, total_pages: int) -> None:
        """Synchronize page navigation controls."""

    def update_zoom_label(self) -> None:
        """Synchronize the zoom label."""

    def draw_rectangle(
        self,
        rectangle: RectangleData,
        coords: tuple[float, float, float, float],
        is_selected: bool,
    ) -> DrawnRectangle:
        """Draw one redaction rectangle and return its canvas item ids."""


class PDFManager:
    """Coordinate PDF loading, rendering, and export."""

    def __init__(
        self,
        state: DocumentState,
        callbacks: PdfUiCallbacks,
        concept_categories: Mapping[int, str],
    ) -> None:
        self._state = state
        self._callbacks = callbacks
        self._concept_categories = concept_categories
        self._redaction_exporter = RedactionPdfExporter(concept_categories)

    def init_new_job(self) -> bool:
        """Reset the active job and load a newly selected PDF."""
        self.reset_current_job()
        return self.load_new_job_pdf()

    def reset_current_job(self) -> None:
        """Clear all document data and rendered UI artifacts."""
        self._state.reset_for_new_job()
        self._callbacks.clear_document_view()

    def load_new_job_pdf(self) -> bool:
        """Ask the user for a PDF and load it into the reset job state."""
        file_path = self._callbacks.request_pdf_file_path()

        if not file_path:
            self._callbacks.set_status(PDF_MANAGER_MESSAGES["new_job_cancelled_status"])
            return False
        return self.load_pdf_path(file_path)

    def load_pdf_path(self, file_path: str) -> bool:
        """Load a PDF path selected by the caller."""

        if not os.path.isfile(file_path):
            self._callbacks.show_error(
                PDF_MANAGER_MESSAGES["missing_file_title"],
                PDF_MANAGER_MESSAGES["missing_file_message"].format(file_path=file_path),
            )
            return False

        self._state.current_pdf_path = file_path

        try:
            self._state.pdf_document = fitz.open(file_path)
            if self.render_current_page():
                self._callbacks.set_status(PDF_MANAGER_MESSAGES["loaded_status"])
                return True
            return False
        except (fitz.FileDataError, fitz.EmptyFileError):
            self._state.reset_for_new_job()
            self._callbacks.clear_document_view()
            self._callbacks.set_status(PDF_MANAGER_MESSAGES["invalid_pdf_status"])
            self._callbacks.show_error(
                PDF_MANAGER_MESSAGES["invalid_pdf_title"],
                PDF_MANAGER_MESSAGES["invalid_pdf_message"],
            )
            return False
        except Exception as error:
            LOGGER.exception("Unable to load PDF")
            self._state.reset_for_new_job()
            self._callbacks.clear_document_view()
            self._callbacks.set_status(PDF_MANAGER_MESSAGES["load_error_status"])
            self._callbacks.show_error(
                PDF_MANAGER_MESSAGES["load_error_title"],
                PDF_MANAGER_MESSAGES["load_error_message"].format(error=error),
            )
            return False

    def render_current_page(self) -> bool:
        """Render the active page on the Tk canvas and redraw rectangles."""
        if not self._state.pdf_document:
            return False

        try:
            page = self._state.pdf_document[self._state.current_page]
            pdf_width = page.rect.width

            canvas_width = self._callbacks.get_canvas_width() - CANVAS_PADDING
            if canvas_width < CANVAS_MIN_WIDTH:
                canvas_width = CANVAS_DEFAULT_WIDTH

            if self._state.current_zoom is None:
                self._state.current_zoom = get_auto_zoom(pdf_width, canvas_width)
                self._callbacks.update_zoom_label()

            matrix = fitz.Matrix(self._state.current_zoom, self._state.current_zoom)
            pixmap = page.get_pixmap(matrix=matrix, colorspace=fitz.csRGB, alpha=False)

            image = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
            self._state.pdf_page_image = ImageTk.PhotoImage(image)
            self._callbacks.draw_page_image(self._state.pdf_page_image, pixmap.width, pixmap.height)

            total_pages = len(self._state.pdf_document)
            file_name = os.path.basename(self._state.current_pdf_path or "")
            self._callbacks.set_status(
                PDF_MANAGER_MESSAGES["file_status"].format(file_name=file_name)
            )
            self._callbacks.update_page_controls(self._state.current_page, total_pages)

            for rect_data in self._state.censored_rectangles:
                rect_data["canvas_rect_id"] = None
                rect_data["canvas_text_id"] = None

                if rect_data["page"] != self._state.current_page:
                    continue

                x1, y1, x2, y2 = self.pdf_rect_to_canvas(rect_data)
                is_selected = rect_data["id"] == self._state.selected_rect_id
                rect_tag = rect_data.get("rect_tag", f"rect-{rect_data['id']}")
                rect_data["rect_tag"] = rect_tag

                drawn_items = self._callbacks.draw_rectangle(
                    rect_data,
                    (x1, y1, x2, y2),
                    is_selected,
                )
                rect_data.update(drawn_items)
            return True
        except Exception as error:
            LOGGER.exception("Unable to render PDF page")
            self._callbacks.set_status(PDF_MANAGER_MESSAGES["render_error_status"])
            self._callbacks.show_error(
                PDF_MANAGER_MESSAGES["render_error_title"],
                PDF_MANAGER_MESSAGES["render_error_message"].format(error=error),
            )
            return False

    def _current_page_object(self) -> fitz.Page | None:
        if not self._state.pdf_document:
            return None
        return self._state.pdf_document[self._state.current_page]

    def _rotated_rect_to_pdf_rect(self, rect: fitz.Rect, page: fitz.Page) -> fitz.Rect:
        if page.rotation:
            rect = rect * page.derotation_matrix
        cropbox = page.cropbox
        rect = fitz.Rect(
            min(max(rect.x0, cropbox.x0), cropbox.x1),
            min(max(rect.y0, cropbox.y0), cropbox.y1),
            min(max(rect.x1, cropbox.x0), cropbox.x1),
            min(max(rect.y1, cropbox.y0), cropbox.y1),
        )
        return fitz.Rect(
            min(rect.x0, rect.x1),
            min(rect.y0, rect.y1),
            max(rect.x0, rect.x1),
            max(rect.y0, rect.y1),
        )

    def _pdf_rect_to_rotated_rect(self, rect: fitz.Rect, page: fitz.Page) -> fitz.Rect:
        if page.rotation:
            rect = rect * page.rotation_matrix
        page_rect = page.rect
        rect = fitz.Rect(
            min(max(rect.x0, page_rect.x0), page_rect.x1),
            min(max(rect.y0, page_rect.y0), page_rect.y1),
            min(max(rect.x1, page_rect.x0), page_rect.x1),
            min(max(rect.y1, page_rect.y0), page_rect.y1),
        )
        return fitz.Rect(
            min(rect.x0, rect.x1),
            min(rect.y0, rect.y1),
            max(rect.x0, rect.x1),
            max(rect.y0, rect.y1),
        )

    def canvas_to_pdf_rect(self, x1: float, y1: float, x2: float, y2: float) -> tuple[float, float, float, float]:
        """Convert canvas coordinates into PDF coordinates."""
        zoom = self._state.current_zoom or 1
        rotated_rect = fitz.Rect(x1 / zoom, y1 / zoom, x2 / zoom, y2 / zoom)
        page = self._current_page_object()
        if page is None:
            normalized = fitz.Rect(rotated_rect)
            normalized.normalize()
            return normalized.x0, normalized.y0, normalized.x1, normalized.y1

        pdf_rect = self._rotated_rect_to_pdf_rect(rotated_rect, page)
        return pdf_rect.x0, pdf_rect.y0, pdf_rect.x1, pdf_rect.y1

    def pdf_rect_to_canvas(self, rect_data: RectangleData) -> tuple[float, float, float, float]:
        """Convert PDF rectangle coordinates into canvas coordinates."""
        zoom = self._state.current_zoom or 1
        page = self._current_page_object()
        pdf_rect = fitz.Rect(
            rect_data["x1"],
            rect_data["y1"],
            rect_data["x2"],
            rect_data["y2"],
        )
        if page is not None:
            pdf_rect = self._pdf_rect_to_rotated_rect(pdf_rect, page)
        return (
            pdf_rect.x0 * zoom,
            pdf_rect.y0 * zoom,
            pdf_rect.x1 * zoom,
            pdf_rect.y1 * zoom,
        )

    def generate_pdf(
        self,
        output_path: str,
        committee_data: Optional[CommitteeData] = None,
        *,
        pdf_bytes: bytes | None = None,
        source_path: str | None = None,
        rectangles: list[RectangleData] | None = None,
        cancel_check: Callable[[], bool] | None = None,
    ) -> None:
        """Generate the exported PDF including redactions and summary pages."""
        if pdf_bytes is None and source_path is None and (not self._state.current_pdf_path or not self._state.pdf_document):
            raise ValueError("No PDF loaded.")

        source = pdf_bytes or source_path or self._state.current_pdf_path
        self._redaction_exporter.export(
            source,
            output_path,
            rectangles or self._state.censored_rectangles,
            committee_data,
            cancel_check,
        )

