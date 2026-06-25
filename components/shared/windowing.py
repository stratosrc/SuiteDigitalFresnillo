"""Shared window geometry helpers."""

from __future__ import annotations


import tkinter as tk


def center_window(window: tk.Misc, width: int, height: int) -> None:
    window.update_idletasks()
    x_position = (window.winfo_screenwidth() - width) // 2
    y_position = (window.winfo_screenheight() - height) // 2
    window.geometry(f"{width}x{height}+{x_position}+{y_position}")


def prepare_window_for_open(window: tk.Misc) -> None:
    try:
        window.withdraw()
    except tk.TclError:
        pass


def maximize_window(window: tk.Misc) -> None:
    try:
        window.update_idletasks()
        window.state("zoomed")
        return
    except tk.TclError:
        pass

    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    window.geometry(f"{screen_width}x{screen_height}+0+0")


def reveal_window_maximized(window: tk.Misc) -> None:
    def reveal() -> None:
        maximize_window(window)
        try:
            window.deiconify()
            window.lift()
        except tk.TclError:
            return

    after_idle = getattr(window, "after_idle", None)
    if callable(after_idle):
        after_idle(reveal)
    else:
        reveal()
