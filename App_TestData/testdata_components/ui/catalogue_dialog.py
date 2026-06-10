"""Catalogue dialog UI."""

import tkinter as tk

import customtkinter as ctk

from App_TestData.testdata_components.config.ui_strings import CATALOGUE_DIALOG
from App_TestData.testdata_components.constants import (
    CATALOGUE_COLUMN_PADDING,
    CATALOGUE_MAIN_PADDING,
    CATALOGUE_WINDOW_HEIGHT,
    CATALOGUE_WINDOW_MIN_HEIGHT,
    CATALOGUE_WINDOW_MIN_WIDTH,
    CATALOGUE_WINDOW_WIDTH,
    CATALOGUE_WRAPLENGTH,
)
from App_TestData.testdata_components.logic.scroll_functions import setup_mousewheel_scroll
from App_TestData.testdata_components.ui.widget_factory import build_font
from components.styles.styles import APP_BG, BUTTON_BG, BUTTON_BG_ACTIVE, TEXT_DARK, TEXT_LIGHT


def show_catalogue_dialog(parent, catalogue_sections, catalogue_items):
    """Open the categorized catalogue dialog."""
    catalogue_window = ctk.CTkToplevel(parent)
    catalogue_window.title(CATALOGUE_DIALOG["title"])
    catalogue_window.geometry(f"{CATALOGUE_WINDOW_WIDTH}x{CATALOGUE_WINDOW_HEIGHT}")
    catalogue_window.minsize(CATALOGUE_WINDOW_MIN_WIDTH, CATALOGUE_WINDOW_MIN_HEIGHT)
    catalogue_window.configure(fg_color=APP_BG)
    catalogue_window.transient(parent)
    catalogue_window.grab_set()

    main_frame = ctk.CTkFrame(catalogue_window, fg_color=APP_BG, corner_radius=0)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=CATALOGUE_MAIN_PADDING, pady=CATALOGUE_MAIN_PADDING)

    columns_container = ctk.CTkFrame(main_frame, fg_color=APP_BG, corner_radius=0)
    columns_container.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

    sections_config = build_catalogue_sections(catalogue_sections, catalogue_items)

    for title_text, items_list in sections_config:
        column_frame = ctk.CTkFrame(columns_container, fg_color=APP_BG, corner_radius=0)
        column_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=CATALOGUE_COLUMN_PADDING)

        ctk.CTkLabel(
            column_frame,
            text=title_text,
            fg_color=APP_BG,
            text_color=TEXT_DARK,
            font=build_font(14, "bold"),
            wraplength=CATALOGUE_WRAPLENGTH,
            justify="left",
        ).pack(anchor=tk.NW, pady=(0, 10), ipady=5)

        scroll_container = ctk.CTkFrame(column_frame, fg_color=APP_BG, corner_radius=0)
        scroll_container.pack(fill=tk.BOTH, expand=True)

        horizontal_scrollbar = ctk.CTkScrollbar(scroll_container, orientation="horizontal")
        horizontal_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        vertical_scrollbar = ctk.CTkScrollbar(scroll_container, orientation="vertical")
        vertical_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        canvas = tk.Canvas(
            scroll_container,
            bg=APP_BG,
            bd=0,
            highlightthickness=0,
            xscrollcommand=horizontal_scrollbar.set,
            yscrollcommand=vertical_scrollbar.set,
        )
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        vertical_scrollbar.configure(command=canvas.yview)
        horizontal_scrollbar.configure(command=canvas.xview)

        list_frame = ctk.CTkFrame(canvas, fg_color=APP_BG, corner_radius=0)
        canvas.create_window((0, 0), window=list_frame, anchor=tk.NW)

        setup_mousewheel_scroll(canvas)
        _bind_widget_scroll(list_frame, canvas)
        list_frame.bind("<Configure>", lambda _event, target_canvas=canvas: target_canvas.configure(scrollregion=target_canvas.bbox("all")))

        for item_id, text_value in items_list:
            item_label = ctk.CTkLabel(
                list_frame,
                text=f"{item_id}. {text_value}",
                fg_color="transparent",
                text_color=TEXT_DARK,
                font=build_font(10),
                anchor="w",
                justify="left",
            )
            item_label.pack(anchor=tk.NW, fill=tk.X, pady=2, padx=2)
            _bind_widget_scroll(item_label, canvas)

    close_button = ctk.CTkButton(
        main_frame,
        text=CATALOGUE_DIALOG["close"],
        command=catalogue_window.destroy,
        fg_color=BUTTON_BG,
        hover_color=BUTTON_BG_ACTIVE,
        text_color=TEXT_LIGHT,
        corner_radius=0,
        font=build_font(12),
    )
    close_button.pack(side=tk.BOTTOM, fill=tk.X)


def build_catalogue_sections(catalogue_sections, catalogue_items):
    """Associate catalogue item labels with their generated numeric ids."""
    item_ids_by_name = {name: item_id for item_id, name in catalogue_items}
    sections = []
    for title, section_items in catalogue_sections:
        numbered_items = [
            (item_ids_by_name.get(item_name, index), item_name)
            for index, item_name in enumerate(section_items, start=1)
        ]
        sections.append((title, numbered_items))
    return sections


def _bind_widget_scroll(widget, target_canvas):
    """Mirror wheel events from inner widgets to the target canvas."""
    widget.bind("<MouseWheel>", lambda event: target_canvas.event_generate("<MouseWheel>", delta=event.delta))
    widget.bind("<Button-4>", lambda _event: target_canvas.event_generate("<Button-4>"))
    widget.bind("<Button-5>", lambda _event: target_canvas.event_generate("<Button-5>"))
