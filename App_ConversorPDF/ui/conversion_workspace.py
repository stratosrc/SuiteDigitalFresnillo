"""Conversor PDF workspace implementation."""

from __future__ import annotations

from dataclasses import dataclass, field
import logging
from pathlib import Path
from queue import Empty, Queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
import sys

import customtkinter as ctk

if sys.platform == "darwin":
    DND_FILES = None
else:
    try:
        from tkinterdnd2 import DND_FILES
    except ImportError:
        DND_FILES = None

from App_ConversorPDF.config import (
    APP_DESCRIPTION,
    CONVERTER_LOGO_PATH,
    DOCUMENT_EXTENSIONS,
    DOWNLOAD_ICON_HOVER_PATH,
    DOWNLOAD_ITEM_ICON_PATH,
    DOWNLOAD_ICON_PATH,
    PDF_EXTENSIONS,
    SEPARATE_ICON_ON_PATH,
    SEPARATE_ICON_PATH,
    SHEET_EXTENSIONS,
    SUPPORTED_EXTENSIONS,
    UPLOAD_ICON_HOVER_PATH,
    UPLOAD_ICON_PATH,
)
from App_ConversorPDF.services.converter import ConversionRequest, PdfConverter
from App_ConversorPDF.services.output_planner import PlannedOutput, build_output_plan
from App_ConversorPDF.services.pdf_merger import PdfMerger
from App_ConversorPDF.ui.dialogs import show_help_dialog
from App_ConversorPDF.ui.theme import (
    APP_BACKGROUND,
    BORDER_COLOR,
    DANGER_BUTTON,
    DANGER_BUTTON_ACTIVE,
    DARK_BACKGROUND,
    HEADER_LOGO_SIZE,
    LEFT_PANEL_BACKGROUND,
    PRIMARY_BUTTON,
    PRIMARY_BUTTON_ACTIVE,
    PRIMARY_BUTTON_PRESSED,
    RIGHT_PANEL_BACKGROUND,
    SURFACE_BACKGROUND,
    TEXT_DARK,
    TEXT_LIGHT,
    TEXT_MUTED,
    make_font,
)
from components.shared.images import load_ctk_image
from components.shared.accessibility import enable_visible_focus
from components.shared.atomic_output import OutputCancelled
from components.shared.shortcuts import bind_common_shortcuts
from components.shared.tooltip import Tooltip
from components.shared.topbar import TopbarButton, TopbarStyle, build_topbar


SPLIT_TOGGLE_TOOLTIP = "Separar cada hoja o pagina seleccionada en PDFs individuales."
LOGGER = logging.getLogger(__name__)
LIST_PANEL_TOP_PADDING = 24
LIST_PANEL_BOTTOM_PADDING = 24
LIST_ACTION_HEIGHT = 62


@dataclass(slots=True)
class SourceFileItem:
    path: Path
    sheet_var: tk.StringVar | None = None
    split_var: tk.BooleanVar | None = None
    output_names: list[str] = field(default_factory=list)


