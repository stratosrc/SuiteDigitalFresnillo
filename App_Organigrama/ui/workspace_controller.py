"""Organigrama workspace controller implementation."""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from copy import deepcopy
import logging
from pathlib import Path
import tempfile
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk

from App_Organigrama.config.assets import REDO_ICON_PATH, TOOLBAR_LOGO_PATH, UNDO_ICON_PATH
from App_Organigrama.exporters import PdfOrgChartExporter
from App_Organigrama.models.document import OrgGridDocument
from App_Organigrama.models.history import DocumentHistory
from App_Organigrama.rendering.engine import RenderingEngine
from App_Organigrama.routing.manhattan_router import ManhattanRouter
from App_Organigrama.services.image_exporter import export_pdf_as_image
from App_Organigrama.services.persistence import PersistenceManager
from App_Organigrama.ui.canvas import OrgGridCanvas
from App_Organigrama.ui.modals import OrientationDialog, show_help_dialog
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
from components.shared.platform import (
    IS_MACOS,
    PRIMARY_MODIFIER_LABEL,
    bind_primary_shortcut,
)
from components.shared.project_lifecycle import ProjectLifecycle
from components.shared.progress_overlay import ProgressOverlay
from components.shared.shortcuts import bind_common_shortcuts
from components.shared.tooltip import Tooltip
from components.shared.topbar import TopbarButton, TopbarStyle, build_topbar

LOGGER = logging.getLogger(__name__)
INVALID_FILENAME_CHARS = '<>:"/\\|?*'


