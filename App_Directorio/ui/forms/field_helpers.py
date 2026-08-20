"""Validation and normalization helpers for directory form fields."""

import tkinter as tk

from App_Directorio.models import PersonReportRow


def empty_person() -> PersonReportRow:
    return PersonReportRow("", "", "", "", "")


def person_has_data(person: PersonReportRow) -> bool:
    return any((person.rank, person.name, person.position, person.email, person.start_date))


def bind_uppercase(variable: tk.StringVar) -> None:
    """Keep a Tk string variable normalized to uppercase while editing."""

    def normalize(*_args: object) -> None:
        value = variable.get()
        uppercase = value.upper()
        if value != uppercase:
            try:
                focused = variable._root.focus_get()
            except tk.TclError:
                focused = None
            cursor = None
            if isinstance(focused, tk.Entry):
                try:
                    cursor = focused.index(tk.INSERT)
                except tk.TclError:
                    cursor = None
            variable.set(uppercase)
            if focused is not None and cursor is not None:
                variable._root.after_idle(lambda: focused.icursor(min(cursor, len(variable.get()))))

    variable.trace_add("write", normalize)


def is_position_input(value: str) -> bool:
    """Allow an empty value while editing, or a positive integer."""
    return not value or (value.isdigit() and int(value) > 0)

