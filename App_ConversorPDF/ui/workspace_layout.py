"""Visual layout for the PDF conversion workspace."""
from __future__ import annotations

import logging

import customtkinter as ctk

try:
    from tkinterdnd2 import DND_FILES
except ImportError:
    DND_FILES = None

from App_ConversorPDF.config import (
    APP_DESCRIPTION,
    CONVERTER_LOGO_PATH,
    DOWNLOAD_ICON_HOVER_PATH,
    DOWNLOAD_ITEM_ICON_PATH,
    DOWNLOAD_ICON_PATH,
    SEPARATE_ICON_ON_PATH,
    SEPARATE_ICON_PATH,
    UPLOAD_ICON_HOVER_PATH,
    UPLOAD_ICON_PATH,
)
from App_ConversorPDF.ui.theme import (
    APP_BACKGROUND,
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
from components.shared.tooltip import Tooltip
from components.shared.topbar import TopbarButton, TopbarStyle, build_topbar


SPLIT_TOGGLE_TOOLTIP = "Separar cada hoja o pagina seleccionada en PDFs individuales."
LOGGER = logging.getLogger(__name__)
LIST_PANEL_TOP_PADDING = 24
LIST_PANEL_BOTTOM_PADDING = 24
LIST_ACTION_HEIGHT = 62



class WorkspaceLayoutMixin:
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
