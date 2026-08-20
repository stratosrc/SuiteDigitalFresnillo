"""File selection and conversion actions for the PDF workspace."""

from __future__ import annotations

import logging
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk

try:
    from tkinterdnd2 import DND_FILES
except ImportError:
    DND_FILES = None

from App_ConversorPDF.config import (
    DOCUMENT_EXTENSIONS,
    PDF_EXTENSIONS,
    SHEET_EXTENSIONS,
    SUPPORTED_EXTENSIONS,
)
from App_ConversorPDF.services.converter import ConversionRequest
from App_ConversorPDF.services.output_planner import PlannedOutput, build_output_plan
from App_ConversorPDF.ui.dialogs import show_help_dialog
from App_ConversorPDF.ui.workspace_models import SourceFileItem
from App_ConversorPDF.ui.theme import (
    BORDER_COLOR,
    DANGER_BUTTON,
    PRIMARY_BUTTON,
    PRIMARY_BUTTON_ACTIVE,
    RIGHT_PANEL_BACKGROUND,
    SURFACE_BACKGROUND,
    TEXT_DARK,
    TEXT_LIGHT,
    make_font,
)
from components.shared.accessibility import enable_visible_focus
from components.shared.atomic_output import OutputCancelled
from components.shared.tooltip import Tooltip


SPLIT_TOGGLE_TOOLTIP = "Separar cada hoja o pagina seleccionada en PDFs individuales."
LOGGER = logging.getLogger(__name__)
LIST_PANEL_TOP_PADDING = 24
LIST_PANEL_BOTTOM_PADDING = 24
LIST_ACTION_HEIGHT = 62


