"""Small platform helpers for Tk bindings."""

from __future__ import annotations

from collections.abc import Callable
import sys
import tkinter as tk


IS_MACOS = sys.platform == "darwin"
PRIMARY_MODIFIER = "Command" if IS_MACOS else "Control"
PRIMARY_MODIFIER_LABEL = "Cmd" if IS_MACOS else "Ctrl"
SECONDARY_CLICK_SEQUENCES = (
    ("<Button-2>", "<Button-3>", "<Control-Button-1>")
    if IS_MACOS
    else ("<Button-3>",)
)


def primary_shortcut_sequences(key: str, *, shift: bool = False) -> tuple[str, ...]:
    """Return native shortcut bindings plus a Control fallback on macOS."""
    normalized_key = key.strip()
    modifiers = f"{PRIMARY_MODIFIER}-{'Shift-' if shift else ''}"
    sequences = [f"<{modifiers}{normalized_key}>"]

    if IS_MACOS:
        control_modifiers = f"Control-{'Shift-' if shift else ''}"
        sequences.append(f"<{control_modifiers}{normalized_key}>")

    return tuple(sequences)


def bind_sequences(
    widget: tk.Misc,
    sequences: tuple[str, ...],
    callback: Callable[[tk.Event], object],
    *,
    add: bool | str = True,
) -> None:
    for sequence in sequences:
        widget.bind(sequence, callback, add=add)


def bind_primary_shortcut(
    widget: tk.Misc,
    key: str,
    callback: Callable[[tk.Event], object],
    *,
    shift: bool = False,
    add: bool | str = True,
) -> None:
    bind_sequences(widget, primary_shortcut_sequences(key, shift=shift), callback, add=add)


def bind_secondary_click(
    widget: tk.Misc,
    callback: Callable[[tk.Event], object],
    *,
    add: bool | str = True,
) -> None:
    bind_sequences(widget, SECONDARY_CLICK_SEQUENCES, callback, add=add)


__all__ = [
    "IS_MACOS",
    "PRIMARY_MODIFIER_LABEL",
    "bind_primary_shortcut",
    "bind_secondary_click",
    "bind_sequences",
    "primary_shortcut_sequences",
]
