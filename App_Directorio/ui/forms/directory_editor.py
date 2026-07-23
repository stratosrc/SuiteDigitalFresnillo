"""Directory form editor and its dynamic row controllers."""

from collections.abc import Callable
import tkinter as tk

import customtkinter as ctk

from App_Directorio.config import (
    PLUS_ICON_HOVER_PATH,
    PLUS_ICON_PATH,
)
from App_Directorio.models import AreaReportData, DirectoryReportData, PersonReportRow
from App_Directorio.ui.theme import (
    APP_BACKGROUND,
    BORDER_COLOR,
    PRIMARY_BUTTON,
    PRIMARY_BUTTON_ACTIVE,
    SURFACE_ALT_BACKGROUND,
    SURFACE_BACKGROUND,
    TEXT_DARK,
    TEXT_LIGHT,
    TEXT_MUTED,
    make_font,
)
from App_Directorio.ui.widgets import HoverIconButton, IconPair, load_icon_pair
from App_Directorio.utils import is_date_input_prefix, is_valid_date
from components.shared.entries import VariablePlaceholderEntry
from App_Directorio.ui.accessibility import enable_visible_focus_for


EMAIL_DOMAIN = "@fresnillo.gob.mx"
PERSONNEL_COLUMN_WEIGHTS = (0, 0, 14, 18, 16, 17, 10)
PERSONNEL_COLUMN_PADX = ((0, 8), (0, 8), (0, 8), (0, 8), (0, 0))


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
                variable._root.after_idle(
                    lambda: focused.icursor(min(cursor, len(variable.get())))
                )

    variable.trace_add("write", normalize)


def is_position_input(value: str) -> bool:
    """Allow an empty value while editing, or a positive integer."""
    return not value or (value.isdigit() and int(value) > 0)


