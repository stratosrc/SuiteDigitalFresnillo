import unittest
from unittest.mock import Mock, patch

from App_Organigrama.ui.canvas_interaction_controller import (
    CanvasInteractionController,
)
from components.shared import platform


class _FakeWidget:
    def __init__(self):
        self.bindings = {}

    def bind(self, sequence, callback, add=False):
        self.bindings[sequence] = (callback, add)

    def focus_set(self):
        return None


class MacosBindingTests(unittest.TestCase):
    def test_shifted_primary_shortcut_uses_native_tk_key_spelling(self):
        with (
            patch.object(platform, "IS_MACOS", True),
            patch.object(platform, "PRIMARY_MODIFIER", "Command"),
        ):
            self.assertEqual(
                platform.primary_shortcut_sequences("s", shift=True),
                ("<Command-Shift-S>", "<Control-Shift-S>"),
            )

    def test_organigram_registers_macos_pan_and_zoom_bindings(self):
        controller = Mock()
        controller.canvas = _FakeWidget()

        with patch(
            "App_Organigrama.ui.canvas_interaction_controller.IS_MACOS",
            True,
        ):
            CanvasInteractionController._bind_events(controller)

        for sequence in (
            "<ButtonPress-2>",
            "<Control-ButtonPress-1>",
            "<B2-Motion>",
            "<Control-B1-Motion>",
            "<ButtonRelease-2>",
            "<Control-ButtonRelease-1>",
            "<Command-MouseWheel>",
        ):
            self.assertIn(sequence, controller.canvas.bindings)


if __name__ == "__main__":
    unittest.main()
