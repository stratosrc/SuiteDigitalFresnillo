"""Application header area."""

import tkinter as tk

import customtkinter as ctk

from App_TestData.config.ui_strings import HEADER_TITLE
from App_TestData.config.settings import LOGO1_PATH
from App_TestData.ui.widgets.factory import build_font
from components.shared.images import load_ctk_image
from components.styles.styles import DARK_BG, HEADER_HEIGHT, HEADER_LOGO_SIZE, TEXT_LIGHT


def build_header(parent):
    """Build the application header with logo and title."""
    title_frame = ctk.CTkFrame(parent, fg_color=DARK_BG, corner_radius=0, height=HEADER_HEIGHT)
    title_frame.pack(side=tk.TOP, fill=tk.X)
    title_frame.pack_propagate(False)

    logo_image = None
    logo_label = None
    logo_image = load_ctk_image(LOGO1_PATH, HEADER_LOGO_SIZE, crop_alpha=True)
    if logo_image is not None:
        logo_label = ctk.CTkLabel(title_frame, image=logo_image, text="", fg_color=DARK_BG)
        logo_label.pack(side=tk.RIGHT, padx=(0, 16))

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
