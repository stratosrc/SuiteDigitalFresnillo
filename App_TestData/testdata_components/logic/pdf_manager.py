"""PDF loading, rendering, and export helpers."""

import os
import tkinter as tk
from tkinter import filedialog, messagebox

import fitz
from PIL import Image, ImageTk

from App_TestData.testdata_components.config.ui_strings import NAVIGATION_LABELS, PDF_MANAGER_MESSAGES
from App_TestData.testdata_components.constants import (
    CANVAS_DEFAULT_WIDTH,
    CANVAS_MIN_WIDTH,
    CANVAS_PADDING,
    PDF_SUMMARY_PAGE_LINE_HEIGHT,
    PDF_SUMMARY_PAGE_MARGIN_X,
    PDF_SUMMARY_PAGE_TITLE_HEIGHT,
    PDF_WATERMARK_LOGO_PATH,
    RECTANGLE_FILL_COLOR_ACTIVE,
    RECTANGLE_FONT_NAME,
    RECTANGLE_FONT_SIZE,
    RECTANGLE_OUTLINE_COLOR_NORMAL,
    RECTANGLE_OUTLINE_COLOR_SELECTED,
    RECTANGLE_OUTLINE_WIDTH_NORMAL,
    RECTANGLE_OUTLINE_WIDTH_SELECTED,
    RECTANGLE_TEXT_COLOR,
)
from App_TestData.testdata_components.logic.editing_functions import iter_rectangles_in_order
from App_TestData.testdata_components.logic.zoom_functions import get_auto_zoom
from components.styles.styles import SEGOE_UI_FONT_FILE


_SEGOE_FITZ_FONT = None
PDF_FONT_REGULAR = "SegoeUI"


def _fitz_font_kwargs():
    """Return the font configuration used to write text into PDFs."""
    if os.path.exists(SEGOE_UI_FONT_FILE):
        return {"fontname": PDF_FONT_REGULAR, "fontfile": SEGOE_UI_FONT_FILE}
    return {}


def _fitz_text_width(text, fontsize):
    """Estimate the rendered width of text in the export font."""
    global _SEGOE_FITZ_FONT

    if os.path.exists(SEGOE_UI_FONT_FILE):
        if _SEGOE_FITZ_FONT is None:
            _SEGOE_FITZ_FONT = fitz.Font(fontfile=SEGOE_UI_FONT_FILE)
        return _SEGOE_FITZ_FONT.text_length(text, fontsize=fontsize)

    return max(len(text), 1) * fontsize * 0.52


