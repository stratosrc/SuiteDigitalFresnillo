from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk

from App_ConversorPDF.config import APP_DESCRIPTION, APP_TITLE, SHEET_EXTENSIONS, SUPPORTED_EXTENSIONS
from App_ConversorPDF.services.converter import ConversionRequest, PdfConverter
from App_ConversorPDF.ui.theme import (
    APP_BACKGROUND,
    BORDER_COLOR,
    DANGER_BUTTON,
    DANGER_BUTTON_ACTIVE,
    DARK_BACKGROUND,
    LEFT_PANEL_BACKGROUND,
    PRIMARY_BUTTON,
    PRIMARY_BUTTON_ACTIVE,
    PRIMARY_BUTTON_PRESSED,
    RIGHT_PANEL_BACKGROUND,
    SURFACE_BACKGROUND,
    TEXT_DARK,
    TEXT_LIGHT,
    TEXT_MUTED,
    make_font,
)


@dataclass(slots=True)
class SourceFileItem:
    path: Path
    sheet_var: tk.StringVar | None = None
    output_names: list[str] = field(default_factory=list)


class PdfConverterMainFrame(ctk.CTkFrame):
    def __init__(self, master: ctk.CTk) -> None:
        super().__init__(master, fg_color=APP_BACKGROUND, corner_radius=0)
        self.master = master
        self.converter = PdfConverter()
        self.files: list[SourceFileItem] = []
        self.output_buttons: list[ctk.CTkButton] = []
        self._build_layout()
        self._refresh_outputs()

    def _build_layout(self) -> None:
        self.pack(fill="both", expand=True)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._build_topbar()
        self._build_header()
        self._build_body()

    def _build_topbar(self) -> None:
        topbar = ctk.CTkFrame(self, fg_color=PRIMARY_BUTTON_PRESSED, corner_radius=0, height=24)
        topbar.grid(row=0, column=0, sticky="ew")
        topbar.grid_columnconfigure(0, weight=1)
        topbar.grid_propagate(False)

        ctk.CTkButton(
            topbar,
            text="Salir",
            command=self.confirm_exit,
            height=24,
            width=72,
            corner_radius=0,
            fg_color=DANGER_BUTTON,
            hover_color=DANGER_BUTTON_ACTIVE,
            text_color=TEXT_LIGHT,
            font=make_font(12),
        ).grid(row=0, column=1, padx=(4, 0), sticky="e")

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

    def _build_body(self) -> None:
        body = ctk.CTkFrame(self, fg_color=APP_BACKGROUND, corner_radius=0)
        body.grid(row=2, column=0, sticky="nsew")
        body.grid_columnconfigure(0, weight=1, uniform="converter")
        body.grid_columnconfigure(1, weight=1, uniform="converter")
        body.grid_rowconfigure(0, weight=1)

        self.left_panel = ctk.CTkFrame(body, fg_color=LEFT_PANEL_BACKGROUND, corner_radius=0)
        self.left_panel.grid(row=0, column=0, sticky="nsew")
        self.left_panel.grid_columnconfigure(0, weight=1)
        self.left_panel.grid_rowconfigure(1, weight=1)

        self.right_panel = ctk.CTkFrame(body, fg_color=RIGHT_PANEL_BACKGROUND, corner_radius=0)
        self.right_panel.grid(row=0, column=1, sticky="nsew")
        self.right_panel.grid_columnconfigure(0, weight=1)
        self.right_panel.grid_rowconfigure(1, weight=1)

        self._build_upload_panel()
        self._build_download_panel()

    def _build_upload_panel(self) -> None:
        ctk.CTkButton(
            self.left_panel,
            text="Upload",
            command=self._select_files,
            width=150,
            height=42,
            corner_radius=0,
            fg_color=SURFACE_BACKGROUND,
            hover_color="#D7DEE6",
            text_color=TEXT_DARK,
            font=make_font(14, "bold"),
        ).grid(row=0, column=0, pady=(28, 18))

        self.files_frame = ctk.CTkScrollableFrame(
            self.left_panel,
            fg_color=LEFT_PANEL_BACKGROUND,
            corner_radius=0,
            scrollbar_button_color=PRIMARY_BUTTON,
            scrollbar_button_hover_color=PRIMARY_BUTTON_ACTIVE,
        )
        self.files_frame.grid(row=1, column=0, sticky="nsew", padx=22, pady=(0, 24))
        self.files_frame.grid_columnconfigure(0, weight=1)

    def _build_download_panel(self) -> None:
        ctk.CTkButton(
            self.right_panel,
            text="Download",
            command=self._convert_first_output,
            width=150,
            height=42,
            corner_radius=0,
            fg_color=PRIMARY_BUTTON,
            hover_color=PRIMARY_BUTTON_ACTIVE,
            text_color=TEXT_LIGHT,
            font=make_font(14, "bold"),
        ).grid(row=0, column=0, pady=(28, 18))

        self.outputs_frame = ctk.CTkScrollableFrame(
            self.right_panel,
            fg_color=RIGHT_PANEL_BACKGROUND,
            corner_radius=0,
            scrollbar_button_color=PRIMARY_BUTTON,
            scrollbar_button_hover_color=PRIMARY_BUTTON_ACTIVE,
        )
        self.outputs_frame.grid(row=1, column=0, sticky="nsew", padx=22, pady=(0, 24))
        self.outputs_frame.grid_columnconfigure(0, weight=1)

    def _select_files(self) -> None:
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

        existing = {item.path for item in self.files}
        for raw_path in selected_paths:
            path = Path(raw_path)
            if path in existing or path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue
            sheet_var = tk.StringVar(value="")
            if path.suffix.lower() in SHEET_EXTENSIONS:
                sheet_var.trace_add("write", lambda *_args: self._refresh_outputs())
            self.files.append(SourceFileItem(path=path, sheet_var=sheet_var if path.suffix.lower() in SHEET_EXTENSIONS else None))

        self._render_files()
        self._refresh_outputs()

    def _render_files(self) -> None:
        for child in self.files_frame.winfo_children():
            child.destroy()

        if not self.files:
            self._empty_label(self.files_frame, "Sin archivos cargados", TEXT_LIGHT).grid(row=0, column=0, sticky="ew", pady=16)
            return

        for row_index, item in enumerate(self.files):
            row = ctk.CTkFrame(self.files_frame, fg_color="#1E2858", corner_radius=0)
            row.grid(row=row_index * 2, column=0, sticky="ew", pady=(0, 8))
            row.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(
                row,
                text=item.path.name,
                text_color=TEXT_LIGHT,
                font=make_font(12, "bold"),
                anchor="w",
            ).grid(row=0, column=0, sticky="ew", padx=12, pady=(8, 2))
            ctk.CTkLabel(
                row,
                text=str(item.path.parent),
                text_color="#B8C2D6",
                font=make_font(10),
                anchor="w",
            ).grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 8))

            if item.sheet_var is not None:
                entry = ctk.CTkEntry(
                    self.files_frame,
                    textvariable=item.sheet_var,
                    placeholder_text="Hojas a convertir: 1, 2, Hoja1-Hoja3",
                    height=30,
                    corner_radius=0,
                    fg_color=SURFACE_BACKGROUND,
                    border_color=BORDER_COLOR,
                    text_color=TEXT_DARK,
                    placeholder_text_color=TEXT_MUTED,
                    font=make_font(12),
                )
                entry.grid(row=row_index * 2 + 1, column=0, sticky="ew", pady=(0, 10))

    def _refresh_outputs(self) -> None:
        for child in getattr(self, "outputs_frame", []).winfo_children() if hasattr(self, "outputs_frame") else []:
            child.destroy()
        self.output_buttons.clear()

        outputs = self._build_output_items()
        if not outputs:
            if hasattr(self, "outputs_frame"):
                self._empty_label(self.outputs_frame, "Sin PDFs generados", TEXT_DARK).grid(row=0, column=0, sticky="ew", pady=16)
            return

        for index, (item, sheet_name, output_name) in enumerate(outputs):
            button = ctk.CTkButton(
                self.outputs_frame,
                text=output_name,
                command=lambda source=item, sheet=sheet_name, name=output_name: self._save_output(source, sheet, name),
                height=38,
                corner_radius=0,
                fg_color=SURFACE_BACKGROUND,
                hover_color="#F2F5F8",
                text_color=TEXT_DARK,
                border_width=1,
                border_color=BORDER_COLOR,
                font=make_font(12, "bold"),
                anchor="w",
            )
            button.grid(row=index, column=0, sticky="ew", pady=(0, 8))
            self.output_buttons.append(button)

    def _build_output_items(self) -> list[tuple[SourceFileItem, str | None, str]]:
        outputs: list[tuple[SourceFileItem, str | None, str]] = []
        for item in self.files:
            sheet_names = self._parse_sheet_input(item.sheet_var.get()) if item.sheet_var is not None else []
            if not sheet_names:
                outputs.append((item, None, f"{item.path.stem}.pdf"))
                continue
            for sheet_name in sheet_names:
                safe_sheet = self._safe_filename(sheet_name)
                outputs.append((item, sheet_name, f"{item.path.stem}_{safe_sheet}.pdf"))
        return outputs

    def _parse_sheet_input(self, raw_value: str) -> list[str]:
        parts = [part.strip() for part in raw_value.replace(";", ",").split(",")]
        return [part for part in parts if part]

    def _convert_first_output(self) -> None:
        outputs = self._build_output_items()
        if not outputs:
            messagebox.showinfo("Sin archivos", "Carga al menos un archivo para convertir.", parent=self)
            return
        item, sheet_name, output_name = outputs[0]
        self._save_output(item, sheet_name, output_name)

    def _save_output(self, item: SourceFileItem, sheet_name: str | None, output_name: str) -> None:
        target = filedialog.asksaveasfilename(
            parent=self,
            title="Guardar PDF",
            defaultextension=".pdf",
            initialfile=output_name,
            filetypes=[("Archivo PDF", "*.pdf"), ("Todos los archivos", "*.*")],
        )
        if not target:
            return

        try:
            self.converter.convert(
                ConversionRequest(
                    source_path=item.path,
                    target_path=Path(target),
                    sheet_name=sheet_name,
                )
            )
        except Exception as error:  # noqa: BLE001
            messagebox.showerror("No se pudo convertir", str(error), parent=self)
            return

        messagebox.showinfo("PDF guardado", f"Archivo guardado en:\n{target}", parent=self)

    def _empty_label(self, parent, text: str, text_color: str) -> ctk.CTkLabel:
        return ctk.CTkLabel(
            parent,
            text=text,
            text_color=text_color,
            font=make_font(12),
        )

    def _safe_filename(self, value: str) -> str:
        safe = "".join(character for character in value if character not in '<>:"/\\|?*')
        return safe.strip() or "hoja"

    def confirm_exit(self) -> None:
        self.master.destroy()