class ConversionWorkflowMixin:
    def _select_files(self) -> None:
        if self.is_busy:
            return
        patterns = " ".join(f"*{extension}" for extension in sorted(SUPPORTED_EXTENSIONS))
        selected_paths = filedialog.askopenfilenames(
            parent=self,
            title="Seleccionar archivos",
            filetypes=[
                ("Archivos soportados", patterns),
                ("Todos los archivos", "*.*"),
            ],
        )
        if not selected_paths:
            return

        self._add_files(selected_paths)

    def _select_active_files(self) -> None:
        if self.active_view == "merge":
            self._select_merge_files()
        else:
            self._select_files()

    def _save_active_output(self) -> None:
        if self.active_view == "merge":
            self._save_merged_pdf()
        else:
            self._convert_first_output()

    def _save_active_output_as(self) -> None:
        if self.active_view == "merge":
            self._save_merged_pdf()
        else:
            self._save_all_outputs()

    def _show_view(self, view_name: str) -> None:
        if self.is_busy or view_name not in {"convert", "merge"}:
            return
        self.active_view = view_name
        if view_name == "merge":
            self.converter_body.grid_remove()
            self.merge_body.grid()
        else:
            self.merge_body.grid_remove()
            self.converter_body.grid()

    def _show_help_dialog(self) -> None:
        if self.is_busy:
            return
        show_help_dialog(self)

    def _add_files(self, raw_paths) -> None:
        changed = False
        for raw_path in raw_paths:
            path = Path(raw_path)
            if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue
            sheet_var = tk.StringVar(value="")
            split_var = tk.BooleanVar(value=False)
            if path.suffix.lower() in DOCUMENT_EXTENSIONS | PDF_EXTENSIONS:
                sheet_var.trace_add("write", lambda *_args: self._refresh_outputs())
                split_var.trace_add("write", lambda *_args: self._refresh_outputs())
            self.files.append(
                SourceFileItem(
                    path=path,
                    sheet_var=sheet_var if path.suffix.lower() in DOCUMENT_EXTENSIONS | PDF_EXTENSIONS else None,
                    split_var=split_var if path.suffix.lower() in DOCUMENT_EXTENSIONS | PDF_EXTENSIONS else None,
                )
            )
            changed = True

        if not changed:
            return
        self._render_files()
        self._refresh_outputs()

    def reset_work(self) -> None:
        if self.is_busy:
            return
        if self.active_view == "merge":
            self.merge_files.clear()
            self._render_merge_files()
        else:
            self.files.clear()
            self._render_files()
            self._refresh_outputs()

    def _remove_file(self, index: int) -> None:
        if self.is_busy:
            return
        if 0 <= index < len(self.files):
            del self.files[index]
            self._render_files()
            self._refresh_outputs()

    def _render_files(self) -> None:
        for child in self.files_frame.winfo_children():
            child.destroy()

        if not self.files:
            self._sync_action_buttons()
            return

        for row_index, item in enumerate(self.files):
            row = ctk.CTkFrame(self.files_frame, fg_color="#1E2858", corner_radius=0)
            row.grid(row=row_index * 2, column=0, sticky="ew", pady=(0, 1))
            row.grid_columnconfigure(1, weight=1)
            row.grid_columnconfigure(2, weight=0)

            ctk.CTkButton(
                row,
                text="X",
                command=lambda index=row_index: self._remove_file(index),
                width=16,
                height=16,
                corner_radius=8,
                fg_color="#344077",
                hover_color=DANGER_BUTTON,
                text_color=TEXT_LIGHT,
                font=make_font(14, "bold"),
            ).grid(row=0, column=0, rowspan=2, sticky="nsw", padx=(8, 0), pady=19)

            ctk.CTkLabel(
                row,
                text=item.path.name,
                text_color=TEXT_LIGHT,
                font=make_font(12, "bold"),
                anchor="w",
            ).grid(row=0, column=1, sticky="ew", padx=12, pady=(6, 1))
            ctk.CTkLabel(
                row,
                text=str(item.path.parent),
                text_color="#B8C2D6",
                font=make_font(10),
                anchor="w",
            ).grid(row=1, column=1, sticky="ew", padx=12, pady=(0, 6))

            if item.sheet_var is not None:
                split_button = ctk.CTkButton(
                    row,
                    text="" if self._split_toggle_image(item) is not None else self._split_toggle_text(item),
                    image=self._split_toggle_image(item),
                    command=lambda source=item: self._toggle_split_output(source),
                    width=34,
                    height=34,
                    corner_radius=0,
                    fg_color=PRIMARY_BUTTON if item.split_var is not None and item.split_var.get() else "#344077",
                    hover_color=PRIMARY_BUTTON_ACTIVE,
                    text_color=TEXT_LIGHT,
                    font=make_font(11, "bold"),
                )
                split_button.grid(row=0, column=2, rowspan=2, sticky="e", padx=(6, 8), pady=12)
                split_button.tooltip = Tooltip(split_button, SPLIT_TOGGLE_TOOLTIP, delay_ms=0)

                entry = ctk.CTkEntry(
                    self.files_frame,
                    placeholder_text=self._selection_placeholder(item.path.suffix.lower()),
                    height=15,
                    corner_radius=0,
                    fg_color=SURFACE_BACKGROUND,
                    border_color=BORDER_COLOR,
                    text_color=TEXT_DARK,
                    placeholder_text_color="#797979",
                    font=make_font(12),
                )
                current_value = item.sheet_var.get()
                if current_value:
                    entry.insert(0, current_value)
                entry.bind("<KeyRelease>", lambda _event, source=item, input_entry=entry: self._update_sheet_value(source, input_entry.get()), add=True)
                entry.bind("<FocusOut>", lambda _event, source=item, input_entry=entry: self._update_sheet_value(source, input_entry.get()), add=True)
                entry.grid(row=row_index * 2 + 1, column=0, sticky="ew", pady=(0, 10))
        enable_visible_focus(self.files_frame)
        self._sync_action_buttons()

    def _refresh_outputs(self) -> None:
        for child in getattr(self, "outputs_frame", []).winfo_children() if hasattr(self, "outputs_frame") else []:
            child.destroy()
        self.output_buttons.clear()

        outputs = self._build_output_items()
        if not outputs:
            self._sync_action_buttons()
            return

        for index, output in enumerate(outputs):
            row = ctk.CTkFrame(self.outputs_frame, fg_color=RIGHT_PANEL_BACKGROUND, corner_radius=0)
            row.grid(row=index, column=0, sticky="ew", pady=(0, 8))
            row.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(
                row,
                text=output.filename,
                height=38,
                corner_radius=0,
                fg_color="#E7E9F1",
                text_color=TEXT_DARK,
                font=make_font(14, "bold"),
                anchor="w",
                padx=12,
            ).grid(row=0, column=0, sticky="ew", padx=4)
            button = ctk.CTkButton(
                row,
                text="" if self.download_item_icon_image is not None else "DL",
                image=self.download_item_icon_image,
                command=lambda planned=output: self._save_output(
                    planned.source,
                    planned.selection,
                    planned.filename,
                ),
                width=38,
                height=38,
                corner_radius=0,
                fg_color=PRIMARY_BUTTON,
                hover_color=PRIMARY_BUTTON_ACTIVE,
                text_color=TEXT_LIGHT,
                font=make_font(11, "bold"),
            )
            button.grid(row=0, column=1, sticky="e")
            Tooltip(button, f"Guardar {output.filename}")
            self.output_buttons.append(button)
        enable_visible_focus(self.outputs_frame)
        self._sync_action_buttons()

    def _update_sheet_value(self, item: SourceFileItem, value: str) -> None:
        if item.sheet_var is None or item.sheet_var.get() == value:
            return
        item.sheet_var.set(value)

    def _toggle_split_output(self, item: SourceFileItem) -> None:
        if item.split_var is None:
            return
        item.split_var.set(not item.split_var.get())
        self._render_files()
        self._refresh_outputs()

    def _split_toggle_text(self, item: SourceFileItem) -> str:
        if item.split_var is not None and item.split_var.get():
            return "N"
        return "1"

    def _split_toggle_image(self, item: SourceFileItem) -> ctk.CTkImage | None:
        if item.split_var is not None and item.split_var.get():
            return self.separate_icon_on_image
        return self.separate_icon_image

    @staticmethod
    def _selection_placeholder(suffix: str) -> str:
        if suffix in SHEET_EXTENSIONS:
            return "Hojas del libro a exportar, ej. 2-4 o 1, 4-6. Dejar vacío para todas."
        return "Páginas a exportar, ej. 2-4 o 1, 4-6. Dejar vacío para convertir todas."

    def _build_output_items(self) -> list[PlannedOutput]:
        return build_output_plan(self.files)

    def _convert_first_output(self) -> None:
        if self.is_busy:
            return
        outputs = self._build_output_items()
        if not outputs:
            messagebox.showinfo("Sin archivos", "Carga al menos un archivo para convertir.", parent=self)
            return
        output = outputs[0]
        self._save_output(output.source, output.selection, output.filename)

    def _save_all_outputs(self) -> None:
        if self.is_busy:
            return
        outputs = self._build_output_items()
        if not outputs:
            messagebox.showinfo("Sin archivos", "Carga al menos un archivo para convertir.", parent=self)
            return

        target_dir = filedialog.askdirectory(parent=self, title="Seleccionar carpeta de descarga")
        if not target_dir:
            return

        output_dir = Path(target_dir)
        self._run_conversion_task(
            status_text=f"Convirtiendo 1 de {len(outputs)}...",
            task=lambda: self._convert_all_outputs(outputs, output_dir),
            on_success=lambda report: self._show_batch_report(report, output_dir),
        )

    def _convert_all_outputs(self, outputs: list[PlannedOutput], output_dir: Path) -> dict[str, object]:
        saved_paths: list[Path] = []
        errors: list[str] = []
        for index, output in enumerate(outputs, start=1):
            if self._cancel_event.is_set():
                break
            self._set_loading_status_from_worker(f"Convirtiendo {index} de {len(outputs)}...")
            try:
                saved_paths.append(
                    self.converter.convert(
                        ConversionRequest(
                            source_path=output.source.path,
                            target_path=output_dir / output.filename,
                            sheet_name=output.selection,
                        ),
                        cancel_check=self._cancel_event.is_set,
                    )
                )
            except OutputCancelled:
                break
            except Exception as error:  # noqa: BLE001
                errors.append(f"{output.filename}: {error}")

        return {
            "saved": saved_paths,
            "errors": errors,
            "cancelled": self._cancel_event.is_set(),
            "total": len(outputs),
        }

    def _show_batch_report(self, report: dict[str, object], output_dir: Path) -> None:
        saved = list(report.get("saved", []))
        errors = list(report.get("errors", []))
        lines = [
            f"Correctas: {len(saved)}",
            f"Fallidas: {len(errors)}",
        ]
        if report.get("cancelled"):
            lines.append("La operación fue cancelada.")
        if saved:
            lines.extend(["", "Archivos generados:", *(f"• {Path(path).name}" for path in saved[:8])])
        if errors:
            lines.extend(["", "Errores:", *(f"• {error}" for error in errors[:8])])
        lines.extend(["", f"Carpeta: {output_dir}"])
        messagebox.showinfo("Reporte de conversión", "\n".join(lines), parent=self)

    def _set_icon_hover(self, button: ctk.CTkButton, image: ctk.CTkImage | None) -> None:
        if image is not None:
            button.configure(image=image)

    def _enable_file_drop(self, widget) -> None:
        if not self._dnd_available:
            return
        register = getattr(widget, "drop_target_register", None)
        bind = getattr(widget, "dnd_bind", None)
        if register is None or bind is None:
            return
        try:
            register(DND_FILES)
            bind("<<Drop>>", self._handle_file_drop)
        except tk.TclError:
            self._dnd_available = False
            LOGGER.warning("TkDND is unavailable; drag and drop has been disabled")

    def _handle_file_drop(self, event) -> None:
        self._add_files(self.tk.splitlist(event.data))

    def _enable_merge_file_drop(self, widget) -> None:
        if not self._dnd_available:
            return
        register = getattr(widget, "drop_target_register", None)
        bind = getattr(widget, "dnd_bind", None)
        if register is None or bind is None:
            return
        try:
            register(DND_FILES)
            bind("<<Drop>>", self._handle_merge_file_drop)
        except tk.TclError:
            self._dnd_available = False
            LOGGER.warning("TkDND is unavailable; drag and drop has been disabled")

    def _handle_merge_file_drop(self, event) -> None:
        self._add_merge_files(self.tk.splitlist(event.data))

    def _sync_action_buttons(self) -> None:
        has_files = bool(self.files)
        has_outputs = bool(self._build_output_items())
        self._set_grid_visibility(self.upload_icon_button, not has_files)
        self._set_grid_visibility(self.files_frame, has_files)
        self._set_grid_visibility(self.upload_action_button, has_files)
        self._set_grid_visibility(self.download_icon_button, not has_outputs)
        self._set_grid_visibility(self.outputs_frame, has_outputs)
        self._set_grid_visibility(self.download_action_button, has_outputs)

    @staticmethod
    def _set_grid_visibility(widget: tk.Misc, visible: bool) -> None:
        if visible:
            widget.grid()
        else:
            widget.grid_remove()

    def _save_output(self, item: SourceFileItem, sheet_name: str | None, output_name: str) -> None:
        if self.is_busy:
            return
        target = filedialog.asksaveasfilename(
            parent=self,
            title="Exportar PDF",
            defaultextension=".pdf",
            initialfile=output_name,
            filetypes=[("Archivo PDF", "*.pdf"), ("Todos los archivos", "*.*")],
        )
        if not target:
            return

        self._run_conversion_task(
            status_text="Convirtiendo archivo...",
            task=lambda: self.converter.convert(
                ConversionRequest(
                    source_path=item.path,
                    target_path=Path(target),
                    sheet_name=sheet_name,
                ),
                cancel_check=self._cancel_event.is_set,
            ),
            on_success=lambda saved_path: messagebox.showinfo(
                "PDF guardado",
                f"Archivo guardado en:\n{saved_path}",
                parent=self,
            ),
        )
