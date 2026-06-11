"""Theme tokens for the Directorio application."""

import customtkinter as ctk

from components.styles.styles import (
    APP_BG,
    BORDER_BG,
    BUTTON_BG,
    BUTTON_BG_ACTIVE,
    CTK_FONT_FAMILY,
    DARK_BG,
    SURFACE_BG,
    TEXT_DARK,
    TEXT_LIGHT,
    TEXT_MUTED,
)

APP_BACKGROUND = APP_BG
SURFACE_BACKGROUND = SURFACE_BG
DARK_BACKGROUND = DARK_BG
BORDER_COLOR = BORDER_BG
PRIMARY_BUTTON = BUTTON_BG
PRIMARY_BUTTON_ACTIVE = BUTTON_BG_ACTIVE
FONT_FAMILY = CTK_FONT_FAMILY

WINDOW_WIDTH = 980
WINDOW_HEIGHT = 680
WINDOW_MIN_WIDTH = 820
WINDOW_MIN_HEIGHT = 560


def apply_theme() -> None:
    ctk.set_appearance_mode("Light")
    ctk.set_default_color_theme("blue")


def make_font(size: int, weight: str | None = None) -> ctk.CTkFont:
    font_options: dict[str, str | int] = {"family": FONT_FAMILY, "size": size}
    if weight is not None:
        font_options["weight"] = weight
    return ctk.CTkFont(**font_options)


__all__ = [
    "APP_BACKGROUND",
    "BORDER_COLOR",
    "DARK_BACKGROUND",
    "PRIMARY_BUTTON",
    "PRIMARY_BUTTON_ACTIVE",
    "SURFACE_BACKGROUND",
    "TEXT_DARK",
    "TEXT_LIGHT",
    "TEXT_MUTED",
    "WINDOW_HEIGHT",
    "WINDOW_MIN_HEIGHT",
    "WINDOW_MIN_WIDTH",
    "WINDOW_WIDTH",
    "apply_theme",
    "make_font",
]
