import customtkinter as ctk
from PIL import Image

from components.launcher.config import BANNER_HEIGHT, BANNER_RELATIVE_PATH, WINDOW_SUBTITLE, WINDOW_TITLE
from components.launcher.ui.image_loader import ImageLoader
from components.styles.styles import CTK_FONT_FAMILY, DARK_BG, DARK_BG_PRESSED, TEXT_LIGHT


def _ctk_font(size, weight=None):
    return ctk.CTkFont(family=CTK_FONT_FAMILY, size=size, weight=weight)


class LauncherHeader(ctk.CTkFrame):
    def __init__(self, parent, image_loader=None):
        super().__init__(parent, fg_color=DARK_BG, corner_radius=0)

        self.image_loader = image_loader or ImageLoader()
        self.banner_original = None
        self.banner_photo = None

        self.columnconfigure(0, weight=1)

        self.banner_label = ctk.CTkLabel(self, text="", fg_color=DARK_BG, height=BANNER_HEIGHT)
        self.banner_label.grid(row=0, column=0, sticky="ew")

        ctk.CTkLabel(
            self,
            text=WINDOW_TITLE,
            fg_color=DARK_BG,
            text_color=TEXT_LIGHT,
            font=_ctk_font(18, "bold"),
            anchor="center",
            height=42,
        ).grid(row=1, column=0, sticky="ew")

        ctk.CTkLabel(
            self,
            text=WINDOW_SUBTITLE,
            fg_color=DARK_BG_PRESSED,
            text_color=TEXT_LIGHT,
            font=_ctk_font(10, "bold"),
            anchor="center",
            height=34,
        ).grid(row=2, column=0, sticky="ew")

        self._load_banner()
        self.bind("<Configure>", self._resize_banner)

    def _load_banner(self):
        self.banner_original = self.image_loader.open_image(BANNER_RELATIVE_PATH)
        self._resize_banner()

    def _resize_banner(self, event=None):
        if self.banner_original is None:
            return

        width = max((event.width if event else self.winfo_width()), 1)
        if width <= 1:
            self.after(50, self._resize_banner)
            return

        original_width, original_height = self.banner_original.size
        banner_height = BANNER_HEIGHT
        ratio_width = width / original_width
        ratio_height = banner_height / original_height
        ratio = min(ratio_width, ratio_height) * 1.8

        resized_width = max(1, int(original_width * ratio))
        resized_height = max(1, int(original_height * ratio))
        resized = self.banner_original.resize((resized_width, resized_height), Image.LANCZOS)

        self.banner_photo = ctk.CTkImage(
            light_image=resized,
            dark_image=resized,
            size=(resized_width, resized_height),
        )
        self.banner_label.configure(image=self.banner_photo, height=banner_height)
