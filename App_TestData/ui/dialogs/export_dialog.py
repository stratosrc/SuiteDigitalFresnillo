"""Dialog used to choose the export variant."""

import tkinter as tk

import customtkinter as ctk

from App_TestData.config.ui_strings import EXPORT_DIALOG
from App_TestData.ui.widgets.factory import build_font
from components.shared.accessibility import enable_visible_focus
from components.styles.styles import (
    APP_BG,
    BORDER_BG,
    BUTTON_BG,
    BUTTON_BG_ACTIVE,
    BUTTON_BG_PRESSED,
    SURFACE_BG,
    TEXT_DARK,
    TEXT_LIGHT,
)


class ExportDialog(ctk.CTkToplevel):
    """Intermediate dialog that lets the user choose the export flow."""

    def __init__(self, app, export_callback=None):
        super().__init__(app)
        self.app = app
        self.export_callback = export_callback or app._generate_pdf
        self.committee_vars = {}
        self.quality_var = tk.StringVar(value="standard")

        self.title(EXPORT_DIALOG["title"])
        self.geometry("640x500")
        self.minsize(600, 480)
        self.configure(fg_color=APP_BG)
        self.transient(app)
        self.grab_set()

        quality_frame = ctk.CTkFrame(
            self,
            fg_color=SURFACE_BG,
            border_color=BORDER_BG,
            border_width=1,
            corner_radius=0,
            height=58,
        )
        quality_frame.pack(fill=tk.X, padx=16, pady=(16, 0))
        quality_frame.pack_propagate(False)

        quality_selector = ctk.CTkFrame(
            quality_frame,
            fg_color="transparent",
            corner_radius=0,
        )
        quality_selector.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        ctk.CTkLabel(
            quality_selector,
            text=EXPORT_DIALOG["quality"]["heading"],
            fg_color=SURFACE_BG,
            text_color=TEXT_DARK,
            font=build_font(13, "bold"),
        ).pack(side=tk.LEFT, padx=(0, 18))

        for value, label_key in (("standard", "standard"), ("compact", "compact")):
            ctk.CTkRadioButton(
                quality_selector,
                text=EXPORT_DIALOG["quality"][label_key],
                variable=self.quality_var,
                value=value,
                fg_color=BUTTON_BG_ACTIVE,
                hover_color=BUTTON_BG,
                text_color=TEXT_DARK,
                font=build_font(12),
                width=112,
            ).pack(side=tk.LEFT, padx=6)

        tab_view = ctk.CTkTabview(
            self,
            fg_color=APP_BG,
            segmented_button_fg_color=BUTTON_BG_PRESSED,
            segmented_button_selected_color=BUTTON_BG_ACTIVE,
            segmented_button_selected_hover_color=BUTTON_BG_ACTIVE,
            segmented_button_unselected_color=BUTTON_BG,
            segmented_button_unselected_hover_color=BUTTON_BG_ACTIVE,
            text_color=TEXT_LIGHT,
            corner_radius=0,
        )
        tab_view.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)

        area_frame = tab_view.add(EXPORT_DIALOG["tabs"]["area"])
        committee_frame = tab_view.add(EXPORT_DIALOG["tabs"]["committee"])
        self.after_idle(lambda: enable_visible_focus(self))

        ctk.CTkButton(
            area_frame,
            text=EXPORT_DIALOG["buttons"]["standard"],
            command=self._export_standard,
            fg_color=BUTTON_BG,
            hover_color=BUTTON_BG_ACTIVE,
            text_color=TEXT_LIGHT,
            font=build_font(13, "bold"),
            corner_radius=0,
            height=36,
        ).pack(anchor=tk.CENTER, pady=95)

        for row_index, (label_text, field_key) in enumerate(EXPORT_DIALOG["committee_fields"]):
            ctk.CTkLabel(
                committee_frame,
                text=label_text,
                fg_color=APP_BG,
                text_color=TEXT_DARK,
                font=build_font(12),
            ).grid(row=row_index, column=0, sticky=tk.W, pady=5, padx=(10, 0))

            variable = tk.StringVar()
            entry = ctk.CTkEntry(
                committee_frame,
                textvariable=variable,
                height=30,
                fg_color=SURFACE_BG,
                text_color=TEXT_DARK,
                border_color=BORDER_BG,
                corner_radius=0,
                font=build_font(12),
            )
            entry.grid(row=row_index, column=1, sticky=tk.EW, pady=5)
            self.committee_vars[field_key] = variable

        committee_frame.columnconfigure(1, weight=1)
        ctk.CTkButton(
            committee_frame,
            text=EXPORT_DIALOG["buttons"]["committee"],
            command=self._export_committee,
            fg_color=BUTTON_BG,
            hover_color=BUTTON_BG_ACTIVE,
            text_color=TEXT_LIGHT,
            font=build_font(13, "bold"),
            corner_radius=0,
            height=36,
        ).grid(row=len(EXPORT_DIALOG["committee_fields"]), column=0, columnspan=2, sticky=tk.EW, pady=(18, 0))

    def _export_standard(self):
        self.destroy()
        self.export_callback(export_quality=self.quality_var.get())

    def _export_committee(self):
        committee_data = {
            key: value.get().strip()
            for key, value in self.committee_vars.items()
        }
        self.destroy()
        self.export_callback(
            committee_data=committee_data,
            export_quality=self.quality_var.get(),
        )
