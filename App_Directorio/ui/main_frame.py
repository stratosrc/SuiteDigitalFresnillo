import tkinter as tk
import logging
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import asdict
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from App_Directorio.config import (
    APP_DESCRIPTION,
    APP_TITLE,
    DIRECTORY_ICON_PATH,
)
from App_Directorio.services.persistence import DirectoryPersistenceManager
from App_Directorio.services.pdf_exporter import DirectoryPdfExporter
from App_Directorio.ui.dialogs import show_help_dialog
from App_Directorio.ui.forms import DirectoryFormFrame
from App_Directorio.ui.theme import (
    APP_BACKGROUND,
    DARK_BACKGROUND,
    DANGER_BUTTON,
    DANGER_BUTTON_ACTIVE,
    HEADER_LOGO_SIZE,
    PRIMARY_BUTTON,
    PRIMARY_BUTTON_ACTIVE,
    PRIMARY_BUTTON_PRESSED,
    SURFACE_BACKGROUND,
    TEXT_LIGHT,
    make_font,
)
from components.shared.images import load_ctk_image
from App_Directorio.ui.accessibility import enable_visible_focus
from components.shared.project_lifecycle import ProjectLifecycle
from components.shared.progress_overlay import ProgressOverlay
from components.shared.shortcuts import bind_common_shortcuts
from components.shared.topbar import TopbarButton, TopbarStyle, build_topbar

LOGGER = logging.getLogger(__name__)


