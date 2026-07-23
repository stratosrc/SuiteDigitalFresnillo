"""Reusable indeterminate progress overlay for long-running operations."""

from __future__ import annotations

import customtkinter as ctk


class ProgressOverlay(ctk.CTkFrame):
    """Centered loading panel displayed above an application's workspace."""

    def __init__(self, master, *, color: str = "#131C46") -> None:
        super().__init__(
            master,
            fg_color="#FFFFFF",
            border_width=1,
            border_color=color,
            corner_radius=0,
        )
        self.label = ctk.CTkLabel(
            self,
            text="Generando PDF...",
            text_color=color,
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self.label.pack(padx=40, pady=(26, 13))
        self.progress = ctk.CTkProgressBar(
            self,
            width=280,
            mode="indeterminate",
            progress_color=color,
            corner_radius=0,
        )
        self.progress.pack(padx=40, pady=(0, 26))

    def show(self, message: str) -> None:
        self.label.configure(text=message)
        self.place(relx=0.5, rely=0.5, anchor="center")
        self.lift()
        self.progress.start()

    def hide(self) -> None:
        self.progress.stop()
        self.place_forget()


__all__ = ["ProgressOverlay"]
