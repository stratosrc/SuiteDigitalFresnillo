import unittest

from components.shared.shortcuts import bind_common_shortcuts


class FakeWindow:
    def __init__(self):
        self.bindings = {}

    def bind(self, sequence, callback, add=False):
        self.bindings[sequence] = callback


class CommonShortcutTests(unittest.TestCase):
    def test_common_shortcuts_are_registered(self):
        window = FakeWindow()
        calls = []
        bind_common_shortcuts(
            window,
            new=lambda: calls.append("new"),
            open_=lambda: calls.append("open"),
            save=lambda: calls.append("save"),
            save_as=lambda: calls.append("save_as"),
            undo=lambda: calls.append("undo"),
            redo=lambda: calls.append("redo"),
        )

        for sequence in (
            "<Control-n>",
            "<Control-o>",
            "<Control-s>",
            "<Control-Shift-S>",
            "<Control-z>",
            "<Control-y>",
        ):
            self.assertIn(sequence, window.bindings)

        window.bindings["<Control-s>"](None)
        self.assertEqual(calls, ["save"])


if __name__ == "__main__":
    unittest.main()
