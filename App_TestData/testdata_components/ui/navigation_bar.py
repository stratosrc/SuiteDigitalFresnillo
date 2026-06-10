"""Bottom navigation bar for page and zoom controls."""

import tkinter as tk

import customtkinter as ctk

from App_TestData.testdata_components.config.ui_strings import NAVIGATION_LABELS
from App_TestData.testdata_components.ui.widget_factory import build_font, create_bottom_toolbar_button, create_toolbar_button
from components.styles.styles import APP_BG, BUTTON_BG, DARK_BG, SURFACE_BG, TEXT_DARK, TEXT_LIGHT


def build_navigation_bar(parent, callbacks: dict):
    """Build the page navigation and zoom controls."""
    navigation_frame = ctk.CTkFrame(parent, fg_color=DARK_BG, corner_radius=0, height=34)
    navigation_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=0, pady=1)

    previous_button = create_bottom_toolbar_button(
        navigation_frame,
        "<",
        callbacks["on_previous_page"],
        width=36,
    )
    previous_button.pack(side=tk.LEFT, padx=(5, 4), pady=5)

    next_button = create_bottom_toolbar_button(
        navigation_frame,
        ">",
        callbacks["on_next_page"],
        width=36,
    )
    next_button.pack(side=tk.LEFT, padx=(0, 9), pady=5)

    ctk.CTkLabel(
        navigation_frame,
        text=NAVIGATION_LABELS["page"],
        fg_color=DARK_BG,
        text_color=TEXT_LIGHT,
        font=build_font(12),
    ).pack(side=tk.LEFT, padx=(0, 4), pady=5)

    page_entry = ctk.CTkEntry(
        navigation_frame,
        width=54,
        height=28,
        fg_color=APP_BG,
        text_color=TEXT_DARK,
        border_color=BUTTON_BG,
        font=build_font(12),
    )
    page_entry.pack(side=tk.LEFT, padx=(0, 4), pady=5)
    page_entry.insert(0, "1")

    total_pages_label = ctk.CTkLabel(
        navigation_frame,
        text=NAVIGATION_LABELS["total_pages"].format(total_pages=0),
        fg_color=DARK_BG,
        text_color=TEXT_LIGHT,
        font=build_font(12),
    )
    total_pages_label.pack(side=tk.LEFT, padx=(0, 8), pady=5)

    go_button = create_bottom_toolbar_button(
        navigation_frame,
        NAVIGATION_LABELS["go"],
        callbacks["on_go_to_page"],
        width=42,
    )
    go_button.pack(side=tk.LEFT, padx=(0, 10), pady=5)

    zoom_frame = ctk.CTkFrame(navigation_frame, fg_color=DARK_BG, corner_radius=0, height=34)
    zoom_frame.pack(side=tk.RIGHT, fill=tk.X, padx=(0,8), pady=1)

    ctk.CTkLabel(
        zoom_frame,
        text=NAVIGATION_LABELS["zoom"],
        fg_color=DARK_BG,
        text_color=TEXT_LIGHT,
        font=build_font(12),
    ).pack(side=tk.LEFT, padx=(0, 4), pady=5)

    zoom_out_button = create_bottom_toolbar_button(
        zoom_frame,
        "-",
        callbacks["on_zoom_out"],
        width=34,
    )
    zoom_out_button.pack(side=tk.LEFT, padx=(0, 5), pady=5)

    zoom_label = ctk.CTkLabel(
        zoom_frame,
        text="100%",
        width=54,
        fg_color=DARK_BG,
        text_color=TEXT_LIGHT,
        font=build_font(12),
        anchor=tk.CENTER,
    )
    zoom_label.pack(side=tk.LEFT, padx=(0, 4), pady=5)

    zoom_in_button = create_bottom_toolbar_button(
        zoom_frame,
        "+",
        callbacks["on_zoom_in"],
        width=34,
    )
    zoom_in_button.pack(side=tk.LEFT, pady=5)

    return {
        "page_entry": page_entry,
        "total_pages_label": total_pages_label,
        "zoom_label": zoom_label,
    }
