import os
from concurrent.futures import ThreadPoolExecutor
import sys
from pathlib import Path
from typing import Any, Deque
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk
import fitz
from PIL import ImageTk


if __package__ in {None, ""}:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from App_TestData.config.ui_strings import (
    APP_WINDOW_TITLE,
    EXIT_MESSAGES,
    PDF_MANAGER_MESSAGES,
)
from App_TestData.config.settings import (
    PDF_CANVAS_BG,
    RECTANGLE_FILL_COLOR_ACTIVE,
    RECTANGLE_FONT_NAME,
    RECTANGLE_FONT_SIZE,
    RECTANGLE_OUTLINE_COLOR_NORMAL,
    RECTANGLE_OUTLINE_COLOR_SELECTED,
    RECTANGLE_OUTLINE_WIDTH_NORMAL,
    RECTANGLE_OUTLINE_WIDTH_SELECTED,
    RECTANGLE_TEXT_COLOR,
    WINDOW_HEIGHT,
    WINDOW_MIN_HEIGHT,
    WINDOW_MIN_WIDTH,
    WINDOW_WIDTH,
)
from App_TestData.data.catalogue_data import (
    CATALOGUE_SECTIONS,
    build_catalogue_categories,
    build_catalogue_items,
)
from App_TestData.ui.interactions.canvas_redactions import setup_canvas_events
from App_TestData.domain.document_state import DocumentState, RectangleData, RedactionHistoryAction
from App_TestData.services.pdf_service import PDFManager
from App_TestData.services.project_persistence import (
    calculate_file_hash,
    deserialize_rectangles,
    load_project,
    save_project,
)
from App_TestData.ui.interactions.scroll import setup_mousewheel_scroll
from App_TestData.ui.controllers import ExportController, NavigationController, RectangleActionController
from App_TestData.ui.dialogs.catalogue_dialog import show_catalogue_dialog
from App_TestData.ui.dialogs.help_dialog import show_help_dialog
from App_TestData.ui.layout.main_layout import build_main_layout
from components.shared.windowing import center_window, prepare_window_for_open, reveal_window_maximized
from components.styles.styles import apply_ctk_style, styles


