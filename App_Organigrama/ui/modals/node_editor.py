from __future__ import annotations

from collections.abc import Callable
import tkinter as tk

import customtkinter as ctk
from PIL import Image

from App_Organigrama.rendering.palette import NODE_COLOR_CHOICES
from App_Organigrama.ui.theme import (
    BORDER_COLOR,
    PRIMARY_BUTTON,
    PRIMARY_BUTTON_ACTIVE,
    SELECTED_OUTLINE,
    SURFACE_BACKGROUND,
    TEXT_DARK,
    make_font,
)
from components.shared.accessibility import enable_visible_focus


class NodeEditorDialog(ctk.CTkToplevel):
    PERSON_BULLET_PREFIX = "• "

    def __init__(
        self,
        master: tk.Misc,
        title: str,
        on_save: Callable[[str, str, str], None],
        name: str = "",
        role: str = "",
        selected_color: str | None = None,
    ) -> None:
        super().__init__(master)
        self.title(title)
        self.resizable(True, True)
        self.configure(fg_color=SURFACE_BACKGROUND)
        self.transient(master.winfo_toplevel())
        self.grab_set()

        self.on_save = on_save
        self.initial_name = name
        self.role_var = tk.StringVar(value=role)
        self.selected_color = selected_color or NODE_COLOR_CHOICES[0][1]
        self.color_buttons: dict[str, ctk.CTkButton] = {}
        self.color_images: dict[str, ctk.CTkImage] = {}

        self._build()
        self.update_idletasks()
        self.minsize(self.winfo_width(), self.winfo_height())
        self.after_idle(lambda: enable_visible_focus(self))
        self.after(60, self.name_entry.focus_set)

    def _build(self) -> None:
        frame = ctk.CTkFrame(self, fg_color=SURFACE_BACKGROUND, corner_radius=0)
        frame.pack(fill="both", expand=True, padx=18, pady=18)
        frame.grid_columnconfigure(0, weight=1)

        self._build_label(frame, "Nombre(s)", row=0)
        self.name_entry = ctk.CTkTextbox(frame, width=560, height=120, corner_radius=0)
        self.name_entry.grid(row=1, column=0, sticky="ew", pady=(4, 4))
        self._populate_name_entry()
        self.name_entry.bind("<Return>", self._ignore_enter)
        self.name_entry.bind("<KP_Enter>", self._ignore_enter)
        self.name_entry.bind("<Control-Return>", self._insert_name_line)
        self.name_entry.bind("<Control-KP_Enter>", self._insert_name_line)
        ctk.CTkLabel(
            frame,
            text="Ctrl + Enter agrega otra persona con viñeta nueva",
            text_color=TEXT_DARK,
            font=make_font(10),
        ).grid(row=2, column=0, sticky="w", pady=(0, 12))

        self._build_label(frame, "Cargo", row=3)
        ctk.CTkEntry(frame, textvariable=self.role_var, width=560, corner_radius=0).grid(
            row=4,
            column=0,
            sticky="ew",
            pady=(4, 12),
        )

        self._build_label(frame, "Color y uso recomendado", row=5)
        self._build_swatches(frame)
        self._build_actions(frame)

    def _build_label(self, parent: ctk.CTkFrame, text: str, row: int) -> None:
        ctk.CTkLabel(
            parent,
            text=text,
            text_color=TEXT_DARK,
            font=make_font(12, "bold"),
        ).grid(row=row, column=0, sticky="w")

    def _build_swatches(self, parent: ctk.CTkFrame) -> None:
        swatch_frame = ctk.CTkFrame(parent, fg_color="transparent")
        swatch_frame.grid(row=6, column=0, sticky="ew", pady=(6, 16))
        swatch_frame.grid_columnconfigure(0, weight=1)

        for index, (label, color) in enumerate(NODE_COLOR_CHOICES):
            image = Image.new("RGB", (42, 26), color)
            color_image = ctk.CTkImage(
                light_image=image,
                dark_image=image,
                size=(42, 26),
            )
            button = ctk.CTkButton(
                swatch_frame,
                text=label,
                image=color_image,
                compound="left",
                command=lambda selected=color: self._select_color(selected),
                height=56,
                corner_radius=0,
                border_width=1,
                border_color=BORDER_COLOR,
                fg_color=SURFACE_BACKGROUND,
                hover_color="#EEF2F5",
                text_color=TEXT_DARK,
                font=make_font(12),
                anchor="w",
            )
            button.grid(row=index, column=0, sticky="ew", pady=(0, 8))
            self.color_images[color] = color_image
            self.color_buttons[color] = button

        self._refresh_swatches()

    def _build_actions(self, parent: ctk.CTkFrame) -> None:
        actions = ctk.CTkFrame(parent, fg_color="transparent")
        actions.grid(row=7, column=0, sticky="e")

        ctk.CTkButton(
            actions,
            text="Cancelar",
            fg_color=PRIMARY_BUTTON,
            hover_color=PRIMARY_BUTTON_ACTIVE,
            command=self.destroy,
            width=90,
            corner_radius=0,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            actions,
            text="Guardar",
            fg_color=PRIMARY_BUTTON,
            hover_color=PRIMARY_BUTTON_ACTIVE,
            command=self._save,
            width=90,
            corner_radius=0,
        ).pack(side="left")

    def _save(self) -> None:
        name = "\n".join(
            self._normalize_person_line(line)
            for line in self.name_entry.get("1.0", "end-1c").splitlines()
            if self._normalize_person_line(line)
        )
        role = self.role_var.get().strip()
        if not name:
            self.name_entry.focus_set()
            return

        self.on_save(name, role, self.selected_color)
        self.destroy()

    def _ignore_enter(self, _event: tk.Event[tk.Text]) -> str:
        return "break"

    def _insert_name_line(self, _event: tk.Event[tk.Text]) -> str:
        self.name_entry.insert("insert", f"\n{self.PERSON_BULLET_PREFIX}")
        self.name_entry.see("insert")
        return "break"

    def _populate_name_entry(self) -> None:
        people = [
            self._normalize_person_line(line)
            for line in self.initial_name.splitlines()
        ]
        people = [person for person in people if person]
        if not people:
            self.name_entry.insert("1.0", self.PERSON_BULLET_PREFIX)
            return
        self.name_entry.insert(
            "1.0",
            "\n".join(f"{self.PERSON_BULLET_PREFIX}{person}" for person in people),
        )

    def _normalize_person_line(self, line: str) -> str:
        cleaned = line.strip()
        if not cleaned:
            return ""
        if cleaned.startswith(self.PERSON_BULLET_PREFIX):
            return cleaned[len(self.PERSON_BULLET_PREFIX):].strip()
        if cleaned.startswith("- "):
            return cleaned[2:].strip()
        return cleaned.lstrip("•").strip()

    def _select_color(self, color: str) -> None:
        self.selected_color = color
        self._refresh_swatches()

    def _refresh_swatches(self) -> None:
        for color, button in self.color_buttons.items():
            outline = SELECTED_OUTLINE if color == self.selected_color else BORDER_COLOR
            width = 2 if color == self.selected_color else 1
            button.configure(border_color=outline, border_width=width)
