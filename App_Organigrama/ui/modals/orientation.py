from collections.abc import Callable
from pathlib import Path
import tkinter as tk

import customtkinter as ctk

from App_Organigrama.config.assets import HORIZONTAL_ICON_PATH, VERTICAL_ICON_PATH
from App_Organigrama.ui.theme import (
    PRIMARY_BUTTON,
    PRIMARY_BUTTON_ACTIVE,
    SURFACE_BACKGROUND,
    TEXT_DARK,
    TEXT_LIGHT,
    make_font,
)
from components.shared.images import load_ctk_image


class OrientationDialog(ctk.CTkToplevel):
    def __init__(self, master: tk.Misc, on_select: Callable[[str], None]) -> None:
        super().__init__(master)
        self.title("Orientación")
        self.resizable(False, False)
        self.configure(fg_color=SURFACE_BACKGROUND)
        self.transient(master.winfo_toplevel())
        self.grab_set()
        self.on_select = on_select
        self.icons: dict[str, ctk.CTkImage] = {}

        self._build()
        self.after(30, self._center)

    def _build(self) -> None:
        frame = ctk.CTkFrame(self, fg_color=SURFACE_BACKGROUND, corner_radius=0)
        frame.pack(fill="both", expand=True, padx=22, pady=20)

        ctk.CTkLabel(
            frame,
            text="Seleccione la orientación",
            text_color=TEXT_DARK,
            font=make_font(15, "bold"),
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 14))

        self._build_option(frame, "Horizontal", HORIZONTAL_ICON_PATH, "horizontal", 0)
        self._build_option(frame, "Vertical", VERTICAL_ICON_PATH, "vertical", 1)

        ctk.CTkButton(
            frame,
            text="Cancelar",
            command=self.destroy,
            width=132,
            height=30,
            corner_radius=0,
            fg_color=PRIMARY_BUTTON,
            hover_color=PRIMARY_BUTTON_ACTIVE,
            text_color=TEXT_LIGHT,
            font=make_font(12, "bold"),
        ).grid(row=2, column=0, columnspan=2, pady=(16, 0))

    def _build_option(
        self,
        parent: ctk.CTkFrame,
        text: str,
        icon_path: Path,
        orientation: str,
        column: int,
    ) -> None:
        ctk.CTkButton(
            parent,
            text=text,
            image=self._load_icon(icon_path),
            compound="top",
            command=lambda: self._select(orientation),
            width=150,
            height=118,
            corner_radius=0,
            fg_color=PRIMARY_BUTTON,
            hover_color=PRIMARY_BUTTON_ACTIVE,
            text_color=TEXT_LIGHT,
            font=make_font(13, "bold"),
        ).grid(row=1, column=column, padx=(0, 12) if column == 0 else (12, 0), sticky="nsew")

    def _load_icon(self, icon_path: Path) -> ctk.CTkImage | None:
        icon = load_ctk_image(icon_path, (58, 58))
        if icon is None:
            return None
        self.icons[str(icon_path)] = icon
        return icon

    def _select(self, orientation: str) -> None:
        self.destroy()
        self.on_select(orientation)

    def _center(self) -> None:
        self.update_idletasks()
        master = self.master.winfo_toplevel()
        x = master.winfo_rootx() + ((master.winfo_width() - self.winfo_width()) // 2)
        y = master.winfo_rooty() + ((master.winfo_height() - self.winfo_height()) // 2)
        self.geometry(f"+{x}+{y}")