class PdfConverterMainFrame(ctk.CTkFrame):
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

    def _build_layout(self) -> None:
        self.pack(fill="both", expand=True)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        self._build_topbar()
        self._build_header()
        self._build_mode_toolbar()
        self._build_body()
        self._build_merge_body()
        self._build_loading_overlay()

    def _build_topbar(self) -> None:
        build_topbar(
            self,
            self._topbar_style(),
            (
                TopbarButton("new", "Nuevo", self.reset_work, 0),
                TopbarButton("help", "Ayuda", self._show_help_dialog, 1),
                TopbarButton("exit", "Salir", self.confirm_exit, 3, danger=True),
            ),
        )

    @staticmethod
    def _topbar_style() -> TopbarStyle:
        return TopbarStyle(
            background=PRIMARY_BUTTON_PRESSED,
            primary=PRIMARY_BUTTON,
            primary_hover=PRIMARY_BUTTON_ACTIVE,
            danger=DANGER_BUTTON,
            danger_hover=DANGER_BUTTON_ACTIVE,
            text=TEXT_LIGHT,
            font=make_font(12),
        )

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color=DARK_BACKGROUND, corner_radius=0, height=118)
        header.grid(row=1, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        header.grid_propagate(False)

        ctk.CTkLabel(
            header,
            text=APP_DESCRIPTION,
            text_color=TEXT_LIGHT,
            font=make_font(18, "bold"),
        ).grid(row=0, column=0, padx=(16, 24), pady=12, sticky="w")
        self._load_header_logo(header)

    def _load_header_logo(self, parent: ctk.CTkFrame) -> None:
        image = load_ctk_image(CONVERTER_LOGO_PATH, HEADER_LOGO_SIZE, crop_alpha=True)
        if image is None:
            return

        self.header_logo_image = image
        ctk.CTkLabel(parent, image=self.header_logo_image, text="").grid(
            row=0,
            column=1,
            padx=(16, 18),
            pady=14,
            sticky="e",
        )

    def _build_mode_toolbar(self) -> None:
        toolbar_height = 36
        toolbar = ctk.CTkFrame(
            self,
            fg_color="#131C46",
            corner_radius=0,
            height=toolbar_height,
        )
        toolbar.grid(row=2, column=0, sticky="ew")
        toolbar.grid_propagate(False)

        self.convert_mode_button = ctk.CTkButton(
            toolbar,
            text="Convertir a PDF",
            command=lambda: self._show_view("convert"),
            width=140,
            height=toolbar_height,
            corner_radius=0,
            border_width=0,
            fg_color="#3B8ED0",
            hover_color="#4B4B4B",
            text_color=TEXT_LIGHT,
            font=make_font(13, "bold"),
        )
        self.convert_mode_button.grid(row=0, column=0, sticky="w")

        self.merge_mode_button = ctk.CTkButton(
            toolbar,
            text="Unir PDFs",
            command=lambda: self._show_view("merge"),
            width=120,
            height=toolbar_height,
            corner_radius=0,
            border_width=0,
            fg_color="#3B8ED0",
            hover_color="#4B4B4B",
            text_color=TEXT_LIGHT,
            font=make_font(13, "bold"),
        )
        self.merge_mode_button.grid(row=0, column=1, sticky="w")

    def _build_body(self) -> None:
        self.converter_body = ctk.CTkFrame(self, fg_color=APP_BACKGROUND, corner_radius=0)
        self.converter_body.grid(row=3, column=0, sticky="nsew")
        self.converter_body.grid_columnconfigure(0, weight=1, uniform="converter")
        self.converter_body.grid_columnconfigure(1, weight=1, uniform="converter")
        self.converter_body.grid_rowconfigure(0, weight=1)

        self.left_panel = ctk.CTkFrame(self.converter_body, fg_color=LEFT_PANEL_BACKGROUND, corner_radius=0)
        self.left_panel.grid(row=0, column=0, sticky="nsew")
        self.left_panel.grid_columnconfigure(0, weight=1)
        self.left_panel.grid_rowconfigure(1, weight=1)
        self.left_panel.grid_rowconfigure(2, weight=0, minsize=LIST_ACTION_HEIGHT)

        self.right_panel = ctk.CTkFrame(self.converter_body, fg_color=RIGHT_PANEL_BACKGROUND, corner_radius=0)
        self.right_panel.grid(row=0, column=1, sticky="nsew")
        self.right_panel.grid_columnconfigure(0, weight=1)
        self.right_panel.grid_rowconfigure(1, weight=1)
        self.right_panel.grid_rowconfigure(2, weight=0, minsize=LIST_ACTION_HEIGHT)

        self._build_upload_panel()
        self._build_download_panel()

    def _build_merge_body(self) -> None:
        self.merge_body = ctk.CTkFrame(self, fg_color=APP_BACKGROUND, corner_radius=0)
        self.merge_body.grid(row=3, column=0, sticky="nsew")
        self.merge_body.grid_columnconfigure(0, weight=3)
        self.merge_body.grid_columnconfigure(1, weight=2)
        self.merge_body.grid_rowconfigure(0, weight=1)

        list_panel = ctk.CTkFrame(self.merge_body, fg_color=LEFT_PANEL_BACKGROUND, corner_radius=0)
        list_panel.grid(row=0, column=0, sticky="nsew")
        list_panel.grid_columnconfigure(0, weight=1)
        list_panel.grid_rowconfigure(1, weight=1)
        self._enable_merge_file_drop(list_panel)

        ctk.CTkLabel(
            list_panel,
            text="Orden de los archivos",
            text_color=TEXT_LIGHT,
            font=make_font(17, "bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 8))

        self.merge_empty_button = ctk.CTkButton(
            list_panel,
            text="Arrastra aquí dos o más PDFs\no haz clic para seleccionarlos",
            command=self._select_merge_files,
            corner_radius=0,
            fg_color=LEFT_PANEL_BACKGROUND,
            hover_color=LEFT_PANEL_BACKGROUND,
            text_color=TEXT_LIGHT,
            font=make_font(14, "bold"),
        )
        self.merge_empty_button.grid(row=1, column=0, sticky="nsew", padx=24, pady=20)
        self._enable_merge_file_drop(self.merge_empty_button)

        self.merge_files_frame = ctk.CTkScrollableFrame(
            list_panel,
            fg_color=LEFT_PANEL_BACKGROUND,
            corner_radius=0,
            scrollbar_button_color=PRIMARY_BUTTON,
            scrollbar_button_hover_color=PRIMARY_BUTTON_ACTIVE,
        )
        self.merge_files_frame.grid(row=1, column=0, sticky="nsew", padx=24, pady=12)
        self.merge_files_frame.grid_columnconfigure(0, weight=1)
        self.merge_files_frame.grid_remove()
        self._enable_merge_file_drop(self.merge_files_frame)

        self.add_merge_files_button = ctk.CTkButton(
            list_panel,
            text="Agregar PDFs",
            command=self._select_merge_files,
            width=150,
            height=38,
            corner_radius=0,
            fg_color=SURFACE_BACKGROUND,
            hover_color="#D7DEE6",
            text_color=TEXT_DARK,
            font=make_font(13, "bold"),
        )
        self.add_merge_files_button.grid(row=2, column=0, pady=(4, 22))
        self.add_merge_files_button.grid_remove()

        action_panel = ctk.CTkFrame(self.merge_body, fg_color=RIGHT_PANEL_BACKGROUND, corner_radius=0)
        action_panel.grid(row=0, column=1, sticky="nsew")
        action_panel.grid_columnconfigure(0, weight=1)
        action_panel.grid_rowconfigure(0, weight=1)

        content = ctk.CTkFrame(action_panel, fg_color=RIGHT_PANEL_BACKGROUND, corner_radius=0)
        content.grid(row=0, column=0, padx=34, pady=34)
        content.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            content,
            text="Unir PDFs",
            text_color=TEXT_DARK,
            font=make_font(22, "bold"),
        ).grid(row=0, column=0, sticky="ew", pady=(0, 10))
        ctk.CTkLabel(
            content,
            text="Arrastra los elementos de la lista para cambiar el orden. "
            "Las páginas se unirán de arriba hacia abajo.",
            text_color=TEXT_MUTED,
            font=make_font(13),
            wraplength=330,
            justify="left",
        ).grid(row=1, column=0, sticky="ew", pady=(0, 24))
        self.merge_count_label = ctk.CTkLabel(
            content,
            text="0 archivos seleccionados",
            text_color=TEXT_DARK,
            font=make_font(13, "bold"),
        )
        self.merge_count_label.grid(row=2, column=0, sticky="ew", pady=(0, 16))
        self.merge_action_button = ctk.CTkButton(
            content,
            text="Unir y guardar",
            command=self._save_merged_pdf,
            height=42,
            corner_radius=0,
            fg_color=PRIMARY_BUTTON,
            hover_color=PRIMARY_BUTTON_ACTIVE,
            text_color=TEXT_LIGHT,
            font=make_font(14, "bold"),
            state="disabled",
        )
        self.merge_action_button.grid(row=3, column=0, sticky="ew")
        self.merge_body.grid_remove()

    def _build_loading_overlay(self) -> None:
        self.loading_overlay = ctk.CTkFrame(self, fg_color="#0F172A", corner_radius=0)
        self.loading_overlay.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.loading_overlay.grid_columnconfigure(0, weight=1)
        self.loading_overlay.grid_rowconfigure(0, weight=1)

        content = ctk.CTkFrame(self.loading_overlay, fg_color="#FFFFFF", corner_radius=0)
        content.grid(row=0, column=0, padx=40, pady=40)
        content.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            content,
            text="Convirtiendo archivos",
            text_color=TEXT_DARK,
            font=make_font(18, "bold"),
        ).grid(row=0, column=0, padx=42, pady=(30, 8), sticky="ew")

        self.loading_status_label = ctk.CTkLabel(
            content,
            text="Preparando conversion...",
            text_color=TEXT_MUTED,
            font=make_font(13),
        )
        self.loading_status_label.grid(row=1, column=0, padx=42, pady=(0, 18), sticky="ew")

        self.loading_progress = ctk.CTkProgressBar(
            content,
            width=280,
            height=8,
            corner_radius=0,
            mode="indeterminate",
            progress_color=PRIMARY_BUTTON,
        )
        self.loading_progress.grid(row=2, column=0, padx=42, pady=(0, 30), sticky="ew")
        self.cancel_conversion_button = ctk.CTkButton(
            content,
            text="Cancelar",
            command=self._cancel_conversion,
            width=110,
            fg_color=DANGER_BUTTON,
            hover_color=DANGER_BUTTON_ACTIVE,
        )
        self.cancel_conversion_button.grid(row=3, column=0, pady=(0, 24))
        self.loading_overlay.grid_remove()

    def _build_upload_panel(self) -> None:
        self._enable_file_drop(self.left_panel)
        self.upload_icon_image = load_ctk_image(UPLOAD_ICON_PATH, (180, 180), crop_alpha=True)
        self.upload_icon_hover_image = load_ctk_image(UPLOAD_ICON_HOVER_PATH, (180, 180), crop_alpha=True)
        self.upload_icon_button = ctk.CTkButton(
            self.left_panel,
            text="Arrastra archivos aquí o haz clic para comenzar",
            image=self.upload_icon_image,
            compound="top",
            command=self._select_files,
            width=1,
            height=1,
            corner_radius=0,
            fg_color=LEFT_PANEL_BACKGROUND,
            hover_color=LEFT_PANEL_BACKGROUND,
            text_color=TEXT_LIGHT,
            font=make_font(14, "bold"),
        )
        self.upload_icon_button.grid(row=1, column=0, sticky="nsew", padx=22, pady=(LIST_PANEL_TOP_PADDING, LIST_PANEL_BOTTOM_PADDING))
        Tooltip(self.upload_icon_button, "Agregar archivos")
        self.upload_icon_button.bind("<Enter>", lambda _event: self._set_icon_hover(self.upload_icon_button, self.upload_icon_hover_image), add=True)
        self.upload_icon_button.bind("<Leave>", lambda _event: self._set_icon_hover(self.upload_icon_button, self.upload_icon_image), add=True)
        self._enable_file_drop(self.upload_icon_button)

        self.files_frame = ctk.CTkScrollableFrame(
            self.left_panel,
            fg_color=LEFT_PANEL_BACKGROUND,
            corner_radius=0,
            scrollbar_button_color=PRIMARY_BUTTON,
            scrollbar_button_hover_color=PRIMARY_BUTTON_ACTIVE,
            height=1,
        )
        self.files_frame.grid(row=1, column=0, sticky="nsew", padx=22, pady=(LIST_PANEL_TOP_PADDING, LIST_PANEL_BOTTOM_PADDING))
        self.files_frame.grid_columnconfigure(0, weight=1)
        self.files_frame.grid_remove()
        self._enable_file_drop(self.files_frame)

        self.upload_action_button = ctk.CTkButton(
            self.left_panel,
            text="Cargar",
            command=self._select_files,
            width=150,
            height=38,
            corner_radius=0,
            fg_color=SURFACE_BACKGROUND,
            hover_color="#D7DEE6",
            text_color=TEXT_DARK,
            font=make_font(13, "bold"),
        )
        self.upload_action_button.grid(row=2, column=0, pady=(0, 24))
        self.upload_action_button.grid_remove()

    def _build_download_panel(self) -> None:
        self.download_icon_image = load_ctk_image(DOWNLOAD_ICON_PATH, (180, 180), crop_alpha=True)
        self.download_icon_hover_image = load_ctk_image(DOWNLOAD_ICON_HOVER_PATH, (180, 180), crop_alpha=True)
        self.download_item_icon_image = load_ctk_image(DOWNLOAD_ITEM_ICON_PATH, (18, 18), crop_alpha=True)
        self.separate_icon_image = load_ctk_image(SEPARATE_ICON_PATH, (28, 28), crop_alpha=True)
        self.separate_icon_on_image = load_ctk_image(SEPARATE_ICON_ON_PATH, (28, 28), crop_alpha=True)
        self.download_icon_button = ctk.CTkButton(
            self.right_panel,
            text="Los archivos listos para convertir aparecerán aquí",
            image=self.download_icon_image,
            compound="top",
            command=self._convert_first_output,
            width=1,
            height=1,
            corner_radius=0,
            fg_color=RIGHT_PANEL_BACKGROUND,
            hover_color=RIGHT_PANEL_BACKGROUND,
            text_color=TEXT_DARK,
            font=make_font(14, "bold"),
        )
        self.download_icon_button.grid(row=1, column=0, sticky="nsew", padx=22, pady=(LIST_PANEL_TOP_PADDING, LIST_PANEL_BOTTOM_PADDING))
        Tooltip(self.download_icon_button, "Convertir y guardar")
        self.download_icon_button.bind("<Enter>", lambda _event: self._set_icon_hover(self.download_icon_button, self.download_icon_hover_image), add=True)
        self.download_icon_button.bind("<Leave>", lambda _event: self._set_icon_hover(self.download_icon_button, self.download_icon_image), add=True)

        self.outputs_frame = ctk.CTkScrollableFrame(
            self.right_panel,
            fg_color=RIGHT_PANEL_BACKGROUND,
            corner_radius=0,
            scrollbar_button_color=PRIMARY_BUTTON,
            scrollbar_button_hover_color=PRIMARY_BUTTON_ACTIVE,
            height=1,
        )
        self.outputs_frame.grid(row=1, column=0, sticky="nsew", padx=22, pady=(LIST_PANEL_TOP_PADDING, LIST_PANEL_BOTTOM_PADDING))
        self.outputs_frame.grid_columnconfigure(0, weight=1)
        self.outputs_frame.grid_remove()

        self.download_action_button = ctk.CTkButton(
            self.right_panel,
            text="Descargar todos",
            command=self._save_all_outputs,
            width=150,
            height=38,
            corner_radius=0,
            fg_color=PRIMARY_BUTTON,
            hover_color=PRIMARY_BUTTON_ACTIVE,
            text_color=TEXT_LIGHT,
            font=make_font(13, "bold"),
        )
        self.download_action_button.grid(row=2, column=0, pady=(0, 24))
        self.download_action_button.grid_remove()

    def _select_files(self) -> None:
        if self.is_busy:
            return
        patterns = " ".join(f"*{extension}" for extension in sorted(SUPPORTED_EXTENSIONS))
        selected_paths = filedialog.askopenfilenames(
            parent=self,
            title="Seleccionar archivos",
            filetypes=[
                ("Archivos soportados", patterns),
                ("Todos los archivos", "*.*"),
            ],
        )
        if not selected_paths:
            return

        self._add_files(selected_paths)

    def _select_active_files(self) -> None:
        if self.active_view == "merge":
            self._select_merge_files()
        else:
            self._select_files()

    def _save_active_output(self) -> None:
        if self.active_view == "merge":
            self._save_merged_pdf()
        else:
            self._convert_first_output()

    def _save_active_output_as(self) -> None:
        if self.active_view == "merge":
            self._save_merged_pdf()
        else:
            self._save_all_outputs()

    def _show_view(self, view_name: str) -> None:
        if self.is_busy or view_name not in {"convert", "merge"}:
            return
        self.active_view = view_name
        if view_name == "merge":
            self.converter_body.grid_remove()
            self.merge_body.grid()
        else:
            self.merge_body.grid_remove()
            self.converter_body.grid()

    def _select_merge_files(self) -> None:
        if self.is_busy:
            return
        selected_paths = filedialog.askopenfilenames(
            parent=self,
            title="Seleccionar PDFs para unir",
            filetypes=[("Archivos PDF", "*.pdf"), ("Todos los archivos", "*.*")],
        )
        if selected_paths:
            self._add_merge_files(selected_paths)

    def _add_merge_files(self, raw_paths) -> None:
        existing = {str(path.resolve()).casefold() for path in self.merge_files}
        invalid_names: list[str] = []
        changed = False
        for raw_path in raw_paths:
            path = Path(raw_path)
            if path.suffix.lower() != ".pdf" or not path.is_file():
                invalid_names.append(path.name)
                continue
            key = str(path.resolve()).casefold()
            if key in existing:
                continue
            self.merge_files.append(path)
            existing.add(key)
            changed = True

        if changed:
            self._render_merge_files()
        if invalid_names:
            messagebox.showwarning(
                "Archivos no admitidos",
                "Sólo se pueden agregar archivos PDF válidos.",
                parent=self,
            )

    def _remove_merge_file(self, index: int) -> None:
        if self.is_busy:
            return
        if 0 <= index < len(self.merge_files):
            del self.merge_files[index]
            self._render_merge_files()

    def _render_merge_files(self) -> None:
        for child in self.merge_files_frame.winfo_children():
            child.destroy()
        self._merge_rows.clear()
        self._merge_drop_indicators.clear()
        self._merge_drag_index = None
        self._merge_drop_index = None

        for index, path in enumerate(self.merge_files):
            indicator = ctk.CTkFrame(
                self.merge_files_frame,
                fg_color="#3B8ED0",
                corner_radius=0,
                height=4,
            )
            indicator.grid(row=index * 2, column=0, sticky="ew", padx=8, pady=2)
            indicator.grid_remove()
            self._merge_drop_indicators.append(indicator)

            row = ctk.CTkFrame(self.merge_files_frame, fg_color="#1E2858", corner_radius=0)
            row.grid(row=index * 2 + 1, column=0, sticky="ew", pady=(0, 7))
            row.grid_columnconfigure(2, weight=1)
            self._merge_rows.append(row)

            handle = ctk.CTkLabel(
                row,
                text="≡",
                width=34,
                text_color="#B8C2D6",
                font=make_font(22, "bold"),
                cursor="fleur",
            )
            handle.grid(row=0, column=0, rowspan=2, padx=(8, 2), pady=8)
            number = ctk.CTkLabel(
                row,
                text=str(index + 1),
                width=28,
                height=28,
                corner_radius=14,
                fg_color=PRIMARY_BUTTON,
                text_color=TEXT_LIGHT,
                font=make_font(12, "bold"),
            )
            number.grid(row=0, column=1, rowspan=2, padx=(0, 8), pady=14)
            name_label = ctk.CTkLabel(
                row,
                text=path.name,
                text_color=TEXT_LIGHT,
                font=make_font(12, "bold"),
                anchor="w",
            )
            name_label.grid(row=0, column=2, sticky="ew", pady=(8, 0))
            path_label = ctk.CTkLabel(
                row,
                text=str(path.parent),
                text_color="#B8C2D6",
                font=make_font(10),
                anchor="w",
            )
            path_label.grid(row=1, column=2, sticky="ew", pady=(0, 8))
            ctk.CTkButton(
                row,
                text="X",
                command=lambda item_index=index: self._remove_merge_file(item_index),
                width=26,
                height=26,
                corner_radius=13,
                fg_color="#344077",
                hover_color=DANGER_BUTTON,
                text_color=TEXT_LIGHT,
                font=make_font(12, "bold"),
            ).grid(row=0, column=3, rowspan=2, padx=10, pady=14)

            for drag_widget in (row, handle, number, name_label, path_label):
                drag_widget.bind(
                    "<ButtonPress-1>",
                    lambda event, item_index=index: self._start_merge_drag(event, item_index),
                    add=True,
                )
                drag_widget.bind("<B1-Motion>", self._update_merge_drag, add=True)
                drag_widget.bind("<ButtonRelease-1>", self._finish_merge_drag, add=True)

        if self.merge_files:
            final_indicator = ctk.CTkFrame(
                self.merge_files_frame,
                fg_color="#3B8ED0",
                corner_radius=0,
                height=4,
            )
            final_indicator.grid(
                row=len(self.merge_files) * 2,
                column=0,
                sticky="ew",
                padx=8,
                pady=2,
            )
            final_indicator.grid_remove()
            self._merge_drop_indicators.append(final_indicator)

        has_files = bool(self.merge_files)
        self._set_grid_visibility(self.merge_empty_button, not has_files)
        self._set_grid_visibility(self.merge_files_frame, has_files)
        self._set_grid_visibility(self.add_merge_files_button, has_files)
        count = len(self.merge_files)
        self.merge_count_label.configure(
            text=f"{count} archivo seleccionado" if count == 1 else f"{count} archivos seleccionados"
        )
        self.merge_action_button.configure(state="normal" if count >= 2 else "disabled")
        enable_visible_focus(self.merge_files_frame)

    def _start_merge_drag(self, _event, index: int) -> None:
        if self.is_busy:
            return
        self._merge_drag_index = index
        self._merge_drop_index = index
        if 0 <= index < len(self._merge_rows):
            self._merge_rows[index].configure(fg_color=PRIMARY_BUTTON_PRESSED)
        self._show_merge_drop_indicator(index)

    def _update_merge_drag(self, event) -> None:
        if self._merge_drag_index is None or not self._merge_rows:
            return
        pointer_y = event.y_root
        target = len(self._merge_rows)
        for index, row in enumerate(self._merge_rows):
            midpoint = row.winfo_rooty() + row.winfo_height() / 2
            if pointer_y < midpoint:
                target = index
                break
        self._merge_drop_index = target
        self._show_merge_drop_indicator(target)
        for index, row in enumerate(self._merge_rows):
            row.configure(
                fg_color=PRIMARY_BUTTON_PRESSED if index == self._merge_drag_index else "#1E2858"
            )

    def _show_merge_drop_indicator(self, target: int | None) -> None:
        for index, indicator in enumerate(self._merge_drop_indicators):
            if target is not None and index == target:
                indicator.grid()
            else:
                indicator.grid_remove()

    def _finish_merge_drag(self, _event) -> None:
        source = self._merge_drag_index
        target = self._merge_drop_index
        self._merge_drag_index = None
        self._merge_drop_index = None
        self._show_merge_drop_indicator(None)
        if source is None or target is None:
            for row in self._merge_rows:
                row.configure(fg_color="#1E2858")
            return
        if 0 <= source < len(self.merge_files) and 0 <= target <= len(self.merge_files):
            item = self.merge_files.pop(source)
            if source < target:
                target -= 1
            self.merge_files.insert(target, item)
            self._render_merge_files()

    def _save_merged_pdf(self) -> None:
        if self.is_busy:
            return
        if len(self.merge_files) < 2:
            messagebox.showinfo(
                "Faltan archivos",
                "Selecciona al menos dos archivos PDF para unir.",
                parent=self,
            )
            return
        target = filedialog.asksaveasfilename(
            parent=self,
            title="Guardar PDF unido",
            defaultextension=".pdf",
            initialfile="PDF unido.pdf",
            filetypes=[("Archivo PDF", "*.pdf"), ("Todos los archivos", "*.*")],
        )
        if not target:
            return

        sources = list(self.merge_files)
        self._run_conversion_task(
            status_text=f"Uniendo 1 de {len(sources)}...",
            task=lambda: self.pdf_merger.merge(
                sources,
                Path(target),
                cancel_check=self._cancel_event.is_set,
                progress_callback=lambda index, total: self._set_loading_status_from_worker(
                    f"Uniendo {index} de {total}..."
                ),
            ),
            on_success=lambda saved_path: messagebox.showinfo(
                "PDF unido",
                f"Archivo guardado en:\n{saved_path}",
                parent=self,
            ),
        )

    def _show_help_dialog(self) -> None:
        if self.is_busy:
            return
        show_help_dialog(self)

    def _add_files(self, raw_paths) -> None:
        changed = False
        for raw_path in raw_paths:
            path = Path(raw_path)
            if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue
            sheet_var = tk.StringVar(value="")
            split_var = tk.BooleanVar(value=False)
            if path.suffix.lower() in DOCUMENT_EXTENSIONS | PDF_EXTENSIONS:
                sheet_var.trace_add("write", lambda *_args: self._refresh_outputs())
                split_var.trace_add("write", lambda *_args: self._refresh_outputs())
            self.files.append(
                SourceFileItem(
                    path=path,
                    sheet_var=sheet_var if path.suffix.lower() in DOCUMENT_EXTENSIONS | PDF_EXTENSIONS else None,
                    split_var=split_var if path.suffix.lower() in DOCUMENT_EXTENSIONS | PDF_EXTENSIONS else None,
                )
            )
            changed = True

        if not changed:
            return
        self._render_files()
        self._refresh_outputs()

    def reset_work(self) -> None:
        if self.is_busy:
            return
        if self.active_view == "merge":
            self.merge_files.clear()
            self._render_merge_files()
        else:
            self.files.clear()
            self._render_files()
            self._refresh_outputs()

    def _remove_file(self, index: int) -> None:
        if self.is_busy:
            return
        if 0 <= index < len(self.files):
            del self.files[index]
            self._render_files()
            self._refresh_outputs()

    def _render_files(self) -> None:
        for child in self.files_frame.winfo_children():
            child.destroy()

        if not self.files:
            self._sync_action_buttons()
            return

        for row_index, item in enumerate(self.files):
            row = ctk.CTkFrame(self.files_frame, fg_color="#1E2858", corner_radius=0)
            row.grid(row=row_index * 2, column=0, sticky="ew", pady=(0, 1))
            row.grid_columnconfigure(1, weight=1)
            row.grid_columnconfigure(2, weight=0)

            ctk.CTkButton(
                row,
                text="X",
                command=lambda index=row_index: self._remove_file(index),
                width=16,
                height=16,
                corner_radius=8,
                fg_color="#344077",
                hover_color=DANGER_BUTTON,
                text_color=TEXT_LIGHT,
                font=make_font(14, "bold"),
            ).grid(row=0, column=0, rowspan=2, sticky="nsw", padx=(8, 0), pady=19)

            ctk.CTkLabel(
                row,
                text=item.path.name,
                text_color=TEXT_LIGHT,
                font=make_font(12, "bold"),
                anchor="w",
            ).grid(row=0, column=1, sticky="ew", padx=12, pady=(6, 1))
            ctk.CTkLabel(
                row,
                text=str(item.path.parent),
                text_color="#B8C2D6",
                font=make_font(10),
                anchor="w",
            ).grid(row=1, column=1, sticky="ew", padx=12, pady=(0, 6))

            if item.sheet_var is not None:
                split_button = ctk.CTkButton(
                    row,
                    text="" if self._split_toggle_image(item) is not None else self._split_toggle_text(item),
                    image=self._split_toggle_image(item),
                    command=lambda source=item: self._toggle_split_output(source),
                    width=34,
                    height=34,
                    corner_radius=0,
                    fg_color=PRIMARY_BUTTON if item.split_var is not None and item.split_var.get() else "#344077",
                    hover_color=PRIMARY_BUTTON_ACTIVE,
                    text_color=TEXT_LIGHT,
                    font=make_font(11, "bold"),
                )
                split_button.grid(row=0, column=2, rowspan=2, sticky="e", padx=(6, 8), pady=12)
                split_button.tooltip = Tooltip(split_button, SPLIT_TOGGLE_TOOLTIP, delay_ms=0)

                entry = ctk.CTkEntry(
                    self.files_frame,
                    placeholder_text=self._selection_placeholder(item.path.suffix.lower()),
                    height=15,
                    corner_radius=0,
                    fg_color=SURFACE_BACKGROUND,
                    border_color=BORDER_COLOR,
                    text_color=TEXT_DARK,
                    placeholder_text_color="#797979",
                    font=make_font(12),
                )
                current_value = item.sheet_var.get()
                if current_value:
                    entry.insert(0, current_value)
                entry.bind("<KeyRelease>", lambda _event, source=item, input_entry=entry: self._update_sheet_value(source, input_entry.get()), add=True)
                entry.bind("<FocusOut>", lambda _event, source=item, input_entry=entry: self._update_sheet_value(source, input_entry.get()), add=True)
                entry.grid(row=row_index * 2 + 1, column=0, sticky="ew", pady=(0, 10))
        enable_visible_focus(self.files_frame)
        self._sync_action_buttons()

    def _refresh_outputs(self) -> None:
        for child in getattr(self, "outputs_frame", []).winfo_children() if hasattr(self, "outputs_frame") else []:
            child.destroy()
        self.output_buttons.clear()

        outputs = self._build_output_items()
        if not outputs:
            self._sync_action_buttons()
            return

        for index, output in enumerate(outputs):
            row = ctk.CTkFrame(self.outputs_frame, fg_color=RIGHT_PANEL_BACKGROUND, corner_radius=0)
            row.grid(row=index, column=0, sticky="ew", pady=(0, 8))
            row.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(
                row,
                text=output.filename,
                height=38,
                corner_radius=0,
                fg_color="#E7E9F1",
                text_color=TEXT_DARK,
                font=make_font(14, "bold"),
                anchor="w",
                padx=12,
            ).grid(row=0, column=0, sticky="ew", padx=4)
            button = ctk.CTkButton(
                row,
                text="" if self.download_item_icon_image is not None else "DL",
                image=self.download_item_icon_image,
                command=lambda planned=output: self._save_output(
                    planned.source,
                    planned.selection,
                    planned.filename,
                ),
                width=38,
                height=38,
                corner_radius=0,
                fg_color=PRIMARY_BUTTON,
                hover_color=PRIMARY_BUTTON_ACTIVE,
                text_color=TEXT_LIGHT,
                font=make_font(11, "bold"),
            )
            button.grid(row=0, column=1, sticky="e")
            Tooltip(button, f"Guardar {output.filename}")
            self.output_buttons.append(button)
        enable_visible_focus(self.outputs_frame)
        self._sync_action_buttons()

    def _update_sheet_value(self, item: SourceFileItem, value: str) -> None:
        if item.sheet_var is None or item.sheet_var.get() == value:
            return
        item.sheet_var.set(value)

    def _toggle_split_output(self, item: SourceFileItem) -> None:
        if item.split_var is None:
            return
        item.split_var.set(not item.split_var.get())
        self._render_files()
        self._refresh_outputs()

    def _split_toggle_text(self, item: SourceFileItem) -> str:
        if item.split_var is not None and item.split_var.get():
            return "N"
        return "1"

    def _split_toggle_image(self, item: SourceFileItem) -> ctk.CTkImage | None:
        if item.split_var is not None and item.split_var.get():
            return self.separate_icon_on_image
        return self.separate_icon_image

    @staticmethod
    def _selection_placeholder(suffix: str) -> str:
        if suffix in SHEET_EXTENSIONS:
            return "Hojas del libro a exportar, ej. 2-4 o 1, 4-6. Dejar vacío para todas."
        return "Páginas a exportar, ej. 2-4 o 1, 4-6. Dejar vacío para convertir todas."

    def _build_output_items(self) -> list[PlannedOutput]:
        return build_output_plan(self.files)

    def _convert_first_output(self) -> None:
        if self.is_busy:
            return
        outputs = self._build_output_items()
        if not outputs:
            messagebox.showinfo("Sin archivos", "Carga al menos un archivo para convertir.", parent=self)
            return
        output = outputs[0]
        self._save_output(output.source, output.selection, output.filename)

    def _save_all_outputs(self) -> None:
        if self.is_busy:
            return
        outputs = self._build_output_items()
        if not outputs:
            messagebox.showinfo("Sin archivos", "Carga al menos un archivo para convertir.", parent=self)
            return

        target_dir = filedialog.askdirectory(parent=self, title="Seleccionar carpeta de descarga")
        if not target_dir:
            return

        output_dir = Path(target_dir)
        self._run_conversion_task(
            status_text=f"Convirtiendo 1 de {len(outputs)}...",
            task=lambda: self._convert_all_outputs(outputs, output_dir),
            on_success=lambda report: self._show_batch_report(report, output_dir),
        )

    def _convert_all_outputs(self, outputs: list[PlannedOutput], output_dir: Path) -> dict[str, object]:
        saved_paths: list[Path] = []
        errors: list[str] = []
        for index, output in enumerate(outputs, start=1):
            if self._cancel_event.is_set():
                break
            self._set_loading_status_from_worker(f"Convirtiendo {index} de {len(outputs)}...")
            try:
                saved_paths.append(
                    self.converter.convert(
                        ConversionRequest(
                            source_path=output.source.path,
                            target_path=output_dir / output.filename,
                            sheet_name=output.selection,
                        ),
                        cancel_check=self._cancel_event.is_set,
                    )
                )
            except OutputCancelled:
                break
            except Exception as error:  # noqa: BLE001
                errors.append(f"{output.filename}: {error}")

        return {
            "saved": saved_paths,
            "errors": errors,
            "cancelled": self._cancel_event.is_set(),
            "total": len(outputs),
        }

    def _show_batch_report(self, report: dict[str, object], output_dir: Path) -> None:
        saved = list(report.get("saved", []))
        errors = list(report.get("errors", []))
        lines = [
            f"Correctas: {len(saved)}",
            f"Fallidas: {len(errors)}",
        ]
        if report.get("cancelled"):
            lines.append("La operación fue cancelada.")
        if saved:
            lines.extend(["", "Archivos generados:", *(f"• {Path(path).name}" for path in saved[:8])])
        if errors:
            lines.extend(["", "Errores:", *(f"• {error}" for error in errors[:8])])
        lines.extend(["", f"Carpeta: {output_dir}"])
        messagebox.showinfo("Reporte de conversión", "\n".join(lines), parent=self)

    def _set_icon_hover(self, button: ctk.CTkButton, image: ctk.CTkImage | None) -> None:
        if image is not None:
            button.configure(image=image)

    def _enable_file_drop(self, widget) -> None:
        if not self._dnd_available:
            return
        register = getattr(widget, "drop_target_register", None)
        bind = getattr(widget, "dnd_bind", None)
        if register is None or bind is None:
            return
        try:
            register(DND_FILES)
            bind("<<Drop>>", self._handle_file_drop)
        except tk.TclError:
            self._dnd_available = False
            LOGGER.warning("TkDND is unavailable; drag and drop has been disabled")

    def _handle_file_drop(self, event) -> None:
        self._add_files(self.tk.splitlist(event.data))

    def _enable_merge_file_drop(self, widget) -> None:
        if not self._dnd_available:
            return
        register = getattr(widget, "drop_target_register", None)
        bind = getattr(widget, "dnd_bind", None)
        if register is None or bind is None:
            return
        try:
            register(DND_FILES)
            bind("<<Drop>>", self._handle_merge_file_drop)
        except tk.TclError:
            self._dnd_available = False
            LOGGER.warning("TkDND is unavailable; drag and drop has been disabled")

    def _handle_merge_file_drop(self, event) -> None:
        self._add_merge_files(self.tk.splitlist(event.data))

    def _sync_action_buttons(self) -> None:
        has_files = bool(self.files)
        has_outputs = bool(self._build_output_items())
        self._set_grid_visibility(self.upload_icon_button, not has_files)
        self._set_grid_visibility(self.files_frame, has_files)
        self._set_grid_visibility(self.upload_action_button, has_files)
        self._set_grid_visibility(self.download_icon_button, not has_outputs)
        self._set_grid_visibility(self.outputs_frame, has_outputs)
        self._set_grid_visibility(self.download_action_button, has_outputs)

    @staticmethod
    def _set_grid_visibility(widget: tk.Misc, visible: bool) -> None:
        if visible:
            widget.grid()
        else:
            widget.grid_remove()

    def _save_output(self, item: SourceFileItem, sheet_name: str | None, output_name: str) -> None:
        if self.is_busy:
            return
        target = filedialog.asksaveasfilename(
            parent=self,
            title="Exportar PDF",
            defaultextension=".pdf",
            initialfile=output_name,
            filetypes=[("Archivo PDF", "*.pdf"), ("Todos los archivos", "*.*")],
        )
        if not target:
            return

        self._run_conversion_task(
            status_text="Convirtiendo archivo...",
            task=lambda: self.converter.convert(
                ConversionRequest(
                    source_path=item.path,
                    target_path=Path(target),
                    sheet_name=sheet_name,
                ),
                cancel_check=self._cancel_event.is_set,
            ),
            on_success=lambda saved_path: messagebox.showinfo(
                "PDF guardado",
                f"Archivo guardado en:\n{saved_path}",
                parent=self,
            ),
        )

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
