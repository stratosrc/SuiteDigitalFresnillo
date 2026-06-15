"""Help dialog shown from the main toolbar."""

import tkinter as tk

import customtkinter as ctk

from App_TestData.config.ui_strings import HELP_DIALOG
from App_TestData.ui.widgets.factory import build_font
from components.styles.styles import (
    APP_BG,
    BUTTON_BG,
    BUTTON_BG_ACTIVE,
    SURFACE_BG,
    TEXT_DARK,
    TEXT_LIGHT,
)


def show_help_dialog(parent):
    """Open the application help dialog."""
    help_window = ctk.CTkToplevel(parent)
    help_window.title(HELP_DIALOG["title"])
    help_window.geometry("550x600")
    help_window.minsize(500, 520)
    help_window.configure(fg_color=APP_BG)
    help_window.transient(parent)

    _center_toplevel(parent, help_window, 550, 600)

    main_frame = ctk.CTkFrame(help_window, fg_color=APP_BG, corner_radius=0)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    ctk.CTkLabel(
        main_frame,
        text=HELP_DIALOG["heading"],
        fg_color=APP_BG,
        text_color=TEXT_DARK,
        font=build_font(18, "bold"),
        anchor="w",
    ).pack(fill=tk.X, anchor=tk.W, pady=(0, 12))

    scroll_frame = ctk.CTkScrollableFrame(
        main_frame,
        fg_color=SURFACE_BG,
        corner_radius=0,
        scrollbar_button_color=BUTTON_BG,
        scrollbar_button_hover_color=BUTTON_BG_ACTIVE,
    )
    scroll_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 14))

    for section_title, bullets in HELP_DIALOG["sections"]:
        ctk.CTkLabel(
            scroll_frame,
            text=section_title,
            fg_color=SURFACE_BG,
            text_color=TEXT_DARK,
            font=build_font(13, "bold"),
            anchor="w",
            justify="left",
        ).pack(fill=tk.X, anchor=tk.W, padx=12, pady=(14, 6))

        for bullet in bullets:
            ctk.CTkLabel(
                scroll_frame,
                text=f"* {bullet}",
                fg_color=SURFACE_BG,
                text_color=TEXT_DARK,
                font=build_font(12),
                anchor="w",
                justify="left",
                wraplength=470,
            ).pack(fill=tk.X, anchor=tk.W, padx=20, pady=(0, 5))

    close_button = ctk.CTkButton(
        main_frame,
        text=HELP_DIALOG["close"],
        command=help_window.destroy,
        fg_color=BUTTON_BG,
        hover_color=BUTTON_BG_ACTIVE,
        text_color=TEXT_LIGHT,
        corner_radius=0,
        font=build_font(12),
    )
    close_button.pack(side=tk.BOTTOM, fill=tk.X)

    help_window.protocol("WM_DELETE_WINDOW", help_window.destroy)
    help_window.focus_set()
    help_window.grab_set()


def _center_toplevel(parent, window, width: int, height: int):
    """Center a child window on top of its parent window."""
    parent.update_idletasks()
    x_position = parent.winfo_rootx() + (parent.winfo_width() - width) // 2
    y_position = parent.winfo_rooty() + (parent.winfo_height() - height) // 2
    window.geometry(f"{width}x{height}+{max(x_position, 0)}+{max(y_position, 0)}")
