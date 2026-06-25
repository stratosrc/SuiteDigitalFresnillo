from __future__ import annotations

from PIL import Image

from components.shared.images import crop_transparent


def crop_transparent_padding(image: Image.Image) -> Image.Image:
    return crop_transparent(image)


__all__ = ["crop_transparent_padding"]
