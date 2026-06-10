from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
import tempfile
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk
from PIL import Image, ImageOps

from App_Organigrama.export.pdf_exporter import PdfOrgChartExporter
from App_Organigrama.models.document import OrgGridDocument
from App_Organigrama.rendering.engine import RenderingEngine
from App_Organigrama.routing.manhattan_router import ManhattanRouter
from App_Organigrama.services.assets import TOOLBAR_LOGO_PATH
from App_Organigrama.services.image_exporter import export_pdf_as_image
from App_Organigrama.services.persistence_manager import PersistenceManager
from App_Organigrama.ui.dialogs import OrientationDialog
from App_Organigrama.ui.grid_canvas import OrgGridCanvas
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
    BUTTON_BG,
    BUTTON_BG_ACTIVE,
    make_font,
)
from components.styles.styles import BUTTON_BG_PRESSED

class MainFrame(ctk.CTkFrame):
    def __init__(self, master: ctk.CTk) -> None:
        super().__init__(master, fg_color=APP_BACKGROUND, corner_radius=0)
        self.master = master
        self.rendering_engine = RenderingEngine()
        self.persistence_manager = PersistenceManager()
        self.document = OrgGridDocument()
        self.router = ManhattanRouter(self.rendering_engine)
        self.pdf_exporter = PdfOrgChartExporter(self.rendering_engine, self.router)

        self.current_project_path: Path | None = None
        self.is_dirty = False
        self._metadata_sync_paused = False
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="orgchart-worker")
        self._pending_task: Future[Path] | None = None
        self.toolbar_logo_image: ctk.CTkImage | None = None

        self.title_var = tk.StringVar(value=self.document.title)
        self.period_var = tk.StringVar(value=self.document.period)
        self.show_logos_var = tk.BooleanVar(value=self.document.show_logos)
        self.block_mode_var = tk.BooleanVar(value=False)

        self._build_layout()
        self._build_menu()
        self._bind_metadata()
        self._update_window_title()

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
        self.file_menu.add_command(label="Nuevo", command=self.new_project)
        self.file_menu_command_indices.append(int(self.file_menu.index("end")))
        self.file_menu.add_command(label="Abrir proyecto", command=self.open_project)
        self.file_menu_command_indices.append(int(self.file_menu.index("end")))
        self.file_menu.add_command(label="Guardar proyecto", command=self.save_project)
        self.file_menu_command_indices.append(int(self.file_menu.index("end")))
        self.file_menu.add_command(label="Guardar proyecto como", command=self.save_project_as)
        self.file_menu_command_indices.append(int(self.file_menu.index("end")))
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exportar PDF", command=self.export_pdf)
        self.file_menu_command_indices.append(int(self.file_menu.index("end")))
        self.file_menu.add_command(label="Exportar imagen", command=self.export_image)
        self.file_menu_command_indices.append(int(self.file_menu.index("end")))

    def _build_topbar(self) -> None:
        topbar = ctk.CTkFrame(self, fg_color=PRIMARY_BUTTON_PRESSED, corner_radius=0, height=24)
        topbar.grid(row=0, column=0, sticky="ew")
        topbar.grid_columnconfigure(2, weight=1)
        topbar.grid_propagate(False)

        self.file_button = ctk.CTkButton(
            topbar,
            text="Archivo",
            command=self._show_file_menu,
            height=24,
            width=78,
            corner_radius=0,
            fg_color=PRIMARY_BUTTON,
            hover_color=PRIMARY_BUTTON_ACTIVE,
            text_color=TEXT_LIGHT,
            font=make_font(12),
        )
        self.file_button.grid(row=0, column=0, padx=(0, 4), sticky="w")

        exit_button = ctk.CTkButton(
            topbar,
            text="Salir",
            command=self._confirm_exit,
            height=24,
            width=72,
            corner_radius=0,
            fg_color=DANGER_BUTTON,
            hover_color=DANGER_BUTTON_ACTIVE,
            text_color=TEXT_LIGHT,
            font=make_font(12),
        )
        exit_button.grid(row=0, column=3, padx=(4, 0), sticky="e")

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
        if not TOOLBAR_LOGO_PATH.exists():
            return
        image = Image.open(TOOLBAR_LOGO_PATH)
        if image.mode != "RGBA":
            image = image.convert("RGBA")
        active_box = image.getbbox()
        if active_box:
            image = image.crop(active_box)
        resized = ImageOps.contain(image, (280, 110), Image.Resampling.LANCZOS)
        self.toolbar_logo_image = ctk.CTkImage(light_image=resized, dark_image=resized, size=resized.size)
        ctk.CTkLabel(parent, image=self.toolbar_logo_image, text="").grid(
            row=0,
            column=1,
            padx=(16, 18),
            pady=14,
            sticky="e",
        )

    def _build_metadata_panel(self) -> None:
        panel = ctk.CTkFrame(self, fg_color=APP_BACKGROUND, corner_radius=0)
        panel.grid(row=2, column=0, sticky="ew", padx=24, pady=(18, 10))
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
            placeholder="Septiembre - Diciembre 2026",
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
        ctk.CTkEntry(
            parent,
            textvariable=variable,
            height=34,
            corner_radius=0,
            fg_color=SURFACE_BACKGROUND,
            border_color=BORDER_COLOR,
            text_color=TEXT_DARK,
            font=make_font(12),
            placeholder_text=placeholder,
        ).grid(row=1, column=column, sticky="ew", pady=(6, 0), padx=padx)

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

        self.block_checkbox = ctk.CTkCheckBox(
            tools,
            text="Modo: Bloquear camino",
            variable=self.block_mode_var,
            command=self._toggle_block_mode,
            fg_color=PRIMARY_BUTTON,
            hover_color=DARK_BACKGROUND_ACTIVE,
            text_color=TEXT_DARK,
            corner_radius=0,
        )
        self.block_checkbox.pack(side="left", padx=(0, 20))

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
            on_document_change=self._mark_dirty,
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
        ctk.CTkButton(
            parent,
            text=text,
            width=width,
            command=lambda: self.grid_canvas.scroll_view(direction),
            corner_radius=0,
        ).grid(row=row, column=column, padx=2, pady=(3, 0) if row else 0)

    def _build_footer(self) -> None:
        footer = ctk.CTkFrame(self, fg_color=DARK_BACKGROUND, corner_radius=0, height=34)
        footer.grid(row=4, column=0, sticky="ew")
        footer.grid_columnconfigure(1, weight=1)
        footer.grid_propagate(False)

        ctk.CTkButton(
            footer,
            text="Enfocar último",
            command=self.grid_canvas.focus_last_node,
            height=25,
            width=130,
            corner_radius=0,
            
            font=make_font(12, "bold"),
        ).grid(row=0, column=0, padx=(5, 0), pady=5, sticky="w")

        zoom_frame = ctk.CTkFrame(footer, fg_color="transparent")
        zoom_frame.grid(row=0, column=2, padx=(12, 5), pady=5, sticky="e")
        ctk.CTkLabel(zoom_frame, text="Zoom", text_color=TEXT_LIGHT, font=make_font(12)).pack(side="left", padx=(0, 4))

        ctk.CTkButton(
            zoom_frame,
            text="-",
            command=lambda: self.grid_canvas.change_zoom("out"),
            width=32,
            height=25,
            corner_radius=0,
            
            font=make_font(13, "bold"),
        ).pack(side="left", padx=(0, 4))

        self.zoom_label = ctk.CTkLabel(zoom_frame, text="100%", width=48, text_color=TEXT_LIGHT, font=make_font(12))
        self.zoom_label.pack(side="left", padx=(0, 4))

        ctk.CTkButton(
            zoom_frame,
            text="+",
            command=lambda: self.grid_canvas.change_zoom("in"),
            width=32,
            height=25,
            corner_radius=0,
            
            font=make_font(13, "bold"),
        ).pack(side="left")

    def _bind_metadata(self) -> None:
        self.title_var.trace_add("write", self._sync_metadata)
        self.period_var.trace_add("write", self._sync_metadata)

    def _sync_metadata(self, *_args: object) -> None:
        if self._metadata_sync_paused:
            return

        self.document.title = self.title_var.get()
        self.document.period = self.period_var.get()
        self._mark_dirty()

    def _toggle_logos(self) -> None:
        self.document.show_logos = self.show_logos_var.get()
        self.grid_canvas.set_show_logos(self.document.show_logos)

    def _toggle_block_mode(self) -> None:
        self.grid_canvas.set_block_mode(self.block_mode_var.get())

    def _show_file_menu(self) -> None:
        self.file_menu.tk_popup(
            self.file_button.winfo_rootx(),
            self.file_button.winfo_rooty() + self.file_button.winfo_height(),
        )
        self.file_menu.grab_release()

    def _update_delete_state(self, has_selection: bool) -> None:
        self.delete_button.configure(state="normal" if has_selection else "disabled")

    def _delete_selected(self) -> None:
        self.grid_canvas.delete_selected_item()

    def _update_zoom_label(self, zoom_percent: int | None = None) -> None:
        percent = self.grid_canvas.zoom_percent() if zoom_percent is None else zoom_percent
        self.zoom_label.configure(text=f"{percent}%")

    def new_project(self) -> None:
        if not self._confirm_discard_changes():
            return

        self.current_project_path = None
        self.document = OrgGridDocument()
        self._load_document_into_ui(self.document)
        self._set_dirty(False)

    def open_project(self) -> None:
        if not self._confirm_discard_changes():
            return

        source_path = filedialog.askopenfilename(
            parent=self,
            title="Abrir proyecto",
            filetypes=[("Proyecto JSON", "*.json"), ("Todos los archivos", "*.*")],
        )
        if not source_path:
            return

        self.document = self.persistence_manager.load(source_path)
        self.current_project_path = Path(source_path)
        self._load_document_into_ui(self.document)
        self._set_dirty(False)

    def save_project(self) -> None:
        if self.current_project_path is None:
            self.save_project_as()
            return

        self._sync_metadata()
        self.persistence_manager.save(self.document, self.current_project_path)
        self._set_dirty(False)
        messagebox.showinfo("Proyecto guardado", f"Proyecto guardado en:\n{self.current_project_path}", parent=self)

    def save_project_as(self) -> None:
        self._sync_metadata()
        target_path = filedialog.asksaveasfilename(
            parent=self,
            title="Guardar proyecto como",
            defaultextension=".json",
            filetypes=[("Proyecto JSON", "*.json"), ("Todos los archivos", "*.*")],
            initialfile="organigrama.json",
        )
        if not target_path:
            return

        self.current_project_path = Path(target_path)
        self.persistence_manager.save(self.document, self.current_project_path)
        self._set_dirty(False)
        messagebox.showinfo("Proyecto guardado", f"Proyecto guardado en:\n{self.current_project_path}", parent=self)

    def export_pdf(self) -> None:
        if not self._can_start_export():
            return
        OrientationDialog(self, self._export_pdf_for_orientation)

    def _export_pdf_for_orientation(self, orientation: str) -> None:
        self.document.page_orientation = orientation
        target_path = filedialog.asksaveasfilename(
            parent=self,
            title="Guardar organigrama como PDF",
            defaultextension=".pdf",
            filetypes=[("Archivo PDF", "*.pdf"), ("Todos los archivos", "*.*")],
            initialfile="organigrama.pdf",
        )
        if not target_path:
            return

        self._run_background_task(lambda: self.pdf_exporter.export(self.document, target_path), success_title="PDF exportado")

    def export_image(self) -> None:
        if not self._can_start_export():
            return
        OrientationDialog(self, self._export_image_for_orientation)

    def _export_image_for_orientation(self, orientation: str) -> None:
        self.document.page_orientation = orientation
        target_path = filedialog.asksaveasfilename(
            parent=self,
            title="Exportar organigrama como imagen",
            defaultextension=".png",
            filetypes=[("Imagen PNG", "*.png"), ("Imagen JPG", "*.jpg"), ("Imagen JPEG", "*.jpeg")],
            initialfile="organigrama.png",
        )
        if not target_path:
            return

        extension = Path(target_path).suffix.lower()
        if extension not in {".png", ".jpg", ".jpeg"}:
            messagebox.showerror("Extensión no válida", "La imagen debe guardarse como .png, .jpg o .jpeg.", parent=self)
            return

        def task() -> Path:
            temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            temp_pdf_path = Path(temp_pdf.name)
            temp_pdf.close()
            try:
                self.pdf_exporter.export(self.document, temp_pdf_path)
                return export_pdf_as_image(temp_pdf_path, target_path, dpi=300)
            finally:
                if temp_pdf_path.exists():
                    temp_pdf_path.unlink(missing_ok=True)

        self._run_background_task(task, success_title="Imagen exportada")

    def _run_background_task(self, task: Callable[[], Path], success_title: str) -> None:
        self._set_busy_state("disabled")
        future = self._executor.submit(task)
        self._pending_task = future
        self.after(120, lambda: self._poll_task(future, success_title))

    def _poll_task(self, future: Future[Path], success_title: str) -> None:
        if not future.done():
            self.after(120, lambda: self._poll_task(future, success_title))
            return

        try:
            result_path = future.result()
            messagebox.showinfo(success_title, f"Archivo generado correctamente en:\n{result_path}", parent=self)
        except Exception as error:  # noqa: BLE001
            messagebox.showerror("Error", f"No se pudo completar la operación:\n{error}", parent=self)
        finally:
            if self._pending_task is future:
                self._pending_task = None
            self._set_busy_state("normal")

    def _is_operation_running(self) -> bool:
        return self._pending_task is not None and not self._pending_task.done()

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
            "Espera a que termine la exportación actual antes de iniciar otra.",
            parent=self,
        )

    def _set_busy_state(self, state: str) -> None:
        self.file_button.configure(state=state)
        for index in self.file_menu_command_indices:
            self.file_menu.entryconfig(index, state=state)

    def _confirm_discard_changes(self) -> bool:
        if not self.is_dirty:
            return True
        return messagebox.askyesno(
            "Cambios sin guardar",
            "Hay cambios sin guardar. ¿Desea continuar y descartarlos?",
            parent=self,
        )

    def _mark_dirty(self) -> None:
        self._set_dirty(True)

    def _set_dirty(self, value: bool) -> None:
        self.is_dirty = value
        self._update_window_title()

    def _update_window_title(self) -> None:
        suffix = " *" if self.is_dirty else ""
        project_name = self.current_project_path.name if self.current_project_path is not None else "sin_guardar.json"
        self.master.title(f"Organigramas | {project_name}{suffix}")

    def _load_document_into_ui(self, document: OrgGridDocument) -> None:
        self._metadata_sync_paused = True
        self.title_var.set(document.title)
        self.period_var.set(document.period)
        self.show_logos_var.set(document.show_logos)
        self.block_mode_var.set(False)
        self._metadata_sync_paused = False
        self.grid_canvas.set_document(document)
        self.grid_canvas.zoom = 1.0
        self.grid_canvas.pan_x = 560.0
        self.grid_canvas.pan_y = 320.0
        self.grid_canvas.set_block_mode(False)
        self.grid_canvas.request_redraw()
        self._update_zoom_label(100)
        self._update_delete_state(False)
        self._update_window_title()

    def _confirm_exit(self) -> None:
        if self._is_operation_running():
            self._show_operation_warning()
            return
        if not self._confirm_discard_changes():
            return
        self.master.destroy()

    def destroy(self) -> None:
        self._executor.shutdown(wait=False, cancel_futures=True)
        super().destroy()
