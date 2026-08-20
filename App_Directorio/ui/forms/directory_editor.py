"""Top-level form composition for the institutional directory editor."""

import tkinter as tk

import customtkinter as ctk

from App_Directorio.config import PLUS_ICON_HOVER_PATH, PLUS_ICON_PATH
from App_Directorio.models import AreaReportData, DirectoryReportData
from App_Directorio.ui.accessibility import enable_visible_focus_for
from App_Directorio.ui.forms.area_section import AreaSection
from App_Directorio.ui.forms.field_helpers import bind_uppercase
from App_Directorio.ui.forms.personnel_row import PersonnelRow
from App_Directorio.ui.theme import (
    APP_BACKGROUND,
    BORDER_COLOR,
    PRIMARY_BUTTON,
    PRIMARY_BUTTON_ACTIVE,
    SURFACE_BACKGROUND,
    TEXT_DARK,
    TEXT_LIGHT,
    TEXT_MUTED,
    make_font,
)
from App_Directorio.ui.widgets import load_icon_pair
from App_Directorio.utils import is_valid_date
from components.shared.entries import VariablePlaceholderEntry


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

    def add_area(
        self,
        removable: bool = True,
        *,
        data: AreaReportData | None = None,
        expand: bool = True,
        refresh: bool = True,
        notify: bool = True,
    ) -> None:
        if self.areas_container is None:
            return
        section = AreaSection(
            self.areas_container,
            add_icons=self.plus_icons,
            on_change=self._notify_change,
            on_reposition=lambda _position: None,
            on_person_actions_request=self._show_person_actions_menu,
            on_area_actions_request=self._show_area_actions_menu,
            on_expand_request=self._request_area_toggle,
            removable=removable,
        )
        section._on_reposition = lambda position, current=section: self.move_area_to(current, position)
        if data is not None:
            section.set_data(data)
        section.grid(row=len(self.area_sections), column=0, sticky="ew", pady=(0, 16))
        self.area_sections.append(section)
        if refresh:
            self._refresh_areas()
        enable_visible_focus_for(section)
        if expand:
            self._expand_only(section)
        if notify:
            self._notify_change()

    def _request_area_toggle(self, section: AreaSection) -> None:
        if section.expanded:
            section.collapse()
        else:
            self._expand_only(section)

    def _expand_only(self, selected: AreaSection) -> None:
        for section in self.area_sections:
            if section is selected:
                section.expand()
            else:
                section.collapse()

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
            if target_section is source_section:
                transfer_menu.add_command(label=f"{index}. {area_name}", state="disabled")
            else:
                transfer_menu.add_command(
                    label=f"{index}. {area_name}",
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
            menu.tk_popup(button.winfo_rootx(), button.winfo_rooty() + button.winfo_height())
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
        removed_index = self.area_sections.index(section)
        was_expanded = section.expanded
        self.area_sections.remove(section)
        section.destroy()
        self._refresh_areas()
        if was_expanded and self.area_sections:
            self._expand_only(self.area_sections[min(removed_index, len(self.area_sections) - 1)])
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
            for area in areas:
                self.add_area(
                    data=area,
                    expand=False,
                    refresh=False,
                    notify=False,
                )
            self._refresh_areas()
            if self.area_sections:
                self._expand_only(self.area_sections[0])
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
            self.add_area(refresh=False, notify=False)
            self._refresh_areas()
        finally:
            self._change_suppressed = False
        self._notify_change()

    def validate_dates(self) -> bool:
        return all(section.validate_dates() for section in self.area_sections)

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