class PersonnelRow:
    def __init__(
        self,
        master: ctk.CTkFrame,
        grid_row: int,
        on_change: Callable[[], None],
        on_reposition: Callable[[int], None],
        on_actions_request: Callable[[ctk.CTkButton], None],
    ) -> None:
        self.master = master
        self.grid_row = grid_row
        self._on_change = on_change
        self._on_reposition = on_reposition
        self._on_actions_request = on_actions_request
        self.entries: list[ctk.CTkEntry] = []
        self.position_entry: ctk.CTkEntry | None = None
        self.date_entry: ctk.CTkEntry | None = None
        self.widgets: list[tk.Widget] = []
        self._build_entries()

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
        position_validation = (self.master.register(is_position_input), "%P")
        self.position_entry.configure(validate="key", validatecommand=position_validation)
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

        placeholders = (
            "Rango / Clave / Nivel",
            "Nombre",
            "Cargo",
            "Correo electronico",
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
                validate_command = (self.master.register(is_date_input_prefix), "%P")
                entry.configure(validate="key", validatecommand=validate_command)
                entry.bind("<FocusOut>", self._handle_date_focus_out)
                self.date_entry = entry
            if data_column == 3:
                entry.bind("<FocusOut>", self._handle_email_focus_out)
                entry.bind("<Return>", self._handle_email_focus_out)
            entry.bind("<KeyRelease>", lambda _event: self._on_change(), add=True)
            entry.grid(row=self.grid_row, column=column, sticky="ew", padx=padx, pady=(0, 8))
            self.entries.append(entry)
            self.widgets.append(entry)

    def _handle_date_focus_out(self, _event: tk.Event) -> None:
        self.validate_date()

    def _handle_email_focus_out(self, _event: tk.Event) -> None:
        email_entry = self.entries[3]
        value = email_entry.get().strip()
        if value and "@" not in value:
            email_entry.delete(0, tk.END)
            email_entry.insert(0, f"{value}{EMAIL_DOMAIN}")
            self._on_change()

    def _handle_position_request(self, _event: tk.Event) -> None:
        if self.position_entry is None:
            return
        try:
            requested_position = int(self.position_entry.get())
        except ValueError:
            requested_position = self.grid_row
        self._on_reposition(requested_position)

    def set_position(self, position: int) -> None:
        if self.position_entry is None:
            return
        self.position_entry.delete(0, tk.END)
        self.position_entry.insert(0, str(position))

    def grid_configure(self, row: int) -> None:
        self.grid_row = row
        for widget in self.widgets:
            widget.grid_configure(row=row)

    def destroy(self) -> None:
        for widget in self.widgets:
            widget.destroy()
        self.widgets.clear()
        self.entries.clear()
        self.position_entry = None
        self.date_entry = None

    def get_data(self) -> PersonReportRow:
        values = [entry.get().strip() for entry in self.entries]
        return PersonReportRow(
            rank=values[0] if len(values) > 0 else "",
            name=values[1] if len(values) > 1 else "",
            position=values[2] if len(values) > 2 else "",
            email=values[3] if len(values) > 3 else "",
            start_date=values[4] if len(values) > 4 else "",
        )

    def set_data(self, person: PersonReportRow) -> None:
        values = (person.rank, person.name, person.position, person.email, person.start_date)
        for entry, value in zip(self.entries, values):
            entry.delete(0, tk.END)
            entry.insert(0, value)
        self.validate_date()

    def has_data(self) -> bool:
        return any(entry.get().strip() for entry in self.entries)

    def validate_date(self) -> bool:
        if self.date_entry is None:
            return True

        date_value = self.date_entry.get().strip()
        is_valid = not self.has_data() or is_valid_date(date_value)
        self.date_entry.configure(border_color=BORDER_COLOR if is_valid else "#C62828")
        return is_valid


class AreaSection(ctk.CTkFrame):
    def __init__(
        self,
        master: ctk.CTkFrame,
        add_icons: IconPair,
        on_change: Callable[[], None],
        on_reposition: Callable[[int], None],
        on_person_actions_request: Callable[["AreaSection", PersonnelRow, ctk.CTkButton], None],
        on_area_actions_request: Callable[["AreaSection", ctk.CTkButton], None],
        removable: bool = True,
    ) -> None:
        super().__init__(
            master,
            fg_color=SURFACE_ALT_BACKGROUND,
            corner_radius=0,
            border_width=1,
            border_color=BORDER_COLOR,
        )
        self.add_icons = add_icons
        self._on_change = on_change
        self._on_reposition = on_reposition
        self._on_person_actions_request = on_person_actions_request
        self._on_area_actions_request = on_area_actions_request
        self.removable = removable
        self.rows: list[PersonnelRow] = []
        self.area_name_var = tk.StringVar()
        bind_uppercase(self.area_name_var)
        self.area_name_var.trace_add("write", lambda *_args: self._on_change())
        self.area_name_entry: ctk.CTkEntry | None = None
        self.detail_frame: ctk.CTkFrame | None = None
        self.add_person_button: HoverIconButton | None = None
        self._build_area()

    def _build_area(self) -> None:
        self.grid_columnconfigure(0, weight=1)

        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 0))
        header_frame.grid_columnconfigure(1, weight=1)

        self.position_entry = ctk.CTkEntry(
            header_frame,
            width=42,
            height=34,
            corner_radius=0,
            fg_color=SURFACE_BACKGROUND,
            border_color=BORDER_COLOR,
            text_color=TEXT_DARK,
            justify="center",
            font=make_font(12, "bold"),
        )
        position_validation = (self.register(is_position_input), "%P")
        self.position_entry.configure(validate="key", validatecommand=position_validation)
        self.position_entry.bind("<FocusOut>", self._handle_position_request)
        self.position_entry.bind("<Return>", self._handle_position_request)
        self.position_entry.grid(row=0, column=0, padx=(0, 8), sticky="w")

        self.area_name_entry = VariablePlaceholderEntry(
            header_frame,
            textvariable=self.area_name_var,
            height=34,
            corner_radius=0,
            fg_color=SURFACE_BACKGROUND,
            border_color=BORDER_COLOR,
            text_color=TEXT_DARK,
            placeholder_text="Agregar Area, ej. Jefatura de Gobierno Digital",
            placeholder_text_color=TEXT_MUTED,
            font=make_font(12),
        )
        self.area_name_entry.grid(row=0, column=1, sticky="ew")

        if self.removable:
            actions_button = ctk.CTkButton(
                header_frame,
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
            actions_button.grid(row=0, column=2, padx=(10, 0), sticky="e")

        self.detail_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.detail_frame.grid(row=1, column=0, sticky="ew", padx=(16, 16), pady=(14, 14))
        for column, weight in enumerate(PERSONNEL_COLUMN_WEIGHTS):
            self.detail_frame.grid_columnconfigure(column, weight=weight, uniform="personnel")
        self._build_headers(self.detail_frame)

        self.add_person_button = HoverIconButton(
            self.detail_frame,
            icons=self.add_icons,
            command=self.add_person_row,
            width=32,
            height=32,
            tooltip_text="Agregar persona",
        )

        self.add_person_row()

    def _build_headers(self, parent: ctk.CTkFrame) -> None:
        ctk.CTkLabel(
            parent,
            text="",
            width=30,
        ).grid(row=0, column=0, sticky="w", padx=(0, 6))

        ctk.CTkLabel(
            parent,
            text="#",
            text_color=TEXT_DARK,
            font=make_font(12, "bold"),
            width=42,
            anchor="center",
        ).grid(row=0, column=1, sticky="w", padx=(0, 8))

        headers = ("Rango / Clave / Nivel", "Nombre", "Cargo", "Correo electronico", "Fecha de Alta")
        for data_column, (label, padx) in enumerate(zip(headers, PERSONNEL_COLUMN_PADX)):
            ctk.CTkLabel(
                parent,
                text=label,
                text_color=TEXT_DARK,
                font=make_font(12, "bold"),
                anchor="w",
            ).grid(row=0, column=data_column + 2, sticky="w", padx=padx)

    def add_person_row(self) -> None:
        if self.detail_frame is None:
            return

        row = PersonnelRow(
            self.detail_frame,
            grid_row=len(self.rows) + 1,
            on_change=self._on_change,
            on_reposition=lambda _position: None,
            on_actions_request=lambda _button: None,
        )
        row._on_reposition = lambda position, current=row: self.move_person_to(current, position)
        row._on_actions_request = (
            lambda button, current=row: self._on_person_actions_request(self, current, button)
        )
        self.rows.append(row)
        self._refresh_rows()
        enable_visible_focus_for(self.detail_frame)
        self._on_change()

    def _handle_position_request(self, _event: tk.Event) -> None:
        try:
            requested_position = int(self.position_entry.get())
        except ValueError:
            requested_position = 1
        self._on_reposition(requested_position)

    def set_position(self, position: int) -> None:
        self.position_entry.delete(0, tk.END)
        self.position_entry.insert(0, str(position))

    def remove_person_row(self, row: PersonnelRow) -> None:
        if row not in self.rows or len(self.rows) <= 1:
            return

        self.rows.remove(row)
        row.destroy()
        self._refresh_rows()
        self._on_change()

    def move_person_row(self, row: PersonnelRow, delta: int) -> None:
        if row not in self.rows:
            return

        current_index = self.rows.index(row)
        target_index = current_index + delta
        if target_index < 0 or target_index >= len(self.rows):
            return

        self.rows[current_index], self.rows[target_index] = self.rows[target_index], self.rows[current_index]
        self._refresh_rows()
        self._on_change()

    def move_person_to(self, row: PersonnelRow, position: int) -> None:
        if row not in self.rows:
            return
        current_index = self.rows.index(row)
        target_index = max(0, min(position - 1, len(self.rows) - 1))
        if target_index != current_index:
            self.rows.pop(current_index)
            self.rows.insert(target_index, row)
            self._on_change()
        self._refresh_rows()

    def transfer_person_out(self, row: PersonnelRow) -> PersonReportRow | None:
        if row not in self.rows:
            return None

        person = row.get_data()
        if len(self.rows) == 1:
            row.set_data(PersonReportRow("", "", "", "", ""))
        else:
            self.rows.remove(row)
            row.destroy()
            self._refresh_rows()
        self._on_change()
        return person

    def append_person(self, person: PersonReportRow) -> None:
        if len(self.rows) == 1 and not self.rows[0].has_data():
            self.rows[0].set_data(person)
        else:
            self.add_person_row()
            self.rows[-1].set_data(person)
        self._refresh_rows()
        self._on_change()

    def _refresh_rows(self) -> None:
        for index, row in enumerate(self.rows):
            row.grid_configure(row=index + 1)
            row.set_position(index + 1)
        self._place_add_person_button()

    def _place_add_person_button(self) -> None:
        if self.add_person_button is None:
            return

        self.add_person_button.grid(row=len(self.rows) + 1, column=6, sticky="e", pady=(2, 0))

    def get_data(self, fallback_name: str = "") -> AreaReportData:
        area_name = self.area_name_var.get().strip()
        if not area_name:
            area_name = fallback_name
        personnel = [row.get_data() for row in self.rows]
        personnel = [row for row in personnel if any((row.rank, row.name, row.position, row.email, row.start_date))]
        return AreaReportData(name=area_name, personnel=personnel)

    def set_data(self, area: AreaReportData) -> None:
        self.area_name_var.set(area.name)

        for row in self.rows:
            row.destroy()
        self.rows.clear()

        personnel = area.personnel or [PersonReportRow("", "", "", "", "")]
        for person in personnel:
            self.add_person_row()
            self.rows[-1].set_data(person)
        self._refresh_rows()

    def validate_dates(self) -> bool:
        results = [row.validate_date() for row in self.rows]
        return all(results)


class DirectoryFormFrame(ctk.CTkFrame):
    def __init__(self, master: ctk.CTkFrame) -> None:
        super().__init__(master, fg_color=APP_BACKGROUND, corner_radius=0)
        self.title_var = tk.StringVar()
        self.period_var = tk.StringVar()
        bind_uppercase(self.title_var)
        bind_uppercase(self.period_var)
        self.plus_icons = load_icon_pair(PLUS_ICON_PATH, PLUS_ICON_HOVER_PATH, (22, 22))
        self.area_sections: list[AreaSection] = []
        self.areas_container: ctk.CTkFrame | None = None
        self._change_suppressed = False
        self._build_layout()
        self.title_var.trace_add("write", self._notify_change)
        self.period_var.trace_add("write", self._notify_change)

    def _notify_change(self, *_args: object) -> None:
        if not self._change_suppressed:
            self.event_generate("<<DirectoryChanged>>", when="tail")

    def _build_layout(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        scrollable = ctk.CTkScrollableFrame(
            self,
            fg_color=SURFACE_BACKGROUND,
            corner_radius=0,
            border_width=0,
            scrollbar_button_color=PRIMARY_BUTTON,
            scrollbar_button_hover_color=PRIMARY_BUTTON_ACTIVE,
        )
        scrollable.grid(row=0, column=0, sticky="nsew")
        scrollable.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            scrollable,
            text=(
                "Completa los datos generales y agrega las personas del directorio. "
                "Los campos se guardan automáticamente para recuperación."
            ),
            text_color=TEXT_MUTED,
            font=make_font(12),
            anchor="w",
            justify="left",
        ).grid(row=0, column=0, sticky="ew", padx=24, pady=(16, 0))
        self._build_metadata_section(scrollable)
        self._build_directory_section(scrollable)

    def _build_metadata_section(self, parent: ctk.CTkScrollableFrame) -> None:
        section = ctk.CTkFrame(parent, fg_color="transparent")
        section.grid(row=1, column=0, sticky="ew", padx=24, pady=(16, 12))
        section.grid_columnconfigure(0, weight=1)
        section.grid_columnconfigure(1, weight=1)

        self._build_labeled_entry(
            section,
            label="Área Administrativa (Título)",
            placeholder="Área administrativa, ej. Unidad de Transparencia",
            variable=self.title_var,
            column=0,
            padx=(0, 10),
        )
        self._build_labeled_entry(
            section,
            label="Período",
            placeholder="ej. Enero - Marzo 2026",
            variable=self.period_var,
            column=1,
            padx=(10, 0),
        )

    def _build_labeled_entry(
        self,
        parent: ctk.CTkFrame,
        label: str,
        placeholder: str,
        variable: tk.StringVar,
        column: int,
        padx: tuple[int, int],
    ) -> None:
        ctk.CTkLabel(
            parent,
            text=label,
            text_color=TEXT_DARK,
            font=make_font(13, "bold"),
        ).grid(row=0, column=column, sticky="w", padx=padx)

        VariablePlaceholderEntry(
            parent,
            textvariable=variable,
            height=34,
            corner_radius=0,
            fg_color=SURFACE_BACKGROUND,
            border_color=BORDER_COLOR,
            text_color=TEXT_DARK,
            placeholder_text=placeholder,
            placeholder_text_color=TEXT_MUTED,
            font=make_font(12),
        ).grid(row=1, column=column, sticky="ew", padx=padx, pady=(6, 0))

    def _build_directory_section(self, parent: ctk.CTkScrollableFrame) -> None:
        section = ctk.CTkFrame(parent, fg_color="transparent")
        section.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 16))
        section.grid_columnconfigure(0, weight=1)

        self.areas_container = ctk.CTkFrame(section, fg_color="transparent")
        self.areas_container.grid(row=0, column=0, sticky="ew")
        self.areas_container.grid_columnconfigure(0, weight=1)

        ctk.CTkButton(
            section,
            text="+ Agregar Área",
            command=self.add_area,
            height=32,
            width=150,
            corner_radius=0,
            fg_color=PRIMARY_BUTTON,
            hover_color=PRIMARY_BUTTON_ACTIVE,
            text_color=TEXT_LIGHT,
            font=make_font(12, "bold"),
        ).grid(row=1, column=0, sticky="w", pady=(8, 0))

        self.add_area()

    def add_area(self, removable: bool = True) -> None:
        if self.areas_container is None:
            return

        section = AreaSection(
            self.areas_container,
            add_icons=self.plus_icons,
            on_change=self._notify_change,
            on_reposition=lambda _position: None,
            on_person_actions_request=self._show_person_actions_menu,
            on_area_actions_request=self._show_area_actions_menu,
            removable=removable,
        )
        section._on_reposition = lambda position, current=section: self.move_area_to(current, position)
        section.grid(row=len(self.area_sections), column=0, sticky="ew", pady=(0, 16))
        self.area_sections.append(section)
        self._refresh_areas()
        enable_visible_focus_for(section)
        self._notify_change()

    def _show_person_actions_menu(
        self,
        source_section: AreaSection,
        row: PersonnelRow,
        button: ctk.CTkButton,
    ) -> None:
        menu = tk.Menu(
            self,
            tearoff=0,
            bg=SURFACE_BACKGROUND,
            fg=TEXT_DARK,
            activebackground=PRIMARY_BUTTON_ACTIVE,
            activeforeground=TEXT_LIGHT,
        )

        menu.add_command(label="Subir persona", command=lambda: source_section.move_person_row(row, -1))
        menu.add_command(label="Bajar persona", command=lambda: source_section.move_person_row(row, 1))
        menu.add_command(label="Eliminar persona", command=lambda: source_section.remove_person_row(row))
        menu.add_separator()
        transfer_menu = tk.Menu(menu, tearoff=0)
        for index, target_section in enumerate(self.area_sections, start=1):
            area_name = target_section.area_name_var.get().strip() or f"Área {index}"
            label = f"{index}. {area_name}"
            if target_section is source_section:
                transfer_menu.add_command(label=label, state="disabled")
            else:
                transfer_menu.add_command(
                    label=label,
                    command=lambda target=target_section: self._transfer_person(
                        source_section,
                        row,
                        target,
                    ),
                )

        if len(self.area_sections) == 1:
            transfer_menu.add_command(label="No hay otra área disponible", state="disabled")
        menu.add_cascade(label="Cambiar área", menu=transfer_menu)

        try:
            menu.tk_popup(
                button.winfo_rootx(),
                button.winfo_rooty() + button.winfo_height(),
            )
        finally:
            menu.grab_release()

    def _show_area_actions_menu(self, section: AreaSection, button: ctk.CTkButton) -> None:
        menu = tk.Menu(
            self,
            tearoff=0,
            bg=SURFACE_BACKGROUND,
            fg=TEXT_DARK,
            activebackground=PRIMARY_BUTTON_ACTIVE,
            activeforeground=TEXT_LIGHT,
        )
        menu.add_command(label="Subir área", command=lambda: self.move_area(section, -1))
        menu.add_command(label="Bajar área", command=lambda: self.move_area(section, 1))
        menu.add_command(label="Eliminar área", command=lambda: self.remove_area(section))
        try:
            menu.tk_popup(button.winfo_rootx(), button.winfo_rooty() + button.winfo_height())
        finally:
            menu.grab_release()

    def _transfer_person(
        self,
        source_section: AreaSection,
        row: PersonnelRow,
        target_section: AreaSection,
    ) -> None:
        if source_section not in self.area_sections or target_section not in self.area_sections:
            return
        if source_section is target_section:
            return

        person = source_section.transfer_person_out(row)
        if person is None:
            return
        target_section.append_person(person)
        self._notify_change()

    def remove_area(self, section: AreaSection) -> None:
        if section not in self.area_sections or len(self.area_sections) <= 1:
            return

        self.area_sections.remove(section)
        section.destroy()
        self._refresh_areas()
        self._notify_change()

    def move_area(self, section: AreaSection, delta: int) -> None:
        if section not in self.area_sections:
            return

        current_index = self.area_sections.index(section)
        target_index = current_index + delta
        if target_index < 0 or target_index >= len(self.area_sections):
            return

        self.area_sections[current_index], self.area_sections[target_index] = (
            self.area_sections[target_index],
            self.area_sections[current_index],
        )
        self._refresh_areas()
        self._notify_change()

    def move_area_to(self, section: AreaSection, position: int) -> None:
        if section not in self.area_sections:
            return
        current_index = self.area_sections.index(section)
        target_index = max(0, min(position - 1, len(self.area_sections) - 1))
        if target_index != current_index:
            self.area_sections.pop(current_index)
            self.area_sections.insert(target_index, section)
            self._notify_change()
        self._refresh_areas()

    def _refresh_areas(self) -> None:
        for index, section in enumerate(self.area_sections):
            section.grid_configure(row=index)
            section.set_position(index + 1)

    def get_report_data(self) -> DirectoryReportData:
        title = self.title_var.get().strip()
        return DirectoryReportData(
            title=title,
            period=self.period_var.get().strip(),
            areas=[section.get_data(fallback_name=title) for section in self.area_sections],
        )

    def set_report_data(self, data: DirectoryReportData) -> None:
        self._change_suppressed = True
        try:
            self.title_var.set(data.title)
            self.period_var.set(data.period)
            for section in self.area_sections:
                section.destroy()
            self.area_sections.clear()

            areas = data.areas or [AreaReportData("", [])]
            for index, area in enumerate(areas):
                self.add_area()
                self.area_sections[-1].set_data(area)
        finally:
            self._change_suppressed = False
        self._notify_change()

    def reset_form(self) -> None:
        self._change_suppressed = True
        try:
            self.title_var.set("")
            self.period_var.set("")
            for section in self.area_sections:
                section.destroy()
            self.area_sections.clear()
            self.add_area()
        finally:
            self._change_suppressed = False
        self._notify_change()

    def validate_dates(self) -> bool:
        results = [section.validate_dates() for section in self.area_sections]
        return all(results)

    def get_preview_summary(self) -> dict[str, object]:
        data = self.get_report_data()
        populated_areas = [area for area in data.areas if area.name or area.personnel]
        date_issues: list[str] = []
        for area_index, area in enumerate(data.areas, start=1):
            area_name = area.name or f"Área {area_index}"
            for person_index, person in enumerate(area.personnel, start=1):
                if not person.start_date or not is_valid_date(person.start_date):
                    label = person.name or person.position or person.rank or f"Fila {person_index}"
                    date_issues.append(f"{area_name}: {label}")

        return {
            "title": data.title,
            "period": data.period,
            "area_count": len(populated_areas),
            "person_count": sum(len(area.personnel) for area in populated_areas),
            "date_issues": date_issues,
        }

    def validate_required_data(self) -> bool:
        data = self.get_report_data()
        if not data.title:
            return False
        return any(area.name and area.personnel for area in data.areas)
