"""CustomTkinter entry helpers shared by the desktop applications."""

from __future__ import annotations

import customtkinter as ctk


class VariablePlaceholderEntry(ctk.CTkEntry):
    """CTkEntry whose placeholder remains visible with ``textvariable``.

    CustomTkinter 5.2.2 does not activate its built-in placeholder when a
    ``StringVar`` is attached. A visual overlay avoids changing the real value.
    """

    def __init__(self, *args, **kwargs) -> None:
        self._placeholder_label: ctk.CTkLabel | None = None
        super().__init__(*args, **kwargs)
        if self._placeholder_text is not None:
            self._placeholder_label = ctk.CTkLabel(
                self,
                text=self._placeholder_text,
                fg_color="transparent",
                text_color=self._placeholder_text_color,
                font=self._font,
                anchor="w",
            )
            self._placeholder_label.bind("<Button-1>", self._focus_from_placeholder)
            self._activate_placeholder()

    def _focus_from_placeholder(self, _event=None) -> None:
        self._entry.focus_set()
        self._deactivate_placeholder()

    def _textvariable_callback(self, _var_name, _index, _mode) -> None:
        if self._textvariable is None or self._textvariable.get() == "":
            self._activate_placeholder()
        else:
            self._deactivate_placeholder()

    def _activate_placeholder(self) -> None:
        variable_is_empty = self._textvariable is None or self._textvariable.get() == ""
        if (
            self._entry.get() != ""
            or self._placeholder_text is None
            or not variable_is_empty
            or self._placeholder_label is None
        ):
            return

        self._placeholder_text_active = True
        self._placeholder_label.place(
            x=self._apply_widget_scaling(self._border_width + 7),
            rely=0.5,
            anchor="w",
        )
        self._placeholder_label.lift()

    def _deactivate_placeholder(self) -> None:
        if not self._placeholder_text_active:
            return

        self._placeholder_text_active = False
        if self._placeholder_label is not None:
            self._placeholder_label.place_forget()


__all__ = ["VariablePlaceholderEntry"]
