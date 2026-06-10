import tkinter as tk

import customtkinter as ctk

from components.styles.styles import APP_BG


class ScrollableFrame(ctk.CTkFrame):
    """Frame CTk con desplazamiento vertical para grids que crecerán con la suite."""

    def __init__(self, parent, **kwargs):
        kwargs.setdefault("fg_color", APP_BG)
        kwargs.setdefault("corner_radius", 0)
        super().__init__(parent, **kwargs)

        self.canvas = tk.Canvas(
            self,
            bg=APP_BG,
            highlightthickness=0,
            bd=0,
        )
        self.scrollbar = ctk.CTkScrollbar(self, orientation="vertical", command=self.canvas.yview)
        self.content = ctk.CTkFrame(self.canvas, fg_color=APP_BG, corner_radius=0)

        self.window_id = self.canvas.create_window((0, 0), window=self.content, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.content.bind("<Configure>", self._on_content_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_content_configure(self, _event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfigure(self.window_id, width=event.width)

    def _on_mousewheel(self, event):
        if self.winfo_ismapped():
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
