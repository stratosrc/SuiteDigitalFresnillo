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
        "1. MENÚ DE HERRAMIENTAS",
        (
            "Debajo del banner encontrarás las opciones Convertir a PDF y Unir PDFs.",
            "Convertir a PDF abre la herramienta original para transformar imágenes y documentos.",
            "Unir PDFs abre una lista ordenable para combinar varios archivos PDF en uno solo.",
        ),
    ),
    (
        "2. CONVERTIR: SUBIR ARCHIVOS",
        (
            "Usa el area izquierda para cargar archivos con clic en el icono de carga.",
            "Tambien puedes arrastrar archivos soportados al area de carga.",
            "Puedes cargar el mismo archivo varias veces si necesitas configuraciones distintas.",
            "Se aceptan imagenes y documentos de Office o formatos equivalentes.",
        ),
    ),
    (
        "3. CONVERTIR: ELEGIR HOJAS O PAGINAS",
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
        "4. CONVERTIR: DESCARGAR PDF",
        (
            "El boton Descargar todos guarda todos los PDFs listados en una carpeta seleccionada.",
            "El icono de descarga al lado de cada archivo permite guardar solo ese PDF.",
            "Mientras se convierte, la aplicacion muestra una capa de carga y permanece activa.",
        ),
    ),
    (
        "5. UNIR PDFS",
        (
            "Carga al menos dos archivos PDF mediante el selector o arrastrándolos a la aplicación.",
            "La lista muestra el orden en que se agregarán las páginas al PDF final.",
            "Arrastra cualquier elemento hacia arriba o abajo; una línea azul indica dónde será colocado.",
            "Usa Unir y guardar para elegir el nombre y la ubicación del archivo resultante.",
        ),
    ),
    (
        "6. NUEVO",
        (
            "El boton Nuevo limpia los archivos de la herramienta que tengas abierta.",
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
