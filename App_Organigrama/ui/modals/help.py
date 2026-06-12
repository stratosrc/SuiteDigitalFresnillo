"""Modal help dialog for the organization chart designer."""

from __future__ import annotations

from typing import Final
import tkinter as tk

import customtkinter as ctk

from App_Organigrama.ui.theme import (
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
HELP_BULLET_WRAP_LENGTH: Final[int] = 580
HELP_HEADING_FONT_SIZE: Final[int] = 18
HELP_SECTION_FONT_SIZE: Final[int] = 15
HELP_BODY_FONT_SIZE: Final[int] = 14

HELP_DIALOG_TITLE: Final[str] = "Ayuda"
HELP_DIALOG_HEADING: Final[str] = "Guia de uso"
HELP_DIALOG_CLOSE: Final[str] = "Cerrar"

HELP_SECTIONS: Final[tuple[DialogSection, ...]] = (
    (
        "1. MENU ARCHIVO Y METADATOS",
        (
            "Nuevo: Permite limpiar el lienzo actual y comenzar un documento completamente desde cero.\n",
            "Exportar PDF: Genera y exporta el organigrama final en formato PDF vectorial.\n",
            "Exportar Imagen: Permite guardar el organigrama en formatos de imagen estándar, soportando las extensiónes PNG, JPG y JPEG.\n",
            "Titulo del Organigrama: Campo de texto para establecer el titulo oficial que encabeza el grafico.\n",
            "Período: Campo de texto para indicar el rango cronológico del organigrama (Ej. Octubre - Diciembre 2026).\n",
        ),
    ),
    (
        "2. CONTROLES DE EDICION Y SEGURIDAD",
        (
            'Modo Bloquear Camino: Permite colocar puntos de obstruccion para forzar rutas alternativas en las conexiones.\n',
            "Boton de Escudos: Activa o desactiva la visualizacion global de los escudos institucionales.\n",
            "Eliminar Seleccion: Remueve del lienzo cualquier nodo, conector o elemento seleccionado.\n",
            "Atajos de Teclado: Tambien puedes eliminar la seleccion con [Supr] (Delete) o [Backspace].\n",
        ),
    ),
    (
        "3. NAVEGACION Y VISUALIZACION DEL LIENZO",
        (
            "Flechas Azules: Controles para desplazar la vista por el lienzo.\n",
            'Arrastre con Mouse: Puedes navegar por el lienzo haciendo clic izquierdo y arrastrando, siempre que no este activo el modo "Bloquear Camino".\n',
            "Enfocar Ultimo: Centra la vista en el ultimo nodo agregado.\n",
            "Botones de Zoom: Permiten acercar o alejar la vista del organigrama.\n",
            "Atajo de Zoom: Usa [Ctrl] + rueda del mouse para controlar el zoom.\n",
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
    heading_font = make_font(HELP_HEADING_FONT_SIZE, "bold")
    section_font = make_font(HELP_SECTION_FONT_SIZE, "bold")
    body_font = make_font(HELP_BODY_FONT_SIZE)

    ctk.CTkLabel(
        main_frame,
        text=HELP_DIALOG_HEADING,
        fg_color=APP_BACKGROUND,
        text_color=TEXT_DARK,
        font=heading_font,
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

    _populate_help_sections(scroll_frame, section_font, body_font)

    ctk.CTkButton(
        main_frame,
        text=HELP_DIALOG_CLOSE,
        command=help_window.destroy,
        fg_color=PRIMARY_BUTTON,
        hover_color=PRIMARY_BUTTON_ACTIVE,
        text_color=TEXT_LIGHT,
        corner_radius=0,
        font=body_font,
    ).pack(side=tk.BOTTOM, fill=tk.X)


def _populate_help_sections(
    scroll_frame: ctk.CTkScrollableFrame,
    section_font: ctk.CTkFont,
    body_font: ctk.CTkFont,
) -> None:
    for section_title, bullet_items in HELP_SECTIONS:
        tk.Label(
            scroll_frame,
            text=section_title,
            bg=SURFACE_BACKGROUND,
            fg=TEXT_DARK,
            font=section_font,
            anchor="w",
            justify="left",
            borderwidth=0,
            highlightthickness=0,
        ).pack(fill=tk.X, anchor=tk.W, padx=12, pady=(14, 6))

        for bullet_text in bullet_items:
            tk.Label(
                scroll_frame,
                text=f"* {bullet_text}",
                bg=SURFACE_BACKGROUND,
                fg=TEXT_DARK,
                font=body_font,
                anchor="w",
                justify="left",
                borderwidth=0,
                highlightthickness=0,
                wraplength=HELP_BULLET_WRAP_LENGTH,
            ).pack(fill=tk.X, anchor=tk.W, padx=20, pady=(0, 5))


def _center_toplevel(parent: tk.Misc, window: ctk.CTkToplevel, width: int, height: int) -> None:
    parent.update_idletasks()
    x_position = parent.winfo_rootx() + (parent.winfo_width() - width) // 2
    y_position = parent.winfo_rooty() + (parent.winfo_height() - height) // 2
    window.geometry(f"{width}x{height}+{max(x_position, 0)}+{max(y_position, 0)}")
