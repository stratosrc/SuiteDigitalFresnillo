"""Reusable modal help dialog used by suite applications."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
import tkinter as tk

import customtkinter as ctk


HelpSection = tuple[str, Sequence[str]]
FontFactory = Callable[[int, str | None], ctk.CTkFont]


@dataclass(frozen=True, slots=True)
class HelpDialogStyle:
    """Visual tokens required by the shared help dialog."""

    app_background: str
    surface_background: str
    primary_button: str
    primary_button_active: str
    text_dark: str
    text_light: str
    make_font: FontFactory


@dataclass(frozen=True, slots=True)
class HelpDialogDimensions:
    """Size constraints for a help window."""

    width: int = 550
    height: int = 600
    min_width: int = 500
    min_height: int = 520
    bullet_wrap_length: int = 470


@dataclass(frozen=True, slots=True)
class HelpDialogConfig:
    """Content and presentation for one application's help window."""

    sections: Sequence[HelpSection]
    style: HelpDialogStyle
    title: str = "Ayuda"
    heading: str = "Guía de uso"
    close_label: str = "Cerrar"
    dimensions: HelpDialogDimensions = HelpDialogDimensions()


def show_help_dialog(parent: tk.Misc, config: HelpDialogConfig) -> None:
    """Open a centered, modal and scrollable help window."""
    dimensions = config.dimensions
    parent_window = parent.winfo_toplevel()
    help_window = ctk.CTkToplevel(parent_window)
    help_window.title(config.title)
    help_window.geometry(f"{dimensions.width}x{dimensions.height}")
    help_window.minsize(dimensions.min_width, dimensions.min_height)
    help_window.configure(fg_color=config.style.app_background)
    help_window.transient(parent_window)

    _center_window(parent_window, help_window, dimensions.width, dimensions.height)
    _build_content(help_window, config)

    help_window.protocol("WM_DELETE_WINDOW", help_window.destroy)
    help_window.focus_set()
    help_window.grab_set()


def _build_content(help_window: ctk.CTkToplevel, config: HelpDialogConfig) -> None:
    style = config.style
    main_frame = ctk.CTkFrame(
        help_window,
        fg_color=style.app_background,
        corner_radius=0,
    )
    main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    ctk.CTkLabel(
        main_frame,
        text=config.heading,
        fg_color=style.app_background,
        text_color=style.text_dark,
        font=style.make_font(18, "bold"),
        anchor="w",
    ).pack(fill=tk.X, anchor=tk.W, pady=(0, 12))

    scroll_frame = ctk.CTkScrollableFrame(
        main_frame,
        fg_color=style.surface_background,
        corner_radius=0,
        scrollbar_button_color=style.primary_button,
        scrollbar_button_hover_color=style.primary_button_active,
    )
    scroll_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 14))
    _populate_sections(scroll_frame, config)

    ctk.CTkButton(
        main_frame,
        text=config.close_label,
        command=help_window.destroy,
        fg_color=style.primary_button,
        hover_color=style.primary_button_active,
        text_color=style.text_light,
        corner_radius=0,
        font=style.make_font(12, None),
    ).pack(side=tk.BOTTOM, fill=tk.X)


def _populate_sections(
    scroll_frame: ctk.CTkScrollableFrame,
    config: HelpDialogConfig,
) -> None:
    style = config.style
    for section_title, bullet_items in config.sections:
        ctk.CTkLabel(
            scroll_frame,
            text=section_title,
            fg_color=style.surface_background,
            text_color=style.text_dark,
            font=style.make_font(13, "bold"),
            anchor="w",
            justify="left",
        ).pack(fill=tk.X, anchor=tk.W, padx=12, pady=(14, 6))

        for bullet_text in bullet_items:
            ctk.CTkLabel(
                scroll_frame,
                text=f"* {bullet_text}",
                fg_color=style.surface_background,
                text_color=style.text_dark,
                font=style.make_font(12, None),
                anchor="w",
                justify="left",
                wraplength=config.dimensions.bullet_wrap_length,
            ).pack(fill=tk.X, anchor=tk.W, padx=20, pady=(0, 5))


def _center_window(
    parent: tk.Misc,
    window: ctk.CTkToplevel,
    width: int,
    height: int,
) -> None:
    parent.update_idletasks()
    x_position = parent.winfo_rootx() + (parent.winfo_width() - width) // 2
    y_position = parent.winfo_rooty() + (parent.winfo_height() - height) // 2
    window.geometry(f"{width}x{height}+{max(x_position, 0)}+{max(y_position, 0)}")


__all__ = [
    "HelpDialogConfig",
    "HelpDialogDimensions",
    "HelpDialogStyle",
    "HelpSection",
    "show_help_dialog",
]
