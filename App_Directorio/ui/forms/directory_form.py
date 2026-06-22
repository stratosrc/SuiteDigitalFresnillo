from collections.abc import Callable
import tkinter as tk

import customtkinter as ctk

from App_Directorio.config import (
    MINUS_ICON_HOVER_PATH,
    MINUS_ICON_PATH,
    PLUS_ICON_HOVER_PATH,
    PLUS_ICON_PATH,
    DOWN_ICON_HOVER_PATH,
    DOWN_ICON_PATH,
    REMOVE_ICON_HOVER_PATH,
    REMOVE_ICON_PATH,
    UP_ICON_HOVER_PATH,
    UP_ICON_PATH,
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


PERSONNEL_COLUMN_WEIGHTS = (14, 18, 16, 17, 10)
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


class PersonnelRow:
    def __init__(
        self,
        master: ctk.CTkFrame,
        grid_row: int,
        on_remove: Callable[[], None],
        on_move_up: Callable[[], None],
        on_move_down: Callable[[], None],
        move_up_icons: IconPair,
        move_down_icons: IconPair,
        remove_icons: IconPair,
        locked: bool = False,
    ) -> None:
        self.master = master
        self.grid_row = grid_row
        self._on_remove = on_remove
        self._on_move_up = on_move_up
        self._on_move_down = on_move_down
        self.move_up_icons = move_up_icons
        self.move_down_icons = move_down_icons
        self.remove_icons = remove_icons
        self.locked = locked
        self.entries: list[ctk.CTkEntry] = []
        self.date_entry: ctk.CTkEntry | None = None
        self.widgets: list[tk.Widget] = []
        self._build_entries()

    def _build_entries(self) -> None:
        placeholders = (
            "Rango / Clave / Nivel",
            "Nombre",
            "Cargo",
            "Correo electronico",
            "dd/mm/aaaa",
        )
        for column, (placeholder, padx) in enumerate(zip(placeholders, PERSONNEL_COLUMN_PADX)):
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
            if column == 4:
                validate_command = (self.master.register(is_date_input_prefix), "%P")
                entry.configure(validate="key", validatecommand=validate_command)
                entry.bind("<FocusOut>", self._handle_date_focus_out)
                self.date_entry = entry
            entry.grid(row=self.grid_row, column=column, sticky="ew", padx=padx, pady=(0, 8))
            self.entries.append(entry)
            self.widgets.append(entry)

        if not self.locked:
            up_button = HoverIconButton(
                self.master,
                icons=self.move_up_icons,
                command=self._handle_move_up,
                width=30,
                height=30,
                tooltip_text="Subir persona",
            )
            up_button.grid(row=self.grid_row, column=5, padx=(10, 4), pady=(0, 8), sticky="e")
            self.widgets.append(up_button)

            down_button = HoverIconButton(
                self.master,
                icons=self.move_down_icons,
                command=self._handle_move_down,
                width=30,
                height=30,
                tooltip_text="Bajar persona",
            )
            down_button.grid(row=self.grid_row, column=6, padx=(0, 4), pady=(0, 8), sticky="e")
            self.widgets.append(down_button)

            remove_button = HoverIconButton(
                self.master,
                icons=self.remove_icons,
                command=self._handle_remove,
                width=30,
                height=30,
                tooltip_text="Eliminar persona",
            )
            remove_button.grid(row=self.grid_row, column=7, padx=(0, 0), pady=(0, 8), sticky="e")
            self.widgets.append(remove_button)

    def _handle_remove(self) -> None:
        self._on_remove()

    def _handle_move_up(self) -> None:
        self._on_move_up()

    def _handle_move_down(self) -> None:
        self._on_move_down()

    def _handle_date_focus_out(self, _event: tk.Event) -> None:
        self.validate_date()

    def grid_configure(self, row: int) -> None:
        self.grid_row = row
        for widget in self.widgets:
            widget.grid_configure(row=row)

    def destroy(self) -> None:
        for widget in self.widgets:
            widget.destroy()
        self.widgets.clear()
        self.entries.clear()
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
        on_remove: Callable[[], None],
        on_move_up: Callable[[], None],
        on_move_down: Callable[[], None],
        move_up_icons: IconPair,
        move_down_icons: IconPair,
        add_icons: IconPair,
        area_remove_icons: IconPair,
        person_remove_icons: IconPair,
        removable: bool = True,
    ) -> None:
        super().__init__(
            master,
            fg_color=SURFACE_ALT_BACKGROUND,
            corner_radius=0,
            border_width=1,
            border_color=BORDER_COLOR,
        )
        self._on_remove = on_remove
        self._on_move_up = on_move_up
        self._on_move_down = on_move_down
        self.move_up_icons = move_up_icons
        self.move_down_icons = move_down_icons
        self.add_icons = add_icons
        self.area_remove_icons = area_remove_icons
        self.person_remove_icons = person_remove_icons
        self.removable = removable
        self.rows: list[PersonnelRow] = []
        self.area_name_var = tk.StringVar()
        bind_uppercase(self.area_name_var)
        self.area_name_entry: ctk.CTkEntry | None = None
        self.detail_frame: ctk.CTkFrame | None = None
        self.add_person_button: HoverIconButton | None = None
        self._build_area()

    def _build_area(self) -> None:
        self.grid_columnconfigure(0, weight=1)

        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 0))
        header_frame.grid_columnconfigure(0, weight=1)

        self.area_name_entry = VariablePlaceholderEntry(
            header_frame,
            textvariable=self.area_name_var,
            height=34,
            corner_radius=0,
            fg_color=SURFACE_BACKGROUND,
            border_color=BORDER_COLOR,
            text_color=TEXT_DARK,
            placeholder_text="Nombre del área",
            placeholder_text_color=TEXT_MUTED,
            font=make_font(12),
        )
        self.area_name_entry.grid(row=0, column=0, sticky="ew")

        if self.removable:
            HoverIconButton(
                header_frame,
                icons=self.move_up_icons,
                command=self._handle_move_up,
                width=32,
                height=32,
                tooltip_text="Subir área",
            ).grid(row=0, column=1, padx=(10, 0), sticky="e")

            HoverIconButton(
                header_frame,
                icons=self.move_down_icons,
                command=self._handle_move_down,
                width=32,
                height=32,
                tooltip_text="Bajar área",
            ).grid(row=0, column=2, padx=(6, 0), sticky="e")

            HoverIconButton(
                header_frame,
                icons=self.area_remove_icons,
                command=self._handle_remove,
                width=32,
                height=32,
                tooltip_text="Eliminar área",
            ).grid(row=0, column=3, padx=(10, 0), sticky="e")

        self.detail_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.detail_frame.grid(row=1, column=0, sticky="ew", padx=(44, 16), pady=(14, 14))
        for column, weight in enumerate(PERSONNEL_COLUMN_WEIGHTS):
            self.detail_frame.grid_columnconfigure(column, weight=weight, uniform="personnel")
        for column in (5, 6, 7):
            self.detail_frame.grid_columnconfigure(column, weight=0)

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
        headers = ("Rango / Clave / Nivel", "Nombre", "Cargo", "Correo electronico", "Fecha de Alta")
        for column, (label, padx) in enumerate(zip(headers, PERSONNEL_COLUMN_PADX)):
            ctk.CTkLabel(
                parent,
                text=label,
                text_color=TEXT_DARK,
                font=make_font(12, "bold"),
                anchor="w",
            ).grid(row=0, column=column, sticky="w", padx=padx)

    def add_person_row(self) -> None:
        if self.detail_frame is None:
            return

        locked = not self.rows
        row = PersonnelRow(
            self.detail_frame,
            grid_row=len(self.rows) + 1,
            on_remove=lambda: None,
            on_move_up=lambda: None,
            on_move_down=lambda: None,
            move_up_icons=self.move_up_icons,
            move_down_icons=self.move_down_icons,
            remove_icons=self.person_remove_icons,
            locked=locked,
        )
        row._on_remove = lambda current=row: self.remove_person_row(current)
        row._on_move_up = lambda current=row: self.move_person_row(current, -1)
        row._on_move_down = lambda current=row: self.move_person_row(current, 1)
        self.rows.append(row)
        self._place_add_person_button()

    def _handle_remove(self) -> None:
        self._on_remove()

    def _handle_move_up(self) -> None:
        self._on_move_up()

    def _handle_move_down(self) -> None:
        self._on_move_down()

    def remove_person_row(self, row: PersonnelRow) -> None:
        if row not in self.rows or row.locked or len(self.rows) <= 1:
            return

        self.rows.remove(row)
        row.destroy()
        self._refresh_rows()

    def move_person_row(self, row: PersonnelRow, delta: int) -> None:
        if row not in self.rows:
            return

        current_index = self.rows.index(row)
        target_index = current_index + delta
        if current_index == 0 or target_index <= 0 or target_index >= len(self.rows):
            return

        self.rows[current_index], self.rows[target_index] = self.rows[target_index], self.rows[current_index]
        self._refresh_rows()

    def _refresh_rows(self) -> None:
        for index, row in enumerate(self.rows):
            row.grid_configure(row=index + 1)
        self._place_add_person_button()

    def _place_add_person_button(self) -> None:
        if self.add_person_button is None:
            return

        self.add_person_button.grid(row=len(self.rows) + 1, column=7, sticky="e", pady=(2, 0))

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
        self.move_up_icons = load_icon_pair(UP_ICON_PATH, UP_ICON_HOVER_PATH, (20, 20))
        self.move_down_icons = load_icon_pair(DOWN_ICON_PATH, DOWN_ICON_HOVER_PATH, (20, 20))
        self.area_remove_icons = load_icon_pair(REMOVE_ICON_PATH, REMOVE_ICON_HOVER_PATH, (20, 20))
        self.person_remove_icons = load_icon_pair(MINUS_ICON_PATH, MINUS_ICON_HOVER_PATH, (20, 20))
        self.area_sections: list[AreaSection] = []
        self.areas_container: ctk.CTkFrame | None = None
        self._build_layout()

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

        self.add_area(removable=False)

    def add_area(self, removable: bool = True) -> None:
        if self.areas_container is None:
            return

        section = AreaSection(
            self.areas_container,
            on_remove=lambda: None,
            on_move_up=lambda: None,
            on_move_down=lambda: None,
            move_up_icons=self.move_up_icons,
            move_down_icons=self.move_down_icons,
            add_icons=self.plus_icons,
            area_remove_icons=self.area_remove_icons,
            person_remove_icons=self.person_remove_icons,
            removable=removable,
        )
        section._on_remove = lambda current=section: self.remove_area(current)
        section._on_move_up = lambda current=section: self.move_area(current, -1)
        section._on_move_down = lambda current=section: self.move_area(current, 1)
        section.grid(row=len(self.area_sections), column=0, sticky="ew", pady=(0, 16))
        self.area_sections.append(section)

    def remove_area(self, section: AreaSection) -> None:
        if section not in self.area_sections or not section.removable or len(self.area_sections) <= 1:
            return

        self.area_sections.remove(section)
        section.destroy()
        self._refresh_areas()

    def move_area(self, section: AreaSection, delta: int) -> None:
        if section not in self.area_sections or not section.removable:
            return

        current_index = self.area_sections.index(section)
        target_index = current_index + delta
        if current_index == 0 or target_index <= 0 or target_index >= len(self.area_sections):
            return

        self.area_sections[current_index], self.area_sections[target_index] = (
            self.area_sections[target_index],
            self.area_sections[current_index],
        )
        self._refresh_areas()

    def _refresh_areas(self) -> None:
        for index, section in enumerate(self.area_sections):
            section.grid_configure(row=index)

    def get_report_data(self) -> DirectoryReportData:
        title = self.title_var.get().strip()
        return DirectoryReportData(
            title=title,
            period=self.period_var.get().strip(),
            areas=[section.get_data(fallback_name=title) for section in self.area_sections],
        )

    def set_report_data(self, data: DirectoryReportData) -> None:
        self.title_var.set(data.title)
        self.period_var.set(data.period)
        for section in self.area_sections:
            section.destroy()
        self.area_sections.clear()

        areas = data.areas or [AreaReportData("", [])]
        for index, area in enumerate(areas):
            self.add_area(removable=index > 0)
            self.area_sections[-1].set_data(area)

    def reset_form(self) -> None:
        self.title_var.set("")
        self.period_var.set("")
        for section in self.area_sections:
            section.destroy()
        self.area_sections.clear()
        self.add_area(removable=False)

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
