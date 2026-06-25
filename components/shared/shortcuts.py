"""Common keyboard shortcuts for suite applications."""

from __future__ import annotations


from typing import Callable
import tkinter as tk


def _is_text_input(widget) -> bool:
    if widget is None:
        return False
    return widget.winfo_class() in {"Entry", "Text", "TEntry", "TCombobox"}


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
    }
    for sequence, callback in bindings.items():
        if callback is None:
            continue

        def invoke(_event, command=callback):
            command()
            return "break"

        window.bind(sequence, invoke, add=True)

    def invoke_edit(_event, project_command, native_action):
        focused = window.focus_get()
        if _is_text_input(focused):
            focused_edit(native_action)
        elif project_command is not None:
            project_command()
        return "break"

    window.bind(
        "<Control-z>",
        lambda event: invoke_edit(event, undo, "<<Undo>>"),
        add=True,
    )
    window.bind(
        "<Control-y>",
        lambda event: invoke_edit(event, redo, "<<Redo>>"),
        add=True,
    )
    window.bind(
        "<Control-Shift-Z>",
        lambda event: invoke_edit(event, redo, "<<Redo>>"),
        add=True,
    )


__all__ = ["bind_common_shortcuts"]
