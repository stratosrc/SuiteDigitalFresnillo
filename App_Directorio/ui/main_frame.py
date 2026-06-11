"""Main frame for the Directorio application."""

from pathlib import Path
import tkinter as tk

import customtkinter as ctk
from PIL import Image, ImageOps

from App_Directorio.ui.theme import (
    APP_BACKGROUND,
    BORDER_COLOR,
    DARK_BACKGROUND,
    PRIMARY_BUTTON,
    PRIMARY_BUTTON_ACTIVE,
    SURFACE_BACKGROUND,
    TEXT_DARK,
    TEXT_LIGHT,
    TEXT_MUTED,
    make_font,
)
from components.shared.paths import resource_path

MODULE_TITLE = "Directorio"
MODULE_DESCRIPTION = "Gestión y Diseño del \nDirectorio de Área"
DIRECTORY_ICON_PATH = resource_path("App_Directorio", "assets", "directorio.png")


class MainFrame(ctk.CTkFrame):
    """Initial Directorio workspace following the suite visual language."""

    def __init__(self, master: ctk.CTk) -> None:
        super().__init__(master, fg_color=APP_BACKGROUND, corner_radius=0)
        self.master = master
        self.directory_icon: ctk.CTkImage | None = None
        self._build_layout()

    def _build_layout(self) -> None:
        self.pack(fill=tk.BOTH, expand=True)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_workspace()

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color=DARK_BACKGROUND, corner_radius=0, height=126)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(1, weight=1)
        header.grid_propagate(False)

        self.directory_icon = self._load_icon(DIRECTORY_ICON_PATH, (74, 74))
        ctk.CTkLabel(header, image=self.directory_icon, text="", fg_color="transparent").grid(
            row=0,
            column=0,
            padx=(26, 18),
            pady=24,
            sticky="w",
        )

        title_block = ctk.CTkFrame(header, fg_color="transparent", corner_radius=0)
        title_block.grid(row=0, column=1, sticky="ew", padx=(0, 26), pady=24)
        title_block.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            title_block,
            text=MODULE_TITLE,
            fg_color="transparent",
            text_color=TEXT_LIGHT,
            font=make_font(24, "bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="ew")

        ctk.CTkLabel(
            title_block,
            text=MODULE_DESCRIPTION,
            fg_color="transparent",
            text_color=TEXT_LIGHT,
            font=make_font(13),
            anchor="w",
        ).grid(row=1, column=0, sticky="ew", pady=(8, 0))

    def _build_workspace(self) -> None:
        workspace = ctk.CTkFrame(self, fg_color=APP_BACKGROUND, corner_radius=0)
        workspace.grid(row=1, column=0, sticky="nsew", padx=24, pady=24)
        workspace.grid_columnconfigure(0, weight=1)
        workspace.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            workspace,
            text="Panel de diseño del directorio",
            text_color=TEXT_DARK,
            font=make_font(16, "bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", pady=(0, 12))

        content = ctk.CTkFrame(
            workspace,
            fg_color=SURFACE_BACKGROUND,
            border_color=BORDER_COLOR,
            border_width=1,
            corner_radius=0,
        )
        content.grid(row=1, column=0, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(0, weight=1)

        empty_state = ctk.CTkFrame(content, fg_color="transparent", corner_radius=0)
        empty_state.grid(row=0, column=0, sticky="")

        ctk.CTkLabel(
            empty_state,
            text=MODULE_TITLE,
            text_color=TEXT_DARK,
            font=make_font(18, "bold"),
        ).grid(row=0, column=0, pady=(0, 8))

        ctk.CTkLabel(
            empty_state,
            text=MODULE_DESCRIPTION,
            text_color=TEXT_MUTED,
            font=make_font(12),
        ).grid(row=1, column=0, pady=(0, 18))

        ctk.CTkButton(
            empty_state,
            text="Preparar nuevo directorio",
            state="disabled",
            fg_color=PRIMARY_BUTTON,
            hover_color=PRIMARY_BUTTON_ACTIVE,
            text_color=TEXT_LIGHT,
            corner_radius=0,
            font=make_font(12, "bold"),
        ).grid(row=2, column=0)

    def _load_icon(self, icon_path: Path, size: tuple[int, int]) -> ctk.CTkImage | None:
        if not icon_path.exists():
            return None

        image = Image.open(icon_path).convert("RGBA")
        image = ImageOps.contain(image, size, Image.Resampling.LANCZOS)
        return ctk.CTkImage(light_image=image, dark_image=image, size=image.size)
