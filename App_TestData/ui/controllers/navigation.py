"""Page navigation and zoom coordination for Test Data."""

from __future__ import annotations


from tkinter import messagebox
import tkinter as tk

from App_TestData.config.ui_strings import NAVIGATION_MESSAGES
from App_TestData.utils.navigation import (
    get_adjacent_page_index,
    is_valid_page_index,
    parse_page_number,
    to_page_index,
)
from App_TestData.utils.zoom import format_zoom_percentage, get_next_zoom


class NavigationController:
    """Own page navigation and zoom behavior for the PDF viewer."""

    def __init__(self, app) -> None:
        self.app = app

    def navigate_page(self, action: str) -> None:
        if not self.app.pdf_document:
            self.update_page_state()
            return

        next_page = get_adjacent_page_index(self.app.current_page, len(self.app.pdf_document), action)
        if next_page == self.app.current_page:
            self.update_page_state()
            return

        self.app.current_page = next_page
        self.app.pdf_manager.render_current_page()

    def go_to_page_from_entry(self) -> None:
        if not self.app.pdf_document:
            messagebox.showwarning(
                NAVIGATION_MESSAGES["pdf_required_title"],
                NAVIGATION_MESSAGES["pdf_required_message"],
                parent=self.app,
            )
            return

        try:
            page_number = parse_page_number(self.app.page_entry.get())
        except ValueError:
            messagebox.showwarning(
                NAVIGATION_MESSAGES["invalid_page_title"],
                NAVIGATION_MESSAGES["invalid_page_message"],
                parent=self.app,
            )
            return

        page_index = to_page_index(page_number)
        total_pages = len(self.app.pdf_document)
        if not is_valid_page_index(page_index, total_pages):
            messagebox.showwarning(
                NAVIGATION_MESSAGES["page_out_of_range_title"],
                NAVIGATION_MESSAGES["page_out_of_range_message"].format(total_pages=total_pages),
                parent=self.app,
            )
            return

        self.app.current_page = page_index
        self.app.pdf_manager.render_current_page()

    def change_zoom(self, action: str) -> None:
        if not self.app.pdf_document:
            return

        next_zoom = get_next_zoom(self.app.current_zoom, action)
        if next_zoom is None or next_zoom == self.app.current_zoom:
            return

        self.app.current_zoom = next_zoom
        self.update_zoom_label()
        self.app.pdf_manager.render_current_page()

    def update_zoom_label(self) -> None:
        zoom_label = getattr(self.app, "zoom_label", None)
        if zoom_label is not None:
            zoom_label.configure(text=format_zoom_percentage(self.app.current_zoom))

    def update_page_state(self, current_page: int | None = None, total_pages: int | None = None) -> None:
        pdf_document = self.app.pdf_document
        total = total_pages if total_pages is not None else (len(pdf_document) if pdf_document else 0)
        page_index = current_page if current_page is not None else self.app.current_page

        previous_button = getattr(self.app, "previous_page_button", None)
        next_button = getattr(self.app, "next_page_button", None)
        if previous_button is not None:
            previous_button.configure(state=tk.NORMAL if total > 0 and page_index > 0 else tk.DISABLED)
        if next_button is not None:
            next_button.configure(state=tk.NORMAL if total > 0 and page_index < total - 1 else tk.DISABLED)
