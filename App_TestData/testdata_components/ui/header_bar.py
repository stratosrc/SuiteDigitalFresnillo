"""Application header area."""

import os
import tkinter as tk

import customtkinter as ctk
from PIL import Image, ImageOps

from App_TestData.testdata_components.config.ui_strings import HEADER_TITLE
from App_TestData.testdata_components.constants import LOGO1_PATH
from App_TestData.testdata_components.ui.widget_factory import build_font
from components.styles.styles import DARK_BG, HEADER_HEIGHT, HEADER_LOGO_SIZE, TEXT_LIGHT


def build_header(parent):
    """Build the application header with logo and title."""
    title_frame = ctk.CTkFrame(parent, fg_color=DARK_BG, corner_radius=0, height=HEADER_HEIGHT)
    title_frame.pack(side=tk.TOP, fill=tk.X)
    title_frame.pack_propagate(False)

    logo_image = None
    logo_label = None
    if os.path.exists(LOGO1_PATH):
        try:
            source_image = Image.open(LOGO1_PATH)
            if source_image.mode in ("RGBA", "LA") or (
                source_image.mode == "P" and "transparency" in source_image.info
            ):
                visible_box = source_image.getbbox()
                if visible_box:
                    source_image = source_image.crop(visible_box)
            resized_image = ImageOps.contain(source_image, HEADER_LOGO_SIZE, Image.Resampling.LANCZOS)
            logo_image = ctk.CTkImage(
                light_image=resized_image,
                dark_image=resized_image,
                size=resized_image.size,
            )
            logo_label = ctk.CTkLabel(title_frame, image=logo_image, text="", fg_color=DARK_BG)
            logo_label.pack(side=tk.RIGHT, padx=(0, 16))
        except OSError:
            logo_image = None
            logo_label = None

    title_label = ctk.CTkLabel(
        title_frame,
        text=HEADER_TITLE,
        fg_color=DARK_BG,
        text_color=TEXT_LIGHT,
        font=build_font(17, "bold"),
        anchor="w",
    )
    title_label.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(16, 0))

    return {
        "logo_image": logo_image,
        "logo_label": logo_label,
        "title_label": title_label,
    }