class TestDataGeneratorApp(ctk.CTk):
    """Main CustomTkinter application."""

    def __init__(self) -> None:
        super().__init__()
        prepare_window_for_open(self)
        apply_ctk_style(ctk)
        self.title(APP_WINDOW_TITLE)
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        center_window(self, WINDOW_WIDTH, WINDOW_HEIGHT)

        self.document_state = DocumentState()
        self.current_project_path: Path | None = None
        self._init_state()
        self._render_resize_after_id = None
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="testdata-worker")
        styles(self)
        self.pdf_manager = PDFManager(
            self.document_state,
            self,
            self.catalogue_categories,
        )
        self.navigation_controller = NavigationController(self)
        self.rectangle_action_controller = RectangleActionController(self)
        self.export_controller = ExportController(self, self._executor)

        widget_map = build_main_layout(self, self._build_callbacks())
        self._register_widgets(widget_map)

        setup_canvas_events(self)
        setup_mousewheel_scroll(
            self.pdf_canvas,
            has_document=lambda: bool(self.pdf_document),
            on_zoom_in=lambda: self.navigation_controller.change_zoom("in"),
            on_zoom_out=lambda: self.navigation_controller.change_zoom("out"),
        )
        self.protocol("WM_DELETE_WINDOW", self.confirm_exit)
        reveal_window_maximized(self)

    def _build_callbacks(self) -> dict[str, Any]:
        """Build the callback map consumed by UI components."""
        return {
            "on_new_job": self._start_new_job,
            "on_open_project": self.open_project,
            "on_save_project": self.save_project,
            "on_save_project_as": self.save_project_as,
            "on_open_export_dialog": self.export_controller.open_export_dialog,
            "on_show_catalogue": lambda: show_catalogue_dialog(
                self,
                self.catalogue_sections,
                self.catalogue_items,
            ),
            "on_show_help": lambda: show_help_dialog(self),
            "on_exit": self.confirm_exit,
            "on_rectangle_action": self.rectangle_action_controller.handle_action,
            "on_previous_page": lambda: self.navigation_controller.navigate_page("prev"),
            "on_next_page": lambda: self.navigation_controller.navigate_page("next"),
            "on_go_to_page": self.navigation_controller.go_to_page_from_entry,
            "on_zoom_in": lambda: self.navigation_controller.change_zoom("in"),
            "on_zoom_out": lambda: self.navigation_controller.change_zoom("out"),
            "on_canvas_resize": self._on_canvas_resize,
        }

    def _register_widgets(self, widget_map: dict[str, Any]) -> None:
        """Expose built widgets as attributes for the rest of the app."""
        for name, widget in widget_map.items():
            setattr(self, name, widget)
        self.navigation_controller.update_zoom_label()
        self.navigation_controller.update_page_state(current_page=0, total_pages=0)
        self.rectangle_action_controller.sync_delete_button_state()

    def _init_state(self) -> None:
        self.catalogue_sections = CATALOGUE_SECTIONS
        self.catalogue_items = build_catalogue_items(self.catalogue_sections)
        self.catalogue_categories = build_catalogue_categories(self.catalogue_sections)
        self.catalogue_name_by_id = dict(self.catalogue_items)

        self.start_x = None
        self.start_y = None
        self.current_rect = None
        self.drag_mode = None
        self.active_rect_data = None
        self.active_resize_corner = None
        self.drag_start_x = None
        self.drag_start_y = None
        self.drag_original_coords = None
        self.drag_original_rectangle = None

    @property
    def current_pdf_path(self) -> str | None:
        return self.document_state.current_pdf_path

    @current_pdf_path.setter
    def current_pdf_path(self, value: str | None) -> None:
        self.document_state.current_pdf_path = value

    @property
    def pdf_document(self) -> fitz.Document | None:
        return self.document_state.pdf_document

    @pdf_document.setter
    def pdf_document(self, value: fitz.Document | None) -> None:
        self.document_state.pdf_document = value

    @property
    def pdf_page_image(self) -> ImageTk.PhotoImage | None:
        return self.document_state.pdf_page_image

    @pdf_page_image.setter
    def pdf_page_image(self, value: ImageTk.PhotoImage | None) -> None:
        self.document_state.pdf_page_image = value

    @property
    def current_page(self) -> int:
        return self.document_state.current_page

    @current_page.setter
    def current_page(self, value: int) -> None:
        self.document_state.current_page = value

    @property
    def current_zoom(self) -> float | None:
        return self.document_state.current_zoom

    @current_zoom.setter
    def current_zoom(self, value: float | None) -> None:
        self.document_state.current_zoom = value

    @property
    def censored_rectangles(self) -> list[RectangleData]:
        return self.document_state.censored_rectangles

    @censored_rectangles.setter
    def censored_rectangles(self, value: list[RectangleData]) -> None:
        self.document_state.censored_rectangles = value

    @property
    def undo_stack(self) -> Deque[RedactionHistoryAction]:
        return self.document_state.undo_stack

    @property
    def redo_stack(self) -> Deque[RedactionHistoryAction]:
        return self.document_state.redo_stack

    @property
    def next_rectangle_id(self) -> int:
        return self.document_state.next_rectangle_id

    @next_rectangle_id.setter
    def next_rectangle_id(self, value: int) -> None:
        self.document_state.next_rectangle_id = value

    @property
    def selected_rect_id(self) -> int | None:
        return self.document_state.selected_rect_id

    @selected_rect_id.setter
    def selected_rect_id(self, value: int | None) -> None:
        self.document_state.selected_rect_id = value

    @property
    def reserved_history(self) -> list[Any]:
        return self.document_state.reserved_history

    @property
    def confidential_history(self) -> list[Any]:
        return self.document_state.confidential_history

    @property
    def other_law_history(self) -> list[Any]:
        return self.document_state.other_law_history

    def _start_new_job(self) -> None:
        """Reset the current job and then open the PDF selector."""
        self.pdf_manager.reset_current_job()
        self.current_project_path = None
        self.after_idle(self.pdf_manager.load_new_job_pdf)

    def request_pdf_file_path(self) -> str | None:
        """Ask the user for the PDF used by the new job."""
        return filedialog.askopenfilename(
            parent=self,
            title=PDF_MANAGER_MESSAGES["load_dialog_title"],
            filetypes=[(PDF_MANAGER_MESSAGES["load_dialog_filetypes_label"], "*.pdf")],
        )

    def clear_document_view(self) -> None:
        """Clear document widgets after the business state has been reset."""
        pdf_canvas = getattr(self, "pdf_canvas", None)
        if pdf_canvas is not None:
            pdf_canvas.delete("all")
            pdf_canvas.configure(bg=PDF_CANVAS_BG, scrollregion=(0, 0, 0, 0), cursor="")

        page_entry = getattr(self, "page_entry", None)
        if page_entry is not None:
            page_entry.delete(0, tk.END)
            page_entry.insert(0, "1")

        total_pages_label = getattr(self, "total_pages_label", None)
        if total_pages_label is not None:
            total_pages_label.configure(text="Página 0 de 0")

        self._reset_canvas_interaction_state()
        self._update_zoom_label()
        self.navigation_controller.update_page_state(current_page=0, total_pages=0)
        self._sync_delete_button_state()

    def set_status(self, message: str) -> None:
        """Update the main status label."""
        message_label = getattr(self, "message_label", None)
        if message_label is not None:
            message_label.configure(text=message)

    def show_error(self, title: str, message: str) -> None:
        """Display a user-facing error dialog."""
        messagebox.showerror(title, message, parent=self)

    def get_canvas_width(self) -> int:
        """Return the current canvas width for PDF rendering."""
        return self.pdf_canvas.winfo_width()

    def draw_page_image(self, image: ImageTk.PhotoImage, width: int, height: int) -> None:
        """Render the current page image into the canvas."""
        self.pdf_canvas.delete("all")
        self.pdf_canvas.create_image(0, 0, anchor=tk.NW, image=image)
        self.pdf_canvas.config(scrollregion=(0, 0, width, height))

    def update_page_controls(self, current_page: int, total_pages: int) -> None:
        """Synchronize page controls after rendering."""
        self.page_entry.delete(0, tk.END)
        self.page_entry.insert(0, str(current_page + 1))
        self.total_pages_label.configure(
            text=f"Página {current_page + 1} de {total_pages}"
        )
        self.navigation_controller.update_page_state(current_page=current_page, total_pages=total_pages)

    def update_zoom_label(self) -> None:
        """Synchronize the zoom label through the PDF manager callback."""
        self._update_zoom_label()

    def draw_rectangle(
        self,
        rectangle: RectangleData,
        coords: tuple[float, float, float, float],
        is_selected: bool,
    ) -> dict[str, int]:
        """Draw one redaction rectangle on the PDF canvas."""
        x1, y1, x2, y2 = coords
        rect_tag = rectangle.get("rect_tag", f"rect-{rectangle['id']}")
        canvas_rect_id = self.pdf_canvas.create_rectangle(
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
        canvas_text_id = self.pdf_canvas.create_text(
            (x1 + x2) / 2,
            (y1 + y2) / 2,
            text=rectangle.get(
                "display_text",
                rectangle.get("concept_name", rectangle.get("label", "")),
            ),
            fill=RECTANGLE_TEXT_COLOR,
            font=(RECTANGLE_FONT_NAME, RECTANGLE_FONT_SIZE, "bold"),
            tags=(rect_tag, "censored_text"),
        )
        return {
            "canvas_rect_id": canvas_rect_id,
            "canvas_text_id": canvas_text_id,
        }

    def _reset_canvas_interaction_state(self) -> None:
        """Clear transient pointer interaction values."""
        self.start_x = None
        self.start_y = None
        self.current_rect = None
        self.drag_mode = None
        self.active_rect_data = None
        self.active_resize_corner = None
        self.drag_start_x = None
        self.drag_start_y = None
        self.drag_original_coords = None

    def _on_canvas_resize(self, _event):
        if not self.pdf_document:
            return
        if self._render_resize_after_id is not None:
            self.after_cancel(self._render_resize_after_id)
        self._render_resize_after_id = self.after(120, self._render_after_resize)

    def _render_after_resize(self):
        self._render_resize_after_id = None
        if self.pdf_document:
            self.pdf_manager.render_current_page()

    def _navigate_page(self, action):
        self.navigation_controller.navigate_page(action)

    def _go_to_page_from_entry(self):
        self.navigation_controller.go_to_page_from_entry()

    def _change_zoom(self, action):
        self.navigation_controller.change_zoom(action)

    def _update_zoom_label(self):
        self.navigation_controller.update_zoom_label()

    def _sync_delete_button_state(self):
        self.rectangle_action_controller.sync_delete_button_state()

    def _handle_rectangle_action(self, action_type):
        self.rectangle_action_controller.handle_action(action_type)

    def _open_export_dialog(self):
        self.export_controller.open_export_dialog()

    def open_project(self) -> None:
        source_path = filedialog.askopenfilename(
            parent=self,
            title="Abrir",
            filetypes=[("Proyecto JSON", "*.json"), ("Todos los archivos", "*.*")],
        )
        if not source_path:
            return

        try:
            payload = load_project(source_path)
            pdf_path = payload.get("pdf_path")
            if not pdf_path or not os.path.isfile(pdf_path):
                raise FileNotFoundError(f"No se encontró el PDF original: {pdf_path}")

            expected_hash = payload.get("pdf_sha256", "")
            if expected_hash and calculate_file_hash(pdf_path) != expected_hash:
                messagebox.showwarning(
                    "PDF modificado",
                    "El PDF original cambió desde que se guardó el proyecto. Se abrirá, pero revisa los recuadros antes de exportar.",
                    parent=self,
                )

            self.pdf_manager.reset_current_job()
            self.current_pdf_path = pdf_path
            self.pdf_document = fitz.open(pdf_path)
            self.current_zoom = payload.get("current_zoom")
            self.censored_rectangles = deserialize_rectangles(payload.get("rectangles", []))
            self.current_page = min(
                max(int(payload.get("current_page", 0)), 0),
                max(len(self.pdf_document) - 1, 0),
            )
            self.reserved_history[:] = list(payload.get("reserved_history", []))
            self.confidential_history[:] = list(payload.get("confidential_history", []))
            self.other_law_history[:] = list(payload.get("other_law_history", []))
            self.document_state.committee_data.clear()
            self.document_state.committee_data.update(payload.get("committee_data", {}))
            self.undo_stack.clear()
            self.redo_stack.clear()
            self.selected_rect_id = None
            self.next_rectangle_id = self._next_rectangle_id_from_project()
            self.current_project_path = Path(source_path)
            self.pdf_manager.render_current_page()
            self.set_status(f"Proyecto cargado: {self.current_project_path}")
        except Exception as error:  # noqa: BLE001
            self.show_error("No se pudo abrir", f"No fue posible cargar el proyecto.\n\n{error}")

    def save_project(self) -> None:
        if self.current_project_path is None:
            self.save_project_as()
            return
        self._save_project_to_path(self.current_project_path)

    def save_project_as(self) -> None:
        if not self.pdf_document or not self.current_pdf_path:
            messagebox.showwarning(
                "PDF requerido",
                "Carga un PDF antes de guardar el proyecto.",
                parent=self,
            )
            return

        target_path = filedialog.asksaveasfilename(
            parent=self,
            title="Guardar como",
            defaultextension=".json",
            initialfile="testado.json",
            filetypes=[("Proyecto JSON", "*.json"), ("Todos los archivos", "*.*")],
        )
        if not target_path:
            return
        self.current_project_path = Path(target_path)
        self._save_project_to_path(self.current_project_path)

    def _save_project_to_path(self, target_path: Path) -> None:
        try:
            saved_path = save_project(self.document_state, target_path)
        except Exception as error:  # noqa: BLE001
            self.show_error("No se pudo guardar", f"No fue posible guardar el proyecto.\n\n{error}")
            return
        self.set_status(f"Proyecto guardado: {saved_path}")
        messagebox.showinfo("Proyecto guardado", f"Proyecto guardado en:\n{saved_path}", parent=self)

    def _next_rectangle_id_from_project(self) -> int:
        if not self.censored_rectangles:
            return 1
        return max(rectangle.get("id", 0) for rectangle in self.censored_rectangles) + 1

    def _generate_pdf(self, committee_data=None):
        self.export_controller.generate_pdf(committee_data=committee_data)

    def _is_export_running(self):
        return self.export_controller.is_running()

    def _set_export_controls_state(self, state):
        self.export_controller.set_controls_state(state)

    def _poll_generate_pdf(self, future, output_path):
        self.export_controller._poll_generate_pdf(future, output_path)

    def confirm_exit(self):
        if self._is_export_running():
            messagebox.showwarning(
                EXIT_MESSAGES["export_running_title"],
                EXIT_MESSAGES["export_running_message"],
                parent=self,
            )
            return

        if messagebox.askyesno(
            EXIT_MESSAGES["confirm_title"],
            EXIT_MESSAGES["confirm_message"],
            parent=self,
        ):
            if self.pdf_document:
                self.pdf_document.close()
            self._executor.shutdown(wait=False, cancel_futures=True)
            self.destroy()


if __name__ == "__main__":
    app = TestDataGeneratorApp()
    app.mainloop()
