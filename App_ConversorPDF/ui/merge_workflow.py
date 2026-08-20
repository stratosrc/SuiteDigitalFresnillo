"""PDF merge interactions for the conversion workspace."""
from __future__ import annotations

import logging
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

try:
    from tkinterdnd2 import DND_FILES
except ImportError:
    DND_FILES = None

from App_ConversorPDF.ui.theme import (
    DANGER_BUTTON,
    PRIMARY_BUTTON,
    PRIMARY_BUTTON_PRESSED,
    TEXT_LIGHT,
    make_font,
)
from components.shared.accessibility import enable_visible_focus


SPLIT_TOGGLE_TOOLTIP = "Separar cada hoja o pagina seleccionada en PDFs individuales."
LOGGER = logging.getLogger(__name__)
LIST_PANEL_TOP_PADDING = 24
LIST_PANEL_BOTTOM_PADDING = 24
LIST_ACTION_HEIGHT = 62



class MergeWorkflowMixin:
    def _select_merge_files(self) -> None:
        if self.is_busy:
            return
        selected_paths = filedialog.askopenfilenames(
            parent=self,
            title="Seleccionar PDFs para unir",
            filetypes=[("Archivos PDF", "*.pdf"), ("Todos los archivos", "*.*")],
        )
        if selected_paths:
            self._add_merge_files(selected_paths)

    def _add_merge_files(self, raw_paths) -> None:
        existing = {str(path.resolve()).casefold() for path in self.merge_files}
        invalid_names: list[str] = []
        changed = False
        for raw_path in raw_paths:
            path = Path(raw_path)
            if path.suffix.lower() != ".pdf" or not path.is_file():
                invalid_names.append(path.name)
                continue
            key = str(path.resolve()).casefold()
            if key in existing:
                continue
            self.merge_files.append(path)
            existing.add(key)
            changed = True

        if changed:
            self._render_merge_files()
        if invalid_names:
            messagebox.showwarning(
                "Archivos no admitidos",
                "Sólo se pueden agregar archivos PDF válidos.",
                parent=self,
            )

    def _remove_merge_file(self, index: int) -> None:
        if self.is_busy:
            return
        if 0 <= index < len(self.merge_files):
            del self.merge_files[index]
            self._render_merge_files()

    def _render_merge_files(self) -> None:
        for child in self.merge_files_frame.winfo_children():
            child.destroy()
        self._merge_rows.clear()
        self._merge_drop_indicators.clear()
        self._merge_drag_index = None
        self._merge_drop_index = None

        for index, path in enumerate(self.merge_files):
            indicator = ctk.CTkFrame(
                self.merge_files_frame,
                fg_color="#3B8ED0",
                corner_radius=0,
                height=4,
            )
            indicator.grid(row=index * 2, column=0, sticky="ew", padx=8, pady=2)
            indicator.grid_remove()
            self._merge_drop_indicators.append(indicator)

            row = ctk.CTkFrame(self.merge_files_frame, fg_color="#1E2858", corner_radius=0)
            row.grid(row=index * 2 + 1, column=0, sticky="ew", pady=(0, 7))
            row.grid_columnconfigure(2, weight=1)
            self._merge_rows.append(row)

            handle = ctk.CTkLabel(
                row,
                text="≡",
                width=34,
                text_color="#B8C2D6",
                font=make_font(22, "bold"),
                cursor="fleur",
            )
            handle.grid(row=0, column=0, rowspan=2, padx=(8, 2), pady=8)
            number = ctk.CTkLabel(
                row,
                text=str(index + 1),
                width=28,
                height=28,
                corner_radius=14,
                fg_color=PRIMARY_BUTTON,
                text_color=TEXT_LIGHT,
                font=make_font(12, "bold"),
            )
            number.grid(row=0, column=1, rowspan=2, padx=(0, 8), pady=14)
            name_label = ctk.CTkLabel(
                row,
                text=path.name,
                text_color=TEXT_LIGHT,
                font=make_font(12, "bold"),
                anchor="w",
            )
            name_label.grid(row=0, column=2, sticky="ew", pady=(8, 0))
            path_label = ctk.CTkLabel(
                row,
                text=str(path.parent),
                text_color="#B8C2D6",
                font=make_font(10),
                anchor="w",
            )
            path_label.grid(row=1, column=2, sticky="ew", pady=(0, 8))
            ctk.CTkButton(
                row,
                text="X",
                command=lambda item_index=index: self._remove_merge_file(item_index),
                width=26,
                height=26,
                corner_radius=13,
                fg_color="#344077",
                hover_color=DANGER_BUTTON,
                text_color=TEXT_LIGHT,
                font=make_font(12, "bold"),
            ).grid(row=0, column=3, rowspan=2, padx=10, pady=14)

            for drag_widget in (row, handle, number, name_label, path_label):
                drag_widget.bind(
                    "<ButtonPress-1>",
                    lambda event, item_index=index: self._start_merge_drag(event, item_index),
                    add=True,
                )
                drag_widget.bind("<B1-Motion>", self._update_merge_drag, add=True)
                drag_widget.bind("<ButtonRelease-1>", self._finish_merge_drag, add=True)

        if self.merge_files:
            final_indicator = ctk.CTkFrame(
                self.merge_files_frame,
                fg_color="#3B8ED0",
                corner_radius=0,
                height=4,
            )
            final_indicator.grid(
                row=len(self.merge_files) * 2,
                column=0,
                sticky="ew",
                padx=8,
                pady=2,
            )
            final_indicator.grid_remove()
            self._merge_drop_indicators.append(final_indicator)

        has_files = bool(self.merge_files)
        self._set_grid_visibility(self.merge_empty_button, not has_files)
        self._set_grid_visibility(self.merge_files_frame, has_files)
        self._set_grid_visibility(self.add_merge_files_button, has_files)
        count = len(self.merge_files)
        self.merge_count_label.configure(
            text=f"{count} archivo seleccionado" if count == 1 else f"{count} archivos seleccionados"
        )
        self.merge_action_button.configure(state="normal" if count >= 2 else "disabled")
        enable_visible_focus(self.merge_files_frame)

    def _start_merge_drag(self, _event, index: int) -> None:
        if self.is_busy:
            return
        self._merge_drag_index = index
        self._merge_drop_index = index
        if 0 <= index < len(self._merge_rows):
            self._merge_rows[index].configure(fg_color=PRIMARY_BUTTON_PRESSED)
        self._show_merge_drop_indicator(index)

    def _update_merge_drag(self, event) -> None:
        if self._merge_drag_index is None or not self._merge_rows:
            return
        pointer_y = event.y_root
        target = len(self._merge_rows)
        for index, row in enumerate(self._merge_rows):
            midpoint = row.winfo_rooty() + row.winfo_height() / 2
            if pointer_y < midpoint:
                target = index
                break
        self._merge_drop_index = target
        self._show_merge_drop_indicator(target)
        for index, row in enumerate(self._merge_rows):
            row.configure(
                fg_color=PRIMARY_BUTTON_PRESSED if index == self._merge_drag_index else "#1E2858"
            )

    def _show_merge_drop_indicator(self, target: int | None) -> None:
        for index, indicator in enumerate(self._merge_drop_indicators):
            if target is not None and index == target:
                indicator.grid()
            else:
                indicator.grid_remove()

    def _finish_merge_drag(self, _event) -> None:
        source = self._merge_drag_index
        target = self._merge_drop_index
        self._merge_drag_index = None
        self._merge_drop_index = None
        self._show_merge_drop_indicator(None)
        if source is None or target is None:
            for row in self._merge_rows:
                row.configure(fg_color="#1E2858")
            return
        if 0 <= source < len(self.merge_files) and 0 <= target <= len(self.merge_files):
            item = self.merge_files.pop(source)
            if source < target:
                target -= 1
            self.merge_files.insert(target, item)
            self._render_merge_files()

    def _save_merged_pdf(self) -> None:
        if self.is_busy:
            return
        if len(self.merge_files) < 2:
            messagebox.showinfo(
                "Faltan archivos",
                "Selecciona al menos dos archivos PDF para unir.",
                parent=self,
            )
            return
        target = filedialog.asksaveasfilename(
            parent=self,
            title="Guardar PDF unido",
            defaultextension=".pdf",
            initialfile="PDF unido.pdf",
            filetypes=[("Archivo PDF", "*.pdf"), ("Todos los archivos", "*.*")],
        )
        if not target:
            return

        sources = list(self.merge_files)
        self._run_conversion_task(
            status_text=f"Uniendo 1 de {len(sources)}...",
            task=lambda: self.pdf_merger.merge(
                sources,
                Path(target),
                cancel_check=self._cancel_event.is_set,
                progress_callback=lambda index, total: self._set_loading_status_from_worker(
                    f"Uniendo {index} de {total}..."
                ),
            ),
            on_success=lambda saved_path: messagebox.showinfo(
                "PDF unido",
                f"Archivo guardado en:\n{saved_path}",
                parent=self,
            ),
        )
