import unittest
from unittest.mock import patch

from App_TestData.ui.interactions import canvas_redactions


class _FakeCanvas:
    def __init__(self, *, fail_on=None):
        self.fail_on = set(fail_on or [])
        self.calls = []

    def configure(self, *, cursor):
        self.calls.append(cursor)
        if cursor in self.fail_on:
            raise RuntimeError("unsupported cursor")


class _FakeApp:
    def __init__(self, canvas):
        self.pdf_canvas = canvas


class TestDataCursorTests(unittest.TestCase):
    def test_resize_corner_uses_crosshair_on_macos(self):
        with patch.object(canvas_redactions, "IS_MACOS", True):
            self.assertEqual(canvas_redactions._cursor_for_corner("nw"), "crosshair")
            self.assertEqual(canvas_redactions._cursor_for_corner("se"), "crosshair")

    def test_cursor_falls_back_when_primary_cursor_is_rejected(self):
        canvas = _FakeCanvas(fail_on={"size_nw_se"})
        app = _FakeApp(canvas)

        canvas_redactions._set_canvas_cursor(app, "size_nw_se")

        self.assertEqual(canvas.calls, ["size_nw_se", "crosshair"])


if __name__ == "__main__":
    unittest.main()
