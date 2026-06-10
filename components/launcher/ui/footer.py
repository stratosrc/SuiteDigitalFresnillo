import customtkinter as ctk

from components.launcher.config import FOOTER_TEXT
from components.styles.styles import CTK_FONT_FAMILY, SURFACE_ALT_BG, TEXT_MUTED


class LauncherFooter(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=SURFACE_ALT_BG, corner_radius=0)

        self.columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self,
            text=FOOTER_TEXT,
            fg_color=SURFACE_ALT_BG,
            text_color=TEXT_MUTED,
            font=ctk.CTkFont(family=CTK_FONT_FAMILY, size=10),
            anchor="center",
            height=36,
        ).grid(row=0, column=0, sticky="ew")
