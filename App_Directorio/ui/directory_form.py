from collections.abc import Callable
import tkinter as tk

import customtkinter as ctk

from App_Directorio.ui.theme import (
    APP_BACKGROUND,
    BORDER_COLOR,
    PRIMARY_BUTTON,
    PRIMARY_BUTTON_ACTIVE,
    SURFACE_ALT_BACKGROUND,
    SUCCESS_BUTTON,
    SUCCESS_BUTTON_ACTIVE,
    SURFACE_BACKGROUND,
    TEXT_DARK,
    TEXT_LIGHT,
    TEXT_MUTED,
    make_font,
)


class PersonnelRow(ctk.CTkFrame):
    def __init__(self, master: ctk.CTkFrame, on_remove: Callable[[], None]) -> None:
        super().__init__(master, fg_color="transparent")
        self._on_remove = on_remove
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=3)
        self.grid_columnconfigure(2, weight=3)
        self.grid_columnconfigure(3, weight=2)
        self.grid_columnconfigure(4, weight=0)
        self._build_entries()

    def _build_entries(self) -> None:
        placeholders = (
            "Rango / Clave / Nivel",
            "Nombre",
            "Cargo",
            "Fecha de Alta",
        )
        paddings = ((0, 8), (0, 8), (0, 8), (0, 0))
        for column, (placeholder, padx) in enumerate(zip(placeholders, paddings)):
            ctk.CTkEntry(
                self,
                height=34,
                corner_radius=0,
                fg_color=SURFACE_BACKGROUND,
                border_color=BORDER_COLOR,
                text_color=TEXT_DARK,
                placeholder_text=placeholder,
                placeholder_text_color=TEXT_MUTED,
                font=make_font(12),
            ).grid(row=0, column=column, sticky="ew", padx=padx)

        ctk.CTkButton(
            self,
            text="X",
            command=self._handle_remove,
            width=24,
            height=24,
            corner_radius=12,
            fg_color="#C62828",
            hover_color="#D32F2F",
            text_color=TEXT_LIGHT,
            font=make_font(11, "bold"),
        ).grid(row=0, column=4, padx=(10, 0), sticky="e")

    def _handle_remove(self) -> None:
        self._on_remove()


