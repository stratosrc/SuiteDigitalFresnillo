"""Focus styling used by the directory module."""

import customtkinter as ctk


FOCUS_COLOR = "#F59E0B"


def enable_visible_focus(root) -> None:
    """Enable keyboard focus without highlighting text entries."""
    def apply(widget) -> None:
        if isinstance(widget, (ctk.CTkButton, ctk.CTkCheckBox)):
            try:
                widget.configure(takefocus=True)
            except Exception:
                pass

            original_width = getattr(widget, "_border_width", 0)
            original_color = getattr(widget, "_border_color", None)

            def focus_in(_event, target=widget) -> None:
                try:
                    target.configure(
                        border_width=max(2, original_width),
                        border_color=FOCUS_COLOR,
                    )
                except Exception:
                    pass

            def focus_out(_event, target=widget) -> None:
                try:
                    target.configure(border_width=original_width)
                    if original_color is not None:
                        target.configure(border_color=original_color)
                except Exception:
                    pass

            widget.bind("<FocusIn>", focus_in, add=True)
            widget.bind("<FocusOut>", focus_out, add=True)

        for child in widget.winfo_children():
            apply(child)

    apply(root)


def enable_visible_focus_for(widget) -> None:
    """Apply the directory focus style to a newly created subtree."""
    enable_visible_focus(widget)


__all__ = ["enable_visible_focus", "enable_visible_focus_for"]