class MainFrame(ctk.CTkFrame):
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
        Tooltip(
            self.undo_button,
            f"Deshacer ({PRIMARY_MODIFIER_LABEL}+Z)",
            show_when_disabled=True,
        )

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
        Tooltip(
            self.redo_button,
            f"Rehacer ({PRIMARY_MODIFIER_LABEL}+Y)",
            show_when_disabled=True,
        )

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
        bind_primary_shortcut(self.master, "z", self.undo, add=True)
        bind_primary_shortcut(self.master, "y", self.redo, add=True)
        bind_primary_shortcut(self.master, "z", self.redo, shift=True, add=True)

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

    def new_project(self) -> None:
        if self._is_operation_running():
            self._show_operation_warning()
            return
        if not self._confirm_discard_changes():
            return

        self.current_project_path = None
        self.document = OrgGridDocument()
        self._load_document_into_ui(self.document)
        self._reset_document_history(mark_saved=True)
        self.project_lifecycle.reset(mark_saved=True)

    def open_project(self) -> None:
        if self._is_operation_running():
            self._show_operation_warning()
            return
        if not self._confirm_discard_changes():
            return

        source_path = filedialog.askopenfilename(
            parent=self,
            title="Abrir proyecto",
            filetypes=[
                ("Proyecto Organigrama", "*.og"),
                ("Proyecto JSON anterior", "*.json"),
                ("Todos los archivos", "*.*"),
            ],
        )
        if not source_path:
            return

        self._start_project_load(source_path)

    def save_project(self) -> bool:
        if self._is_operation_running():
            self._show_operation_warning()
            return False
        self._commit_pending_metadata_history()
        if self.current_project_path is None:
            return self.save_project_as()

        try:
            self._sync_metadata()
            self.persistence_manager.save(self.document, self.current_project_path)
        except Exception as error:  # noqa: BLE001
            LOGGER.exception("Unable to save organigram project")
            messagebox.showerror(
                "No se pudo guardar",
                f"No fue posible guardar el proyecto:\n{error}",
                parent=self,
            )
            return False
        self.document_history.mark_saved(self.document)
        self.project_lifecycle.mark_saved(self.current_project_path)
        self._set_dirty(False)
        self._update_history_buttons()
        messagebox.showinfo("Proyecto guardado", f"Proyecto guardado en:\n{self.current_project_path}", parent=self)
        return True

    def save_project_as(self) -> bool:
        self._commit_pending_metadata_history()
        self._sync_metadata()
        target_path = filedialog.asksaveasfilename(
            parent=self,
            title="Guardar proyecto como",
            defaultextension=".og",
            filetypes=[("Proyecto Organigrama", "*.og"), ("Todos los archivos", "*.*")],
            initialfile=self._default_export_filename(".og"),
        )
        if not target_path:
            return False

        candidate_path = Path(target_path)
        try:
            self.persistence_manager.save(self.document, candidate_path)
        except Exception as error:  # noqa: BLE001
            LOGGER.exception("Unable to save organigram project")
            messagebox.showerror(
                "No se pudo guardar",
                f"No fue posible guardar el proyecto:\n{error}",
                parent=self,
            )
            return False
        self.current_project_path = candidate_path
        self.document_history.mark_saved(self.document)
        self.project_lifecycle.mark_saved(self.current_project_path)
        self._set_dirty(False)
        self._update_history_buttons()
        messagebox.showinfo("Proyecto guardado", f"Proyecto guardado en:\n{self.current_project_path}", parent=self)
        return True

    def export_pdf(self) -> None:
        if not self._can_start_export():
            return
        target_path = filedialog.asksaveasfilename(
            parent=self,
            title="Exportar organigrama como PDF",
            defaultextension=".pdf",
            filetypes=[("Archivo PDF", "*.pdf"), ("Todos los archivos", "*.*")],
            initialfile=self._default_export_filename(".pdf"),
        )
        if not target_path:
            return

        export_document = deepcopy(self.document)
        self._run_background_task(lambda: self.pdf_exporter.export(export_document, target_path), success_title="PDF exportado")

    def export_image(self) -> None:
        if not self._can_start_export():
            return
        OrientationDialog(self, self._export_image_for_orientation)

    def _export_image_for_orientation(self, orientation: str) -> None:
        target_path = filedialog.asksaveasfilename(
            parent=self,
            title="Exportar organigrama como imagen",
            defaultextension=".png",
            filetypes=[("Imagen PNG", "*.png"), ("Imagen JPG", "*.jpg"), ("Imagen JPEG", "*.jpeg")],
            initialfile=self._default_export_filename(".png"),
        )
        if not target_path:
            return

        extension = Path(target_path).suffix.lower()
        if extension not in {".png", ".jpg", ".jpeg"}:
            messagebox.showerror("Extensión no válida", "La imagen debe guardarse como .png, .jpg o .jpeg.", parent=self)
            return

        export_document = deepcopy(self.document)
        export_document.page_orientation = orientation

        def task() -> Path:
            temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            temp_pdf_path = Path(temp_pdf.name)
            temp_pdf.close()
            try:
                self.pdf_exporter.export(
                    export_document,
                    temp_pdf_path,
                    digital=False,
                )
                return export_pdf_as_image(temp_pdf_path, target_path, dpi=300)
            finally:
                if temp_pdf_path.exists():
                    temp_pdf_path.unlink(missing_ok=True)

        self._run_background_task(task, success_title="Imagen exportada")

    def _run_background_task(self, task: Callable[[], Path], success_title: str) -> None:
        self._set_busy_state("disabled")
        message = "Generando imagen..." if "Imagen" in success_title else "Generando PDF..."
        self.progress_overlay.show(message)
        if IS_MACOS:
            self.update_idletasks()
            try:
                result_path = task()
                messagebox.showinfo(
                    success_title,
                    f"Archivo generado correctamente en:\n{result_path}",
                    parent=self,
                )
            except Exception as error:  # noqa: BLE001
                LOGGER.exception("Unable to complete org chart export task")
                messagebox.showerror(
                    "Error",
                    f"No se pudo completar la operación:\n{error}",
                    parent=self,
                )
            finally:
                self.progress_overlay.hide()
                self._set_busy_state("normal")
            return

        future = self._executor.submit(task)
        self._pending_task = future
        self.after(120, lambda: self._poll_task(future, success_title))

    def _poll_task(self, future: Future[Path], success_title: str) -> None:
        if not future.done():
            self.after(120, lambda: self._poll_task(future, success_title))
            return

        try:
            if future.cancelled():
                messagebox.showinfo("Exportación cancelada", "La exportación fue cancelada.", parent=self)
                return
            result_path = future.result()
            messagebox.showinfo(success_title, f"Archivo generado correctamente en:\n{result_path}", parent=self)
        except Exception as error:  # noqa: BLE001
            LOGGER.exception("Unable to complete org chart background task")
            messagebox.showerror("Error", f"No se pudo completar la operación:\n{error}", parent=self)
        finally:
            if self._pending_task is future:
                self._pending_task = None
            self.progress_overlay.hide()
            self._set_busy_state("normal")

    def _start_project_load(
        self,
        source_path: str | Path,
        *,
        remove_recent_on_error: bool = False,
    ) -> None:
        self._set_busy_state("disabled")
        self.progress_overlay.show("Cargando proyecto...")
        future = self._executor.submit(self.persistence_manager.load, source_path)
        self._pending_task = future
        self.after(
            120,
            lambda: self._poll_project_load(
                future,
                Path(source_path),
                remove_recent_on_error,
            ),
        )

    def _poll_project_load(
        self,
        future: Future,
        source_path: Path,
        remove_recent_on_error: bool,
    ) -> None:
        if not future.done():
            self.after(
                120,
                lambda: self._poll_project_load(
                    future,
                    source_path,
                    remove_recent_on_error,
                ),
            )
            return

        try:
            document = future.result()
            self.document = document
            self.current_project_path = source_path
            self._load_document_into_ui(document)
            self._reset_document_history(mark_saved=True)
            self.project_lifecycle.mark_saved(source_path)
        except Exception as error:  # noqa: BLE001
            if remove_recent_on_error:
                self.project_lifecycle.recent_files.remove(source_path)
            LOGGER.exception("Unable to load org chart project from %s", source_path)
            messagebox.showerror(
                "No se pudo abrir",
                f"No fue posible cargar el proyecto:\n{error}",
                parent=self,
            )
        finally:
            if self._pending_task is future:
                self._pending_task = None
            self.progress_overlay.hide()
            self._set_busy_state("normal")

    def _is_operation_running(self) -> bool:
        return self._pending_task is not None

    def _can_start_export(self) -> bool:
        if not self.document.nodes:
            messagebox.showwarning("Organigrama vacío", "Agrega al menos un nodo antes de exportar.", parent=self)
            return False
        if self._is_operation_running():
            self._show_operation_warning()
            return False
        return True

    def _show_operation_warning(self) -> None:
        messagebox.showwarning(
            "Operación en curso",
            "Espera a que termine la operación actual antes de iniciar otra.",
            parent=self,
        )

    def _set_busy_state(self, state: str) -> None:
        self.file_button.configure(state=state)
        for index in self.file_menu_command_indices:
            self.file_menu.entryconfig(index, state=state)

    def _confirm_discard_changes(self) -> bool:
        return self.project_lifecycle.confirm_discard(self, "continuar")

    def _record_document_change(self) -> None:
        if self.document_history.record(self.document):
            self._set_dirty(self.document_history.is_dirty)
            self._update_history_buttons()

    def _commit_pending_metadata_history(self) -> None:
        if self._metadata_history_after_id is not None:
            self.after_cancel(self._metadata_history_after_id)
            self._commit_metadata_history()

    def undo(self, _event: tk.Event | None = None) -> str | None:
        restored = self.document_history.undo()
        if restored is None:
            return "break" if _event is not None else None
        self.document = restored
        self._load_document_into_ui(restored, preserve_viewport=True)
        self._set_dirty(self.document_history.is_dirty)
        self._update_history_buttons()
        return "break" if _event is not None else None

    def redo(self, _event: tk.Event | None = None) -> str | None:
        restored = self.document_history.redo()
        if restored is None:
            return "break" if _event is not None else None
        self.document = restored
        self._load_document_into_ui(restored, preserve_viewport=True)
        self._set_dirty(self.document_history.is_dirty)
        self._update_history_buttons()
        return "break" if _event is not None else None

    def _reset_document_history(self, *, mark_saved: bool) -> None:
        self.document_history.reset(self.document, mark_saved=mark_saved)
        self._set_dirty(self.document_history.is_dirty)
        self._update_history_buttons()

    def _update_history_buttons(self) -> None:
        if not hasattr(self, "undo_button"):
            return
        self.undo_button.configure(state="normal" if self.document_history.can_undo else "disabled")
        self.redo_button.configure(state="normal" if self.document_history.can_redo else "disabled")

    def _set_dirty(self, value: bool) -> None:
        self.is_dirty = value
        self._update_window_title()

    def _update_window_title(self) -> None:
        marker = " *" if self.project_lifecycle.is_dirty else ""
        self.master.title(f"Organigramas{marker}")

    def _default_export_filename(self, extension: str) -> str:
        title = self.document.title.strip()
        if not title:
            base_name = "organigrama"
        else:
            sanitized = "".join("_" if char in INVALID_FILENAME_CHARS else char for char in title)
            base_name = " ".join(sanitized.split()).strip(" .") or "organigrama"
        normalized_extension = extension if extension.startswith(".") else f".{extension}"
        return f"{base_name}{normalized_extension}"

    def _load_document_into_ui(
        self,
        document: OrgGridDocument,
        *,
        preserve_viewport: bool = False,
    ) -> None:
        document.title = document.title.upper()
        document.period = document.period.upper()
        self._metadata_sync_paused = True
        self.title_var.set(document.title)
        self.period_var.set(document.period)
        self.show_logos_var.set(document.show_logos)
        self._metadata_sync_paused = False
        self.grid_canvas.set_document(document)
        if preserve_viewport:
            self._update_zoom_label()
        else:
            self.grid_canvas.zoom = 1.0
            self.grid_canvas.fit_document_to_content_top()
            self._update_zoom_label(100)
        self._update_delete_state(False)
        self._update_window_title()

    def _confirm_exit(self) -> None:
        if self._is_operation_running():
            self._show_operation_warning()
            return

        if not self.project_lifecycle.confirm_discard(self, "salir"):
            return
        self.master.destroy()

    def _refresh_recent_menu(self) -> None:
        if not hasattr(self, "recent_menu"):
            return
        self.recent_menu.delete(0, tk.END)
        recent_paths = self.project_lifecycle.recent_files.list()
        if not recent_paths:
            self.recent_menu.add_command(label="Sin archivos recientes", state="disabled")
            return
        for path in recent_paths:
            self.recent_menu.add_command(
                label=str(path),
                command=lambda selected=path: self._open_project_path(selected),
            )

    def _open_project_path(self, source_path: str | Path) -> None:
        if self._is_operation_running():
            self._show_operation_warning()
            return
        if not self._confirm_discard_changes():
            return
        self._start_project_load(source_path, remove_recent_on_error=True)

    def _restore_autosave(self, snapshot: object, path: Path | None) -> None:
        if not isinstance(snapshot, dict):
            return
        self.document = self.persistence_manager.from_dict(snapshot)
        self.current_project_path = path
        self._load_document_into_ui(self.document)
        self._reset_document_history(mark_saved=False)

    def destroy(self) -> None:
        self.project_lifecycle.stop_autosave()
        self._executor.shutdown(wait=False, cancel_futures=True)
        super().destroy()
