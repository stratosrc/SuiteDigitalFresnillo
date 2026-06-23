import customtkinter as ctk

from components.launcher.config import FOOTER_TEXT, LEGAL_NOTICE_TEXT
from components.styles.styles import CTK_FONT_FAMILY, SURFACE_ALT_BG, TEXT_MUTED


class LauncherFooter(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=SURFACE_ALT_BG, corner_radius=0)

        self.columnconfigure(0, weight=1)

        self.legal_notice_label = ctk.CTkLabel(
            self,
            text=LEGAL_NOTICE_TEXT,
            fg_color=SURFACE_ALT_BG,
            text_color=TEXT_MUTED,
            font=ctk.CTkFont(family=CTK_FONT_FAMILY, size=10),
            anchor="center",
            justify="center",
            wraplength=760,
        )
        self.legal_notice_label.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=16,
            pady=(12, 4),
        )

        ctk.CTkLabel(
            self,
            text=FOOTER_TEXT,
            fg_color=SURFACE_ALT_BG,
            text_color=TEXT_MUTED,
            font=ctk.CTkFont(family=CTK_FONT_FAMILY, size=10),
            anchor="center",
            height=36,
        ).grid(row=1, column=0, sticky="ew")

        self.bind("<Configure>", self._update_notice_wraplength)

    def _update_notice_wraplength(self, event):
        self.legal_notice_label.configure(wraplength=max(event.width - 32, 1))
