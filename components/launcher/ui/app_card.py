import customtkinter as ctk

from components.styles.styles import (
    CTK_FONT_FAMILY,
    DARK_BG,
    DARK_BG_ACTIVE,
    TEXT_LIGHT,
)


def _ctk_font(size, weight=None):
    return ctk.CTkFont(family=CTK_FONT_FAMILY, size=size, weight=weight)


class ApplicationCard(ctk.CTkFrame):
    def __init__(self, parent, app_config, image_loader, launch_callback):
        super().__init__(
            parent,
            fg_color=DARK_BG,
            corner_radius=0,
            border_width=1,
            border_color=DARK_BG,
            cursor="hand2",
        )

        self.app_config = app_config
        self.launch_callback = launch_callback
        self.columnconfigure(0, weight=1)

        icon = image_loader.load_icon(app_config["icon_path"])
        self.icon_label = ctk.CTkLabel(self, image=icon, text="", fg_color="transparent", cursor="hand2")
        self.icon_label.image = icon
        self.icon_label.grid(row=0, column=0, pady=(18, 10), padx=18)

        self.name_label = ctk.CTkLabel(
            self,
            text=app_config["name"],
            fg_color="transparent",
            text_color=TEXT_LIGHT,
            font=_ctk_font(13, "bold"),
            anchor="center",
            cursor="hand2",
        )
        self.name_label.grid(row=1, column=0, sticky="ew", padx=18)

        self.description_label = ctk.CTkLabel(
            self,
            text=app_config.get("description", ""),
            fg_color="transparent",
            text_color=TEXT_LIGHT,
            font=_ctk_font(10),
            anchor="center",
            wraplength=180,
            justify="center",
            cursor="hand2",
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
        self.configure(fg_color=DARK_BG_ACTIVE, border_color=DARK_BG_ACTIVE)

    def _on_leave(self, _event):
        self.configure(fg_color=DARK_BG, border_color=DARK_BG)

    def _on_click(self, _event):
        self.launch_callback(self.app_config)
