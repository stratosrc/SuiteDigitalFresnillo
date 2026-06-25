"""Shared image loading helpers for Tk/CustomTkinter apps."""

from __future__ import annotations

from pathlib import Path

import customtkinter as ctk
from PIL import Image, ImageOps


ImageSize = tuple[int, int]
_CTK_IMAGE_CACHE: dict[tuple[Path, ImageSize, bool], ctk.CTkImage] = {}


def load_pil_rgba(path: str | Path) -> Image.Image | None:
    image_path = Path(path)
    if not image_path.exists():
        return None

    try:
        return Image.open(image_path).convert("RGBA")
    except OSError:
        return None


def crop_transparent(image: Image.Image) -> Image.Image:
    rgba_image = image.convert("RGBA")
    visible_box = rgba_image.getchannel("A").getbbox()
    if visible_box:
        return rgba_image.crop(visible_box)
    return rgba_image


def load_ctk_image(
    path: str | Path,
    size: ImageSize,
    *,
    crop_alpha: bool = False,
    use_cache: bool = True,
) -> ctk.CTkImage | None:
    image_path = Path(path)
    cache_key = (image_path, size, crop_alpha)
    if use_cache and cache_key in _CTK_IMAGE_CACHE:
        return _CTK_IMAGE_CACHE[cache_key]

    image = load_pil_rgba(image_path)
    if image is None:
        return None
    if crop_alpha:
        image = crop_transparent(image)

    resized = ImageOps.contain(image, size, Image.Resampling.LANCZOS)
    ctk_image = ctk.CTkImage(light_image=resized, dark_image=resized, size=resized.size)
    if use_cache:
        _CTK_IMAGE_CACHE[cache_key] = ctk_image
    return ctk_image
