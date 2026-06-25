import customtkinter as ctk

from App_Organigrama.ui.main_frame import MainFrame
from App_Organigrama.ui.theme import APP_BACKGROUND, WINDOW_HEIGHT, WINDOW_MIN_HEIGHT, WINDOW_MIN_WIDTH, WINDOW_WIDTH, apply_theme
from components.shared.windowing import center_window, prepare_window_for_open, reveal_window_maximized


class OrgChartApplication(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        prepare_window_for_open(self)
        apply_theme()
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self.configure(fg_color=APP_BACKGROUND)
        center_window(self, WINDOW_WIDTH, WINDOW_HEIGHT)
        self.main_frame = MainFrame(self)
        self.protocol("WM_DELETE_WINDOW", self.main_frame._confirm_exit)
        reveal_window_maximized(self)
