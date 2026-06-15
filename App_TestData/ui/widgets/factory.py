"""Shared UI widget factories and font helpers."""

import tkinter as tk

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


class Tooltip:
    """Small hover tooltip for Tk/CustomTkinter widgets."""

    def __init__(self, widget, text: str, delay_ms: int = 450, show_when_disabled: bool = False):
        self.widget = widget
        self.text = text
        self.delay_ms = delay_ms
        self.show_when_disabled = show_when_disabled
        self._after_id = None
        self._window = None

        widget.bind("<Enter>", self._schedule, add=True)
        widget.bind("<Leave>", self._hide, add=True)
        widget.bind("<ButtonPress>", self._hide, add=True)
        widget.bind("<FocusOut>", self._hide, add=True)
        widget.bind("<Unmap>", self._hide, add=True)
        widget.bind("<Destroy>", self._hide, add=True)

    def _schedule(self, _event=None):
        self._cancel()
        if not self._can_show():
            return
        self._after_id = self.widget.after(self.delay_ms, self._show)

    def _show(self):
        if self._window is not None or not self.text or not self._can_show():
            return

        x = self.widget.winfo_rootx() + self.widget.winfo_width() // 2
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6

        self._window = tk.Toplevel(self.widget)
        self._window.wm_overrideredirect(True)
        self._window.transient(self.widget.winfo_toplevel())
        self._window.wm_geometry(f"+{x}+{y}")
        self._window.bind("<FocusOut>", self._hide, add=True)
        self._window.bind("<ButtonPress>", self._hide, add=True)

        label = tk.Label(
            self._window,
            text=self.text,
            bg=SURFACE_BG,
            fg=TEXT_DARK,
            relief=tk.SOLID,
            borderwidth=1,
            padx=8,
            pady=4,
            font=(CTK_FONT_FAMILY, 9),
        )
        label.pack()

    def _hide(self, _event=None):
        self._cancel()
        if self._window is not None:
            try:
                self._window.destroy()
            except tk.TclError:
                pass
            self._window = None

    def _cancel(self):
        if self._after_id is not None:
            try:
                self.widget.after_cancel(self._after_id)
            except tk.TclError:
                pass
            self._after_id = None

    def _can_show(self) -> bool:
        try:
            if not self.widget.winfo_exists() or not self.widget.winfo_ismapped():
                return False
            return self.show_when_disabled or str(self.widget.cget("state")) != tk.DISABLED
        except tk.TclError:
            return False


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
    disabled_tooltip: str | None = None,
):
    """Create a compact toolbar button with an icon and tooltip-friendly text."""
    image = load_ctk_image(icon_path, (18, 18))
    button = ctk.CTkButton(
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
        text_color_disabled=TEXT_LIGHT,
        font=build_font(12, "bold" if danger else None),
    )
    button._normal_fg_color = DANGER_BG if danger else BUTTON_BG
    button._disabled_fg_color = BORDER_BG
    button._tooltip_text = text
    button._disabled_tooltip_text = disabled_tooltip or text
    button.tooltip = Tooltip(button, text, show_when_disabled=disabled_tooltip is not None)
    return button


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
