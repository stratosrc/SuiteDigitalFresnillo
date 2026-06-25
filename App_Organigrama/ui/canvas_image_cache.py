"""Image loading and cache helpers for the organigram canvas."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageOps, ImageTk

from components.shared.images import crop_transparent, load_pil_rgba


def load_rgba_image(path: Path) -> Image.Image | None:
    """Load an image as RGBA, returning None if it cannot be read."""
    return load_pil_rgba(path)


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

    image = crop_transparent(source_image) if crop_alpha else source_image.copy()
    resized = ImageOps.contain(image, (size, size), Image.Resampling.LANCZOS)
    tk_image = ImageTk.PhotoImage(resized)
    cache[size] = tk_image
    return tk_image
