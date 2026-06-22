"""Viewport, pan, zoom, and node-move controller for the organigram canvas."""

from __future__ import annotations

import tkinter as tk

from App_Organigrama.rendering.engine import NodeLayout
from App_Organigrama.ui.canvas_state import InteractionMode
from App_Organigrama.ui.canvas_viewport import (
    offset_screen_layout,
    scale_box,
    screen_to_grid,
    screen_to_subgrid,
    to_screen_layout,
    world_to_screen,
)


GridPoint = tuple[float, float]


class CanvasViewportController:
    def zoom_percent(self) -> int:
        return int(round(self.zoom * 100))

    def change_zoom(self, direction: str) -> None:
        factor = 1.1 if direction == "in" else 1 / 1.1
        width = max(self.canvas.winfo_width(), 1)
        height = max(self.canvas.winfo_height(), 1)
        self._zoom_at(width / 2, height / 2, factor)

    def scroll_view(self, direction: str, pixels: int = 180) -> None:
        movement = {
            "up": (0, pixels),
            "down": (0, -pixels),
            "left": (pixels, 0),
            "right": (-pixels, 0),
        }
        dx, dy = movement[direction]
        self.pan_x += dx
        self.pan_y += dy
        self.request_redraw()

    def focus_last_node(self) -> None:
        node = self.document.nodes.get(self.last_node_id) if self.last_node_id else None
        if node is None and self.document.nodes:
            node = min(
                self.document.nodes.values(),
                key=lambda item: (item.grid_y, item.grid_x, item.id),
            )
        if node is None:
            return
        width = max(self.canvas.winfo_width(), 1)
        height = max(self.canvas.winfo_height(), 1)
        world_x, world_y = self.rendering_engine.grid_to_world(node.grid_x, node.grid_y)
        self.pan_x = (width / 2) - (world_x * self.zoom)
        self.pan_y = (height / 2) - (world_y * self.zoom)
        self.request_redraw()

    def fit_document_to_content_top(self) -> None:
        if not self.document.nodes:
            self.pan_x = 560.0
            self.pan_y = 320.0
            self.route_cache = []
            self._routes_dirty = False
            self.request_redraw()
            return
        routes = self.router.route_document(self.document)
        bounds = self.rendering_engine.compute_document_bounds(
            self.document,
            [list(route.points) for route in routes],
            include_blocked_points=False,
        )
        canvas_width = max(self.canvas.winfo_width(), 1)
        content_width = max(bounds.width * self.zoom, 1.0)
        self.pan_x = ((canvas_width - content_width) / 2) - (bounds.left * self.zoom)
        self.pan_y = self.rendering_engine.content_top_margin - (bounds.top * self.zoom)
        self.route_cache = routes
        self._routes_dirty = False
        self.request_redraw()

    def _on_pan_press(self, event: tk.Event[tk.Canvas]) -> None:
        self.canvas.focus_set()
        if self.block_mode:
            return
        self.pan_dragged = False
        self.pan_drag_press = (event.x, event.y, self.pan_x, self.pan_y)
        node = self._node_at_screen(event.x, event.y)
        self.drag_node_id = node.id if node is not None else None
        self.drag_screen_point = None
        self.drag_node_offset = None
        if node is not None:
            self.interaction.transition(InteractionMode.MOVING_NODE)
            screen_layout = self._to_screen_layout(
                self._get_node_layout(node, include_logo=self.document.show_logos)
            )
            self.drag_node_offset = (
                screen_layout.center_x - event.x,
                screen_layout.center_y - event.y,
            )
            self.drag_screen_point = (
                int(event.x + self.drag_node_offset[0]),
                int(event.y + self.drag_node_offset[1]),
            )
            self._update_custom_cursor(visible=False)
            self._set_selection(node_id=node.id)
            self._emit_context_change("Arrastra con clic derecho para mover")
        else:
            self.interaction.transition(InteractionMode.PANNING)
            self._update_custom_cursor(visible=False)
            self._emit_context_change("Arrastra con clic derecho para desplazar el lienzo")

    def _on_pan_drag(self, event: tk.Event[tk.Canvas]) -> None:
        if self.pan_drag_press is None:
            return
        start_x, start_y, initial_pan_x, initial_pan_y = self.pan_drag_press
        dx = event.x - start_x
        dy = event.y - start_y
        if abs(dx) < 4 and abs(dy) < 4:
            return
        self.pan_dragged = True
        if self.drag_node_id is not None:
            offset_x, offset_y = self.drag_node_offset or (0.0, 0.0)
            self.drag_screen_point = (int(event.x + offset_x), int(event.y + offset_y))
        else:
            self.pan_x = initial_pan_x + dx
            self.pan_y = initial_pan_y + dy
        self.request_redraw()

    def _on_pan_release(self, event: tk.Event[tk.Canvas]) -> None:
        drag_node_id = self.drag_node_id
        drop_point = self.drag_screen_point
        self.drag_node_id = None
        self.drag_screen_point = None
        self.drag_node_offset = None
        if drag_node_id is not None and self.pan_dragged:
            drop_x, drop_y = drop_point or (event.x, event.y)
            grid_x, grid_y = self._screen_to_grid(drop_x, drop_y)
            if self.document.move_node(drag_node_id, grid_x, grid_y):
                self._mark_recent_node(drag_node_id)
                self._mark_document_changed()
            self._set_selection(node_id=drag_node_id)
        elif not self.pan_dragged:
            self._show_context_menu(event)
        self.pan_drag_press = None
        self.pan_dragged = False
        self.interaction.transition(
            InteractionMode.BLOCKING if self.block_mode else InteractionMode.IDLE
        )
        self.request_redraw()
        self._emit_context_change()

    def _on_double_click(self, event: tk.Event[tk.Canvas]) -> None:
        node = self._node_at_screen(event.x, event.y)
        if node is not None:
            self._open_node_dialog(node)

    def _on_mousewheel(self, event: tk.Event[tk.Canvas]) -> None:
        if event.state & 0x0004:
            factor = 1.1 if event.delta > 0 else 1 / 1.1
            self._zoom_at(event.x, event.y, factor)
            return
        self.pan_y += event.delta / 2
        self.request_redraw()

    def _world_to_screen(self, world_x: float, world_y: float) -> tuple[float, float]:
        return world_to_screen(world_x, world_y, self.pan_x, self.pan_y, self.zoom)

    def _screen_to_grid(self, screen_x: int, screen_y: int) -> tuple[int, int]:
        return screen_to_grid(
            screen_x,
            screen_y,
            self.pan_x,
            self.pan_y,
            self.zoom,
            self.rendering_engine,
        )

    def _screen_to_subgrid(self, screen_x: int, screen_y: int) -> GridPoint:
        return screen_to_subgrid(
            screen_x,
            screen_y,
            self.pan_x,
            self.pan_y,
            self.zoom,
            self.rendering_engine,
        )

    def _zoom_at(self, screen_x: float, screen_y: float, factor: float) -> None:
        previous_zoom = self.zoom
        next_zoom = min(self.max_zoom, max(self.min_zoom, previous_zoom * factor))
        if next_zoom == previous_zoom:
            return
        world_x = (screen_x - self.pan_x) / previous_zoom
        world_y = (screen_y - self.pan_y) / previous_zoom
        self.zoom = next_zoom
        self.pan_x = screen_x - (world_x * next_zoom)
        self.pan_y = screen_y - (world_y * next_zoom)
        self.request_redraw()
        if self.on_zoom_change is not None:
            self.on_zoom_change(self.zoom_percent())

    def _to_screen_layout(self, layout: NodeLayout) -> NodeLayout:
        return to_screen_layout(layout, self.pan_x, self.pan_y, self.zoom)

    def _scale_box(self, box):
        return scale_box(box, self.pan_x, self.pan_y, self.zoom)

    def _offset_screen_layout(
        self,
        layout: NodeLayout,
        delta_x: float,
        delta_y: float,
    ) -> NodeLayout:
        return offset_screen_layout(layout, delta_x, delta_y)


__all__ = ["CanvasViewportController"]
