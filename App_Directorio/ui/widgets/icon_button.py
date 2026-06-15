from collections.abc import Callable
from pathlib import Path
import tkinter as tk

import customtkinter as ctk

from components.shared.images import load_ctk_image


IconPair = tuple[ctk.CTkImage | None, ctk.CTkImage | None]


def load_action_icon(path: Path, size: tuple[int, int]) -> ctk.CTkImage | None:
    return load_ctk_image(path, size)


def load_icon_pair(path: Path, hover_path: Path, size: tuple[int, int]) -> IconPair:
    normal_icon = load_action_icon(path, size)
    hover_icon = load_action_icon(hover_path, size)
    return normal_icon, hover_icon or normal_icon


class HoverIconButton(ctk.CTkButton):
    def __init__(
        self,
        master: ctk.CTkFrame,
        icons: IconPair,
        command: Callable[[], None],
        width: int,
        height: int,
    ) -> None:
        self.normal_icon, self.hover_icon = icons
        super().__init__(
            master,
            text="",
            image=self.normal_icon,
            command=command,
            width=width,
            height=height,
            corner_radius=0,
            border_width=0,
            fg_color="transparent",
            hover=False,
            cursor="hand2",
        )
        self.bind("<Enter>", self._show_hover_icon)
        self.bind("<Leave>", self._show_normal_icon)

    def _show_hover_icon(self, _event: tk.Event) -> None:
        if self.hover_icon is not None:
            self.configure(image=self.hover_icon)

    def _show_normal_icon(self, _event: tk.Event) -> None:
        if self.normal_icon is not None:
            self.configure(image=self.normal_icon)


__all__ = [
    "HoverIconButton",
    "IconPair",
    "load_action_icon",
    "load_icon_pair",
]
