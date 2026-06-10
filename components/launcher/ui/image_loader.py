import os

import customtkinter as ctk
from PIL import Image

from components.launcher.paths import build_path
from components.styles.styles import DARK_BG_ACTIVE


class ImageLoader:
    def __init__(self):
        self._icon_cache = {}

    def load_icon(self, relative_path, size=(64, 64)):
        absolute_path = build_path(relative_path)
        cache_key = (absolute_path, size)

        if cache_key in self._icon_cache:
            return self._icon_cache[cache_key]

        try:
            image = Image.open(absolute_path).convert("RGBA") if os.path.exists(absolute_path) else None
        except OSError:
            image = None

        if image is None:
            image = Image.new("RGBA", size, DARK_BG_ACTIVE)

        image.thumbnail(size, Image.LANCZOS)
        canvas = Image.new("RGBA", size, (255, 255, 255, 0))
        x = (size[0] - image.width) // 2
        y = (size[1] - image.height) // 2
        canvas.paste(image, (x, y), image)

        photo = ctk.CTkImage(light_image=canvas, dark_image=canvas, size=size)
        self._icon_cache[cache_key] = photo
        return photo

    def open_image(self, relative_path):
        absolute_path = build_path(relative_path)
        if not os.path.exists(absolute_path):
            return None
        try:
            return Image.open(absolute_path).convert("RGBA")
        except OSError:
            return None
