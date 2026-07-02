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
from components.shared.platform import PRIMARY_MODIFIER_LABEL


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
        "ATAJOS DE TECLADO",
        (
            f"{PRIMARY_MODIFIER_LABEL}+N: Crear un proyecto nuevo.",
            f"{PRIMARY_MODIFIER_LABEL}+O: Abrir un proyecto existente.",
            f"{PRIMARY_MODIFIER_LABEL}+S: Guardar el proyecto actual.",
            f"{PRIMARY_MODIFIER_LABEL}+Z: Deshacer la última edición.",
            f"{PRIMARY_MODIFIER_LABEL}+Y o {PRIMARY_MODIFIER_LABEL}+Mayús+Z: Rehacer la edición deshecha.",
            "Tab y Mayús+Tab: Recorrer los campos y botones del formulario.",
        ),
    ),
    (
        "3. DATOS DEL COLABORADOR",
        (
            "En el campo de Código (Rango/Clave/Nivel) va el código correspondiente del colaborador.",
            "En el campo de Nombre va el nombre del colaborador.",
            "En el campo de Cargo va el cargo del colaborador.",
            "En Correo electrónico puede escribir solamente la primera parte; al salir del campo o presionar Enter se agregará automáticamente @fresnillo.gob.mx.",
            "El correo permanece completamente editable para ingresar una dirección diferente o hacer correcciones.",
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
            "El número situado a la izquierda de cada área indica su posición y se puede editar para cambiarla de lugar.",
            "Al indicar una nueva posición y salir del campo o presionar Enter, todas las áreas se reordenan y renumeran automáticamente.",
        ),
    ),
    (
        "5. ORDEN DEL PERSONAL",
        (
            "Cada colaborador está numerado a la izquierda dentro de su propia área.",
            "Para moverlo directamente, edite su número de posición y salga del campo o presione Enter.",
            "El resto del personal de esa área se reordena y renumera automáticamente.",
            "La flecha situada a la izquierda del número muestra la lista de áreas con su número y nombre.",
            "Al seleccionar otra área, el colaborador se transfiere y se coloca en la última posición de esa área.",
            "Los botones de subir y bajar continúan disponibles para realizar cambios de una posición a la vez.",
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
