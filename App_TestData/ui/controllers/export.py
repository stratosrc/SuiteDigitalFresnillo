"""PDF export coordination for Test Data."""

from __future__ import annotations

from copy import deepcopy
import logging
import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox

from App_TestData.config.ui_strings import EXPORT_MESSAGES, FILE_MENU_LABELS
from App_TestData.ui.dialogs.export_dialog import ExportDialog
from components.shared.atomic_output import OutputCancelled
from components.shared.platform import IS_MACOS

LOGGER = logging.getLogger(__name__)


class ExportController:
    """Own export dialog, background task and export UI state."""

    def __init__(self, app, executor) -> None:
        self.app = app
        self.executor = executor
        self.pending_future = None
        self.cancel_requested = False
        self.cancel_event = threading.Event()

    def open_export_dialog(self) -> None:
        if not self.app.pdf_document or not self.app.current_pdf_path:
            messagebox.showwarning(
                EXPORT_MESSAGES["pdf_required_title"],
                EXPORT_MESSAGES["pdf_required_message"],
                parent=self.app,
            )
            return
        ExportDialog(self.app, export_callback=self.generate_pdf)

    def generate_pdf(self, committee_data=None, export_quality="standard") -> None:
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
        self.cancel_event.clear()
        self.set_controls_state("disabled")
        self.app.show_export_progress(EXPORT_MESSAGES["generating_status"])
        rectangles_snapshot = deepcopy(self.app.censored_rectangles)
        committee_snapshot = deepcopy(committee_data)
        if IS_MACOS:
            self._generate_pdf_synchronously(
                output_path,
                committee_snapshot,
                rectangles_snapshot,
                export_quality,
            )
            return

        future = self.executor.submit(
            self.app.pdf_manager.generate_pdf,
            output_path,
            committee_snapshot,
            source_path=self.app.current_pdf_path,
            rectangles=rectangles_snapshot,
            cancel_check=self.cancel_event.is_set,
            export_quality=export_quality,
        )
        self.pending_future = future
        self.app.after(100, lambda: self._poll_generate_pdf(future, output_path))

    def _generate_pdf_synchronously(
        self,
        output_path: str,
        committee_data,
        rectangles,
        export_quality,
    ) -> None:
        try:
            self.app.update_idletasks()
            self.app.pdf_manager.generate_pdf(
                output_path,
                committee_data,
                source_path=self.app.current_pdf_path,
                rectangles=rectangles,
                cancel_check=self.cancel_event.is_set,
                export_quality=export_quality,
            )
            self.app.message_label.configure(
                text=EXPORT_MESSAGES["generated_status"].format(output_path=output_path)
            )
            messagebox.showinfo(
                EXPORT_MESSAGES["generated_title"],
                EXPORT_MESSAGES["generated_message"],
                parent=self.app,
            )
        except OutputCancelled:
            self.app.message_label.configure(text="Exportación cancelada")
        except Exception as error:  # noqa: BLE001
            LOGGER.exception("Unable to generate redacted PDF")
            self.app.message_label.configure(text=EXPORT_MESSAGES["error_status"])
            messagebox.showerror(
                EXPORT_MESSAGES["error_title"],
                EXPORT_MESSAGES["error_message"].format(error=error),
                parent=self.app,
            )
        finally:
            self.cancel_requested = False
            self.cancel_event.clear()
            self.app.hide_export_progress()
            self.set_controls_state("normal")

    def is_running(self) -> bool:
        return self.pending_future is not None and not self.pending_future.done()

    def cancel(self) -> None:
        if self.pending_future is None:
            return
        self.cancel_requested = True
        self.cancel_event.set()
        self.pending_future.cancel()
        self.app.update_export_progress("Cancelando al terminar el paso actual...")

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
        except OutputCancelled:
            self.app.message_label.configure(text="Exportación cancelada")
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
            self.cancel_event.clear()
            self.app.hide_export_progress()
            self.set_controls_state("normal")
