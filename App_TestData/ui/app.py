import os
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import logging
import sys
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
    EXPORT_MESSAGES,
    FILE_MENU_LABELS,
    NAVIGATION_LABELS,
    NAVIGATION_MESSAGES,
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
from App_TestData.domain.redaction_editing import (
    delete_selected_rectangle,
    redo_last_rectangle,
    refresh_rectangle_metadata,
    undo_last_rectangle,
)
from App_TestData.utils.navigation import (
    get_adjacent_page_index,
    is_valid_page_index,
    parse_page_number,
    to_page_index,
)
from App_TestData.services.pdf_service import PDFManager
from App_TestData.ui.interactions.scroll import setup_mousewheel_scroll
from App_TestData.utils.zoom import format_zoom_percentage, get_next_zoom
from App_TestData.ui.dialogs.catalogue_dialog import show_catalogue_dialog
from App_TestData.ui.dialogs.export_dialog import ExportDialog
from App_TestData.ui.dialogs.help_dialog import show_help_dialog
from App_TestData.ui.layout.main_layout import build_main_layout
from components.shared.windowing import center_window
from components.styles.styles import apply_ctk_style, styles

LOGGER = logging.getLogger(__name__)


class TestDataGeneratorApp(ctk.CTk):
    """Main CustomTkinter application."""

    def __init__(self) -> None:
        super().__init__()
        apply_ctk_style(ctk)
        self.title(APP_WINDOW_TITLE)
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        center_window(self, WINDOW_WIDTH, WINDOW_HEIGHT)

        self.document_state = DocumentState()
        self._init_state()
        self._render_resize_after_id = None
        self._pending_export_future = None
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="testdata-worker")
        styles(self)
        self.pdf_manager = PDFManager(
            self.document_state,
            self,
            self.catalogue_categories,
        )

        widget_map = build_main_layout(self, self._build_callbacks())
        self._register_widgets(widget_map)

        setup_canvas_events(self)
        setup_mousewheel_scroll(
            self.pdf_canvas,
            has_document=lambda: bool(self.pdf_document),
            on_zoom_in=lambda: self._change_zoom("in"),
            on_zoom_out=lambda: self._change_zoom("out"),
        )
        self.protocol("WM_DELETE_WINDOW", self.confirm_exit)

    def _build_callbacks(self) -> dict[str, Any]:
        """Build the callback map consumed by UI components."""
        return {
            "on_new_job": self._start_new_job,
            "on_open_export_dialog": self._open_export_dialog,
            "on_show_catalogue": lambda: show_catalogue_dialog(
                self,
                self.catalogue_sections,
                self.catalogue_items,
            ),
            "on_show_help": lambda: show_help_dialog(self),
            "on_exit": self.confirm_exit,
            "on_rectangle_action": self._handle_rectangle_action,
            "on_previous_page": lambda: self._navigate_page("prev"),
            "on_next_page": lambda: self._navigate_page("next"),
            "on_go_to_page": self._go_to_page_from_entry,
            "on_zoom_in": lambda: self._change_zoom("in"),
            "on_zoom_out": lambda: self._change_zoom("out"),
            "on_canvas_resize": self._on_canvas_resize,
        }

    def _register_widgets(self, widget_map: dict[str, Any]) -> None:
        """Expose built widgets as attributes for the rest of the app."""
        for name, widget in widget_map.items():
            setattr(self, name, widget)
        self._update_zoom_label()
        self._sync_delete_button_state()

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
            total_pages_label.configure(text=NAVIGATION_LABELS["total_pages"].format(total_pages=0))

        self._reset_canvas_interaction_state()
        self._update_zoom_label()
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
            text=NAVIGATION_LABELS["total_pages"].format(total_pages=total_pages)
        )

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
        if not self.pdf_document:
            return

        next_page = get_adjacent_page_index(self.current_page, len(self.pdf_document), action)
        if next_page == self.current_page:
            return

        self.current_page = next_page
        self.pdf_manager.render_current_page()

    def _go_to_page_from_entry(self):
        if not self.pdf_document:
            messagebox.showwarning(
                NAVIGATION_MESSAGES["pdf_required_title"],
                NAVIGATION_MESSAGES["pdf_required_message"],
                parent=self,
            )
            return

        try:
            page_number = parse_page_number(self.page_entry.get())
        except ValueError:
            messagebox.showwarning(
                NAVIGATION_MESSAGES["invalid_page_title"],
                NAVIGATION_MESSAGES["invalid_page_message"],
                parent=self,
            )
            return

        page_index = to_page_index(page_number)
        total_pages = len(self.pdf_document)
        if not is_valid_page_index(page_index, total_pages):
            messagebox.showwarning(
                NAVIGATION_MESSAGES["page_out_of_range_title"],
                NAVIGATION_MESSAGES["page_out_of_range_message"].format(total_pages=total_pages),
                parent=self,
            )
            return

        self.current_page = page_index
        self.pdf_manager.render_current_page()

    def _change_zoom(self, action):
        if not self.pdf_document:
            return

        next_zoom = get_next_zoom(self.current_zoom, action)
        if next_zoom is None or next_zoom == self.current_zoom:
            return

        self.current_zoom = next_zoom
        self._update_zoom_label()
        self.pdf_manager.render_current_page()

    def _update_zoom_label(self):
        zoom_label = getattr(self, "zoom_label", None)
        if zoom_label is not None:
            zoom_label.configure(text=format_zoom_percentage(self.current_zoom))

    def _sync_delete_button_state(self):
        delete_button = getattr(self, "delete_rect_btn", None)
        if delete_button is not None:
            delete_button.configure(state=tk.NORMAL if self.selected_rect_id else tk.DISABLED)

    def _handle_rectangle_action(self, action_type):
        if action_type == "delete":
            rectangles, selected_rect_id, affected_rectangle, action = delete_selected_rectangle(
                self.censored_rectangles,
                self.selected_rect_id,
            )
            if action is not None:
                self.undo_stack.append(action)
                self.redo_stack.clear()
            self.censored_rectangles = rectangles
            self.selected_rect_id = selected_rect_id
        elif action_type == "undo":
            rectangles, undo_stack, redo_stack, affected_rectangle = undo_last_rectangle(
                self.censored_rectangles,
                list(self.undo_stack),
                list(self.redo_stack),
            )
            self.censored_rectangles = rectangles
            self._replace_stack(self.undo_stack, undo_stack)
            self._replace_stack(self.redo_stack, redo_stack)
            self.selected_rect_id = None
        elif action_type == "redo":
            rectangles, undo_stack, redo_stack, affected_rectangle = redo_last_rectangle(
                self.censored_rectangles,
                list(self.undo_stack),
                list(self.redo_stack),
            )
            self.censored_rectangles = rectangles
            self._replace_stack(self.undo_stack, undo_stack)
            self._replace_stack(self.redo_stack, redo_stack)
            self.selected_rect_id = None
        else:
            return

        if affected_rectangle:
            self._hide_canvas_item(affected_rectangle.get("canvas_rect_id"))
            self._hide_canvas_item(affected_rectangle.get("canvas_text_id"))

        refresh_rectangle_metadata(self.censored_rectangles)
        self._sync_delete_button_state()
        if self.pdf_document:
            self.pdf_manager.render_current_page()

    def _replace_stack(self, target_stack, new_items):
        target_stack.clear()
        for item in new_items:
            target_stack.append(item)

    def _hide_canvas_item(self, item_id):
        if item_id:
            self.pdf_canvas.itemconfigure(item_id, state="hidden")

    def _open_export_dialog(self):
        if not self.pdf_document or not self.current_pdf_path:
            messagebox.showwarning(
                EXPORT_MESSAGES["pdf_required_title"],
                EXPORT_MESSAGES["pdf_required_message"],
                parent=self,
            )
            return
        ExportDialog(self)

    def _generate_pdf(self, committee_data=None):
        if self._is_export_running():
            messagebox.showwarning(
                EXPORT_MESSAGES["export_running_title"],
                EXPORT_MESSAGES["export_running_message"],
                parent=self,
            )
            return

        if not self.censored_rectangles:
            messagebox.showwarning(
                EXPORT_MESSAGES["no_changes_title"],
                EXPORT_MESSAGES["no_changes_message"],
                parent=self,
            )
            return

        output_path = filedialog.asksaveasfilename(
            parent=self,
            title=EXPORT_MESSAGES["save_dialog_title"],
            defaultextension=".pdf",
            filetypes=[(EXPORT_MESSAGES["save_dialog_filetypes_label"], "*.pdf")],
        )
        if not output_path:
            return

        if os.path.abspath(output_path) == os.path.abspath(self.current_pdf_path):
            messagebox.showwarning(
                EXPORT_MESSAGES["invalid_path_title"],
                EXPORT_MESSAGES["invalid_path_message"],
                parent=self,
            )
            return

        self.message_label.configure(text=EXPORT_MESSAGES["generating_status"])
        self._set_export_controls_state("disabled")
        pdf_bytes = self.pdf_document.tobytes()
        rectangles_snapshot = deepcopy(self.censored_rectangles)
        committee_snapshot = deepcopy(committee_data)
        future = self._executor.submit(
            self.pdf_manager.generate_pdf,
            output_path,
            committee_snapshot,
            pdf_bytes=pdf_bytes,
            rectangles=rectangles_snapshot,
        )
        self._pending_export_future = future
        self.after(100, lambda: self._poll_generate_pdf(future, output_path))

    def _is_export_running(self):
        return self._pending_export_future is not None and not self._pending_export_future.done()

    def _set_export_controls_state(self, state):
        for widget_name in ("file_button", "catalogue_button"):
            widget = getattr(self, widget_name, None)
            if widget is not None:
                widget.configure(state=state)

        if hasattr(self, "file_menu"):
            try:
                self.file_menu.entryconfig(FILE_MENU_LABELS["save_pdf"], state=state)
            except tk.TclError:
                pass

    def _poll_generate_pdf(self, future, output_path):
        if not future.done():
            self.after(100, lambda: self._poll_generate_pdf(future, output_path))
            return

        try:
            future.result()
            self.message_label.configure(
                text=EXPORT_MESSAGES["generated_status"].format(output_path=output_path)
            )
            messagebox.showinfo(
                EXPORT_MESSAGES["generated_title"],
                EXPORT_MESSAGES["generated_message"],
                parent=self,
            )
        except Exception as error:
            LOGGER.exception("Unable to generate redacted PDF")
            self.message_label.configure(text=EXPORT_MESSAGES["error_status"])
            messagebox.showerror(
                EXPORT_MESSAGES["error_title"],
                EXPORT_MESSAGES["error_message"].format(error=error),
                parent=self,
            )
        finally:
            if self._pending_export_future is future:
                self._pending_export_future = None
            self._set_export_controls_state("normal")

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
