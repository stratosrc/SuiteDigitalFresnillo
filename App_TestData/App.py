import os
import sys
from collections import deque
from concurrent.futures import ThreadPoolExecutor
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk


if __package__ in {None, ""}:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from App_TestData.testdata_components.config.ui_strings import (
    APP_WINDOW_TITLE,
    EXIT_MESSAGES,
    EXPORT_MESSAGES,
    FILE_MENU_LABELS,
    NAVIGATION_MESSAGES,
)
from App_TestData.testdata_components.constants import (
    UNDO_REDO_STACK_LIMIT,
    WINDOW_HEIGHT,
    WINDOW_MIN_HEIGHT,
    WINDOW_MIN_WIDTH,
    WINDOW_WIDTH,
)
from App_TestData.testdata_components.data.catalogue_data import (
    CATALOGUE_SECTIONS,
    build_catalogue_categories,
    build_catalogue_items,
)
from App_TestData.testdata_components.logic.drawing_functions import setup_canvas_events
from App_TestData.testdata_components.logic.editing_functions import (
    delete_selected_rectangle,
    redo_last_rectangle,
    refresh_rectangle_metadata,
    undo_last_rectangle,
)
from App_TestData.testdata_components.logic.navigation_functions import (
    get_adjacent_page_index,
    is_valid_page_index,
    parse_page_number,
    to_page_index,
)
from App_TestData.testdata_components.logic.pdf_manager import PDFManager
from App_TestData.testdata_components.logic.scroll_functions import setup_mousewheel_scroll
from App_TestData.testdata_components.logic.zoom_functions import format_zoom_percentage, get_next_zoom
from App_TestData.testdata_components.ui.catalogue_dialog import show_catalogue_dialog
from App_TestData.testdata_components.ui.export_dialog import ExportDialog
from App_TestData.testdata_components.ui.help_dialog import show_help_dialog
from App_TestData.testdata_components.ui.main_layout import build_main_layout
from components.shared.windowing import center_window
from components.styles.styles import apply_ctk_style, styles


class TestDataGeneratorApp(ctk.CTk):
    """Main CustomTkinter application."""

    def __init__(self):
        super().__init__()
        apply_ctk_style(ctk)
        self.title(APP_WINDOW_TITLE)
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        center_window(self, WINDOW_WIDTH, WINDOW_HEIGHT)

        self._init_state()
        self._render_resize_after_id = None
        self._pending_export_future = None
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="testdata-worker")
        styles(self)
        self.pdf_manager = PDFManager(self)

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

    def _build_callbacks(self):
        """Build the callback map consumed by UI components."""
        return {
            "on_load_pdf": self.pdf_manager.load_pdf,
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

    def _register_widgets(self, widget_map):
        """Expose built widgets as attributes for the rest of the app."""
        for name, widget in widget_map.items():
            setattr(self, name, widget)
        self._update_zoom_label()
        self._sync_delete_button_state()

    def _init_state(self):
        self.current_pdf_path = None
        self.pdf_document = None
        self.pdf_page_image = None
        self.current_page = 0
        self.current_zoom = None
        self.censored_rectangles = []
        self.undo_stack = deque(maxlen=UNDO_REDO_STACK_LIMIT)
        self.redo_stack = deque(maxlen=UNDO_REDO_STACK_LIMIT)
        self.next_rectangle_id = 1
        self.selected_rect_id = None
        self.reserved_history = []
        self.confidential_history = []
        self.other_law_history = []

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
            rectangles, selected_rect_id, affected_rectangle = delete_selected_rectangle(
                self.censored_rectangles,
                self.selected_rect_id,
            )
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
        future = self._executor.submit(self.pdf_manager.generate_pdf, output_path, committee_data)
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
