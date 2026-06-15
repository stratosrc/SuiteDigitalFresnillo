"""Dialog used to configure rectangle metadata."""

import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk

from App_TestData.config.ui_strings import CONCEPT_DIALOG
from App_TestData.config.settings import (
    CONCEPT_DIALOG_HEIGHT,
    CONCEPT_DIALOG_MIN_HEIGHT,
    CONCEPT_DIALOG_MIN_WIDTH,
    CONCEPT_DIALOG_WIDTH,
    LISTBOX_FONT_NAME,
    LISTBOX_FONT_SIZE,
    LISTBOX_HEIGHT,
    SPINBOX_DEFAULT_VALUE,
    SPINBOX_MAX_VALUE,
    SPINBOX_MIN_VALUE,
)
from App_TestData.utils.validation import is_within_range, parse_int
from App_TestData.ui.widgets.factory import build_font, create_entry
from components.styles.styles import (
    APP_BG,
    BORDER_BG,
    BUTTON_BG,
    BUTTON_BG_ACTIVE,
    BUTTON_BG_PRESSED,
    DARK_BG_ACTIVE,
    PLACEHOLDER_TEXT,
    SURFACE_BG,
    TEXT_DARK,
    TEXT_LIGHT,
)


def _create_number_entry(parent, textvariable=None):
    entry = create_entry(parent, textvariable=textvariable, width=76)
    if textvariable is None:
        entry.insert(0, str(SPINBOX_DEFAULT_VALUE))
    return entry


