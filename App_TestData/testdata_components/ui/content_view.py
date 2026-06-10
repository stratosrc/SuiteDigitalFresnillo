"""Central PDF content view."""

import tkinter as tk

import customtkinter as ctk

from App_TestData.testdata_components.config.ui_strings import CONTENT_LABELS
from App_TestData.testdata_components.constants import PDF_CANVAS_BG
from App_TestData.testdata_components.ui.widget_factory import build_font
from components.styles.styles import APP_BG, SURFACE_BG, TEXT_DARK


def build_content_view(parent, on_canvas_resize):
    """Build the main message area and PDF canvas."""
    content_frame = ctk.CTkFrame(parent, fg_color=APP_BG, corner_radius=0)
    content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    message_label = ctk.CTkLabel(
        content_frame,
        text=CONTENT_LABELS["empty_state"],
        fg_color=APP_BG,
        text_color=TEXT_DARK,
        font=build_font(14),
        anchor="w",
    )
    message_label.pack(anchor=tk.NW, pady=(0, 10))

    canvas_frame = ctk.CTkFrame(content_frame, fg_color=SURFACE_BG, corner_radius=0)
    canvas_frame.pack(fill=tk.BOTH, expand=True)

    vertical_scrollbar = ctk.CTkScrollbar(canvas_frame, orientation="vertical")
    vertical_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    horizontal_scrollbar = ctk.CTkScrollbar(canvas_frame, orientation="horizontal")
    horizontal_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

    pdf_canvas = tk.Canvas(
        canvas_frame,
        bg=PDF_CANVAS_BG,
        xscrollcommand=horizontal_scrollbar.set,
        yscrollcommand=vertical_scrollbar.set,
        highlightthickness=0,
        bd=0,
    )
    pdf_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    vertical_scrollbar.configure(command=pdf_canvas.yview)
    horizontal_scrollbar.configure(command=pdf_canvas.xview)
    pdf_canvas.bind("<Configure>", on_canvas_resize)

    return {
        "content_frame": content_frame,
        "message_label": message_label,
        "pdf_canvas": pdf_canvas,
    }
