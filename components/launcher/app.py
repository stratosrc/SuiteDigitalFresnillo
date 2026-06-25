import customtkinter as ctk

from components.launcher.config import APPLICATIONS_CONFIG, WINDOW_MIN_SIZE, WINDOW_SIZE, WINDOW_TITLE
from components.launcher.services.app_runner import ApplicationRunner
from components.launcher.ui.app_grid import ApplicationGrid
from components.launcher.ui.footer import LauncherFooter
from components.launcher.ui.header import LauncherHeader
from components.launcher.ui.image_loader import ImageLoader
from components.launcher.ui.styles import configure_launcher_styles
from components.shared.windowing import center_window, prepare_window_for_open, reveal_window_maximized
from components.styles.styles import APP_BG, apply_ctk_style


class SuiteLauncher(ctk.CTk):
    def __init__(self):
        super().__init__()
        prepare_window_for_open(self)
        apply_ctk_style(ctk)

        width, height = WINDOW_SIZE
        min_width, min_height = WINDOW_MIN_SIZE

        self.title(WINDOW_TITLE)
        self.geometry(f"{width}x{height}")
        self.minsize(min_width, min_height)
        self.configure(fg_color=APP_BG)

        self.image_loader = ImageLoader()
        self.app_runner = ApplicationRunner(self)

        center_window(self, width, height)
        configure_launcher_styles(self)
        self._build_layout()
        reveal_window_maximized(self)

    def _build_layout(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        header = LauncherHeader(self, image_loader=self.image_loader)
        header.grid(row=0, column=0, sticky="ew")

        body = ApplicationGrid(
            self,
            applications_config=APPLICATIONS_CONFIG,
            image_loader=self.image_loader,
            launch_callback=self.app_runner.launch,
        )
        body.grid(row=1, column=0, sticky="nsew", padx=18, pady=18)

        footer = LauncherFooter(self)
        footer.grid(row=2, column=0, sticky="ew")
