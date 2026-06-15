"""Image loading and cache helpers for the organigram canvas."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageOps, ImageTk


def load_rgba_image(path: Path) -> Image.Image | None:
    """Load an image as RGBA, returning None if it cannot be read."""
    if not path.exists():
        return None
    try:
        return Image.open(path).convert("RGBA")
    except OSError:
        return None


def get_resized_photo(
    source_image: Image.Image | None,
    cache: dict[int, ImageTk.PhotoImage],
    size: int,
    *,
    crop_alpha: bool = False,
) -> ImageTk.PhotoImage | None:
    """Return a cached resized PhotoImage."""
    if source_image is None or size <= 0:
        return None
    if size in cache:
        return cache[size]

    image = source_image.copy()
    active_box = image.getchannel("A").getbbox() if crop_alpha else image.getbbox()
    if active_box:
        image = image.crop(active_box)
    resized = ImageOps.contain(image, (size, size), Image.Resampling.LANCZOS)
    tk_image = ImageTk.PhotoImage(resized)
    cache[size] = tk_image
    return tk_image
