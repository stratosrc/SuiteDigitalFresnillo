import tkinter as tk
import logging
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

LOGGER = logging.getLogger(__name__)


class DirectoryMainFrame(ctk.CTkFrame):
    def __init__(self, master: ctk.CTk) -> None:
        super().__init__(master, fg_color=APP_BACKGROUND, corner_radius=0)
        self.master = master
        self.header_icon_image: ctk.CTkImage | None = None
        self.current_project_path: Path | None = None
        self.persistence_manager = DirectoryPersistenceManager()
        self._build_layout()
        self._build_menu()

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
        self.file_menu.add_command(label="Nuevo", command=self.nuevo_proyecto)
        self.file_menu.add_command(label="Abrir", command=self.abrir_proyecto)
        self.file_menu.add_command(label="Guardar proyecto", command=self.guardar_proyecto)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exportar PDF", command=self.guardar_pdf)

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

        self.help_button = ctk.CTkButton(
            topbar,
            text="Ayuda",
            command=self._show_help_dialog,
            height=24,
            width=72,
            corner_radius=0,
            fg_color=PRIMARY_BUTTON,
            hover_color=PRIMARY_BUTTON_ACTIVE,
            text_color=TEXT_LIGHT,
            font=make_font(12),
        )
        self.help_button.grid(row=0, column=1, padx=(0, 4), sticky="w")

        self.exit_button = ctk.CTkButton(
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
        )
        self.exit_button.grid(row=0, column=3, padx=(4, 0), sticky="e")

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
        self.file_menu.tk_popup(
            self.file_button.winfo_rootx(),
            self.file_button.winfo_rooty() + self.file_button.winfo_height(),
        )
        self.file_menu.grab_release()

    def _show_help_dialog(self) -> None:
        show_help_dialog(self)

    def guardar_pdf(self) -> None:
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

        try:
            output_path = DirectoryPdfExporter().export(data, Path(target))
        except Exception as error:
            LOGGER.exception("Unable to export directory PDF")
            messagebox.showerror(
                "No se pudo guardar",
                f"No fue posible generar el PDF.\n\n{error}",
                parent=self,
            )
            return

        messagebox.showinfo(
            "PDF guardado",
            f"El reporte se guardó correctamente en:\n{output_path}",
            parent=self,
        )

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

    def nuevo_proyecto(self) -> None:
        self.directory_form.reset_form()
        self.current_project_path = None

    def abrir_proyecto(self) -> None:
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

    def guardar_proyecto(self) -> None:
        if self.current_project_path is None:
            self.guardar_proyecto_como()
            return
        self._save_project_to_path(self.current_project_path)

    def guardar_proyecto_como(self) -> None:
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
            return
        self.current_project_path = Path(target_path)
        self._save_project_to_path(self.current_project_path)

    def _save_project_to_path(self, target_path: Path) -> None:
        try:
            saved_path = self.persistence_manager.save(self.directory_form.get_report_data(), target_path)
        except Exception as error:
            LOGGER.exception("Unable to save directory project to %s", target_path)
            messagebox.showerror(
                "No se pudo guardar",
                f"No fue posible guardar el proyecto.\n\n{error}",
                parent=self,
            )
            return
        messagebox.showinfo("Proyecto guardado", f"Proyecto guardado en:\n{saved_path}", parent=self)

    def confirm_exit(self) -> None:
        if not messagebox.askyesno(
            "Confirmar salida",
            f"¿Estás seguro de que quieres salir de {APP_TITLE}?",
            parent=self,
        ):
            return
        self.master.destroy()
