"""Help content for the organization chart designer."""

from __future__ import annotations

import tkinter as tk

from App_Organigrama.ui.theme import (
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
        "1. MENU ARCHIVO Y METADATOS",
        (
            "Nuevo: Permite limpiar el lienzo actual y comenzar un documento completamente desde cero.\n",
            "Guardar proyecto: Conserva el organigrama editable para abrirlo despues.\n",
            "Exportar PDF: Genera el organigrama final en formato PDF vectorial.\n",
            "Exportar imagen: Permite exportar el organigrama en formatos de imagen estándar, soportando PNG, JPG y JPEG.\n",
            "Titulo del Organigrama: Campo de texto para establecer el titulo oficial que encabeza el grafico.\n",
            "Período: Campo de texto para indicar el rango cronológico del organigrama (Ej. Octubre - Diciembre 2026).\n",
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
            "Las conexiones muestran una flecha cerca del nodo destino y la barra inferior indica el flujo origen → destino.\n",
            "Ruta manual: Selecciona una conexión y arrastra uno de sus tramos intermedios. Los tramos junto a los nodos permanecen bloqueados para conservar los puertos.\n",
            "Movimiento de rutas: Los tramos horizontales solo suben o bajan; los verticales solo se desplazan a izquierda o derecha. La ruta se previsualiza mientras arrastras y no puede atravesar nodos.\n",
            "Persistencia de rutas: Los ajustes manuales se guardan dentro del proyecto .og y los extremos se recalculan si mueves alguno de los nodos conectados.\n",
            "Restaurar ruta automática: Selecciona una conexión editada y pulsa este botón para descartar sus puntos manuales y volver al enrutado automático.\n",
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
            "Deshacer y Rehacer: Los botones con flechas de la barra inferior revierten o recuperan cambios del organigrama. También puedes usar [Ctrl] + [Z] para deshacer y [Ctrl] + [Y] o [Ctrl] + [Mayús] + [Z] para rehacer.\n",
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
    """Show the organization chart help dialog."""
    show_shared_help_dialog(parent, HELP_CONFIG)


__all__ = ["show_help_dialog"]
