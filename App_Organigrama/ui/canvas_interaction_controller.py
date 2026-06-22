"""Pointer event dispatch and selection controller."""

from __future__ import annotations

import tkinter as tk

from App_Organigrama.ui.canvas_selection import (
    draw_connection_selection_overlay,
    draw_node_selection_overlay,
)
from App_Organigrama.ui.canvas_state import InteractionMode


GridPoint = tuple[float, float]
SELECTION_BLINK_INTERVAL_MS = 420
CUSTOM_CURSOR_SIZE = 32


class CanvasInteractionController:
    def _bind_events(self) -> None:
        self.canvas.bind("<Configure>", lambda _event: self.request_redraw())
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<ButtonPress-3>", self._on_pan_press)
        self.canvas.bind("<B3-Motion>", self._on_pan_drag)
        self.canvas.bind("<ButtonRelease-3>", self._on_pan_release)
        self.canvas.bind("<Double-Button-1>", self._on_double_click)
        self.canvas.bind("<Motion>", self._on_motion)
        self.canvas.bind("<Leave>", self._on_leave)
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Delete>", self._delete_selected)
        self.canvas.bind("<BackSpace>", self._delete_selected)
        self.canvas.bind("<Escape>", self._cancel_connection)
        self.canvas.bind("<Menu>", self._show_keyboard_context_menu)
        self.canvas.bind("<Shift-F10>", self._show_keyboard_context_menu)
        self.canvas.bind("<Up>", lambda _event: self.scroll_view("up"))
        self.canvas.bind("<Down>", lambda _event: self.scroll_view("down"))
        self.canvas.bind("<Left>", lambda _event: self.scroll_view("left"))
        self.canvas.bind("<Right>", lambda _event: self.scroll_view("right"))
        self.canvas.bind("<Return>", lambda _event: self.edit_selected_node())
        self.canvas.focus_set()

    def _show_keyboard_context_menu(self, _event=None) -> str:
        event = type(
            "ContextEvent",
            (),
            {
                "x": self.canvas.winfo_width() // 2,
                "y": self.canvas.winfo_height() // 2,
                "x_root": self.canvas.winfo_rootx() + self.canvas.winfo_width() // 2,
                "y_root": self.canvas.winfo_rooty() + self.canvas.winfo_height() // 2,
                "keyboard": True,
            },
        )()
        self._show_context_menu(event)
        return "break"

    def _redraw_selection_overlay(self) -> None:
        self.canvas.delete("selection-overlay")
        draw_connection_selection_overlay(self)
        if self.canvas.find_withtag("node"):
            self.canvas.tag_lower("connection-selection-overlay", "node")
        draw_node_selection_overlay(self)
        self.canvas.tag_raise("node-selection-overlay")

    def _on_press(self, event: tk.Event[tk.Canvas]) -> None:
        self.canvas.focus_set()
        self.dragged = False
        self.connection_press_source_id = None
        self.connection_press_source_port = None
        self.drag_press = (event.x, event.y, self.pan_x, self.pan_y)
        if self.block_mode:
            self.drag_press = None
            self._select_or_add_blocked_point(event.x, event.y)
            return
        bend_point = self._selected_bend_point_at_screen(event.x, event.y)
        if bend_point is not None:
            self._clear_retained_manual_ghost()
            route, point_index = bend_point
            self.interaction.transition(InteractionMode.EDITING_ROUTE)
            self.manual_drag_connection_id = route.connection.id
            self.manual_drag_kind = "bend"
            self.manual_drag_point_index = point_index
            self.manual_drag_original_route = route.points
            self.manual_drag_candidate_route = route.points
            self.manual_drag_collision_node_ids = ()
            self._emit_context_change("Arrastra el punto de doblez libremente")
            return
        movable_segment = self._selected_movable_segment_at_screen(event.x, event.y)
        if movable_segment is not None:
            self._clear_retained_manual_ghost()
            route, segment_index = movable_segment
            self.interaction.transition(InteractionMode.EDITING_ROUTE)
            self.manual_drag_connection_id = route.connection.id
            self.manual_drag_kind = "segment"
            self.manual_drag_segment_index = segment_index
            self.manual_drag_original_route = route.points
            self.manual_drag_candidate_route = route.points
            self.manual_drag_collision_node_ids = ()
            self._emit_context_change("Arrastra el segmento en su eje perpendicular")
            return
        node = self._node_at_screen(event.x, event.y)
        port_node = node or self._node_near_screen(event.x, event.y)
        if port_node is not None:
            port = self._nearest_port(port_node, event.x, event.y)
            if node is None or self._is_near_port_marker(
                port_node,
                port,
                event.x,
                event.y,
            ):
                self.interaction.transition(InteractionMode.CONNECTING)
                self.drag_node_id = None
                self.drag_screen_point = None
                self.connection_drag_source_id = port_node.id
                self.connection_drag_source_port = port
                self.connection_drag_screen_point = (event.x, event.y)
                self._update_custom_cursor(visible=False)
                if self.pending_connection_source_id is None:
                    self.pending_connection_source_id = port_node.id
                    self.pending_source_port = port
                self._set_selection(node_id=port_node.id)
                self._emit_context_change()
                self.request_redraw()
                return
        if node is not None:
            self.connection_press_source_id = node.id
            self.connection_press_source_port = self._nearest_port(
                node,
                event.x,
                event.y,
            )
            self._update_custom_cursor(visible=False)
            self._set_selection(node_id=node.id)
            self._emit_context_change()

    def _on_drag(self, event: tk.Event[tk.Canvas]) -> None:
        if self.drag_press is None:
            return
        start_x, start_y, _, _ = self.drag_press
        dx = event.x - start_x
        dy = event.y - start_y
        if abs(dx) < 4 and abs(dy) < 4:
            return
        self.dragged = True
        if self.interaction.mode is InteractionMode.EDITING_ROUTE:
            self._preview_manual_segment_drag(event.x, event.y)
            return
        if (
            self.connection_drag_source_id is None
            and self.connection_press_source_id is not None
        ):
            self.interaction.transition(InteractionMode.CONNECTING)
            self.connection_drag_source_id = self.connection_press_source_id
            self.connection_drag_source_port = self.connection_press_source_port or "bottom"
            self.connection_drag_screen_point = (event.x, event.y)
            if self.pending_connection_source_id is None:
                self.pending_connection_source_id = self.connection_drag_source_id
                self.pending_source_port = self.connection_drag_source_port
            self._update_custom_cursor(visible=False)
        if self.interaction.mode is InteractionMode.CONNECTING:
            self.connection_drag_screen_point = (event.x, event.y)
            target_node = self._node_near_screen(event.x, event.y)
            if (
                target_node is not None
                and target_node.id != self.connection_drag_source_id
            ):
                self.hover_port = (
                    target_node.id,
                    self._nearest_port(target_node, event.x, event.y),
                )
            else:
                self.hover_port = None
        self._emit_context_change()
        self.request_redraw()

    def _on_release(self, event: tk.Event[tk.Canvas]) -> None:
        if self.drag_press is None:
            return
        self.drag_press = None
        if self.interaction.mode is InteractionMode.EDITING_ROUTE:
            self._finish_manual_segment_drag()
            return
        self.drag_node_id = None
        self.drag_screen_point = None
        self.drag_node_offset = None
        self.connection_press_source_id = None
        self.connection_press_source_port = None
        connection_source_id = self.connection_drag_source_id
        connection_source_port = self.connection_drag_source_port
        self.connection_drag_source_id = None
        self.connection_drag_source_port = None
        self.connection_drag_screen_point = None
        if connection_source_id is not None:
            if self.dragged:
                self._finish_connection_drag(
                    connection_source_id,
                    connection_source_port or "bottom",
                    event.x,
                    event.y,
                )
            else:
                self._connect_by_click(
                    connection_source_id,
                    connection_source_port or "bottom",
                    event.x,
                    event.y,
                )
            self.interaction.transition(InteractionMode.IDLE)
            self.request_redraw()
            self._emit_context_change()
            return
        if self.dragged:
            self.interaction.transition(InteractionMode.IDLE)
            self.request_redraw()
            self._emit_context_change()
            return
        self._handle_click(event.x, event.y)

    def _on_motion(self, event: tk.Event[tk.Canvas]) -> None:
        if self.drag_press is not None:
            return
        if self.block_mode:
            self._update_custom_cursor(event.x, event.y, visible=True)
            self.preview_obstacle = self._screen_to_subgrid(event.x, event.y)
            self.request_redraw()
            self._emit_context_change()
            return
        connection = self._connection_at_screen(event.x, event.y)
        node = None if connection is not None else self._node_at_screen(event.x, event.y)
        nearby_node = (
            None if connection is not None else self._node_near_screen(event.x, event.y)
        )
        port_node = node or nearby_node
        self.hover_port = (
            (port_node.id, self._nearest_port(port_node, event.x, event.y))
            if port_node is not None
            else None
        )
        self._update_custom_cursor(
            event.x,
            event.y,
            visible=self.hover_port is not None,
        )
        if node is not None:
            self.last_hover_cell = None
            self.request_redraw()
            self._emit_context_change()
            return
        grid_x, grid_y = self._screen_to_grid(event.x, event.y)
        hover_cell = None if connection is not None else (grid_x, grid_y)
        if hover_cell != self.last_hover_cell:
            self.last_hover_cell = hover_cell
            self.request_redraw()
        self._emit_context_change()

    def _on_leave(self, _event: tk.Event[tk.Canvas]) -> None:
        self.hover_port = None
        self.preview_obstacle = None
        self.last_hover_cell = None
        self._update_custom_cursor(visible=False)
        self.request_redraw()
        self._emit_context_change()

    def _handle_click(self, screen_x: int, screen_y: int) -> None:
        if self.block_mode:
            self._select_or_add_blocked_point(screen_x, screen_y)
            return
        node = self._node_at_screen(screen_x, screen_y)
        if node is not None:
            self._set_selection(node_id=node.id)
            self.request_redraw()
            return
        connection = self._connection_at_screen(screen_x, screen_y)
        if connection is not None:
            self._set_selection(connection_id=connection.connection.id)
            self.request_redraw()
            return
        blocked_point = self._blocked_point_at_screen(screen_x, screen_y)
        if blocked_point is not None:
            self._set_selection(blocked_point=blocked_point)
            self.request_redraw()
            return
        self._cancel_connection()
        grid_x, grid_y = self._screen_to_grid(screen_x, screen_y)
        if self.document.get_node_at(grid_x, grid_y) is None:
            self._open_node_dialog_at(grid_x, grid_y)

    def _set_selection(
        self,
        node_id: str | None = None,
        connection_id: str | None = None,
        blocked_point: GridPoint | None = None,
    ) -> None:
        self.selected_node_id = node_id
        self.selected_connection_id = connection_id
        self.selected_blocked_point = blocked_point
        self._sync_selection_blink()
        self._emit_selection_change()
        self._emit_context_change()

    def _sync_selection_blink(self) -> None:
        has_selection = any(
            (
                self.selected_node_id is not None,
                self.selected_connection_id is not None,
                self.selected_blocked_point is not None,
            )
        )
        if has_selection:
            if self.selection_blink_after_id is None:
                self.selection_blink_visible = True
                self._schedule_selection_blink()
            return
        if self.selection_blink_after_id is not None:
            self.after_cancel(self.selection_blink_after_id)
            self.selection_blink_after_id = None
        self.selection_blink_visible = True

    def _schedule_selection_blink(self) -> None:
        self.selection_blink_after_id = self.after(
            SELECTION_BLINK_INTERVAL_MS,
            self._toggle_selection_blink,
        )

    def _toggle_selection_blink(self) -> None:
        self.selection_blink_after_id = None
        if (
            self.selected_node_id is None
            and self.selected_connection_id is None
            and self.selected_blocked_point is None
        ):
            self.selection_blink_visible = True
            return
        self.selection_blink_visible = not self.selection_blink_visible
        self._redraw_selection_overlay()
        self._schedule_selection_blink()

    def _cancel_connection(self, _event: tk.Event[tk.Canvas] | None = None) -> None:
        self.pending_connection_source_id = None
        self.pending_source_port = None
        self.hover_port = None
        self._clear_manual_drag()
        self.interaction.reset_pointer_action()
        if self.block_mode:
            self.interaction.transition(InteractionMode.BLOCKING)
        self._update_custom_cursor(visible=self.block_mode)
        self.request_redraw()
        self._emit_context_change()

    def _emit_selection_change(self) -> None:
        if self.on_selection_change is not None:
            self.on_selection_change(
                self.selected_node_id is not None
                or self.selected_connection_id is not None
                or self.selected_blocked_point is not None
            )

    def _emit_document_change(self) -> None:
        if self.on_document_change is not None:
            self.on_document_change()

    def _emit_context_change(self, message: str | None = None) -> None:
        if self.on_context_change is not None:
            self.on_context_change(message or self._context_message())

    def _context_message(self) -> str:
        if self.block_mode:
            return "Clic para marcar o quitar obstáculo"
        if self.interaction.mode is InteractionMode.CONNECTING:
            hover_target_id = self._hover_target_id(
                self.connection_drag_source_id or ""
            )
            if hover_target_id is not None:
                return self._connection_flow_message(
                    self.connection_drag_source_id or "",
                    hover_target_id,
                    "Suelta para conectar",
                )
            return "Suelta sobre un nodo para conectar"
        if self.pending_connection_source_id is not None:
            hover_target_id = self._hover_target_id(
                self.pending_connection_source_id
            )
            if hover_target_id is not None:
                return self._connection_flow_message(
                    self.pending_connection_source_id,
                    hover_target_id,
                    "Clic para conectar",
                )
            return "Clic izquierdo en el nodo destino para conectar"
        if self.hover_port is not None:
            return "Clic izquierdo o arrastra desde el indicador para conectar"
        if self.selected_node_id is not None:
            return "Clic derecho y arrastra para mover. Doble clic para editar"
        if self.selected_connection_id is not None:
            connection = self.document.get_connection(self.selected_connection_id)
            if connection is not None:
                suffix = (
                    ". Arrastra un tramo intermedio; puedes restaurar la ruta automática"
                    if connection.manual_points
                    else ". Arrastra un tramo intermedio para ajustar la ruta"
                )
                return self._connection_flow_message(
                    connection.source_id,
                    connection.target_id,
                    "Flujo",
                ) + suffix
            return "Conexión seleccionada. Supr para eliminar"
        if self.selected_blocked_point is not None:
            return "Obstáculo seleccionado. Supr para eliminar"
        return "Clic para crear nodo"

    def _mark_document_changed(
        self,
        routes_dirty: bool = True,
        layout_dirty: bool = True,
    ) -> None:
        if layout_dirty:
            self._invalidate_layout_cache()
        if routes_dirty:
            self._routes_dirty = True
        self._emit_document_change()
        self.request_redraw()

    def _update_custom_cursor(
        self,
        screen_x: int | None = None,
        screen_y: int | None = None,
        *,
        visible: bool | None = None,
    ) -> None:
        if screen_x is not None and screen_y is not None:
            self.custom_cursor_position = (screen_x, screen_y)
        if visible is not None:
            self.custom_cursor_visible = visible
        self._draw_custom_cursor()

    def _draw_custom_cursor(self) -> None:
        if not self.custom_cursor_visible or self.custom_cursor_position is None:
            if self.custom_cursor_canvas_id is not None:
                self.canvas.delete(self.custom_cursor_canvas_id)
                self.custom_cursor_canvas_id = None
            self.canvas.configure(cursor="")
            return
        cursor_image = self._get_cross_cursor_image(CUSTOM_CURSOR_SIZE)
        if cursor_image is None:
            self.canvas.configure(cursor="crosshair")
            return
        self.canvas.configure(cursor="none")
        screen_x, screen_y = self.custom_cursor_position
        if self.custom_cursor_canvas_id is None:
            self.custom_cursor_canvas_id = self.canvas.create_image(
                screen_x,
                screen_y,
                image=cursor_image,
                anchor="center",
                tags="custom-cursor",
            )
        else:
            self.canvas.coords(self.custom_cursor_canvas_id, screen_x, screen_y)
            self.canvas.itemconfigure(
                self.custom_cursor_canvas_id,
                image=cursor_image,
                state="normal",
            )
        self.canvas.tag_raise(self.custom_cursor_canvas_id)

    def destroy(self) -> None:
        if self.selection_blink_after_id is not None:
            self.after_cancel(self.selection_blink_after_id)
            self.selection_blink_after_id = None
        if self.redraw_after_id is not None:
            self.after_cancel(self.redraw_after_id)
            self.redraw_after_id = None
        if self.manual_ghost_after_id is not None:
            self.after_cancel(self.manual_ghost_after_id)
            self.manual_ghost_after_id = None
        self.custom_cursor_canvas_id = None
        super().destroy()


__all__ = ["CanvasInteractionController"]
