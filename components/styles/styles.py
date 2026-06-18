"""Compatibility facade for shared UI style tokens."""

import tkinter as tk

from components.styles.colors import (
    APP_BG,
    BORDER_BG,
    BUTTON_BG,
    BUTTON_BG_ACTIVE,
    BUTTON_BG_PRESSED,
    BUTTON_BG2,
    CANVAS_BG,
    DANGER_BG,
    DANGER_BG_ACTIVE,
    DARK_BG,
    DARK_BG_ACTIVE,
    DARK_BG_PRESSED,
    GHOST_AVAILABLE_FILL,
    GHOST_OCCUPIED_FILL,
    GRID_AXIS,
    GRID_LINE,
    LIGHT_BLUE,
    NEUTRAL_GRAY,
    PLACEHOLDER_TEXT,
    PRIMARY_BLUE,
    SECONDARY_BLUE,
    SELECTED_OUTLINE,
    SUCCESS_BG,
    SUCCESS_BG_ACTIVE,
    SURFACE_ALT_BG,
    SURFACE_BG,
    TEXT_DARK,
    TEXT_LIGHT,
    TEXT_MUTED,
)
from components.styles.spacing import (
    BUTTON_RADIUS,
    CONTROL_GAP,
    CTK_COMPACT_BUTTON_SIZE,
    CTK_ENTRY_HEIGHT,
    CTK_RADIUS,
    FOOTER_HEIGHT,
    HEADER_HEIGHT,
    HEADER_LOGO_SIZE,
    SECTION_GAP,
    WINDOW_PAD,
)
from components.styles.typography import (
    CTK_FONT_FAMILY,
    FONT_FAMILY,
    SEGOE_UI_BOLD_FONT_FILE,
    SEGOE_UI_FONT_FILE,
)


def apply_ctk_style(ctk):
    ctk.set_appearance_mode("Light")
    ctk.set_default_color_theme("blue")


def styles(app):
    try:
        app.configure(fg_color=APP_BG)
    except (tk.TclError, TypeError):
        app.configure(bg=APP_BG)


__all__ = [
    "APP_BG",
    "BORDER_BG",
    "BUTTON_BG",
    "BUTTON_BG2",
    "BUTTON_BG_ACTIVE",
    "BUTTON_BG_PRESSED",
    "BUTTON_RADIUS",
    "CANVAS_BG",
    "CONTROL_GAP",
    "CTK_COMPACT_BUTTON_SIZE",
    "CTK_ENTRY_HEIGHT",
    "CTK_FONT_FAMILY",
    "CTK_RADIUS",
    "DANGER_BG",
    "DANGER_BG_ACTIVE",
    "DARK_BG",
    "DARK_BG_ACTIVE",
    "DARK_BG_PRESSED",
    "FONT_FAMILY",
    "FOOTER_HEIGHT",
    "GHOST_AVAILABLE_FILL",
    "GHOST_OCCUPIED_FILL",
    "GRID_AXIS",
    "GRID_LINE",
    "HEADER_HEIGHT",
    "HEADER_LOGO_SIZE",
    "LIGHT_BLUE",
    "NEUTRAL_GRAY",
    "PLACEHOLDER_TEXT",
    "PRIMARY_BLUE",
    "SECONDARY_BLUE",
    "SECTION_GAP",
    "SEGOE_UI_BOLD_FONT_FILE",
    "SEGOE_UI_FONT_FILE",
    "SELECTED_OUTLINE",
    "SUCCESS_BG",
    "SUCCESS_BG_ACTIVE",
    "SURFACE_ALT_BG",
    "SURFACE_BG",
    "TEXT_DARK",
    "TEXT_LIGHT",
    "TEXT_MUTED",
    "WINDOW_PAD",
    "apply_ctk_style",
    "styles",
]
