"""Help dialog for the Directorio module."""

from typing import Final
import tkinter as tk

import customtkinter as ctk

from App_Directorio.ui.theme import (
    APP_BACKGROUND,
    PRIMARY_BUTTON,
    PRIMARY_BUTTON_ACTIVE,
    SURFACE_BACKGROUND,
    TEXT_DARK,
    TEXT_LIGHT,
    make_font,
)


DialogSection = tuple[str, tuple[str, ...]]

HELP_WINDOW_WIDTH: Final[int] = 550
HELP_WINDOW_HEIGHT: Final[int] = 600
HELP_WINDOW_MIN_WIDTH: Final[int] = 500
HELP_WINDOW_MIN_HEIGHT: Final[int] = 520
HELP_BULLET_WRAP_LENGTH: Final[int] = 470

HELP_DIALOG_TITLE: Final[str] = "Ayuda"
HELP_DIALOG_HEADING: Final[str] = "GuÃ­a de uso"
HELP_DIALOG_CLOSE: Final[str] = "Cerrar"

HELP_SECTIONS: Final[tuple[DialogSection, ...]] = (
    (
        "1. ARCHIVO Y PROYECTO",
        (
            "Para generar el reporte se va a Archivo y Guardar PDF.",
            "Para empezar un nuevo proyecto se va a Archivo y Nuevo.",
        ),
    ),
    (
        "2. DATOS GENERALES",
        (
            "En el campo de Ãrea Administrativa (TÃ­tulo) va el nombre de la Ã¡rea administrativa correspondiente al directorio.",
            "En el campo de PerÃ­odo va el perÃ­odo correspondiente.",
            "En el Nombre de la Ãrea va el nombre de la subdivisiÃ³n de la Ã¡rea administrativa.",
        ),
    ),
    (
        "3. DATOS DEL COLABORADOR",
        (
            "En el campo de CÃ³digo (Rango/Clave/Nivel) va el cÃ³digo correspondiente del colaborador.",
            "En el campo de Nombre va el nombre del colaborador.",
            "En el campo de Cargo va el cargo del colaborador.",
            "En la Fecha de Alta va la fecha en la que comenzÃ³ a ejercer su cargo el colaborador.",
        ),
    ),
    (
        "4. ÃREAS",
        (
            "El botÃ³n de Agregar Ãrea permite agregar una subdivisiÃ³n mÃ¡s a la Ã¡rea administrativa.",
            'El icono verde "+" permite agregar una fila adicional de colaborador dentro de un Ã¡rea.',
            'El icono "-" permite eliminar una fila de registro de colaborador.',
            'El icono "x" permite eliminar un Ã¡rea completa.',
        ),
    ),
)


def show_help_dialog(parent: tk.Misc) -> None:
    parent_window = parent.winfo_toplevel()
    help_window = ctk.CTkToplevel(parent_window)
    help_window.title(HELP_DIALOG_TITLE)
    help_window.geometry(f"{HELP_WINDOW_WIDTH}x{HELP_WINDOW_HEIGHT}")
    help_window.minsize(HELP_WINDOW_MIN_WIDTH, HELP_WINDOW_MIN_HEIGHT)
    help_window.configure(fg_color=APP_BACKGROUND)
    help_window.transient(parent_window)

    _center_toplevel(parent_window, help_window, HELP_WINDOW_WIDTH, HELP_WINDOW_HEIGHT)
    _build_help_content(help_window)

    help_window.protocol("WM_DELETE_WINDOW", help_window.destroy)
    help_window.focus_set()
    help_window.grab_set()


def _build_help_content(help_window: ctk.CTkToplevel) -> None:
    main_frame = ctk.CTkFrame(help_window, fg_color=APP_BACKGROUND, corner_radius=0)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    ctk.CTkLabel(
        main_frame,
        text=HELP_DIALOG_HEADING,
        fg_color=APP_BACKGROUND,
        text_color=TEXT_DARK,
        font=make_font(18, "bold"),
        anchor="w",
    ).pack(fill=tk.X, anchor=tk.W, pady=(0, 12))

    scroll_frame = ctk.CTkScrollableFrame(
        main_frame,
        fg_color=SURFACE_BACKGROUND,
        corner_radius=0,
        scrollbar_button_color=PRIMARY_BUTTON,
        scrollbar_button_hover_color=PRIMARY_BUTTON_ACTIVE,
    )
    scroll_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 14))

    _populate_help_sections(scroll_frame)

    ctk.CTkButton(
        main_frame,
        text=HELP_DIALOG_CLOSE,
        command=help_window.destroy,
        fg_color=PRIMARY_BUTTON,
        hover_color=PRIMARY_BUTTON_ACTIVE,
        text_color=TEXT_LIGHT,
        corner_radius=0,
        font=make_font(12),
    ).pack(side=tk.BOTTOM, fill=tk.X)


def _populate_help_sections(scroll_frame: ctk.CTkScrollableFrame) -> None:
    for section_title, bullet_items in HELP_SECTIONS:
        ctk.CTkLabel(
            scroll_frame,
            text=section_title,
            fg_color=SURFACE_BACKGROUND,
            text_color=TEXT_DARK,
            font=make_font(13, "bold"),
            anchor="w",
            justify="left",
        ).pack(fill=tk.X, anchor=tk.W, padx=12, pady=(14, 6))

        for bullet_text in bullet_items:
            ctk.CTkLabel(
                scroll_frame,
                text=f"* {bullet_text}",
                fg_color=SURFACE_BACKGROUND,
                text_color=TEXT_DARK,
                font=make_font(12),
                anchor="w",
                justify="left",
                wraplength=HELP_BULLET_WRAP_LENGTH,
            ).pack(fill=tk.X, anchor=tk.W, padx=20, pady=(0, 5))


def _center_toplevel(parent: tk.Misc, window: ctk.CTkToplevel, width: int, height: int) -> None:
    parent.update_idletasks()
    x_position = parent.winfo_rootx() + (parent.winfo_width() - width) // 2
    y_position = parent.winfo_rooty() + (parent.winfo_height() - height) // 2
    window.geometry(f"{width}x{height}+{max(x_position, 0)}+{max(y_position, 0)}")


__all__ = ["show_help_dialog"]
