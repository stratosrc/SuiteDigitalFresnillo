"""Rectangle action coordination for Test Data."""

from __future__ import annotations


import tkinter as tk

from App_TestData.domain.redaction_editing import (
    delete_selected_rectangle,
    redo_last_rectangle,
    refresh_rectangle_metadata,
    undo_last_rectangle,
)


class RectangleActionController:
    """Own undo, redo and delete behavior for redaction rectangles."""

    def __init__(self, app) -> None:
        self.app = app

    def handle_action(self, action_type: str) -> None:
        if action_type == "delete":
            rectangles, selected_rect_id, affected_rectangle, action = delete_selected_rectangle(
                self.app.censored_rectangles,
                self.app.selected_rect_id,
            )
            if action is not None:
                self.app.undo_stack.append(action)
                self.app.redo_stack.clear()
            self.app.censored_rectangles = rectangles
            self.app.selected_rect_id = selected_rect_id
        elif action_type == "undo":
            rectangles, undo_stack, redo_stack, affected_rectangle = undo_last_rectangle(
                self.app.censored_rectangles,
                list(self.app.undo_stack),
                list(self.app.redo_stack),
            )
            self.app.censored_rectangles = rectangles
            self._replace_stack(self.app.undo_stack, undo_stack)
            self._replace_stack(self.app.redo_stack, redo_stack)
            self.app.selected_rect_id = None
        elif action_type == "redo":
            rectangles, undo_stack, redo_stack, affected_rectangle = redo_last_rectangle(
                self.app.censored_rectangles,
                list(self.app.undo_stack),
                list(self.app.redo_stack),
            )
            self.app.censored_rectangles = rectangles
            self._replace_stack(self.app.undo_stack, undo_stack)
            self._replace_stack(self.app.redo_stack, redo_stack)
            self.app.selected_rect_id = None
        else:
            return

        if affected_rectangle:
            self._hide_canvas_item(affected_rectangle.get("canvas_rect_id"))
            self._hide_canvas_item(affected_rectangle.get("canvas_text_id"))

        refresh_rectangle_metadata(self.app.censored_rectangles)
        self.sync_delete_button_state()
        if self.app.pdf_document:
            self.app.pdf_manager.render_current_page()

    def sync_delete_button_state(self) -> None:
        delete_button = getattr(self.app, "delete_rect_btn", None)
        if delete_button is not None:
            has_selection = bool(self.app.selected_rect_id)
            delete_button.configure(
                state=tk.NORMAL if has_selection else tk.DISABLED,
                fg_color=(
                    getattr(delete_button, "_normal_fg_color", None)
                    if has_selection
                    else getattr(delete_button, "_disabled_fg_color", None)
                ),
            )
            tooltip = getattr(delete_button, "tooltip", None)
            if tooltip is not None:
                tooltip.text = (
                    getattr(delete_button, "_tooltip_text", "")
                    if has_selection
                    else getattr(delete_button, "_disabled_tooltip_text", "")
                )

    def _replace_stack(self, target_stack, new_items) -> None:
        target_stack.clear()
        for item in new_items:
            target_stack.append(item)

    def _hide_canvas_item(self, item_id) -> None:
        if item_id:
            self.app.pdf_canvas.itemconfigure(item_id, state="hidden")
