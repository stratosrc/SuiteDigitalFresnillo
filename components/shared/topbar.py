"""Shared top bar builder for suite applications."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

import customtkinter as ctk


@dataclass(frozen=True, slots=True)
class TopbarStyle:
    """Colors and font used by a suite top bar."""

    background: str
    primary: str
    primary_hover: str
    danger: str
    danger_hover: str
    text: str
    font: ctk.CTkFont


@dataclass(frozen=True, slots=True)
class TopbarButton:
    """Declarative definition of one top bar command."""

    key: str
    text: str
    command: Callable[[], None]
    column: int
    width: int = 72
    danger: bool = False


def build_topbar(
    parent: ctk.CTkFrame,
    style: TopbarStyle,
    buttons: Sequence[TopbarButton],
) -> tuple[ctk.CTkFrame, dict[str, ctk.CTkButton]]:
    """Build the standard fixed-height suite top bar."""
    topbar = ctk.CTkFrame(parent, fg_color=style.background, corner_radius=0, height=24)
    topbar.grid(row=0, column=0, sticky="ew")
    topbar.grid_columnconfigure(2, weight=1)
    topbar.grid_propagate(False)

    widgets: dict[str, ctk.CTkButton] = {}
    for definition in buttons:
        button = ctk.CTkButton(
            topbar,
            text=definition.text,
            command=definition.command,
            height=24,
            width=definition.width,
            corner_radius=0,
            fg_color=style.danger if definition.danger else style.primary,
            hover_color=style.danger_hover if definition.danger else style.primary_hover,
            text_color=style.text,
            font=style.font,
        )
        is_trailing = definition.column >= 3
        button.grid(
            row=0,
            column=definition.column,
            padx=(4, 0) if is_trailing else (0, 4),
            sticky="e" if is_trailing else "w",
        )
        widgets[definition.key] = button
    return topbar, widgets


__all__ = ["TopbarButton", "TopbarStyle", "build_topbar"]
