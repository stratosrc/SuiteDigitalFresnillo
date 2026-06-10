"""Shared window geometry helpers."""

import tkinter as tk


def center_window(window: tk.Misc, width: int, height: int) -> None:
    window.update_idletasks()
    x_position = (window.winfo_screenwidth() - width) // 2
    y_position = (window.winfo_screenheight() - height) // 2
    window.geometry(f"{width}x{height}+{x_position}+{y_position}")
