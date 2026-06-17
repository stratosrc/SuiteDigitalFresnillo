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
HELP_BULLET_WRAP_LENGTH: Final[int] = 470

HELP_DIALOG_TITLE: Final[str] = "Ayuda"
HELP_DIALOG_HEADING: Final[str] = "Guia de uso"
HELP_DIALOG_CLOSE: Final[str] = "Cerrar"

HELP_SECTIONS: Final[tuple[DialogSection, ...]] = (
    (
        "1. MENU ARCHIVO Y METADATOS",
        (
            "Nuevo: Permite limpiar el lienzo actual y comenzar un documento completamente desde cero.\n",
            "Guardar proyecto: Conserva el organigrama editable para abrirlo despues.\n",
            "Exportar PDF: Genera el organigrama final en formato PDF vectorial.\n",
            "Exportar imagen: Permite exportar el organigrama en formatos de imagen estÃ¡ndar, soportando las extensiÃ³nes PNG, JPG y JPEG.\n",
            "Titulo del Organigrama: Campo de texto para establecer el titulo oficial que encabeza el grafico.\n",
            "PerÃ­odo: Campo de texto para indicar el rango cronolÃ³gico del organigrama (Ej. Octubre - Diciembre 2026).\n",
        ),
    ),
    (
        "2. CONTROLES DE EDICION Y CONEXIONES",
        (
            "Clic izquierdo en un espacio vacio: Crea un nuevo nodo en la celda seleccionada.\n",
            "Clic izquierdo en un nodo, conector u obstaculo: Selecciona el elemento.\n",
            "Indicador de conexion: Al acercar el cursor a un nodo aparece el puerto disponible para conectar.\n",
            "Conectar con clic: Haz clic izquierdo en el indicador del nodo origen y despues en el indicador del nodo destino.\n",
            "Conectar arrastrando: Arrastra desde el indicador de origen hasta otro nodo; la linea fantasma muestra la previsualizacion.\n",
            "Eliminar Seleccion: Remueve del lienzo cualquier nodo, conector o elemento seleccionado.\n",
            "Atajos de Teclado: Tambien puedes eliminar la seleccion con [Supr] (Delete) o [Backspace].\n",
        ),
    ),
    (
        "3. NAVEGACION Y MOVIMIENTO",
        (
            "Clic derecho y arrastre sobre un nodo: Mueve el nodo a otra celda del lienzo.\n",
            "Clic derecho y arrastre sobre el lienzo vacio: Desplaza la camara.\n",
            "Flechas Azules: Controles para desplazar la vista por el lienzo.\n",
            "Enfocar Ultimo: Centra la vista en el ultimo nodo agregado.\n",
            "Botones de Zoom: Permiten acercar o alejar la vista del organigrama.\n",
            "Atajo de Zoom: Usa [Ctrl] + rueda del mouse para controlar el zoom.\n",
        ),
    ),
    (
        "4. CONTROLES DE SEGURIDAD",
        (
            "Obstaculos de Ruta: Permite colocar puntos de obstruccion para forzar rutas alternativas en las conexiones.\n",
            "Boton de Escudos: Activa o desactiva la visualizacion global de los escudos institucionales.\n",
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
