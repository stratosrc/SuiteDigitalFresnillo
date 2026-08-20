"""Organigrama workspace controller implementation."""

from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
import logging
from pathlib import Path
import tkinter as tk
from tkinter import filedialog  # noqa: F401 - compatibility export for ui.main_frame

import customtkinter as ctk

from App_Organigrama.config.assets import REDO_ICON_PATH, TOOLBAR_LOGO_PATH, UNDO_ICON_PATH
from App_Organigrama.exporters import PdfOrgChartExporter
from App_Organigrama.models.document import OrgGridDocument
from App_Organigrama.models.history import DocumentHistory
from App_Organigrama.rendering.engine import RenderingEngine
from App_Organigrama.routing.manhattan_router import ManhattanRouter
from App_Organigrama.services.persistence import PersistenceManager
from App_Organigrama.ui.canvas import OrgGridCanvas
from App_Organigrama.ui.modals import show_help_dialog
from App_Organigrama.ui.theme import (
    APP_BACKGROUND,
    BORDER_COLOR,
    DARK_BACKGROUND,
    DARK_BACKGROUND_ACTIVE,
    DANGER_BUTTON,
    DANGER_BUTTON_ACTIVE,
    PRIMARY_BUTTON,
    PRIMARY_BUTTON_ACTIVE,
    PRIMARY_BUTTON_PRESSED,
    SURFACE_BACKGROUND,
    TEXT_DARK,
    TEXT_LIGHT,
    make_font,
)
from components.shared.images import load_ctk_image
from components.shared.entries import VariablePlaceholderEntry
from components.shared.accessibility import enable_visible_focus
from components.shared.project_lifecycle import ProjectLifecycle
from components.shared.progress_overlay import ProgressOverlay
from components.shared.shortcuts import bind_common_shortcuts
from components.shared.tooltip import Tooltip
from components.shared.topbar import TopbarButton, TopbarStyle, build_topbar

from App_Organigrama.ui.workspace_project import WorkspaceProjectMixin

LOGGER = logging.getLogger(__name__)
INVALID_FILENAME_CHARS = '<>:"/\\|?*'


