from PIL import Image


def crop_transparent_padding(image: Image.Image) -> Image.Image:
    rgba_image = image.convert("RGBA")
    visible_box = rgba_image.getchannel("A").getbbox()
    if visible_box:
        return rgba_image.crop(visible_box)
    return rgba_image


__all__ = ["crop_transparent_padding"]
