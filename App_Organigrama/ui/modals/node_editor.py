from collections.abc import Callable
import tkinter as tk

import customtkinter as ctk

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
        self.resizable(False, False)
        self.configure(fg_color=SURFACE_BACKGROUND)
        self.transient(master.winfo_toplevel())
        self.grab_set()

        self.on_save = on_save
        self.initial_name = name
        self.role_var = tk.StringVar(value=role)
        self.selected_color = selected_color or NODE_COLOR_CHOICES[0][1]
        self.swatches: dict[str, tk.Canvas] = {}

        self._build()
        self.after_idle(lambda: enable_visible_focus(self))
        self.after(60, self.name_entry.focus_set)

    def _build(self) -> None:
        frame = ctk.CTkFrame(self, fg_color=SURFACE_BACKGROUND, corner_radius=0)
        frame.pack(fill="both", expand=True, padx=18, pady=18)
        frame.grid_columnconfigure(0, weight=1)

        self._build_label(frame, "Nombre(s)", row=0)
        self.name_entry = ctk.CTkTextbox(frame, width=340, height=120, corner_radius=0)
        self.name_entry.grid(row=1, column=0, sticky="ew", pady=(4, 4))
        self.name_entry.insert("1.0", self.initial_name)
        self.name_entry.bind("<Return>", self._ignore_enter)
        self.name_entry.bind("<KP_Enter>", self._ignore_enter)
        self.name_entry.bind("<Control-Return>", self._insert_name_line)
        self.name_entry.bind("<Control-KP_Enter>", self._insert_name_line)
        ctk.CTkLabel(
            frame,
            text="Ctrl + Enter agrega otra persona",
            text_color=TEXT_DARK,
            font=make_font(10),
        ).grid(row=2, column=0, sticky="w", pady=(0, 12))

        self._build_label(frame, "Cargo", row=3)
        ctk.CTkEntry(frame, textvariable=self.role_var, width=340, corner_radius=0).grid(
            row=4,
            column=0,
            sticky="ew",
            pady=(4, 12),
        )

        self._build_label(frame, "Color", row=5)
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
        swatch_frame.grid(row=6, column=0, sticky="w", pady=(6, 16))

        for index, (_label, color) in enumerate(NODE_COLOR_CHOICES):
            swatch = tk.Canvas(
                swatch_frame,
                width=34,
                height=26,
                bg=SURFACE_BACKGROUND,
                highlightthickness=0,
                cursor="hand2",
            )
            swatch.grid(row=0, column=index, padx=(0, 8))
            swatch.create_rectangle(3, 3, 31, 23, fill=color, outline=BORDER_COLOR, width=1, tags="fill")
            swatch.bind("<Button-1>", lambda _event, selected=color: self._select_color(selected))
            self.swatches[color] = swatch

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
            line.strip()
            for line in self.name_entry.get("1.0", "end-1c").splitlines()
            if line.strip()
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
        self.name_entry.insert("insert", "\n")
        self.name_entry.see("insert")
        return "break"

    def _select_color(self, color: str) -> None:
        self.selected_color = color
        self._refresh_swatches()

    def _refresh_swatches(self) -> None:
        for color, swatch in self.swatches.items():
            outline = SELECTED_OUTLINE if color == self.selected_color else BORDER_COLOR
            width = 3 if color == self.selected_color else 1
            swatch.itemconfigure("fill", outline=outline, width=width)
