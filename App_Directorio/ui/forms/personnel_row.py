"""Reusable personnel row used by the directory editor."""

from collections.abc import Callable
import tkinter as tk

import customtkinter as ctk

from App_Directorio.models import PersonReportRow
from App_Directorio.ui.forms.field_helpers import is_position_input, person_has_data
from App_Directorio.ui.theme import (
    BORDER_COLOR,
    PRIMARY_BUTTON,
    PRIMARY_BUTTON_ACTIVE,
    SURFACE_BACKGROUND,
    TEXT_DARK,
    TEXT_LIGHT,
    TEXT_MUTED,
    make_font,
)
from App_Directorio.utils import is_date_input_prefix, is_valid_date


EMAIL_DOMAIN = "@fresnillo.gob.mx"
PERSONNEL_COLUMN_WEIGHTS = (0, 0, 14, 18, 16, 17, 10)
PERSONNEL_COLUMN_PADX = ((0, 8), (0, 8), (0, 8), (0, 8), (0, 0))


class PersonnelRow:
    """One reusable set of entry widgets bound to a person in the area model."""

    def __init__(
        self,
        master: ctk.CTkFrame,
        grid_row: int,
        on_change: Callable[["PersonnelRow", PersonReportRow], None],
        on_reposition: Callable[["PersonnelRow", int], None],
        on_actions_request: Callable[[ctk.CTkButton], None],
        on_mousewheel: Callable[[tk.Event], str | None],
    ) -> None:
        self.master = master
        self.grid_row = grid_row
        self._on_change = on_change
        self._on_reposition = on_reposition
        self._on_actions_request = on_actions_request
        self._on_mousewheel = on_mousewheel
        self.data_index: int | None = None
        self.entries: list[ctk.CTkEntry] = []
        self.position_entry: ctk.CTkEntry | None = None
        self.date_entry: ctk.CTkEntry | None = None
        self.widgets: list[tk.Widget] = []
        self._build_entries()

    def _bind_common_events(self, widget: tk.Widget) -> None:
        widget.bind("<MouseWheel>", self._on_mousewheel, add=True)

    def _build_entries(self) -> None:
        actions_button = ctk.CTkButton(
            self.master,
            text="▼",
            command=lambda: self._on_actions_request(actions_button),
            width=30,
            height=30,
            corner_radius=0,
            fg_color=PRIMARY_BUTTON,
            hover_color=PRIMARY_BUTTON_ACTIVE,
            text_color=TEXT_LIGHT,
            font=make_font(10, "bold"),
        )
        actions_button.grid(
            row=self.grid_row,
            column=0,
            sticky="w",
            padx=(0, 6),
            pady=(0, 8),
        )
        self.widgets.append(actions_button)
        self._bind_common_events(actions_button)

        self.position_entry = ctk.CTkEntry(
            self.master,
            width=42,
            height=34,
            corner_radius=0,
            fg_color=SURFACE_BACKGROUND,
            border_color=BORDER_COLOR,
            text_color=TEXT_DARK,
            justify="center",
            font=make_font(12, "bold"),
        )
        validation = (self.master.register(is_position_input), "%P")
        self.position_entry.configure(validate="key", validatecommand=validation)
        self.position_entry.bind("<FocusOut>", self._handle_position_request)
        self.position_entry.bind("<Return>", self._handle_position_request)
        self.position_entry.grid(
            row=self.grid_row,
            column=1,
            sticky="w",
            padx=(0, 8),
            pady=(0, 8),
        )
        self.widgets.append(self.position_entry)
        self._bind_common_events(self.position_entry)

        placeholders = (
            "Rango / Clave / Nivel",
            "Nombre",
            "Cargo",
            "Correo electrónico",
            "dd/mm/aaaa",
        )
        for data_column, (placeholder, padx) in enumerate(zip(placeholders, PERSONNEL_COLUMN_PADX)):
            column = data_column + 2
            entry = ctk.CTkEntry(
                self.master,
                height=34,
                corner_radius=0,
                fg_color=SURFACE_BACKGROUND,
                border_color=BORDER_COLOR,
                text_color=TEXT_DARK,
                placeholder_text=placeholder,
                placeholder_text_color=TEXT_MUTED,
                font=make_font(12),
            )
            if data_column == 4:
                validation = (self.master.register(is_date_input_prefix), "%P")
                entry.configure(validate="key", validatecommand=validation)
                entry.bind("<FocusOut>", self._handle_date_focus_out)
                self.date_entry = entry
            if data_column == 3:
                entry.bind("<FocusOut>", self._handle_email_focus_out)
                entry.bind("<Return>", self._handle_email_focus_out)
            entry.bind("<KeyRelease>", self._handle_data_change, add=True)
            entry.grid(row=self.grid_row, column=column, sticky="ew", padx=padx, pady=(0, 8))
            self.entries.append(entry)
            self.widgets.append(entry)
            self._bind_common_events(entry)

    def _handle_data_change(self, _event: tk.Event | None = None) -> None:
        if self.data_index is not None:
            self._on_change(self, self.get_data())

    def _handle_date_focus_out(self, _event: tk.Event) -> None:
        self.validate_date()

    def _handle_email_focus_out(self, _event: tk.Event) -> None:
        email_entry = self.entries[3]
        value = email_entry.get().strip()
        if value and "@" not in value:
            email_entry.delete(0, tk.END)
            email_entry.insert(0, f"{value}{EMAIL_DOMAIN}")
            self._handle_data_change()

    def _handle_position_request(self, _event: tk.Event) -> None:
        if self.position_entry is None or self.data_index is None:
            return
        try:
            requested_position = int(self.position_entry.get())
        except ValueError:
            requested_position = self.data_index + 1
        self._on_reposition(self, requested_position)

    def bind_data(self, data_index: int, person: PersonReportRow) -> None:
        self.data_index = data_index
        values = (person.rank, person.name, person.position, person.email, person.start_date)
        for entry, value in zip(self.entries, values):
            entry.delete(0, tk.END)
            entry.insert(0, value)
        self.set_position(data_index + 1)
        self.validate_date()

    def set_position(self, position: int) -> None:
        if self.position_entry is None:
            return
        self.position_entry.delete(0, tk.END)
        self.position_entry.insert(0, str(position))

    def show(self) -> None:
        for widget in self.widgets:
            widget.grid()

    def hide(self) -> None:
        for widget in self.widgets:
            widget.grid_remove()
        self.data_index = None

    def destroy(self) -> None:
        for widget in self.widgets:
            widget.destroy()
        self.widgets.clear()
        self.entries.clear()
        self.position_entry = None
        self.date_entry = None
        self.data_index = None

    def get_data(self) -> PersonReportRow:
        values = [entry.get().strip() for entry in self.entries]
        return PersonReportRow(
            rank=values[0] if len(values) > 0 else "",
            name=values[1] if len(values) > 1 else "",
            position=values[2] if len(values) > 2 else "",
            email=values[3] if len(values) > 3 else "",
            start_date=values[4] if len(values) > 4 else "",
        )

    def has_data(self) -> bool:
        return person_has_data(self.get_data())

    def validate_date(self) -> bool:
        if self.date_entry is None:
            return True
        date_value = self.date_entry.get().strip()
        is_valid = not self.has_data() or is_valid_date(date_value)
        self.date_entry.configure(border_color=BORDER_COLOR if is_valid else "#C62828")
        return is_valid