class MainFrame(WorkspaceProjectMixin, ctk.CTkFrame):
    def __init__(self, master: ctk.CTk) -> None:
        super().__init__(master, fg_color=APP_BACKGROUND, corner_radius=0)
        self.master = master
        self.rendering_engine = RenderingEngine()
        self.persistence_manager = PersistenceManager()
        self.document = OrgGridDocument()
        self.document_history = DocumentHistory(self.document)
        self.project_lifecycle = ProjectLifecycle(
            "organigrama",
            snapshot=lambda: self.document.to_dict(),
            save=self.save_project,
        )
        self.router = ManhattanRouter(self.rendering_engine)
        self.pdf_exporter = PdfOrgChartExporter(self.rendering_engine, self.router)

        self.current_project_path: Path | None = None
        self.is_dirty = False
        self._metadata_sync_paused = False
        self._metadata_history_after_id: str | None = None
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="orgchart-worker")
        self._pending_task: Future | None = None
        self.toolbar_logo_image: ctk.CTkImage | None = None
        self.undo_icon: ctk.CTkImage | None = None
        self.redo_icon: ctk.CTkImage | None = None

        self.title_var = tk.StringVar(value=self.document.title)
        self.period_var = tk.StringVar(value=self.document.period)
        self.show_logos_var = tk.BooleanVar(value=self.document.show_logos)

        self._build_layout()
        self.progress_overlay = ProgressOverlay(self, color=PRIMARY_BUTTON)
        self._build_menu()
        self._bind_metadata()
        bind_common_shortcuts(
            self.master,
            new=self.new_project,
            open_=self.open_project,
            save=self.save_project,
            undo=self.undo,
            redo=self.redo,
        )
        self._update_history_buttons()
        self._update_window_title()
        self.project_lifecycle.start_autosave(self.master, self._restore_autosave)
        self.after_idle(lambda: enable_visible_focus(self))

    def _build_layout(self) -> None:
        self.pack(fill="both", expand=True)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        self._build_topbar()
        self._build_toolbar()
        self._build_metadata_panel()
        self._build_workspace()
        self._build_footer()

    def _build_menu(self) -> None:
        self.file_menu_command_indices: list[int] = []
        self.file_menu = tk.Menu(
            self.master,
            tearoff=0,
            bg=PRIMARY_BUTTON_PRESSED,
            fg=TEXT_LIGHT,
            activebackground=PRIMARY_BUTTON_ACTIVE,
            activeforeground=TEXT_LIGHT,
        )
        self.file_menu.add_command(label="Nuevo Proyecto", command=self.new_project)
        self.file_menu_command_indices.append(int(self.file_menu.index("end")))
        self.file_menu.add_command(label="Abrir Proyecto", command=self.open_project)
        self.file_menu_command_indices.append(int(self.file_menu.index("end")))
        self.recent_menu = tk.Menu(self.file_menu, tearoff=0)
        self.file_menu.add_cascade(label="Archivos recientes", menu=self.recent_menu)
        self.file_menu.add_command(label="Guardar proyecto", command=self.save_project)
        self.file_menu_command_indices.append(int(self.file_menu.index("end")))
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exportar PDF", command=self.export_pdf)
        self.file_menu_command_indices.append(int(self.file_menu.index("end")))
        self.file_menu.add_command(label="Exportar imagen", command=self.export_image)
        self.file_menu_command_indices.append(int(self.file_menu.index("end")))
        self._refresh_recent_menu()

    def _build_topbar(self) -> None:
        _, buttons = build_topbar(
            self,
            self._topbar_style(),
            (
                TopbarButton("file", "Archivo", self._show_file_menu, 0, width=78),
                TopbarButton("help", "Ayuda", self._show_help_dialog, 1),
                TopbarButton("exit", "Salir", self._confirm_exit, 3, danger=True),
            ),
        )
        self.file_button = buttons["file"]
        self.help_button = buttons["help"]

    @staticmethod
    def _topbar_style() -> TopbarStyle:
        return TopbarStyle(
            background=PRIMARY_BUTTON_PRESSED,
            primary=PRIMARY_BUTTON,
            primary_hover=PRIMARY_BUTTON_ACTIVE,
            danger=DANGER_BUTTON,
            danger_hover=DANGER_BUTTON_ACTIVE,
            text=TEXT_LIGHT,
            font=make_font(12),
        )

    def _build_toolbar(self) -> None:
        toolbar = ctk.CTkFrame(self, fg_color=DARK_BACKGROUND, corner_radius=0, height=118)
        toolbar.grid(row=1, column=0, sticky="ew")
        toolbar.grid_columnconfigure(1, weight=1)
        toolbar.grid_propagate(False)

        ctk.CTkLabel(
            toolbar,
            text="Gestión del diseño y estructura institucional",
            text_color=TEXT_LIGHT,
            font=make_font(18, "bold"),
        ).grid(row=0, column=0, padx=(16, 24), pady=12, sticky="w")

        self._load_toolbar_logo(toolbar)

    def _load_toolbar_logo(self, parent: ctk.CTkFrame) -> None:
        image = load_ctk_image(TOOLBAR_LOGO_PATH, (280, 110), crop_alpha=True)
        if image is None:
            return
        self.toolbar_logo_image = image
        ctk.CTkLabel(parent, image=self.toolbar_logo_image, text="").grid(
            row=0,
            column=1,
            padx=(16, 18),
            pady=14,
            sticky="e",
        )

    def _build_metadata_panel(self) -> None:
        panel = ctk.CTkFrame(self, fg_color=APP_BACKGROUND, corner_radius=0)
        panel.grid(row=2, column=0, sticky="ew", padx=24, pady=(4, 4))
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_columnconfigure(1, weight=1)

        self._build_labeled_entry(
            panel,
            label="Título del organigrama",
            variable=self.title_var,
            placeholder="Título del organigrama",
            column=0,
            padx=(0, 10),
        )
        self._build_labeled_entry(
            panel,
            label="Período",
            variable=self.period_var,
            placeholder="ej. Enero - Marzo 2026",
            column=1,
            padx=(0, 0),
        )

    def _build_labeled_entry(
        self,
        parent: ctk.CTkFrame,
        label: str,
        variable: tk.StringVar,
        placeholder: str,
        column: int,
        padx: tuple[int, int],
    ) -> None:
        ctk.CTkLabel(parent, text=label, text_color=TEXT_DARK, font=make_font(13, "bold")).grid(
            row=0,
            column=column,
            sticky="w",
        )
        entry = VariablePlaceholderEntry(
            parent,
            textvariable=variable,
            height=34,
            corner_radius=0,
            fg_color=SURFACE_BACKGROUND,
            border_color=BORDER_COLOR,
            text_color=TEXT_DARK,
            font=make_font(12),
            placeholder_text=placeholder,
        )
        entry.grid(row=1, column=column, sticky="ew", pady=(6, 0), padx=padx)
        if variable is self.title_var:
            self.title_entry = entry
        elif variable is self.period_var:
            self.period_entry = entry

    def _build_workspace(self) -> None:
        body = ctk.CTkFrame(self, fg_color=APP_BACKGROUND, corner_radius=0)
        body.grid(row=3, column=0, sticky="nsew", padx=24, pady=(4, 12))
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(body, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        tools = ctk.CTkFrame(header, fg_color="transparent")
        tools.grid(row=0, column=0, sticky="w")

        self.logos_checkbox = ctk.CTkCheckBox(
            tools,
            text="Escudos",
            variable=self.show_logos_var,
            command=self._toggle_logos,
            fg_color=PRIMARY_BUTTON,
            hover_color=DARK_BACKGROUND_ACTIVE,
            text_color=TEXT_DARK,
            corner_radius=0,
        )
        self.logos_checkbox.pack(side="left", padx=(0, 20))

        self.delete_button = ctk.CTkButton(
            tools,
            text="Eliminar selección",
            command=self._delete_selected,
            width=120,
            fg_color=DANGER_BUTTON,
            hover_color=DANGER_BUTTON_ACTIVE,
            state="disabled",
            corner_radius=0,
        )
        self.delete_button.pack(side="left", padx=(20, 0))

        self.reset_route_button = ctk.CTkButton(
            tools,
            text="Restaurar ruta automática",
            command=self._reset_selected_route,
            width=165,
            fg_color=PRIMARY_BUTTON,
            hover_color=PRIMARY_BUTTON_ACTIVE,
            state="disabled",
            corner_radius=0,
        )
        self.reset_route_button.pack(side="left", padx=(10, 0))

        nav = ctk.CTkFrame(header, fg_color="transparent")
        nav.grid(row=0, column=1, sticky="e")
        self._build_nav_button(nav, "↑", "up", 0, 1, 68)
        self._build_nav_button(nav, "←", "left", 1, 0, 58)
        self._build_nav_button(nav, "↓", "down", 1, 1, 68)
        self._build_nav_button(nav, "→", "right", 1, 2, 58)

        self.grid_canvas = OrgGridCanvas(
            body,
            document=self.document,
            rendering_engine=self.rendering_engine,
            router=self.router,
            on_selection_change=self._update_delete_state,
            on_zoom_change=self._update_zoom_label,
            on_document_change=self._record_document_change,
            corner_radius=0,
        )
        self.grid_canvas.grid(row=1, column=0, sticky="nsew", pady=(8, 0))

    def _build_nav_button(
        self,
        parent: ctk.CTkFrame,
        text: str,
        direction: str,
        row: int,
        column: int,
        width: int,
    ) -> None:
        button = ctk.CTkButton(
            parent,
            text=text,
            width=width,
            command=lambda: self.grid_canvas.scroll_view(direction),
            corner_radius=0,
        )
        button.grid(row=row, column=column, padx=2, pady=(3, 0) if row else 0)
        Tooltip(button, f"Desplazar vista hacia {direction}")

    def _build_footer(self) -> None:
        footer = ctk.CTkFrame(self, fg_color=DARK_BACKGROUND, corner_radius=0, height=34)
        footer.grid(row=4, column=0, sticky="ew")
        footer.grid_columnconfigure(1, weight=1)
        footer.grid_propagate(False)

        footer_actions = ctk.CTkFrame(footer, fg_color="transparent")
        footer_actions.grid(row=0, column=0, padx=(5, 0), pady=5, sticky="w")

        ctk.CTkButton(
            footer_actions,
            text="Enfocar último",
            command=self.grid_canvas.focus_last_node,
            height=25,
            width=130,
            fg_color=PRIMARY_BUTTON,
            hover_color=PRIMARY_BUTTON_ACTIVE,
            corner_radius=0,
            font=make_font(12, "bold"),
        ).pack(side="left")

        self.undo_icon = load_ctk_image(UNDO_ICON_PATH, (18, 18), crop_alpha=True)
        self.undo_button = ctk.CTkButton(
            footer_actions,
            text="",
            image=self.undo_icon,
            command=self.undo,
            height=25,
            width=34,
            fg_color=PRIMARY_BUTTON,
            hover_color=PRIMARY_BUTTON_ACTIVE,
            state="disabled",
            corner_radius=0,
            font=make_font(12, "bold"),
        )
        self.undo_button.pack(side="left", padx=(6, 3))
        Tooltip(self.undo_button, "Deshacer (Ctrl+Z)", show_when_disabled=True)

        self.redo_icon = load_ctk_image(REDO_ICON_PATH, (18, 18), crop_alpha=True)
        self.redo_button = ctk.CTkButton(
            footer_actions,
            text="",
            image=self.redo_icon,
            command=self.redo,
            height=25,
            width=34,
            fg_color=PRIMARY_BUTTON,
            hover_color=PRIMARY_BUTTON_ACTIVE,
            state="disabled",
            corner_radius=0,
            font=make_font(12, "bold"),
        )
        self.redo_button.pack(side="left", padx=(3, 0))
        Tooltip(self.redo_button, "Rehacer (Ctrl+Y)", show_when_disabled=True)

        zoom_frame = ctk.CTkFrame(footer, fg_color="transparent")
        zoom_frame.grid(row=0, column=2, padx=(12, 5), pady=5, sticky="e")
        ctk.CTkLabel(zoom_frame, text="Zoom", text_color=TEXT_LIGHT, font=make_font(12)).pack(side="left", padx=(0, 4))

        zoom_out_button = ctk.CTkButton(
            zoom_frame,
            text="-",
            command=lambda: self.grid_canvas.change_zoom("out"),
            width=32,
            height=25,
            corner_radius=0,
            
            font=make_font(13, "bold"),
        )
        zoom_out_button.pack(side="left", padx=(0, 4))
        Tooltip(zoom_out_button, "Alejar")

        self.zoom_label = ctk.CTkLabel(zoom_frame, text="100%", width=48, text_color=TEXT_LIGHT, font=make_font(12))
        self.zoom_label.pack(side="left", padx=(0, 4))

        zoom_in_button = ctk.CTkButton(
            zoom_frame,
            text="+",
            command=lambda: self.grid_canvas.change_zoom("in"),
            width=32,
            height=25,
            corner_radius=0,
            
            font=make_font(13, "bold"),
        )
        zoom_in_button.pack(side="left")
        Tooltip(zoom_in_button, "Acercar")

    def _bind_metadata(self) -> None:
        self.title_var.trace_add("write", self._sync_metadata)
        self.period_var.trace_add("write", self._sync_metadata)

    def _sync_metadata(self, *_args: object) -> None:
        if self._metadata_sync_paused:
            return

        active_entry = self.master.focus_get()
        cursor_entry = next(
            (
                entry
                for entry in (getattr(self, "title_entry", None), getattr(self, "period_entry", None))
                if entry is not None and active_entry in {entry, entry._entry}
            ),
            None,
        )
        cursor_position = cursor_entry.index(tk.INSERT) if cursor_entry is not None else None
        title = self.title_var.get().upper()
        period = self.period_var.get().upper()
        if title != self.title_var.get() or period != self.period_var.get():
            self._metadata_sync_paused = True
            self.title_var.set(title)
            self.period_var.set(period)
            self._metadata_sync_paused = False
            if cursor_entry is not None and cursor_position is not None:
                cursor_entry.icursor(min(cursor_position, len(cursor_entry.get())))
        self.document.title = title
        self.document.period = period
        if self._metadata_history_after_id is not None:
            self.after_cancel(self._metadata_history_after_id)
        self._metadata_history_after_id = self.after(500, self._commit_metadata_history)

    def _commit_metadata_history(self) -> None:
        self._metadata_history_after_id = None
        self._record_document_change()

    def _bind_history_shortcuts(self) -> None:
        self.master.bind("<Control-z>", self.undo, add=True)
        self.master.bind("<Control-y>", self.redo, add=True)
        self.master.bind("<Control-Shift-Z>", self.redo, add=True)

    def _toggle_logos(self) -> None:
        self.document.show_logos = self.show_logos_var.get()
        self.grid_canvas.set_show_logos(self.document.show_logos)

    def _show_file_menu(self) -> None:
        self._refresh_recent_menu()
        self.file_menu.tk_popup(
            self.file_button.winfo_rootx(),
            self.file_button.winfo_rooty() + self.file_button.winfo_height(),
        )
        self.file_menu.grab_release()

    def _show_help_dialog(self) -> None:
        show_help_dialog(self)

    def _update_delete_state(self, has_selection: bool) -> None:
        self.delete_button.configure(state="normal" if has_selection else "disabled")
        if hasattr(self, "grid_canvas"):
            self.reset_route_button.configure(
                state="normal" if self.grid_canvas.can_reset_selected_route() else "disabled"
            )

    def _delete_selected(self) -> None:
        self.grid_canvas.delete_selected_item()

    def _reset_selected_route(self) -> None:
        self.grid_canvas.reset_selected_route()

    def _update_zoom_label(self, zoom_percent: int | None = None) -> None:
        percent = self.grid_canvas.zoom_percent() if zoom_percent is None else zoom_percent
        self.zoom_label.configure(text=f"{percent}%")
