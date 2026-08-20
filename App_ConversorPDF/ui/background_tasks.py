"""Background worker lifecycle for PDF conversions."""
from __future__ import annotations

import logging
from pathlib import Path
from queue import Empty
import threading
from tkinter import messagebox


try:
    from tkinterdnd2 import DND_FILES
except ImportError:
    DND_FILES = None

from components.shared.atomic_output import OutputCancelled


SPLIT_TOGGLE_TOOLTIP = "Separar cada hoja o pagina seleccionada en PDFs individuales."
LOGGER = logging.getLogger(__name__)
LIST_PANEL_TOP_PADDING = 24
LIST_PANEL_BOTTOM_PADDING = 24
LIST_ACTION_HEIGHT = 62



class BackgroundTaskMixin:
    def _run_conversion_task(self, status_text: str, task, on_success) -> None:
        if self.is_busy:
            return
        self._cancel_event.clear()
        self._show_loading(status_text)

        def worker() -> None:
            try:
                result = task()
            except OutputCancelled:
                self._worker_events.put(("cancelled",))
                return
            except Exception as error:  # noqa: BLE001
                self._worker_events.put(("error", error))
                return
            if self._cancel_event.is_set() and isinstance(result, Path):
                result.unlink(missing_ok=True)
                self._worker_events.put(("cancelled",))
                return
            self._worker_events.put(("success", result, on_success))

        threading.Thread(target=worker, daemon=True).start()

    def _show_loading(self, status_text: str) -> None:
        self.is_busy = True
        self.loading_status_label.configure(text=status_text)
        self.loading_overlay.grid()
        self.loading_overlay.lift()
        self.loading_progress.start()

    def _hide_loading(self) -> None:
        self.loading_progress.stop()
        self.loading_overlay.grid_remove()
        self.is_busy = False

    def _cancel_conversion(self) -> None:
        if not self.is_busy:
            return
        self._cancel_event.set()
        self.cancel_conversion_button.configure(state="disabled")
        self.loading_status_label.configure(text="Cancelando operación...")

    def _set_loading_status_from_worker(self, status_text: str) -> None:
        self._worker_events.put(("status", status_text))

    def _poll_worker_events(self) -> None:
        self._worker_poll_after_id = None
        while True:
            try:
                event = self._worker_events.get_nowait()
            except Empty:
                break

            event_type = event[0]
            if event_type == "status":
                self.loading_status_label.configure(text=event[1])
            elif event_type == "success":
                self._finish_conversion_success(event[1], event[2])
            elif event_type == "error":
                self._finish_conversion_error(event[1])
            elif event_type == "cancelled":
                self._hide_loading()
                self.cancel_conversion_button.configure(state="normal")
                messagebox.showinfo("Conversión cancelada", "La conversión fue cancelada.", parent=self)

        if not self._closing and self.winfo_exists():
            self._worker_poll_after_id = self.after(50, self._poll_worker_events)

    def _finish_conversion_success(self, result, on_success) -> None:
        self._hide_loading()
        self.cancel_conversion_button.configure(state="normal")
        on_success(result)

    def _finish_conversion_error(self, error: Exception) -> None:
        self._hide_loading()
        self.cancel_conversion_button.configure(state="normal")
        messagebox.showerror("No se pudo convertir", str(error), parent=self)
