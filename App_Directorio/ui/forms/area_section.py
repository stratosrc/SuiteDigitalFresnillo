"""Expandable and virtualized area section for the directory editor."""

from collections.abc import Callable
import tkinter as tk

import customtkinter as ctk

from App_Directorio.models import AreaReportData, PersonReportRow
from App_Directorio.ui.accessibility import enable_visible_focus_for
from App_Directorio.ui.forms.field_helpers import bind_uppercase, empty_person, is_position_input, person_has_data
from App_Directorio.ui.forms.personnel_row import PERSONNEL_COLUMN_WEIGHTS, PersonnelRow
from App_Directorio.ui.forms.virtualization import start_from_fraction, virtual_window
from App_Directorio.ui.theme import (
    AREA_SECTION_BACKGROUND,
    BORDER_COLOR,
    PRIMARY_BUTTON,
    PRIMARY_BUTTON_ACTIVE,
    SURFACE_BACKGROUND,
    TEXT_DARK,
    TEXT_LIGHT,
    TEXT_MUTED,
    make_font,
)
from App_Directorio.ui.widgets import HoverIconButton, IconPair
from App_Directorio.utils import is_valid_date
from components.shared.entries import VariablePlaceholderEntry


VISIBLE_PERSON_ROWS = 12


class AreaSection(ctk.CTkFrame):
    """Area header backed by model data; personnel widgets exist only while expanded."""

    def __init__(
        self,
        master: ctk.CTkFrame,
        add_icons: IconPair,
        on_change: Callable[[], None],
        on_reposition: Callable[[int], None],
        on_person_actions_request: Callable[["AreaSection", PersonnelRow, ctk.CTkButton], None],
        on_area_actions_request: Callable[["AreaSection", ctk.CTkButton], None],
        on_expand_request: Callable[["AreaSection"], None],
        removable: bool = True,
    ) -> None:
        super().__init__(
            master,
            fg_color=AREA_SECTION_BACKGROUND,
            corner_radius=0,
            border_width=1,
            border_color=BORDER_COLOR,
        )
        self.add_icons = add_icons
        self._on_change = on_change
        self._on_reposition = on_reposition
        self._on_person_actions_request = on_person_actions_request
        self._on_area_actions_request = on_area_actions_request
        self._on_expand_request = on_expand_request
        self.removable = removable
        self.personnel: list[PersonReportRow] = [empty_person()]
        self.rows: list[PersonnelRow] = []
        self.area_name_var = tk.StringVar()
        bind_uppercase(self.area_name_var)
        self.area_name_var.trace_add("write", lambda *_args: self._on_change())
        self.position_entry: ctk.CTkEntry | None = None
        self.area_name_entry: ctk.CTkEntry | None = None
        self.count_label: ctk.CTkLabel | None = None
        self.toggle_button: ctk.CTkButton | None = None
        self.detail_container: ctk.CTkFrame | None = None
        self.detail_frame: ctk.CTkFrame | None = None
        self.scrollbar: ctk.CTkScrollbar | None = None
        self.range_label: ctk.CTkLabel | None = None
        self.add_person_button: HoverIconButton | None = None
        self.expanded = False
        self._window_start = 0
        self._build_header()

    def _build_header(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=14)
        header.grid_columnconfigure(1, weight=1)

        self.position_entry = ctk.CTkEntry(
            header,
            width=42,
            height=34,
            corner_radius=0,
            fg_color=SURFACE_BACKGROUND,
            border_color=BORDER_COLOR,
            text_color=TEXT_DARK,
            justify="center",
            font=make_font(12, "bold"),
        )
        validation = (self.register(is_position_input), "%P")
        self.position_entry.configure(validate="key", validatecommand=validation)
        self.position_entry.bind("<FocusOut>", self._handle_position_request)
        self.position_entry.bind("<Return>", self._handle_position_request)
        self.position_entry.grid(row=0, column=0, padx=(0, 8), sticky="w")

        self.area_name_entry = VariablePlaceholderEntry(
            header,
            textvariable=self.area_name_var,
            height=34,
            corner_radius=0,
            fg_color=SURFACE_BACKGROUND,
            border_color=BORDER_COLOR,
            text_color=TEXT_DARK,
            placeholder_text="Agregar Área, ej. Jefatura de Gobierno Digital",
            placeholder_text_color=TEXT_MUTED,
            font=make_font(12),
        )
        self.area_name_entry.grid(row=0, column=1, sticky="ew")

        self.count_label = ctk.CTkLabel(
            header,
            text="",
            text_color=TEXT_MUTED,
            font=make_font(11),
            width=90,
            anchor="e",
        )
        self.count_label.grid(row=0, column=2, padx=(10, 8), sticky="e")

        self.toggle_button = ctk.CTkButton(
            header,
            text="Expandir",
            command=lambda: self._on_expand_request(self),
            width=84,
            height=32,
            corner_radius=0,
            fg_color=PRIMARY_BUTTON,
            hover_color=PRIMARY_BUTTON_ACTIVE,
            text_color=TEXT_LIGHT,
            font=make_font(11, "bold"),
        )
        self.toggle_button.grid(row=0, column=3, sticky="e")

        if self.removable:
            actions_button = ctk.CTkButton(
                header,
                text="...",
                command=lambda: self._on_area_actions_request(self, actions_button),
                width=36,
                height=32,
                corner_radius=0,
                fg_color=PRIMARY_BUTTON,
                hover_color=PRIMARY_BUTTON_ACTIVE,
                text_color=TEXT_LIGHT,
                font=make_font(10, "bold"),
            )
            actions_button.grid(row=0, column=4, padx=(10, 0), sticky="e")

        self._refresh_count()

    def _build_detail(self) -> None:
        self.detail_container = ctk.CTkFrame(self, fg_color="transparent")
        self.detail_container.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 14))
        self.detail_container.grid_columnconfigure(0, weight=1)
        self.detail_container.grid_rowconfigure(0, weight=1)

        self.detail_frame = ctk.CTkFrame(self.detail_container, fg_color="transparent")
        self.detail_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        for column, weight in enumerate(PERSONNEL_COLUMN_WEIGHTS):
            self.detail_frame.grid_columnconfigure(column, weight=weight, uniform="personnel")
        self._build_headers(self.detail_frame)

        self.scrollbar = ctk.CTkScrollbar(
            self.detail_container,
            orientation="vertical",
            command=self._on_virtual_scroll,
            button_color=PRIMARY_BUTTON,
            button_hover_color=PRIMARY_BUTTON_ACTIVE,
            width=16,
        )
        self.scrollbar.grid(row=0, column=1, sticky="ns")

        for slot in range(VISIBLE_PERSON_ROWS):
            row = PersonnelRow(
                self.detail_frame,
                grid_row=slot + 1,
                on_change=self._update_person,
                on_reposition=self._move_person_from_row,
                on_actions_request=lambda _button: None,
                on_mousewheel=self._on_mousewheel,
            )
            row._on_actions_request = (
                lambda button, current=row: self._on_person_actions_request(self, current, button)
            )
            self.rows.append(row)

        self.range_label = ctk.CTkLabel(
            self.detail_frame,
            text="",
            text_color=TEXT_MUTED,
            font=make_font(11),
            anchor="w",
        )
        self.range_label.grid(
            row=VISIBLE_PERSON_ROWS + 1,
            column=0,
            columnspan=6,
            sticky="w",
            pady=(2, 0),
        )
        self.range_label.bind("<MouseWheel>", self._on_mousewheel, add=True)

        self.add_person_button = HoverIconButton(
            self.detail_frame,
            icons=self.add_icons,
            command=self.add_person_row,
            width=32,
            height=32,
            tooltip_text="Agregar persona",
        )
        self.add_person_button.grid(
            row=VISIBLE_PERSON_ROWS + 1,
            column=6,
            sticky="e",
            pady=(2, 0),
        )
        self._render_window()
        enable_visible_focus_for(self.detail_container)

    def _build_headers(self, parent: ctk.CTkFrame) -> None:
        header_specs = (
            ("", 0, 30, (0, 6)),
            ("#", 1, 42, (0, 8)),
            ("Rango / Clave / Nivel", 2, 0, (0, 8)),
            ("Nombre", 3, 0, (0, 8)),
            ("Cargo", 4, 0, (0, 8)),
            ("Correo electrónico", 5, 0, (0, 8)),
            ("Fecha de Alta", 6, 0, (0, 0)),
        )
        for text, column, width, padx in header_specs:
            label = ctk.CTkLabel(
                parent,
                text=text,
                text_color=TEXT_DARK,
                font=make_font(12, "bold"),
                width=width,
                anchor="center" if column == 1 else "w",
            )
            label.grid(row=0, column=column, sticky="w", padx=padx)
            label.bind("<MouseWheel>", self._on_mousewheel, add=True)

    def _handle_position_request(self, _event: tk.Event) -> None:
        if self.position_entry is None:
            return
        try:
            requested_position = int(self.position_entry.get())
        except ValueError:
            requested_position = 1
        self._on_reposition(requested_position)

    def set_position(self, position: int) -> None:
        if self.position_entry is None:
            return
        self.position_entry.delete(0, tk.END)
        self.position_entry.insert(0, str(position))

    def expand(self) -> None:
        if self.expanded:
            return
        self.expanded = True
        if self.toggle_button is not None:
            self.toggle_button.configure(text="Contraer")
        self._build_detail()

    def collapse(self) -> None:
        if not self.expanded:
            return
        self._commit_visible_rows()
        self.expanded = False
        if self.detail_container is not None:
            self.detail_container.destroy()
        self.rows.clear()
        self.detail_container = None
        self.detail_frame = None
        self.scrollbar = None
        self.range_label = None
        self.add_person_button = None
        if self.toggle_button is not None:
            self.toggle_button.configure(text="Expandir")

    def _render_window(self) -> None:
        if not self.expanded:
            return
        window = virtual_window(len(self.personnel), VISIBLE_PERSON_ROWS, self._window_start)
        self._window_start = window.start
        for slot, row in enumerate(self.rows):
            data_index = window.start + slot
            if data_index < window.stop:
                row.bind_data(data_index, self.personnel[data_index])
                row.show()
            else:
                row.hide()

        if self.scrollbar is not None:
            self.scrollbar.set(window.first_fraction, window.last_fraction)
        if self.range_label is not None:
            if window.total:
                self.range_label.configure(
                    text=f"Mostrando {window.start + 1}–{window.stop} de {window.total} personas"
                )
            else:
                self.range_label.configure(text="Sin personas")

    def _commit_visible_rows(self) -> None:
        """Persist the reusable controls before their model bindings change."""
        for row in self.rows:
            if row.data_index is not None and 0 <= row.data_index < len(self.personnel):
                self.personnel[row.data_index] = row.get_data()

    def _on_virtual_scroll(self, *args: str) -> None:
        if not args:
            return
        self._commit_visible_rows()
        if args[0] == "moveto" and len(args) > 1:
            self._window_start = start_from_fraction(
                len(self.personnel),
                VISIBLE_PERSON_ROWS,
                float(args[1]),
            )
        elif args[0] == "scroll" and len(args) > 2:
            amount = int(args[1])
            step = VISIBLE_PERSON_ROWS - 1 if args[2] == "pages" else 1
            self._window_start += amount * step
        self._render_window()

    def _on_mousewheel(self, event: tk.Event) -> str | None:
        if len(self.personnel) <= VISIBLE_PERSON_ROWS:
            return None
        self._commit_visible_rows()
        previous_start = self._window_start
        delta = getattr(event, "delta", 0)
        if delta:
            steps = max(1, abs(int(delta)) // 120)
            self._window_start += -steps if delta > 0 else steps
        self._render_window()
        return "break" if self._window_start != previous_start else None

    def _update_person(self, row: PersonnelRow, person: PersonReportRow) -> None:
        if row.data_index is None or not 0 <= row.data_index < len(self.personnel):
            return
        self.personnel[row.data_index] = person
        self._on_change()

    def _move_person_from_row(self, row: PersonnelRow, position: int) -> None:
        if row.data_index is not None:
            self.move_person_to_index(row.data_index, position)

    def add_person_row(self) -> None:
        self._commit_visible_rows()
        self.personnel.append(empty_person())
        self._window_start = max(0, len(self.personnel) - VISIBLE_PERSON_ROWS)
        self._refresh_count()
        if not self.expanded:
            self._on_expand_request(self)
        self._render_window()
        self._on_change()

    def remove_person_row(self, row: PersonnelRow) -> None:
        if row.data_index is None or len(self.personnel) <= 1:
            return
        self._commit_visible_rows()
        self.personnel.pop(row.data_index)
        self._refresh_count()
        self._render_window()
        self._on_change()

    def move_person_row(self, row: PersonnelRow, delta: int) -> None:
        if row.data_index is None:
            return
        self.move_person_to_index(row.data_index, row.data_index + delta + 1)

    def move_person_to_index(self, source_index: int, position: int) -> None:
        if not 0 <= source_index < len(self.personnel):
            return
        self._commit_visible_rows()
        target_index = max(0, min(position - 1, len(self.personnel) - 1))
        if target_index != source_index:
            person = self.personnel.pop(source_index)
            self.personnel.insert(target_index, person)
            if target_index < self._window_start:
                self._window_start = target_index
            elif target_index >= self._window_start + VISIBLE_PERSON_ROWS:
                self._window_start = target_index - VISIBLE_PERSON_ROWS + 1
            self._on_change()
        self._render_window()

    def transfer_person_out(self, row: PersonnelRow) -> PersonReportRow | None:
        if row.data_index is None or not 0 <= row.data_index < len(self.personnel):
            return None
        self._commit_visible_rows()
        person = self.personnel[row.data_index]
        if len(self.personnel) == 1:
            self.personnel[0] = empty_person()
        else:
            self.personnel.pop(row.data_index)
        self._refresh_count()
        self._render_window()
        self._on_change()
        return person

    def append_person(self, person: PersonReportRow) -> None:
        self._commit_visible_rows()
        if len(self.personnel) == 1 and not person_has_data(self.personnel[0]):
            self.personnel[0] = person
        else:
            self.personnel.append(person)
        self._refresh_count()
        self._render_window()
        self._on_change()

    def _refresh_count(self) -> None:
        if self.count_label is not None:
            count = len([person for person in self.personnel if person_has_data(person)])
            suffix = "persona" if count == 1 else "personas"
            self.count_label.configure(text=f"{count} {suffix}")

    def get_data(self, fallback_name: str = "") -> AreaReportData:
        self._commit_visible_rows()
        area_name = self.area_name_var.get().strip() or fallback_name
        personnel = [person for person in self.personnel if person_has_data(person)]
        return AreaReportData(name=area_name, personnel=list(personnel))

    def set_data(self, area: AreaReportData) -> None:
        self.area_name_var.set(area.name)
        self.personnel = list(area.personnel) or [empty_person()]
        self._window_start = 0
        self._refresh_count()
        self._render_window()

    def validate_dates(self) -> bool:
        self._commit_visible_rows()
        is_valid = all(
            not person_has_data(person) or is_valid_date(person.start_date)
            for person in self.personnel
        )
        self._render_window()
        return is_valid

    def destroy(self) -> None:
        self.collapse()
        super().destroy()