class ConceptDialog(ctk.CTkToplevel):
    """Dialog window that classifies a new censorship rectangle."""

    def __init__(self, parent, catalogue_items, initial_data=None):
        super().__init__(parent)
        self.owner_app = parent
        self.catalogue_items = catalogue_items
        self.initial_data = initial_data or {}
        self.filtered_item_ids = []
        self.result = None
        self.reserved_widgets = {}
        self.confidential_widgets = {}
        self.other_law_widgets = {}

        self.title(CONCEPT_DIALOG["title"])
        self.geometry(f"{max(CONCEPT_DIALOG_WIDTH, 540)}x{max(CONCEPT_DIALOG_HEIGHT, 550)}")
        self.minsize(max(CONCEPT_DIALOG_MIN_WIDTH, 540), max(CONCEPT_DIALOG_MIN_HEIGHT, 550))
        self.configure(fg_color=APP_BG)
        self.transient(parent)
        self.grab_set()

        self._build_ui()
        self._filter_list()
        self._apply_initial_data()
        self.bind("<Return>", lambda _event: self._on_accept())
        self.geometry(f"+{parent.winfo_rootx() + 50}+{parent.winfo_rooty() + 50}")

    def _build_ui(self):
        main_frame = ctk.CTkFrame(self, fg_color=APP_BG, corner_radius=0)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)

        ctk.CTkLabel(
            main_frame,
            text=CONCEPT_DIALOG["heading"],
            fg_color=APP_BG,
            text_color=TEXT_DARK,
            font=build_font(14, "bold"),
        ).pack(anchor=tk.W, pady=(0, 10))

        self.tab_view = ctk.CTkTabview(
            main_frame,
            fg_color=APP_BG,
            segmented_button_fg_color=BUTTON_BG_PRESSED,
            segmented_button_selected_color=BUTTON_BG_ACTIVE,
            segmented_button_selected_hover_color=BUTTON_BG_ACTIVE,
            segmented_button_unselected_color=BUTTON_BG,
            segmented_button_unselected_hover_color=BUTTON_BG_ACTIVE,
            text_color=TEXT_LIGHT,
        )
        self.tab_view.pack(fill=tk.BOTH, expand=True)

        general_tab = self.tab_view.add(CONCEPT_DIALOG["tabs"]["general"])
        reserved_tab = self.tab_view.add(CONCEPT_DIALOG["tabs"]["reserved"])
        confidential_tab = self.tab_view.add(CONCEPT_DIALOG["tabs"]["confidential"])
        other_law_tab = self.tab_view.add(CONCEPT_DIALOG["tabs"]["other_law"])

        self._build_general_tab(general_tab)
        self.reserved_widgets = self._build_classification_tab(
            reserved_tab,
            history=getattr(self.owner_app, "reserved_history", []),
        )
        self.confidential_widgets = self._build_classification_tab(
            confidential_tab,
            history=getattr(self.owner_app, "confidential_history", []),
        )
        self.other_law_widgets = self._build_other_law_tab(
            other_law_tab,
            history=getattr(self.owner_app, "other_law_history", []),
        )

        button_frame = ctk.CTkFrame(main_frame, fg_color=APP_BG, corner_radius=0)
        button_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(12, 0))

        ctk.CTkButton(
            button_frame,
            text=CONCEPT_DIALOG["buttons"]["cancel"],
            command=self.destroy,
            fg_color=BUTTON_BG,
            hover_color=BUTTON_BG_ACTIVE,
            font=build_font(12),
            width=96,
            corner_radius=0,
        ).pack(side=tk.RIGHT, padx=(8, 0))

        ctk.CTkButton(
            button_frame,
            text=CONCEPT_DIALOG["buttons"]["accept"],
            command=self._on_accept,
            fg_color=BUTTON_BG,
            hover_color=BUTTON_BG_ACTIVE,
            font=build_font(12),
            width=96,
            corner_radius=0,
        ).pack(side=tk.RIGHT)

    def _build_general_tab(self, tab):
        ctk.CTkLabel(
            tab,
            text=CONCEPT_DIALOG["general_fields"]["search"],
            fg_color=APP_BG,
            text_color=TEXT_DARK,
            font=build_font(12),
        ).pack(anchor=tk.W)

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_args: self._filter_list())
        search_entry = create_entry(tab, textvariable=self.search_var)
        search_entry.pack(fill=tk.X, pady=(6, 12))
        search_entry.focus_set()

        list_frame = ctk.CTkFrame(tab, fg_color=APP_BG, corner_radius=0)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 14))
        scrollbar = ctk.CTkScrollbar(list_frame, orientation="vertical")
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            height=LISTBOX_HEIGHT,
            font=build_font(15),
            bg=SURFACE_BG,
            fg=TEXT_DARK,
            selectbackground=DARK_BG_ACTIVE,
            selectforeground=TEXT_LIGHT,
            activestyle="none",
            relief="flat",
            highlightthickness=1,
            highlightbackground=BORDER_BG,
            highlightcolor=BORDER_BG,
        )
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.configure(command=self.listbox.yview)

        config_frame = ctk.CTkFrame(tab, fg_color=APP_BG, corner_radius=0)
        config_frame.pack(fill=tk.X, pady=(0, 12))

        ctk.CTkLabel(
            config_frame,
            text=CONCEPT_DIALOG["general_fields"]["rows"],
            fg_color=APP_BG,
            text_color=TEXT_DARK,
            font=build_font(12),
        ).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.rows_entry = _create_number_entry(config_frame)
        self.rows_entry.grid(row=0, column=1, sticky=tk.W, padx=10, pady=5)

        ctk.CTkLabel(
            config_frame,
            text=CONCEPT_DIALOG["general_fields"]["paragraphs"],
            fg_color=APP_BG,
            text_color=TEXT_DARK,
            font=build_font(12),
        ).grid(row=1, column=0, sticky=tk.W, pady=5)
        self.paragraphs_entry = _create_number_entry(config_frame)
        self.paragraphs_entry.grid(row=1, column=1, sticky=tk.W, padx=10, pady=5)

    def _build_classification_tab(self, tab, history):
        widgets = {
            "legal_basis": tk.StringVar(),
            "reason": tk.StringVar(),
            "paragraphs": tk.StringVar(value=str(SPINBOX_DEFAULT_VALUE)),
            "rows": tk.StringVar(value=str(SPINBOX_DEFAULT_VALUE)),
        }
        fields = [
            ("legal_basis", widgets["legal_basis"]),
            ("reason", widgets["reason"]),
            ("paragraphs", widgets["paragraphs"]),
            ("rows", widgets["rows"]),
        ]

        for row_index, (field_name, variable) in enumerate(fields):
            ctk.CTkLabel(
                tab,
                text=CONCEPT_DIALOG["classification_fields"][field_name],
                fg_color=APP_BG,
                text_color=TEXT_DARK,
                font=build_font(12),
            ).grid(row=row_index, column=0, sticky=tk.W, pady=5)
            entry = create_entry(tab, textvariable=variable) if row_index < 2 else _create_number_entry(tab, textvariable=variable)
            entry.grid(row=row_index, column=1, sticky=tk.EW, padx=(10, 0), pady=5)
            widgets[f"{field_name}_entry"] = entry

        ctk.CTkLabel(
            tab,
            text=CONCEPT_DIALOG["classification_fields"]["history"],
            fg_color=APP_BG,
            text_color=TEXT_DARK,
            font=build_font(12),
        ).grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=(14, 4))

        history_box = tk.Listbox(
            tab,
            height=5,
            font=(LISTBOX_FONT_NAME, LISTBOX_FONT_SIZE),
            bg=SURFACE_BG,
            relief="flat",
        )
        history_box.grid(row=5, column=0, columnspan=2, sticky=tk.NSEW)
        for item in history[-10:]:
            history_box.insert(tk.END, self._format_classification_history(item))
        history_box.bind(
            "<ButtonRelease-1>",
            lambda _event, listbox=history_box, history_items=history, widget_map=widgets: self._apply_classification_history(
                listbox,
                history_items,
                widget_map,
            ),
        )

        tab.columnconfigure(1, weight=1)
        tab.rowconfigure(5, weight=1)
        widgets["history_box"] = history_box
        return widgets

    def _build_other_law_tab(self, tab, history):
        widgets = {
            "object": tk.StringVar(),
            "articles": tk.StringVar(),
            "law": tk.StringVar(),
            "paragraphs": tk.StringVar(value=str(SPINBOX_DEFAULT_VALUE)),
            "rows": tk.StringVar(value=str(SPINBOX_DEFAULT_VALUE)),
        }
        fields = [
            ("object", widgets["object"]),
            ("articles", widgets["articles"]),
            ("law", widgets["law"]),
            ("paragraphs", widgets["paragraphs"]),
            ("rows", widgets["rows"]),
        ]

        for row_index, (field_name, variable) in enumerate(fields):
            ctk.CTkLabel(
                tab,
                text=CONCEPT_DIALOG["other_law_fields"][field_name],
                fg_color=APP_BG,
                text_color=TEXT_DARK,
                font=build_font(12),
            ).grid(row=row_index, column=0, sticky=tk.W, pady=5)
            if row_index < 3:
                entry = create_entry(tab, textvariable=variable)
                self._setup_placeholder(entry, CONCEPT_DIALOG["placeholders"][field_name])
            else:
                entry = _create_number_entry(tab, textvariable=variable)
            entry.grid(row=row_index, column=1, sticky=tk.EW, padx=(10, 0), pady=5)
            widgets[f"{field_name}_entry"] = entry

        ctk.CTkLabel(
            tab,
            text=CONCEPT_DIALOG["other_law_fields"]["history"],
            fg_color=APP_BG,
            text_color=TEXT_DARK,
            font=build_font(12),
        ).grid(row=5, column=0, columnspan=2, sticky=tk.W, pady=(14, 4))

        history_box = tk.Listbox(
            tab,
            height=5,
            font=(LISTBOX_FONT_NAME, LISTBOX_FONT_SIZE),
            bg=SURFACE_BG,
            relief="flat",
        )
        history_box.grid(row=6, column=0, columnspan=2, sticky=tk.NSEW)
        for item in history[-10:]:
            history_box.insert(tk.END, self._format_other_law_history(item))
        history_box.bind(
            "<ButtonRelease-1>",
            lambda _event, listbox=history_box, history_items=history, widget_map=widgets: self._apply_other_law_history(
                listbox,
                history_items,
                widget_map,
            ),
        )

        tab.columnconfigure(1, weight=1)
        tab.rowconfigure(6, weight=1)
        widgets["history_box"] = history_box
        return widgets

    def _setup_placeholder(self, entry, placeholder_text):
        def on_focus_in(_event):
            if entry.get() == placeholder_text:
                entry.delete(0, tk.END)
                entry.configure(text_color=TEXT_DARK)

        def on_focus_out(_event):
            if not entry.get().strip():
                entry.insert(0, placeholder_text)
                entry.configure(text_color=PLACEHOLDER_TEXT)

        entry.insert(0, placeholder_text)
        entry.configure(text_color=PLACEHOLDER_TEXT)
        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)

    def _filter_list(self):
        search_term = self.search_var.get().lower()
        self.listbox.delete(0, tk.END)
        self.filtered_item_ids = []
        for item_id, name in self.catalogue_items:
            if search_term in name.lower() or search_term in str(item_id):
                self.listbox.insert(tk.END, f"{item_id}. {name}")
                self.filtered_item_ids.append(item_id)

        if self.filtered_item_ids:
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(0)
            self.listbox.activate(0)

    def _apply_initial_data(self):
        if not self.initial_data:
            return

        classification = self.initial_data.get("classification", "general")
        if classification == "reserved":
            self.tab_view.set(CONCEPT_DIALOG["tabs"]["reserved"])
            self._set_classification_fields(self.reserved_widgets)
        elif classification == "confidential":
            self.tab_view.set(CONCEPT_DIALOG["tabs"]["confidential"])
            self._set_classification_fields(self.confidential_widgets)
        elif classification == "other_law":
            self.tab_view.set(CONCEPT_DIALOG["tabs"]["other_law"])
            self._set_other_law_fields()
        else:
            self.tab_view.set(CONCEPT_DIALOG["tabs"]["general"])
            self._set_general_fields()

    def _set_general_fields(self):
        concept_id = self.initial_data.get("concept_id")
        self._set_entry_text(self.rows_entry, self.initial_data.get("rows", SPINBOX_DEFAULT_VALUE))
        self._set_entry_text(self.paragraphs_entry, self.initial_data.get("paragraphs", SPINBOX_DEFAULT_VALUE))
        if concept_id not in self.filtered_item_ids:
            return

        index = self.filtered_item_ids.index(concept_id)
        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(index)
        self.listbox.activate(index)
        self.listbox.see(index)

    def _set_classification_fields(self, widgets):
        widgets["legal_basis"].set(self.initial_data.get("legal_basis", ""))
        widgets["reason"].set(self.initial_data.get("reason", ""))
        widgets["paragraphs"].set(str(self.initial_data.get("paragraphs", SPINBOX_DEFAULT_VALUE)))
        widgets["rows"].set(str(self.initial_data.get("rows", SPINBOX_DEFAULT_VALUE)))

    def _set_other_law_fields(self):
        for field_name in ("object", "articles", "law", "paragraphs", "rows"):
            value = self.initial_data.get(field_name, SPINBOX_DEFAULT_VALUE if field_name in {"paragraphs", "rows"} else "")
            self.other_law_widgets[field_name].set(str(value))
            entry = self.other_law_widgets.get(f"{field_name}_entry")
            if entry is not None and str(value).strip():
                entry.configure(text_color=TEXT_DARK)

    def _set_entry_text(self, entry, value):
        entry.delete(0, tk.END)
        entry.insert(0, str(value))

    def _on_accept(self):
        selected_tab = self.tab_view.get()
        if selected_tab == CONCEPT_DIALOG["tabs"]["general"]:
            self._accept_general()
        elif selected_tab == CONCEPT_DIALOG["tabs"]["reserved"]:
            self._accept_classification("reserved", self.reserved_widgets)
        elif selected_tab == CONCEPT_DIALOG["tabs"]["confidential"]:
            self._accept_classification("confidential", self.confidential_widgets)
        else:
            self._accept_other_law()

    def _accept_general(self):
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showwarning(
                CONCEPT_DIALOG["warnings"]["selection_required_title"],
                CONCEPT_DIALOG["warnings"]["selection_required_message"],
                parent=self,
            )
            return

        try:
            rows = parse_int(self.rows_entry.get())
            paragraphs = parse_int(self.paragraphs_entry.get())
        except ValueError:
            messagebox.showwarning(
                CONCEPT_DIALOG["warnings"]["invalid_value_title"],
                CONCEPT_DIALOG["warnings"]["general_integer_message"],
                parent=self,
            )
            return

        if not (
            is_within_range(rows, SPINBOX_MIN_VALUE, SPINBOX_MAX_VALUE)
            and is_within_range(paragraphs, SPINBOX_MIN_VALUE, SPINBOX_MAX_VALUE)
        ):
            messagebox.showwarning(
                CONCEPT_DIALOG["warnings"]["invalid_value_title"],
                CONCEPT_DIALOG["warnings"]["general_range_message"],
                parent=self,
            )
            return

        self.result = {
            "classification": "general",
            "concept_id": self.filtered_item_ids[selection[0]],
            "rows": rows,
            "paragraphs": paragraphs,
        }
        self.destroy()

    def _accept_classification(self, classification, widgets):
        try:
            rows = parse_int(widgets["rows"].get())
            paragraphs = parse_int(widgets["paragraphs"].get())
        except ValueError:
            messagebox.showwarning(
                CONCEPT_DIALOG["warnings"]["invalid_value_title"],
                CONCEPT_DIALOG["warnings"]["classification_integer_message"],
                parent=self,
            )
            return

        if not (
            is_within_range(rows, SPINBOX_MIN_VALUE, SPINBOX_MAX_VALUE)
            and is_within_range(paragraphs, SPINBOX_MIN_VALUE, SPINBOX_MAX_VALUE)
        ):
            messagebox.showwarning(
                CONCEPT_DIALOG["warnings"]["invalid_value_title"],
                CONCEPT_DIALOG["warnings"]["classification_range_message"],
                parent=self,
            )
            return

        history_item = {
            "legal_basis": widgets["legal_basis"].get().strip(),
            "reason": widgets["reason"].get().strip(),
            "paragraphs": paragraphs,
            "rows": rows,
        }
        target_history = (
            self.owner_app.reserved_history
            if classification == "reserved"
            else self.owner_app.confidential_history
        )
        self._add_history_item(target_history, history_item)
        self.result = {"classification": classification, **history_item}
        self.destroy()

    def _accept_other_law(self):
        widgets = self.other_law_widgets
        try:
            rows = parse_int(widgets["rows"].get())
            paragraphs = parse_int(widgets["paragraphs"].get())
        except ValueError:
            messagebox.showwarning(
                CONCEPT_DIALOG["warnings"]["invalid_value_title"],
                CONCEPT_DIALOG["warnings"]["classification_integer_message"],
                parent=self,
            )
            return

        if not (
            is_within_range(rows, SPINBOX_MIN_VALUE, SPINBOX_MAX_VALUE)
            and is_within_range(paragraphs, SPINBOX_MIN_VALUE, SPINBOX_MAX_VALUE)
        ):
            messagebox.showwarning(
                CONCEPT_DIALOG["warnings"]["invalid_value_title"],
                CONCEPT_DIALOG["warnings"]["classification_range_message"],
                parent=self,
            )
            return

        history_item = {
            "object": widgets["object"].get().strip(),
            "articles": widgets["articles"].get().strip(),
            "law": widgets["law"].get().strip(),
            "paragraphs": paragraphs,
            "rows": rows,
        }
        self._add_history_item(self.owner_app.other_law_history, history_item)
        self.result = {"classification": "other_law", **history_item}
        self.destroy()

    def _add_history_item(self, history, item):
        history[:] = [existing for existing in history if existing != item]
        history.append(item)
        del history[:-10]

    def _apply_classification_history(self, listbox, history, widgets):
        selection = listbox.curselection()
        if not selection:
            return
        item = history[-10:][selection[0]]
        widgets["legal_basis"].set(item.get("legal_basis", ""))
        widgets["reason"].set(item.get("reason", ""))
        widgets["paragraphs"].set(str(item.get("paragraphs", SPINBOX_DEFAULT_VALUE)))
        widgets["rows"].set(str(item.get("rows", SPINBOX_DEFAULT_VALUE)))

    def _apply_other_law_history(self, listbox, history, widgets):
        selection = listbox.curselection()
        if not selection:
            return
        item = history[-10:][selection[0]]
        widgets["object"].set(item.get("object", ""))
        widgets["articles"].set(item.get("articles", ""))
        widgets["law"].set(item.get("law", ""))
        widgets["paragraphs"].set(str(item.get("paragraphs", SPINBOX_DEFAULT_VALUE)))
        widgets["rows"].set(str(item.get("rows", SPINBOX_DEFAULT_VALUE)))

    def _format_classification_history(self, item):
        return f"{item.get('reason', '')} | {item.get('legal_basis', '')}"

    def _format_other_law_history(self, item):
        return f"{item.get('object', '')} | {item.get('articles', '')} | {item.get('law', '')}"
