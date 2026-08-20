"""PDF conversion workspace coordinator."""

from __future__ import annotations

import logging
from pathlib import Path
from queue import Queue
import threading
from tkinter import messagebox

import customtkinter as ctk

try:
    from tkinterdnd2 import DND_FILES
except ImportError:
    DND_FILES = None

from App_ConversorPDF.services.converter import PdfConverter
from App_ConversorPDF.services.pdf_merger import PdfMerger
from App_ConversorPDF.ui.background_tasks import BackgroundTaskMixin
from App_ConversorPDF.ui.conversion_workflow import ConversionWorkflowMixin
from App_ConversorPDF.ui.merge_workflow import MergeWorkflowMixin
from App_ConversorPDF.ui.theme import APP_BACKGROUND
from App_ConversorPDF.ui.workspace_layout import WorkspaceLayoutMixin
from App_ConversorPDF.ui.workspace_models import SourceFileItem
from components.shared.accessibility import enable_visible_focus
from components.shared.shortcuts import bind_common_shortcuts


LOGGER = logging.getLogger(__name__)


class PdfConverterMainFrame(
    WorkspaceLayoutMixin,
    MergeWorkflowMixin,
    ConversionWorkflowMixin,
    BackgroundTaskMixin,
    ctk.CTkFrame,
):
    def __init__(self, master: ctk.CTk) -> None:
        super().__init__(master, fg_color=APP_BACKGROUND, corner_radius=0)
        self.master = master
        self.converter = PdfConverter()
        self.pdf_merger = PdfMerger()
        self.files: list[SourceFileItem] = []
        self.merge_files: list[Path] = []
        self.active_view = "convert"
        self._merge_drag_index: int | None = None
        self._merge_drop_index: int | None = None
        self._merge_rows: list[ctk.CTkFrame] = []
        self._merge_drop_indicators: list[ctk.CTkFrame] = []
        self.output_buttons: list[ctk.CTkButton] = []
        self.header_logo_image: ctk.CTkImage | None = None
        self.upload_icon_image: ctk.CTkImage | None = None
        self.upload_icon_hover_image: ctk.CTkImage | None = None
        self.download_icon_image: ctk.CTkImage | None = None
        self.download_icon_hover_image: ctk.CTkImage | None = None
        self.download_item_icon_image: ctk.CTkImage | None = None
        self.separate_icon_image: ctk.CTkImage | None = None
        self.separate_icon_on_image: ctk.CTkImage | None = None
        self.is_busy = False
        self._worker_events: Queue[tuple] = Queue()
        self._worker_poll_after_id: str | None = None
        self._closing = False
        self._cancel_event = threading.Event()
        self._dnd_available = DND_FILES is not None
        self._build_layout()
        self._refresh_outputs()
        self._worker_poll_after_id = self.after(50, self._poll_worker_events)
        bind_common_shortcuts(
            self.master,
            new=self.reset_work,
            open_=self._select_active_files,
            save=self._save_active_output,
            save_as=self._save_active_output_as,
        )
        self.after_idle(lambda: enable_visible_focus(self))

    def confirm_exit(self) -> None:
        if self.is_busy:
            messagebox.showwarning(
                "Conversión en curso",
                "Espera a que termine la conversión antes de cerrar la aplicación.",
                parent=self,
            )
            return
        self._closing = True
        if self._worker_poll_after_id is not None:
            self.after_cancel(self._worker_poll_after_id)
            self._worker_poll_after_id = None
        self.master.destroy()

    def destroy(self) -> None:
        self._closing = True
        if self._worker_poll_after_id is not None:
            self.after_cancel(self._worker_poll_after_id)
            self._worker_poll_after_id = None
        super().destroy()
