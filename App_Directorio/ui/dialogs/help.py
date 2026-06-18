"""Help content for the directory module."""

from __future__ import annotations

import tkinter as tk

from App_Directorio.ui.theme import (
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
        "1. ARCHIVO Y PROYECTO",
        (
            "Para generar el reporte se va a Archivo y Exportar PDF.",
            "Para guardar el proyecto editable se va a Archivo y Guardar proyecto; se crea un archivo .dir.",
            "Para continuar un proyecto anterior se va a Archivo y Abrir.",
            "Para empezar un nuevo proyecto se va a Archivo y Nuevo.",
        ),
    ),
    (
        "2. DATOS GENERALES",
        (
            "En el campo de Área Administrativa (Título) va el nombre del área administrativa correspondiente al directorio.",
            "En el campo de Período va el período correspondiente.",
            "En el Nombre del Área va el nombre de la subdivisión del área administrativa.",
        ),
    ),
    (
        "3. DATOS DEL COLABORADOR",
        (
            "En el campo de Código (Rango/Clave/Nivel) va el código correspondiente del colaborador.",
            "En el campo de Nombre va el nombre del colaborador.",
            "En el campo de Cargo va el cargo del colaborador.",
            "En el campo de Correo electrónico va el correo institucional del colaborador.",
            "En la Fecha de Alta va la fecha en la que comenzó a ejercer su cargo el colaborador.",
        ),
    ),
    (
        "4. ÁREAS",
        (
            "El botón de Agregar Área permite agregar una subdivisión más al área administrativa.",
            'El icono verde "+" permite agregar una fila adicional de colaborador dentro de un área.',
            'El icono "-" permite eliminar una fila de registro de colaborador.',
            'El icono "x" permite eliminar un área completa.',
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
    """Show the directory help dialog."""
    show_shared_help_dialog(parent, HELP_CONFIG)


__all__ = ["show_help_dialog"]