class PDFManager:
    """Coordinate PDF loading, rendering, and export."""

    def __init__(self, app):
        self.app = app

    def load_pdf(self):
        """Load a PDF file and reset the related application state."""
        file_path = filedialog.askopenfilename(
            parent=self.app,
            title=PDF_MANAGER_MESSAGES["load_dialog_title"],
            filetypes=[(PDF_MANAGER_MESSAGES["load_dialog_filetypes_label"], "*.pdf")],
        )

        if not file_path:
            return

        if not os.path.isfile(file_path):
            messagebox.showerror(
                PDF_MANAGER_MESSAGES["missing_file_title"],
                PDF_MANAGER_MESSAGES["missing_file_message"].format(file_path=file_path),
                parent=self.app,
            )
            return

        self.app.current_pdf_path = file_path
        self.app.current_page = 0
        self.app.censored_rectangles.clear()
        self.app.undo_stack.clear()
        self.app.redo_stack.clear()
        self.app.next_rectangle_id = 1
        self.app.selected_rect_id = None
        self.app.current_zoom = None

        try:
            if self.app.pdf_document:
                self.app.pdf_document.close()

            self.app.pdf_document = fitz.open(file_path)
            self.render_current_page()
            self.app.message_label.configure(text=PDF_MANAGER_MESSAGES["loaded_status"])
        except fitz.FileError:
            self.app.message_label.configure(text=PDF_MANAGER_MESSAGES["invalid_pdf_status"])
            messagebox.showerror(
                PDF_MANAGER_MESSAGES["invalid_pdf_title"],
                PDF_MANAGER_MESSAGES["invalid_pdf_message"],
                parent=self.app,
            )
        except Exception as error:
            self.app.message_label.configure(text=PDF_MANAGER_MESSAGES["load_error_status"])
            messagebox.showerror(
                PDF_MANAGER_MESSAGES["load_error_title"],
                PDF_MANAGER_MESSAGES["load_error_message"].format(error=error),
                parent=self.app,
            )

    def render_current_page(self):
        """Render the active page on the Tk canvas and redraw rectangles."""
        if not self.app.pdf_document:
            return

        try:
            page = self.app.pdf_document[self.app.current_page]
            pdf_width = page.rect.width

            canvas_width = self.app.pdf_canvas.winfo_width() - CANVAS_PADDING
            if canvas_width < CANVAS_MIN_WIDTH:
                canvas_width = CANVAS_DEFAULT_WIDTH

            if self.app.current_zoom is None:
                self.app.current_zoom = get_auto_zoom(pdf_width, canvas_width)
                self.app._update_zoom_label()

            matrix = fitz.Matrix(self.app.current_zoom, self.app.current_zoom)
            pixmap = page.get_pixmap(matrix=matrix)

            image = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
            self.app.pdf_page_image = ImageTk.PhotoImage(image)

            self.app.pdf_canvas.delete("all")
            self.app.pdf_canvas.create_image(0, 0, anchor=tk.NW, image=self.app.pdf_page_image)
            self.app.pdf_canvas.config(scrollregion=(0, 0, pixmap.width, pixmap.height))

            total_pages = len(self.app.pdf_document)
            file_name = os.path.basename(self.app.current_pdf_path)
            self.app.message_label.configure(
                text=PDF_MANAGER_MESSAGES["file_status"].format(file_name=file_name)
            )

            self.app.page_entry.delete(0, tk.END)
            self.app.page_entry.insert(0, str(self.app.current_page + 1))
            self.app.total_pages_label.configure(
                text=NAVIGATION_LABELS["total_pages"].format(total_pages=total_pages)
            )

            for rect_data in self.app.censored_rectangles:
                rect_data["canvas_rect_id"] = None
                rect_data["canvas_text_id"] = None

                if rect_data["page"] != self.app.current_page:
                    continue

                x1, y1, x2, y2 = self.pdf_rect_to_canvas(rect_data)
                is_selected = rect_data["id"] == self.app.selected_rect_id
                rect_tag = rect_data.get("rect_tag", f"rect-{rect_data['id']}")
                rect_data["rect_tag"] = rect_tag

                rect_data["canvas_rect_id"] = self.app.pdf_canvas.create_rectangle(
                    x1,
                    y1,
                    x2,
                    y2,
                    fill=RECTANGLE_FILL_COLOR_ACTIVE,
                    outline=(
                        RECTANGLE_OUTLINE_COLOR_SELECTED
                        if is_selected
                        else RECTANGLE_OUTLINE_COLOR_NORMAL
                    ),
                    width=(
                        RECTANGLE_OUTLINE_WIDTH_SELECTED
                        if is_selected
                        else RECTANGLE_OUTLINE_WIDTH_NORMAL
                    ),
                    tags=(rect_tag, "censored_rect"),
                )
                rect_data["canvas_text_id"] = self.app.pdf_canvas.create_text(
                    (x1 + x2) / 2,
                    (y1 + y2) / 2,
                    text=rect_data.get(
                        "display_text",
                        rect_data.get("concept_name", rect_data.get("label", "")),
                    ),
                    fill=RECTANGLE_TEXT_COLOR,
                    font=(RECTANGLE_FONT_NAME, RECTANGLE_FONT_SIZE, "bold"),
                    tags=(rect_tag, "censored_text"),
                )
        except Exception as error:
            self.app.message_label.configure(text=PDF_MANAGER_MESSAGES["render_error_status"])
            messagebox.showerror(
                PDF_MANAGER_MESSAGES["render_error_title"],
                PDF_MANAGER_MESSAGES["render_error_message"].format(error=error),
                parent=self.app,
            )

    def canvas_to_pdf_rect(self, x1, y1, x2, y2):
        """Convert canvas coordinates into PDF coordinates."""
        zoom = self.app.current_zoom or 1
        left, right = sorted((x1 / zoom, x2 / zoom))
        top, bottom = sorted((y1 / zoom, y2 / zoom))
        return left, top, right, bottom

    def pdf_rect_to_canvas(self, rect_data):
        """Convert PDF rectangle coordinates into canvas coordinates."""
        zoom = self.app.current_zoom or 1
        return (
            rect_data["x1"] * zoom,
            rect_data["y1"] * zoom,
            rect_data["x2"] * zoom,
            rect_data["y2"] * zoom,
        )

    def generate_pdf(self, output_path, committee_data=None):
        """Generate the exported PDF including redactions and summary pages."""
        if not self.app.current_pdf_path:
            raise ValueError("No PDF loaded.")

        output_document = fitz.open(stream=self.app.pdf_document.tobytes(), filetype="pdf")
        ordered_rectangles = iter_rectangles_in_order(self.app.censored_rectangles)

        try:
            self._assign_final_numbers(ordered_rectangles)
            self._apply_redactions(output_document, ordered_rectangles)
            self._draw_rectangle_labels(output_document, ordered_rectangles)
            self._append_summary_page(output_document, ordered_rectangles)
            if committee_data:
                self._append_committee_cover_page(output_document, committee_data, ordered_rectangles)
            output_document.save(output_path, garbage=4, deflate=True)
        finally:
            output_document.close()

    def _apply_redactions(self, document, ordered_rectangles):
        """Apply irreversible redactions to the exported document."""
        for rect_data in ordered_rectangles:
            page = document[rect_data["page"]]
            rect = fitz.Rect(rect_data["x1"], rect_data["y1"], rect_data["x2"], rect_data["y2"])
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
            page = document[rect_data["page"]]
            page.draw_rect(rect_data["rect"], color=(0, 0, 0), width=1)

    def _draw_rectangle_labels(self, document, ordered_rectangles):
        """Write the final labels centered on top of each redaction."""
        for rect_data in ordered_rectangles:
            page = document[rect_data["page"]]
            label_text = rect_data.get("final_number", rect_data.get("label", ""))
            font_size = 10

            text_width = _fitz_text_width(label_text, font_size)
            start_x = ((rect_data["x1"] + rect_data["x2"]) / 2) - (text_width / 2)
            center_y = (rect_data["y1"] + rect_data["y2"]) / 2
            baseline_y = center_y + (font_size * 0.35)

            background = fitz.Rect(
                start_x - 2,
                center_y - 6,
                start_x + text_width + 2,
                center_y + 6,
            )
            page.draw_rect(background, color=(1, 1, 1), fill=(1, 1, 1), width=0)
            page.insert_text(
                (start_x, baseline_y),
                label_text,
                fontsize=font_size,
                color=(0, 0, 0),
                **_fitz_font_kwargs(),
            )

    def _append_summary_page(self, document, ordered_rectangles):
        """Append one or more summary pages listing the legal grounds."""
        margin_x = PDF_SUMMARY_PAGE_MARGIN_X
        y_position = 50
        max_y = 750
        line_height = PDF_SUMMARY_PAGE_LINE_HEIGHT
        title_height = PDF_SUMMARY_PAGE_TITLE_HEIGHT

        page = self._create_summary_page(document, margin_x, y_position)
        y_position += title_height

        for rect_data in ordered_rectangles:
            if y_position > max_y:
                page = self._create_summary_page(document, margin_x, 50, continuation=True)
                y_position = 50 + title_height

            summary_label = rect_data.get("final_number", rect_data.get("label", ""))
            line = self._build_summary_line(summary_label, rect_data)
            y_position = self._write_summary_line(page, line, margin_x, y_position, line_height)

    def _create_summary_page(self, document, margin_x, y_position, continuation=False):
        """Create a summary page and write its title."""
        page = document.new_page()
        self._apply_watermark(page)
        title = (
            "Fundamentos de la Ley de Transparencia y Acceso a la Información Pública \n"
            "del Estado de Zacatecas (continuación)"
            if continuation
            else "Fundamentos de la Ley de Transparencia y Acceso a la Información Pública \n"
            "del Estado de Zacatecas"
        )
        page.insert_text(
            (margin_x, y_position),
            title,
            fontsize=16,
            color=(0, 0, 0),
            **_fitz_font_kwargs(),
        )
        return page

    def _write_summary_line(self, page, line, margin_x, y_position, line_height):
        """Write a wrapped summary paragraph and return the next y offset."""
        page_width = page.rect.width
        available_width = page_width - (margin_x * 2)
        text_rect = fitz.Rect(margin_x, y_position, margin_x + available_width, y_position + 60)

        used_height = page.insert_textbox(
            text_rect,
            line,
            fontsize=10,
            color=(0, 0, 0),
            align=0,
            **_fitz_font_kwargs(),
        )
        return y_position + max(line_height, 60 - used_height) + 10

    def _build_summary_line(self, summary_label, rect_data):
        """Build the summary text for a single rectangle."""
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
            f"el {article_reference} de la Ley de protección de datos personales en posesión de sujetos obligados "
            f"del estado de Zacatecas ({paragraphs} párrafo{'s' if paragraphs != 1 else ''} "
            f"{rows} renglón{'es' if rows != 1 else ''})."
        )

    def _build_reserved_summary_line(self, summary_label, rect_data):
        """Build the legal summary text for reserved information."""
        return (
            f"{summary_label}: El {rect_data.get('reason', '')}, {rect_data.get('paragraphs', 1)} párrafos y "
            f"{rect_data.get('rows', 1)} renglones por ser considerado como información reservada "
            f"de conformidad con los artículos 99, 100 y 101 de la Ley de Transparencia y Acceso "
            f"a la Información Pública del Estado de Zacatecas y los lineamientos generales en "
            f"materia de clasificación y desclasificación de la información, así como para la "
            f"elaboración de versiones públicas {rect_data.get('legal_basis', '')}."
        )

    def _build_confidential_summary_line(self, summary_label, rect_data):
        """Build the legal summary text for confidential information."""
        return (
            f"{summary_label}: {rect_data.get('reason', '')}, {rect_data.get('paragraphs', 1)} párrafos y "
            f"{rect_data.get('rows', 1)} renglones por ser considerado como información confidencial "
            f"de conformidad con los artículos 102, 103, 104, 105 y 106 de la Ley de Transparencia "
            f"y Acceso a la Información Pública del Estado de Zacatecas y con "
            f"{rect_data.get('legal_basis', '')}."
        )

    def _build_other_law_summary_line(self, summary_label, rect_data):
        """Build the legal summary text for the custom-law classification."""
        return (
            f"{summary_label}: Eliminado {rect_data.get('object', '')} en base a "
            f"{rect_data.get('articles', '')} de la {rect_data.get('law', '')} "
            f"({rect_data.get('paragraphs', 1)} párrafo"
            f"{'s' if rect_data.get('paragraphs', 1) != 1 else ''} "
            f"{rect_data.get('rows', 1)} renglón"
            f"{'es' if rect_data.get('rows', 1) != 1 else ''})."
        )

    def _legal_reference_for_concept(self, concept_id):
        """Return the legal reference derived from the concept category."""
        category = self.app.catalogue_categories.get(concept_id, "normal")
        if category == "sensitive":
            return "artículo 3, sección X, inciso a"
        if category == "biometric":
            return "artículo 3, sección X, inciso b"
        return "artículo 3, sección X"

    def _append_committee_cover_page(self, document, committee_data, ordered_rectangles):
        """Append the committee cover sheet to the exported PDF."""
        page = document.new_page()
        self._apply_watermark(page)
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
            ("Fecha de clasificación", committee_data.get("date", ""), 34),
            ("Área", committee_data.get("department", ""), 34),
            ("Documentos", committee_data.get("document", ""), 44),
            ("Partes o secciones que se suprimen. Confidencial y/o reservada", suppressed_text, 86),
            ("Fundamento Legal confidencial", committee_data.get("confidential_legal_basis", ""), 58),
            ("Fundamento legal reservada", committee_data.get("reserved_legal_basis", ""), 58),
            ("Periodo de reserva", committee_data.get("reservation_period", ""), 38),
            ("Firma del titular de área y de quien clasifica", committee_data.get("area_owner_name", ""), 58),
            ("Sello de la dependencia", "", 120),
        ]

        page.insert_text(
            (margin_x, y_position),
            "Comité de Transparencia del Estado de Zacatecas",
            fontsize=14,
            color=(0, 0, 0),
            **_fitz_font_kwargs(),
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

    def _apply_watermark(self, page):
        """Insert the watermark image on summary pages."""
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
        watermark_rect = fitz.Rect(
            x0,
            y0,
            x0 + watermark_width,
            y0 + watermark_height,
        )
        page.insert_image(watermark_rect, filename=PDF_WATERMARK_LOGO_PATH, overlay=False)

    def _write_table_cell(self, page, rect, text):
        """Write text inside a table cell rectangle."""
        inner_rect = fitz.Rect(rect.x0 + 5, rect.y0 + 6, rect.x1 - 5, rect.y1 - 5)
        page.insert_textbox(
            inner_rect,
            text,
            fontsize=9,
            color=(0, 0, 0),
            align=0,
            **_fitz_font_kwargs(),
        )

    def _joined_reason_items(self, ordered_rectangles, classification):
        """Join the saved reason values for the given classification."""
        items = [
            rect_data.get("reason", "").strip()
            for rect_data in ordered_rectangles
            if rect_data.get("classification") == classification and rect_data.get("reason", "").strip()
        ]
        return ", ".join(items)

    def _assign_final_numbers(self, ordered_rectangles):
        """Assign stable final numbering right before export."""
        concept_counters = {}
        reserved_counter = 0
        confidential_counter = 0
        other_law_counter = 0

        for rect_data in ordered_rectangles:
            classification = rect_data.get("classification", "general")
            if classification == "reserved":
                reserved_counter += 1
                rect_data["final_number"] = f"Reservada.{reserved_counter}"
            elif classification == "confidential":
                confidential_counter += 1
                rect_data["final_number"] = f"Confidencial.{confidential_counter}"
            elif classification == "other_law":
                other_law_counter += 1
                rect_data["final_number"] = f"Otra.{other_law_counter}"
            else:
                concept_id = rect_data["concept_id"]
                concept_counters[concept_id] = concept_counters.get(concept_id, 0) + 1
                rect_data["final_number"] = f"#{concept_id}.{concept_counters[concept_id]}"
