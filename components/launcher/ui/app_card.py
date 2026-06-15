import customtkinter as ctk

from components.styles.styles import (
    CTK_FONT_FAMILY,
    DARK_BG,
    DARK_BG_ACTIVE,
    TEXT_LIGHT,
)

DISABLED_CARD_BG = "#3E4A56"
DISABLED_TEXT = "#B7C0C9"


def _ctk_font(size, weight=None):
    return ctk.CTkFont(family=CTK_FONT_FAMILY, size=size, weight=weight)


class ApplicationCard(ctk.CTkFrame):
    def __init__(self, parent, app_config, image_loader, launch_callback):
        self.is_available = bool(app_config.get("available", True))
        default_bg = DARK_BG if self.is_available else DISABLED_CARD_BG
        cursor = "hand2" if self.is_available else "arrow"

        super().__init__(
            parent,
            fg_color=default_bg,
            corner_radius=0,
            border_width=1,
            border_color=default_bg,
            cursor=cursor,
        )

        self.app_config = app_config
        self.launch_callback = launch_callback
        self.default_bg = default_bg
        self.hover_bg = DARK_BG_ACTIVE if self.is_available else DISABLED_CARD_BG
        self.text_color = TEXT_LIGHT if self.is_available else DISABLED_TEXT
        self.columnconfigure(0, weight=1)

        icon = image_loader.load_icon(app_config["icon_path"])
        self.icon_label = ctk.CTkLabel(self, image=icon, text="", fg_color="transparent", cursor=cursor)
        self.icon_label.image = icon
        self.icon_label.grid(row=0, column=0, pady=(18, 10), padx=18)

        self.name_label = ctk.CTkLabel(
            self,
            text=app_config["name"],
            fg_color="transparent",
            text_color=self.text_color,
            font=_ctk_font(13, "bold"),
            anchor="center",
            cursor=cursor,
        )
        self.name_label.grid(row=1, column=0, sticky="ew", padx=18)

        description = app_config.get("description", "")
        if not self.is_available:
            description = f"{description}\n\nNo disponible"

        self.description_label = ctk.CTkLabel(
            self,
            text=description,
            fg_color="transparent",
            text_color=self.text_color,
            font=_ctk_font(10),
            anchor="center",
            wraplength=180,
            justify="center",
            cursor=cursor,
        )
        self.description_label.grid(row=2, column=0, sticky="ew", pady=(8, 18), padx=18)

        self._bind_events()

    def _bind_events(self):
        for widget in self._clickable_widgets:
            widget.bind("<Enter>", self._on_enter)
            widget.bind("<Leave>", self._on_leave)
            widget.bind("<Button-1>", self._on_click)

    @property
    def _clickable_widgets(self):
        return [self, self.icon_label, self.name_label, self.description_label]

    def _on_enter(self, _event):
        if not self.is_available:
            return
        self.configure(fg_color=self.hover_bg, border_color=self.hover_bg)

    def _on_leave(self, _event):
        self.configure(fg_color=self.default_bg, border_color=self.default_bg)

    def _on_click(self, _event):
        if not self.is_available:
            return
        self.launch_callback(self.app_config)
