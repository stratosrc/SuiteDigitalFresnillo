from __future__ import annotations

from pathlib import Path

import customtkinter as ctk
from PIL import Image

from components.shared.images import load_pil_rgba
from components.shared.paths import build_path
from components.styles.styles import DARK_BG_ACTIVE

IconSize = tuple[int, int]


class ImageLoader:
    def __init__(self) -> None:
        self._icon_cache: dict[tuple[Path, IconSize], ctk.CTkImage] = {}

    def load_icon(self, relative_path: str, size: IconSize = (64, 64)) -> ctk.CTkImage:
        absolute_path = build_path(relative_path)
        cache_key = (absolute_path, size)

        if cache_key in self._icon_cache:
            return self._icon_cache[cache_key]

        image = load_pil_rgba(absolute_path)

        if image is None:
            image = Image.new("RGBA", size, DARK_BG_ACTIVE)

        image.thumbnail(size, Image.Resampling.LANCZOS)
        canvas = Image.new("RGBA", size, (255, 255, 255, 0))
        x = (size[0] - image.width) // 2
        y = (size[1] - image.height) // 2
        canvas.paste(image, (x, y), image)

        photo = ctk.CTkImage(light_image=canvas, dark_image=canvas, size=size)
        self._icon_cache[cache_key] = photo
        return photo

    def open_image(self, relative_path: str) -> Image.Image | None:
        absolute_path = build_path(relative_path)
        if not absolute_path.exists():
            return None
        return load_pil_rgba(absolute_path)
