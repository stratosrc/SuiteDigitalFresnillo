import tkinter as tk
import unittest

from App_Directorio.ui.forms.directory_form import bind_uppercase


class UppercaseFieldTests(unittest.TestCase):
    def test_bound_string_variable_converts_text_to_uppercase(self):
        try:
            interpreter = tk.Tcl()
        except tk.TclError as error:
            self.skipTest(f"Tcl is not available: {error}")

        variable = tk.StringVar(master=interpreter)
        bind_uppercase(variable)

        variable.set("Área administrativa 2026")

        self.assertEqual(variable.get(), "ÁREA ADMINISTRATIVA 2026")


if __name__ == "__main__":
    unittest.main()
