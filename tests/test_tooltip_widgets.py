import tkinter as tk
import unittest

import customtkinter as ctk

from App_TestData.config.settings import DELETE_ICON_PATH
from App_TestData.ui.widgets.factory import create_toolbar_icon_button


class TooltipWidgetTests(unittest.TestCase):
    def test_icon_button_exposes_tooltip_text(self):
        try:
            root = ctk.CTk()
            root.withdraw()
        except tk.TclError as error:
            self.skipTest(f"Tk display is not available: {error}")

        try:
            button = create_toolbar_icon_button(
                root,
                "Eliminar",
                lambda: None,
                DELETE_ICON_PATH,
                disabled_tooltip="No hay recuadro seleccionado",
            )
            self.assertTrue(hasattr(button, "tooltip"))
            self.assertEqual(button.tooltip.text, "Eliminar")
            self.assertEqual(button._disabled_tooltip_text, "No hay recuadro seleccionado")
        finally:
            root.destroy()


if __name__ == "__main__":
    unittest.main()
