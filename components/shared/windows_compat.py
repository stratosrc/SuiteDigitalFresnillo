"""Compatibility helpers for Windows versions predating Windows 8.1."""

from __future__ import annotations

import sys


def configure_customtkinter_dpi(customtkinter_module) -> None:
    """Use the legacy DPI API when Windows does not expose shcore."""
    if not sys.platform.startswith("win"):
        return

    import ctypes

    try:
        set_process_dpi_awareness = ctypes.windll.shcore.SetProcessDpiAwareness
    except (AttributeError, OSError):
        customtkinter_module.deactivate_automatic_dpi_awareness()
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except (AttributeError, OSError):
            pass
        return

    try:
        set_process_dpi_awareness(2)
    except OSError:
        pass


__all__ = ["configure_customtkinter_dpi"]
