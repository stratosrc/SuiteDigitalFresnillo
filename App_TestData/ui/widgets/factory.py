"""Shared UI widget factories and font helpers."""

import customtkinter as ctk
from PIL import Image

from components.styles.styles import (
    BORDER_BG,
    BUTTON_BG,
    BUTTON_BG_ACTIVE,
    CTK_FONT_FAMILY,
    DANGER_BG,
    DANGER_BG_ACTIVE,
    SURFACE_BG,
    TEXT_DARK,
    TEXT_LIGHT,
    BUTTON_BG2,
)

_IMAGE_CACHE = {}


def build_font(size: int, weight: str | None = None) -> ctk.CTkFont:
    """Create a consistent CTk font instance."""
    return ctk.CTkFont(family=CTK_FONT_FAMILY, size=size, weight=weight)


def create_toolbar_button(
    parent,
    text: str,
    command,
    width: int = 100,
    danger: bool = False,
):
    """Create a standard toolbar button."""
    return ctk.CTkButton(
        parent,
        text=text,
        command=command,
        width=width,
        height=28,
        corner_radius=0,
        fg_color=DANGER_BG if danger else BUTTON_BG,
        hover_color=DANGER_BG_ACTIVE if danger else BUTTON_BG_ACTIVE,
        text_color=TEXT_LIGHT,
        font=build_font(12, "bold" if danger else None),
    )


def load_ctk_image(path: str, size: tuple[int, int]) -> ctk.CTkImage | None:
    """Load and cache a CTk-compatible image."""
    cache_key = (path, size)
    if cache_key in _IMAGE_CACHE:
        return _IMAGE_CACHE[cache_key]
    try:
        image = Image.open(path).convert("RGBA")
    except OSError:
        return None
    image.thumbnail(size, Image.Resampling.LANCZOS)
    ctk_image = ctk.CTkImage(light_image=image, dark_image=image, size=image.size)
    _IMAGE_CACHE[cache_key] = ctk_image
    return ctk_image


def create_toolbar_icon_button(
    parent,
    text: str,
    command,
    icon_path: str,
    width: int = 42,
    danger: bool = False,
):
    """Create a compact toolbar button with an icon and tooltip-friendly text."""
    image = load_ctk_image(icon_path, (18, 18))
    return ctk.CTkButton(
        parent,
        text="" if image is not None else text,
        image=image,
        command=command,
        width=width,
        height=28,
        corner_radius=0,
        fg_color=DANGER_BG if danger else BUTTON_BG,
        hover_color=DANGER_BG_ACTIVE if danger else BUTTON_BG_ACTIVE,
        text_color=TEXT_LIGHT,
        font=build_font(12, "bold" if danger else None),
    )


def create_bottom_toolbar_button(
    parent,
    text: str,
    command,
    width: int = 130,
    danger: bool = False,
):
    """Create a standard toolbar button."""
    return ctk.CTkButton(
        parent,
        text=text,
        command=command,
        width=width,
        height=25,
        corner_radius=0,
        fg_color=BUTTON_BG2 if not danger else DANGER_BG,
        hover_color=BUTTON_BG_ACTIVE if not danger else DANGER_BG_ACTIVE,
        text_color=TEXT_LIGHT,
        font=build_font(12, "bold" if danger else None),
    )

def create_entry(parent, textvariable=None, width: int | None = None):
    """Create a standard text entry."""
    return ctk.CTkEntry(
        parent,
        textvariable=textvariable,
        width=width or 180,
        height=30,
        fg_color=SURFACE_BG,
        text_color=TEXT_DARK,
        border_color=BORDER_BG,
        corner_radius=0,
        font=build_font(12),
    )
