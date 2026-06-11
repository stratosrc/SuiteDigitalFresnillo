"""Root CustomTkinter window for the Directorio application."""

import customtkinter as ctk

from App_Directorio.ui.main_frame import MainFrame
from App_Directorio.ui.theme import (
    APP_BACKGROUND,
    WINDOW_HEIGHT,
    WINDOW_MIN_HEIGHT,
    WINDOW_MIN_WIDTH,
    WINDOW_WIDTH,
    apply_theme,
)
from components.shared.windowing import center_window


class DirectoryApplication(ctk.CTk):
    """Main application window for the Directorio module."""

    def __init__(self) -> None:
        super().__init__()
        apply_theme()
        self.title("Directorio")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self.configure(fg_color=APP_BACKGROUND)
        center_window(self, WINDOW_WIDTH, WINDOW_HEIGHT)
        self.main_frame = MainFrame(self)
