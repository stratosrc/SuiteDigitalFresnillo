"""Common keyboard shortcuts for suite applications."""

from collections.abc import Callable
import tkinter as tk

from components.shared.platform import bind_primary_shortcut


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

    bindings = (
        ("n", False, new),
        ("o", False, open_),
        ("s", False, save),
        ("s", True, save_as),
    )
    for key, shift, callback in bindings:
        if callback is None:
            continue

        def invoke(_event, command=callback):
            command()
            return "break"

        bind_primary_shortcut(window, key, invoke, shift=shift, add=True)

    def invoke_edit(_event, project_command, native_action):
        focused = window.focus_get()
        if _is_text_input(focused):
            focused_edit(native_action)
        elif project_command is not None:
            project_command()
        return "break"

    bind_primary_shortcut(window, "z", lambda event: invoke_edit(event, undo, "<<Undo>>"), add=True)
    bind_primary_shortcut(window, "y", lambda event: invoke_edit(event, redo, "<<Redo>>"), add=True)
    bind_primary_shortcut(window, "z", lambda event: invoke_edit(event, redo, "<<Redo>>"), shift=True, add=True)


__all__ = ["bind_common_shortcuts"]
