import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk
from PIL import Image, ImageOps

from App_Directorio.config import (
    APP_DESCRIPTION,
    APP_TITLE,
    DIRECTORY_ICON_PATH,
)
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
from App_Directorio.utils import crop_transparent_padding


class DirectoryMainFrame(ctk.CTkFrame):
    def __init__(self, master: ctk.CTk) -> None:
        super().__init__(master, fg_color=APP_BACKGROUND, corner_radius=0)
        self.master = master
        self.header_icon_image: ctk.CTkImage | None = None
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
        self.file_menu.add_command(label="Guardar", command=self.guardar_pdf)

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
            width=78,
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
        if not DIRECTORY_ICON_PATH.exists():
            return

        try:
            image = Image.open(DIRECTORY_ICON_PATH).convert("RGBA")
        except OSError:
            return

        image = crop_transparent_padding(image)
        resized = ImageOps.contain(image, HEADER_LOGO_SIZE, Image.Resampling.LANCZOS)
        self.header_icon_image = ctk.CTkImage(light_image=resized, dark_image=resized, size=resized.size)
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
            title="Guardar directorio como PDF",
            defaultextension=".pdf",
            initialfile=default_name,
            filetypes=(("Archivo PDF", "*.pdf"), ("Todos los archivos", "*.*")),
        )
        if not target:
            return

        try:
            output_path = DirectoryPdfExporter().export(data, Path(target))
        except Exception as error:
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

    def nuevo_proyecto(self) -> None:
        self.directory_form.reset_form()

    def confirm_exit(self) -> None:
        if not messagebox.askyesno(
            "Confirmar salida",
            f"¿Estás seguro de que quieres salir de {APP_TITLE}?",
            parent=self,
        ):
            return
        self.master.destroy()
