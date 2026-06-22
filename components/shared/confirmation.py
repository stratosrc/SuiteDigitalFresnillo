"""Consistent three-way confirmation dialogs."""

import tkinter as tk

import customtkinter as ctk


def ask_save_discard_cancel(parent, action: str) -> str:
    """Return ``save``, ``discard`` or ``cancel``."""
    result = tk.StringVar(master=parent, value="cancel")
    dialog = ctk.CTkToplevel(parent)
    dialog.title("Cambios sin guardar")
    dialog.resizable(False, False)
    dialog.transient(parent)
    dialog.grab_set()

    ctk.CTkLabel(
        dialog,
        text=f"Hay cambios sin guardar.\n¿Qué deseas hacer antes de {action}?",
        justify="left",
    ).pack(fill="x", padx=22, pady=(20, 16))

    buttons = ctk.CTkFrame(dialog, fg_color="transparent")
    buttons.pack(fill="x", padx=18, pady=(0, 18))

    def choose(value: str) -> None:
        result.set(value)
        dialog.destroy()

    created_buttons = []
    for text, value in (
        ("Guardar", "save"),
        ("Descartar", "discard"),
        ("Cancelar", "cancel"),
    ):
        button = ctk.CTkButton(
            buttons,
            text=text,
            command=lambda selected=value: choose(selected),
            width=92,
        )
        button.pack(side="left", padx=4)
        created_buttons.append(button)

    dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
    dialog.bind("<Escape>", lambda _event: choose("cancel"))
    dialog.update_idletasks()
    x = parent.winfo_rootx() + max(0, (parent.winfo_width() - dialog.winfo_reqwidth()) // 2)
    y = parent.winfo_rooty() + max(0, (parent.winfo_height() - dialog.winfo_reqheight()) // 2)
    dialog.geometry(f"+{x}+{y}")
    created_buttons[0].focus_set()
    dialog.wait_window()
    return result.get()


__all__ = ["ask_save_discard_cancel"]
