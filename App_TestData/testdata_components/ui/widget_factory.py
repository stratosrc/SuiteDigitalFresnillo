"""Shared UI widget factories and font helpers."""

import customtkinter as ctk

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
)


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