class DirectoryMainFrame(ctk.CTkFrame):
    def __init__(self, master: ctk.CTk) -> None:
        super().__init__(master, fg_color=APP_BACKGROUND, corner_radius=0)
        self.master = master
        self.header_icon_image: ctk.CTkImage | None = None
        self.current_project_path: Path | None = None
        self.persistence_manager = DirectoryPersistenceManager()
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="directory-worker")
        self._pending_export: Future[Path] | None = None
        self._build_layout()
        self.export_progress_overlay = ProgressOverlay(self, color=PRIMARY_BUTTON)
        self.project_lifecycle = ProjectLifecycle(
            "directorio",
            snapshot=lambda: asdict(self.directory_form.get_report_data()),
            save=self.save_project,
        )
        self._build_menu()
        self._history: list[dict] = [asdict(self.directory_form.get_report_data())]
        self._redo_history: list[dict] = []
        self._history_paused = False
        self._history_after_id: str | None = None
        self.directory_form.bind("<<DirectoryChanged>>", self._on_directory_changed)
        bind_common_shortcuts(
            self.master,
            new=self.new_project,
            open_=self.open_project,
            save=self.save_project,
            undo=self.undo,
            redo=self.redo,
        )
        self.project_lifecycle.start_autosave(self.master, self._restore_autosave)
        self.after_idle(lambda: enable_visible_focus(self))

    def _build_layout(self) -> None:
        self.pack(fill="both", expand=True)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._build_topbar()
        self._build_header()
        self._build_form_body()

    def _build_menu(self) -> None:
        self.file_menu = tk.Menu(
            self.master,
            tearoff=0,
            bg=PRIMARY_BUTTON_PRESSED,
            fg=TEXT_LIGHT,
            activebackground=PRIMARY_BUTTON_ACTIVE,
            activeforeground=TEXT_LIGHT,
        )
        self.file_menu.add_command(label="Nuevo Proyecto", command=self.new_project)
        self.file_menu.add_command(label="Abrir Proyecto", command=self.open_project)
        self.recent_menu = tk.Menu(self.file_menu, tearoff=0)
        self.file_menu.add_cascade(label="Archivos recientes", menu=self.recent_menu)
        self.file_menu.add_command(label="Guardar proyecto", command=self.save_project)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exportar PDF", command=self.export_pdf)
        self._refresh_recent_menu()

    def _build_topbar(self) -> None:
        _, buttons = build_topbar(
            self,
            self._topbar_style(),
            (
                TopbarButton("file", "Archivo", self._show_file_menu, 0, width=78),
                TopbarButton("help", "Ayuda", self._show_help_dialog, 1),
                TopbarButton("exit", "Salir", self.confirm_exit, 3, danger=True),
            ),
        )
        self.file_button = buttons["file"]
        self.help_button = buttons["help"]
        self.exit_button = buttons["exit"]

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

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color=DARK_BACKGROUND, corner_radius=0, height=118)
        header.grid(row=1, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        header.grid_propagate(False)

        ctk.CTkLabel(
            header,
            text=APP_DESCRIPTION,
            text_color=TEXT_LIGHT,
            font=make_font(18, "bold"),
        ).grid(row=0, column=0, padx=(16, 24), pady=12, sticky="w")

        self._load_header_icon(header)

    def _load_header_icon(self, parent: ctk.CTkFrame) -> None:
        image = load_ctk_image(DIRECTORY_ICON_PATH, HEADER_LOGO_SIZE, crop_alpha=True)
        if image is None:
            return

        self.header_icon_image = image
        ctk.CTkLabel(parent, image=self.header_icon_image, text="").grid(
            row=0,
            column=1,
            padx=(16, 18),
            pady=14,
            sticky="e",
        )

    def _build_form_body(self) -> None:
        body = ctk.CTkFrame(self, fg_color=APP_BACKGROUND, corner_radius=0)
        body.grid(row=2, column=0, sticky="nsew")
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(0, weight=1)

        self.workspace_frame = ctk.CTkFrame(
            body,
            fg_color=SURFACE_BACKGROUND,
            border_width=0,
            corner_radius=0,
        )
        self.workspace_frame.grid(row=0, column=0, sticky="nsew", padx=24, pady=(18, 24))
        self.workspace_frame.grid_columnconfigure(0, weight=1)
        self.workspace_frame.grid_rowconfigure(0, weight=1)

        self.directory_form = DirectoryFormFrame(self.workspace_frame)
        self.directory_form.grid(row=0, column=0, sticky="nsew")

    def _show_file_menu(self) -> None:
        self._refresh_recent_menu()
        self.file_menu.tk_popup(
            self.file_button.winfo_rootx(),
            self.file_button.winfo_rooty() + self.file_button.winfo_height(),
        )
        self.file_menu.grab_release()

    def _show_help_dialog(self) -> None:
        show_help_dialog(self)

    def export_pdf(self) -> None:
        if not self.directory_form.validate_required_data():
            messagebox.showerror(
                "Datos incompletos",
                "Captura un título, al menos un área y al menos una persona antes de generar el PDF.",
                parent=self,
            )
            return

        if not self._confirm_export_preview():
            return

        if not self.directory_form.validate_dates():
            messagebox.showerror(
                "Fecha inválida",
                "La Fecha de Alta debe tener un valor válido con formato dd/mm/aaaa.",
                parent=self,
            )
            return

        data = self.directory_form.get_report_data()
        safe_name = "".join(character for character in (data.title or "directorio") if character not in '<>:"/\\|?*')
        default_name = f"{safe_name.strip() or 'directorio'}.pdf"
        target = filedialog.asksaveasfilename(
            parent=self,
            title="Exportar directorio como PDF",
            defaultextension=".pdf",
            initialfile=default_name,
            filetypes=(("Archivo PDF", "*.pdf"), ("Todos los archivos", "*.*")),
        )
        if not target:
            return

        self._set_export_busy("disabled")
        self.export_progress_overlay.show("Generando PDF...")
        future = self._executor.submit(DirectoryPdfExporter().export, data, Path(target))
        self._pending_export = future
        self.after(100, lambda: self._poll_pdf_export(future))

    def _poll_pdf_export(self, future: Future[Path]) -> None:
        if not future.done():
            self.after(100, lambda: self._poll_pdf_export(future))
            return
        try:
            output_path = future.result()
            messagebox.showinfo(
                "PDF guardado",
                f"El reporte se guardó correctamente en:\n{output_path}",
                parent=self,
            )
        except Exception as error:  # noqa: BLE001
            LOGGER.exception("Unable to export directory PDF")
            messagebox.showerror(
                "No se pudo guardar",
                f"No fue posible generar el PDF.\n\n{error}",
                parent=self,
            )
        finally:
            if self._pending_export is future:
                self._pending_export = None
            self.export_progress_overlay.hide()
            self._set_export_busy("normal")

    def _set_export_busy(self, state: str) -> None:
        self.file_button.configure(state=state)
        self.help_button.configure(state=state)
        try:
            self.file_menu.entryconfig("Exportar PDF", state=state)
        except tk.TclError:
            pass

    def _confirm_export_preview(self) -> bool:
        summary = self.directory_form.get_preview_summary()
        date_issues = summary["date_issues"]
        lines = [
            "Vista previa del directorio",
            "",
            f"Título: {summary['title'] or '(sin título)'}",
            f"Período: {summary['period'] or '(sin período)'}",
            f"Áreas: {summary['area_count']}",
            f"Personas: {summary['person_count']}",
        ]

        if date_issues:
            lines.extend(["", "Fechas vacías o inválidas:"])
            lines.extend(f"- {issue}" for issue in date_issues[:12])
            if len(date_issues) > 12:
                lines.append(f"- ... y {len(date_issues) - 12} más")
            lines.extend(["", "Corrige las fechas antes de generar el PDF."])
            messagebox.showwarning("Vista previa", "\n".join(lines), parent=self)
            return False

        lines.extend(["", "¿Generar PDF con estos datos?"])
        return messagebox.askyesno("Vista previa", "\n".join(lines), parent=self)

    def new_project(self) -> None:
        if not self.project_lifecycle.confirm_discard(self, "crear un proyecto nuevo"):
            return
        self.directory_form.reset_form()
        self.current_project_path = None
        self.project_lifecycle.reset(mark_saved=True)
        self._reset_history()
        self._update_window_title()

    def open_project(self) -> None:
        if not self.project_lifecycle.confirm_discard(self, "abrir otro proyecto"):
            return
        source_path = filedialog.askopenfilename(
            parent=self,
            title="Abrir proyecto",
            filetypes=[("Proyecto Directorio", "*.dir"), ("Todos los archivos", "*.*")],
        )
        if not source_path:
            return

        try:
            data = self.persistence_manager.load(source_path)
        except Exception as error:
            LOGGER.exception("Unable to load directory project from %s", source_path)
            messagebox.showerror(
                "No se pudo abrir",
                f"No fue posible cargar el proyecto.\n\n{error}",
                parent=self,
            )
            return

        self.current_project_path = Path(source_path)
        self.directory_form.set_report_data(data)
        self.project_lifecycle.mark_saved(self.current_project_path)
        self._reset_history()
        self._update_window_title()

    def save_project(self) -> bool:
        if self.current_project_path is None:
            return self.save_project_as()
        return self._save_project_to_path(self.current_project_path)

    def save_project_as(self) -> bool:
        data = self.directory_form.get_report_data()
        safe_name = "".join(character for character in (data.title or "directorio") if character not in '<>:"/\\|?*')
        target_path = filedialog.asksaveasfilename(
            parent=self,
            title="Guardar proyecto como",
            defaultextension=".dir",
            initialfile=f"{safe_name.strip() or 'directorio'}.dir",
            filetypes=[("Proyecto Directorio", "*.dir"), ("Todos los archivos", "*.*")],
        )
        if not target_path:
            return False
        candidate_path = Path(target_path)
        if not self._save_project_to_path(candidate_path):
            return False
        self.current_project_path = candidate_path
        return True

    def _save_project_to_path(self, target_path: Path) -> bool:
        try:
            saved_path = self.persistence_manager.save(self.directory_form.get_report_data(), target_path)
        except Exception as error:
            LOGGER.exception("Unable to save directory project to %s", target_path)
            messagebox.showerror(
                "No se pudo guardar",
                f"No fue posible guardar el proyecto.\n\n{error}",
                parent=self,
            )
            return False
        self.current_project_path = saved_path
        self.project_lifecycle.mark_saved(saved_path)
        self._update_window_title()
        messagebox.showinfo("Proyecto guardado", f"Proyecto guardado en:\n{saved_path}", parent=self)
        return True

    def confirm_exit(self) -> None:
        if self._pending_export is not None and not self._pending_export.done():
            messagebox.showwarning(
                "Exportación en curso",
                "Espera a que termine la generación del PDF antes de cerrar.",
                parent=self,
            )
            return
        if not self.project_lifecycle.confirm_discard(self, f"salir de {APP_TITLE}"):
            return
        self.master.destroy()

    def _on_directory_changed(self, _event=None) -> None:
        self._update_window_title()
        if self._history_paused:
            return
        if self._history_after_id is not None:
            self.after_cancel(self._history_after_id)
        self._history_after_id = self.after(350, self._commit_history_change)

    def _commit_history_change(self) -> None:
        self._history_after_id = None
        snapshot = asdict(self.directory_form.get_report_data())
        if not self._history_paused and snapshot != self._history[-1]:
            self._history.append(snapshot)
            self._history = self._history[-100:]
            self._redo_history.clear()

    def undo(self) -> None:
        if len(self._history) < 2:
            return
        self._redo_history.append(self._history.pop())
        self._apply_history_snapshot(self._history[-1])

    def redo(self) -> None:
        if not self._redo_history:
            return
        snapshot = self._redo_history.pop()
        self._history.append(snapshot)
        self._apply_history_snapshot(snapshot)

    def _apply_history_snapshot(self, snapshot: dict) -> None:
        self._history_paused = True
        try:
            self.directory_form.set_report_data(self.persistence_manager.from_dict(snapshot))
        finally:
            self._history_paused = False

    def _reset_history(self) -> None:
        self._history = [asdict(self.directory_form.get_report_data())]
        self._redo_history.clear()

    def _update_window_title(self) -> None:
        marker = " *" if self.project_lifecycle.is_dirty else ""
        self.master.title(f"{APP_TITLE}{marker}")

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
        if not self.project_lifecycle.confirm_discard(self, "abrir otro proyecto"):
            return
        try:
            data = self.persistence_manager.load(source_path)
        except Exception as error:
            self.project_lifecycle.recent_files.remove(source_path)
            LOGGER.exception("Unable to load directory project from %s", source_path)
            messagebox.showerror(
                "No se pudo abrir",
                f"No fue posible cargar el proyecto.\n\n{error}",
                parent=self,
            )
            return
        self.current_project_path = Path(source_path)
        self.directory_form.set_report_data(data)
        self.project_lifecycle.mark_saved(self.current_project_path)
        self._reset_history()
        self._update_window_title()

    def _restore_autosave(self, snapshot: object, path: Path | None) -> None:
        if not isinstance(snapshot, dict):
            return
        self.directory_form.set_report_data(self.persistence_manager.from_dict(snapshot))
        self.current_project_path = path
        self._history = [snapshot]
        self._redo_history.clear()

    def destroy(self) -> None:
        self.project_lifecycle.stop_autosave()
        self._executor.shutdown(wait=False, cancel_futures=True)
        if self._history_after_id is not None:
            self.after_cancel(self._history_after_id)
            self._history_after_id = None
        super().destroy()
