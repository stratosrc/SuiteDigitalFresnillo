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
HELP_DIALOG_HEADING: Final[str] = "Guía de uso"
HELP_DIALOG_CLOSE: Final[str] = "Cerrar"

HELP_SECTIONS: Final[tuple[DialogSection, ...]] = (
    (
        "1. MENÚ ARCHIVO Y METADATOS",
        (
            "Nuevo: Permite limpiar el lienzo actual y comenzar un documento completamente desde cero.\n",
            "Exportar PDF: Genera y exporta el organigrama final en formato PDF vectorial.\n",
            "Exportar Imagen: Permite guardar el organigrama en formatos de imagen estándar, soportando las extensiones PNG, JPG y JPEG.\n",
            "Título del Organigrama: Campo de texto diseñado para establecer el título oficial que encabezará el gráfico.\n",
            "Período: Campo de texto para indicar el rango cronológico que abarca el organigrama (Ej. Octubre - Diciembre 2026).\n",
        ),
    ),
    (
        "2. CONTROLES DE EDICIÓN Y SEGURIDAD",
        (
            'Modo Bloquear Camino: Al activarse, permite colocar puntos de obstrucción en el grid para que las líneas conectoras ortogonales no puedan cruzar por esa zona y se vean obligadas a recalcular una ruta alterna.\n',
            "Botón de Escudos: Activa o desactiva de forma global la visualización y renderizado de los logotipos o escudos institucionales.\n",
            "Eliminar Selección: Botón para remover del lienzo cualquier nodo, conector o elemento que se encuentre seleccionado actualmente.\n",
            "Atajos de Teclado: También puedes eliminar el elemento seleccionado de forma rápida presionando las teclas [Supr] (Delete) o [Backspace] en tu teclado.\n",
        ),
    ),
    (
        "3. NAVEGACIÓN Y VISUALIZACIÓN DEL LIENZO",
        (
            "Flechas Azules: Controles direccionales en pantalla para desplazar y navegar visualmente a través del lienzo.\n",
            'Arrastre con Mouse: Puedes navegar libremente por el lienzo haciendo clic izquierdo y arrastrando el cursor, siempre y cuando la aplicación NO se encuentre en el modo "Bloquear Camino".\n',
            "Enfocar Último: Centra de forma automática la vista de la pantalla en el último nodo que haya sido colocado. Es ideal para regresar instantáneamente al área de trabajo activa si el usuario se llega a perder en el lienzo infinito.\n",
            "Botones de Zoom: Permiten acercar o alejar la perspectiva de observación del organigrama.\n",
            "Atajo de Zoom: También puedes controlar el zoom manteniendo presionada la tecla [Ctrl] mientras giras la rueda de desplazamiento del ratón (Mousewheel).\n",
        ),
    ),
)


def show_help_dialog(parent: tk.Misc) -> None:
    """Open the organization chart help dialog as a centered modal window."""
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
    """Create the static dialog layout."""
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
    """Render all guide sections inside the scrollable content area."""
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
                text=f"• {bullet_text}",
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
    """Center a child window over its parent, clamping coordinates to the screen."""
    parent.update_idletasks()
    x_position = parent.winfo_rootx() + (parent.winfo_width() - width) // 2
    y_position = parent.winfo_rooty() + (parent.winfo_height() - height) // 2
    window.geometry(f"{width}x{height}+{max(x_position, 0)}+{max(y_position, 0)}")
