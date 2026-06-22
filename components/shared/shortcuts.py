"""Common keyboard shortcuts for suite applications."""

from collections.abc import Callable
import tkinter as tk


def bind_common_shortcuts(
    window: tk.Misc,
    *,
    new: Callable[[], object] | None = None,
    open_: Callable[[], object] | None = None,
    save: Callable[[], object] | None = None,
    save_as: Callable[[], object] | None = None,
    undo: Callable[[], object] | None = None,
    redo: Callable[[], object] | None = None,
) -> None:
    def focused_edit(action: str) -> None:
        focused = window.focus_get()
        if focused is not None:
            focused.event_generate(action)

    bindings = {
        "<Control-n>": new,
        "<Control-o>": open_,
        "<Control-s>": save,
        "<Control-Shift-S>": save_as,
        "<Control-z>": undo or (lambda: focused_edit("<<Undo>>")),
        "<Control-y>": redo or (lambda: focused_edit("<<Redo>>")),
        "<Control-Shift-Z>": redo or (lambda: focused_edit("<<Redo>>")),
    }
    for sequence, callback in bindings.items():
        if callback is None:
            continue

        def invoke(_event, command=callback):
            command()
            return "break"

        window.bind(sequence, invoke, add=True)


__all__ = ["bind_common_shortcuts"]
