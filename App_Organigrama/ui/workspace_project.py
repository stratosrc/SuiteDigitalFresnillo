"""Project, export and recovery workflow for the organigram workspace."""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import Future
from copy import deepcopy
import logging
from pathlib import Path
import tempfile
import tkinter as tk
from tkinter import filedialog, messagebox


from App_Organigrama.models.document import OrgGridDocument
from App_Organigrama.services.image_exporter import export_pdf_as_image
from App_Organigrama.ui.modals import OrientationDialog

LOGGER = logging.getLogger(__name__)
INVALID_FILENAME_CHARS = '<>:"/\\|?*'


class WorkspaceProjectMixin:
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