class AreaSection(ctk.CTkFrame):
    def __init__(self, master: ctk.CTkFrame, on_remove: Callable[[], None]) -> None:
        super().__init__(
            master,
            fg_color=SURFACE_ALT_BACKGROUND,
            corner_radius=0,
            border_width=1,
            border_color=BORDER_COLOR,
        )
        self._on_remove = on_remove
        self.rows: list[PersonnelRow] = []
        self.rows_frame: ctk.CTkFrame | None = None
        self._build_area()

    def _build_area(self) -> None:
        self.grid_columnconfigure(0, weight=1)

        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 0))
        header_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkEntry(
            header_frame,
            height=34,
            corner_radius=0,
            fg_color=SURFACE_BACKGROUND,
            border_color=BORDER_COLOR,
            text_color=TEXT_DARK,
            placeholder_text="Nombre del area",
            placeholder_text_color=TEXT_MUTED,
            font=make_font(12),
        ).grid(row=0, column=0, sticky="ew")

        ctk.CTkButton(
            header_frame,
            text="X",
            command=self._handle_remove,
            width=26,
            height=26,
            corner_radius=13,
            fg_color="#C62828",
            hover_color="#D32F2F",
            text_color=TEXT_LIGHT,
            font=make_font(11, "bold"),
        ).grid(row=0, column=1, padx=(10, 0), sticky="e")

        detail_frame = ctk.CTkFrame(self, fg_color="transparent")
        detail_frame.grid(row=1, column=0, sticky="ew", padx=(44, 16), pady=(14, 14))
        detail_frame.grid_columnconfigure(0, weight=1)

        self._build_headers(detail_frame)

        self.rows_frame = ctk.CTkFrame(detail_frame, fg_color="transparent")
        self.rows_frame.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        self.rows_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkButton(
            detail_frame,
            text="+",
            command=self.add_person_row,
            width=20,
            height=20,
            corner_radius=10,
            fg_color=SUCCESS_BUTTON,
            hover_color=SUCCESS_BUTTON_ACTIVE,
            text_color=TEXT_LIGHT,
            font=make_font(13, "bold"),
        ).grid(row=2, column=0, sticky="e", pady=(10, 0))

        self.add_person_row()

    def _build_headers(self, parent: ctk.CTkFrame) -> None:
        header_frame = ctk.CTkFrame(parent, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew")
        header_frame.grid_columnconfigure(0, weight=2)
        header_frame.grid_columnconfigure(1, weight=3)
        header_frame.grid_columnconfigure(2, weight=3)
        header_frame.grid_columnconfigure(3, weight=2)

        headers = ("Rango / Clave / Nivel", "Nombre", "Cargo", "Fecha de Alta")
        paddings = ((0, 8), (0, 8), (0, 8), (0, 0))
        for column, (label, padx) in enumerate(zip(headers, paddings)):
            ctk.CTkLabel(
                header_frame,
                text=label,
                text_color=TEXT_DARK,
                font=make_font(12, "bold"),
                anchor="w",
            ).grid(row=0, column=column, sticky="w", padx=padx)

    def add_person_row(self) -> None:
        if self.rows_frame is None:
            return

        row = PersonnelRow(self.rows_frame, on_remove=lambda: None)
        row._on_remove = lambda current=row: self.remove_person_row(current)
        row.grid(row=len(self.rows), column=0, sticky="ew", pady=(0, 8))
        self.rows.append(row)

    def _handle_remove(self) -> None:
        self._on_remove()

    def remove_person_row(self, row: PersonnelRow) -> None:
        if row not in self.rows:
            return

        self.rows.remove(row)
        row.destroy()
        self._refresh_rows()

    def _refresh_rows(self) -> None:
        for index, row in enumerate(self.rows):
            row.grid_configure(row=index)


class DirectoryFormFrame(ctk.CTkFrame):
    def __init__(self, master: ctk.CTkFrame) -> None:
        super().__init__(master, fg_color=APP_BACKGROUND, corner_radius=0)
        self.title_var = tk.StringVar()
        self.period_var = tk.StringVar()
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

        self._build_metadata_section(scrollable)
        self._build_directory_section(scrollable)

    def _build_metadata_section(self, parent: ctk.CTkScrollableFrame) -> None:
        section = ctk.CTkFrame(parent, fg_color="transparent")
        section.grid(row=0, column=0, sticky="ew", padx=24, pady=(22, 12))
        section.grid_columnconfigure(0, weight=1)
        section.grid_columnconfigure(1, weight=1)

        self._build_labeled_entry(
            section,
            label="Titulo",
            placeholder="Titulo del directorio",
            variable=self.title_var,
            column=0,
            padx=(0, 10),
        )
        self._build_labeled_entry(
            section,
            label="Periodo",
            placeholder="Enero - Diciembre 2026",
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

        ctk.CTkEntry(
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
        section.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 16))
        section.grid_columnconfigure(0, weight=1)

        self.areas_container = ctk.CTkFrame(section, fg_color="transparent")
        self.areas_container.grid(row=0, column=0, sticky="ew")
        self.areas_container.grid_columnconfigure(0, weight=1)

        ctk.CTkButton(
            section,
            text="+ Agregar Area",
            command=self.add_area,
            height=32,
            width=150,
            corner_radius=0,
            fg_color=PRIMARY_BUTTON,
            hover_color=PRIMARY_BUTTON_ACTIVE,
            text_color=TEXT_LIGHT,
            font=make_font(12, "bold"),
        ).grid(row=1, column=0, sticky="w", pady=(8, 0))

    def add_area(self) -> None:
        if self.areas_container is None:
            return

        section = AreaSection(self.areas_container, on_remove=lambda: None)
        section._on_remove = lambda current=section: self.remove_area(current)
        section.grid(row=len(self.area_sections), column=0, sticky="ew", pady=(0, 16))
        self.area_sections.append(section)

    def remove_area(self, section: AreaSection) -> None:
        if section not in self.area_sections:
            return

        self.area_sections.remove(section)
        section.destroy()
        self._refresh_areas()

    def _refresh_areas(self) -> None:
        for index, section in enumerate(self.area_sections):
            section.grid_configure(row=index)
