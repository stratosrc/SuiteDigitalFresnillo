"""PDF export coordination for Test Data."""

from __future__ import annotations

from copy import deepcopy
import logging
import os
import tkinter as tk
from tkinter import filedialog, messagebox

from App_TestData.config.ui_strings import EXPORT_MESSAGES, FILE_MENU_LABELS
from App_TestData.ui.dialogs.export_dialog import ExportDialog

LOGGER = logging.getLogger(__name__)


class ExportController:
    """Own export dialog, background task and export UI state."""

    def __init__(self, app, executor) -> None:
        self.app = app
        self.executor = executor
        self.pending_future = None
        self.cancel_requested = False

    def open_export_dialog(self) -> None:
        if not self.app.pdf_document or not self.app.current_pdf_path:
            messagebox.showwarning(
                EXPORT_MESSAGES["pdf_required_title"],
                EXPORT_MESSAGES["pdf_required_message"],
                parent=self.app,
            )
            return
        ExportDialog(self.app, export_callback=self.generate_pdf)

    def generate_pdf(self, committee_data=None) -> None:
        if self.is_running():
            messagebox.showwarning(
                EXPORT_MESSAGES["export_running_title"],
                EXPORT_MESSAGES["export_running_message"],
                parent=self.app,
            )
            return

        if not self.app.censored_rectangles:
            messagebox.showwarning(
                EXPORT_MESSAGES["no_changes_title"],
                EXPORT_MESSAGES["no_changes_message"],
                parent=self.app,
            )
            return

        output_path = filedialog.asksaveasfilename(
            parent=self.app,
            title=EXPORT_MESSAGES["save_dialog_title"],
            defaultextension=".pdf",
            filetypes=[(EXPORT_MESSAGES["save_dialog_filetypes_label"], "*.pdf")],
        )
        if not output_path:
            return

        if os.path.abspath(output_path) == os.path.abspath(self.app.current_pdf_path):
            messagebox.showwarning(
                EXPORT_MESSAGES["invalid_path_title"],
                EXPORT_MESSAGES["invalid_path_message"],
                parent=self.app,
            )
            return

        self.app.message_label.configure(text=EXPORT_MESSAGES["generating_status"])
        self.cancel_requested = False
        self.set_controls_state("disabled")
        rectangles_snapshot = deepcopy(self.app.censored_rectangles)
        committee_snapshot = deepcopy(committee_data)
        future = self.executor.submit(
            self.app.pdf_manager.generate_pdf,
            output_path,
            committee_snapshot,
            source_path=self.app.current_pdf_path,
            rectangles=rectangles_snapshot,
        )
        self.pending_future = future
        self.app.after(100, lambda: self._poll_generate_pdf(future, output_path))

    def is_running(self) -> bool:
        return self.pending_future is not None and not self.pending_future.done()

    def cancel(self) -> None:
        if self.pending_future is None:
            return
        self.cancel_requested = True
        self.pending_future.cancel()
        self.app.message_label.configure(text="Cancelando exportación...")

    def set_controls_state(self, state: str) -> None:
        for widget_name in ("file_button", "catalogue_button"):
            widget = getattr(self.app, widget_name, None)
            if widget is not None:
                widget.configure(state=state)

        if hasattr(self.app, "file_menu"):
            try:
                self.app.file_menu.entryconfig(FILE_MENU_LABELS["export_pdf"], state=state)
            except tk.TclError:
                pass

    def _poll_generate_pdf(self, future, output_path: str) -> None:
        if not future.done():
            self.app.after(100, lambda: self._poll_generate_pdf(future, output_path))
            return

        try:
            if future.cancelled():
                self.app.message_label.configure(text="Exportación cancelada")
                return
            future.result()
            if self.cancel_requested:
                try:
                    os.unlink(output_path)
                except OSError:
                    pass
                self.app.message_label.configure(text="Exportación cancelada")
                return
            self.app.message_label.configure(
                text=EXPORT_MESSAGES["generated_status"].format(output_path=output_path)
            )
            messagebox.showinfo(
                EXPORT_MESSAGES["generated_title"],
                EXPORT_MESSAGES["generated_message"],
                parent=self.app,
            )
        except Exception as error:  # noqa: BLE001
            LOGGER.exception("Unable to generate redacted PDF")
            self.app.message_label.configure(text=EXPORT_MESSAGES["error_status"])
            messagebox.showerror(
                EXPORT_MESSAGES["error_title"],
                EXPORT_MESSAGES["error_message"].format(error=error),
                parent=self.app,
            )
        finally:
            if self.pending_future is future:
                self.pending_future = None
            self.cancel_requested = False
            self.set_controls_state("normal")
