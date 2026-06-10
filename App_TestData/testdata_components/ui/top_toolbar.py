"""Top toolbar components for the main window."""

import tkinter as tk

import customtkinter as ctk

from App_TestData.testdata_components.config.ui_strings import (
    ACTION_LABELS,
    FILE_MENU_LABELS,
    TOPBAR_LABELS,
)
from App_TestData.testdata_components.ui.widget_factory import create_toolbar_button
from components.styles.styles import BUTTON_BG_ACTIVE, BUTTON_BG_PRESSED, TEXT_LIGHT


def build_menu_toolbar(parent, callbacks: dict):
    """Build the file and utility toolbar."""
    toolbar = ctk.CTkFrame(parent, fg_color=BUTTON_BG_PRESSED, corner_radius=0, height=22)
    toolbar.pack(side=tk.TOP, fill=tk.X)
    toolbar.pack_propagate(False)

    file_menu = tk.Menu(
        parent,
        tearoff=False,
        bg=BUTTON_BG_PRESSED,
        fg=TEXT_LIGHT,
        activebackground=BUTTON_BG_ACTIVE,
        activeforeground=TEXT_LIGHT,
    )
    file_menu.add_command(label=FILE_MENU_LABELS["load_pdf"], command=callbacks["on_load_pdf"])
    file_menu.add_command(label=FILE_MENU_LABELS["save_pdf"], command=callbacks["on_open_export_dialog"])

    file_button = create_toolbar_button(
        toolbar,
        FILE_MENU_LABELS["button"],
        command=lambda: _show_file_menu(file_button, file_menu),
        width=92,
    )
    file_button.pack(side=tk.LEFT, padx=(0, 4), pady=0)

    catalogue_button = create_toolbar_button(
        toolbar,
        TOPBAR_LABELS["catalogue"],
        callbacks["on_show_catalogue"],
        width=92,
    )
    catalogue_button.pack(side=tk.LEFT, padx=(0, 4), pady=0)

    help_button = create_toolbar_button(
        toolbar,
        TOPBAR_LABELS["help"],
        callbacks["on_show_help"],
        width=86,
    )
    help_button.pack(side=tk.LEFT, padx=(0, 4), pady=0)

    exit_button = create_toolbar_button(
        toolbar,
        TOPBAR_LABELS["exit"],
        callbacks["on_exit"],
        width=86,
        danger=True,
    )
    exit_button.pack(side=tk.RIGHT, padx=(4, 0), pady=0)

    return {
        "file_menu": file_menu,
        "file_button": file_button,
        "catalogue_button": catalogue_button,
        "help_button": help_button,
        "exit_button": exit_button,
    }


def build_action_toolbar(parent, callbacks: dict):
    """Build the toolbar with rectangle editing actions."""
    toolbar_frame = ctk.CTkFrame(parent, fg_color=parent.cget("fg_color"), corner_radius=0)
    toolbar_frame.pack(side=tk.TOP, fill=tk.X, padx=12, pady=8)

    undo_button = create_toolbar_button(
        toolbar_frame,
        ACTION_LABELS["undo"],
        lambda: callbacks["on_rectangle_action"]("undo"),
        width=132,
    )
    undo_button.pack(side=tk.LEFT, padx=(0, 8))

    redo_button = create_toolbar_button(
        toolbar_frame,
        ACTION_LABELS["redo"],
        lambda: callbacks["on_rectangle_action"]("redo"),
        width=132,
    )
    redo_button.pack(side=tk.LEFT, padx=(0, 8))

    delete_button = create_toolbar_button(
        toolbar_frame,
        ACTION_LABELS["delete"],
        lambda: callbacks["on_rectangle_action"]("delete"),
        width=132,
        danger=True,
    )
    delete_button.configure(state=tk.DISABLED)
    delete_button.pack(side=tk.LEFT, padx=(6, 0))

    return {
        "delete_rect_btn": delete_button,
    }


def _show_file_menu(file_button, file_menu):
    """Show the file popup menu below its trigger button."""
    x_position = file_button.winfo_rootx()
    y_position = file_button.winfo_rooty() + file_button.winfo_height()
    file_menu.tk_popup(x_position, y_position)
    file_menu.grab_release()
