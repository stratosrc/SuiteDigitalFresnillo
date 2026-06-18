"""Help content for the PDF converter."""

from __future__ import annotations

import tkinter as tk

from App_ConversorPDF.ui.theme import (
    APP_BACKGROUND,
    PRIMARY_BUTTON,
    PRIMARY_BUTTON_ACTIVE,
    SURFACE_BACKGROUND,
    TEXT_DARK,
    TEXT_LIGHT,
    make_font,
)
from components.shared.help_dialog import (
    HelpDialogConfig,
    HelpDialogStyle,
    HelpSection,
    show_help_dialog as show_shared_help_dialog,
)


HELP_SECTIONS: tuple[HelpSection, ...] = (
    (
        "1. SUBIR ARCHIVOS",
        (
            "Usa el area izquierda para cargar archivos con clic en el icono de carga.",
            "Tambien puedes arrastrar archivos soportados al area de carga.",
            "Puedes cargar el mismo archivo varias veces si necesitas configuraciones distintas.",
            "Se aceptan imagenes y documentos de Office o formatos equivalentes.",
        ),
    ),
    (
        "2. ELEGIR HOJAS O PAGINAS",
        (
            "En hojas de calculo, los numeros seleccionan las pestañas del libro, no las paginas del PDF.",
            "Cada pestaña se exporta completa aunque ocupe varias paginas en el PDF.",
            "En documentos, presentaciones y PDFs, los numeros seleccionan las paginas a exportar.",
            "Usa un numero unico como 1, un rango como 2-4, o varias selecciones como 1,3-5.",
            "El boton de separar de cada fila cambia entre un solo PDF o PDFs separados por cada hoja/pagina seleccionada.",
            "Deja el campo vacio para convertir todo el archivo.",
        ),
    ),
    (
        "3. DESCARGAR PDF",
        (
            "El boton Descargar todos guarda todos los PDFs listados en una carpeta seleccionada.",
            "El icono de descarga al lado de cada archivo permite guardar solo ese PDF.",
            "Mientras se convierte, la aplicacion muestra una capa de carga y permanece activa.",
        ),
    ),
    (
        "4. NUEVO",
        (
            "El boton Nuevo limpia todos los archivos cargados y reinicia la lista de conversiones.",
            "Usalo para comenzar otro trabajo sin cerrar la aplicacion.",
        ),
    ),
)

HELP_CONFIG = HelpDialogConfig(
    sections=HELP_SECTIONS,
    style=HelpDialogStyle(
        app_background=APP_BACKGROUND,
        surface_background=SURFACE_BACKGROUND,
        primary_button=PRIMARY_BUTTON,
        primary_button_active=PRIMARY_BUTTON_ACTIVE,
        text_dark=TEXT_DARK,
        text_light=TEXT_LIGHT,
        make_font=make_font,
    ),
)


def show_help_dialog(parent: tk.Misc) -> None:
    """Show the converter help dialog."""
    show_shared_help_dialog(parent, HELP_CONFIG)


__all__ = ["show_help_dialog"]
