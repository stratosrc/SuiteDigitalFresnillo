"""Node, obstacle, layout, and node-image controller."""

from __future__ import annotations

import math
import tkinter as tk

from PIL import Image, ImageTk

from App_Organigrama.config.assets import CROSS_CURSOR_PATH, NODE_LOGO_PATH
from App_Organigrama.models.document import OrgNode
from App_Organigrama.rendering.engine import NodeLayout
from App_Organigrama.ui.canvas_hit_testing import find_blocked_point_at_screen
from App_Organigrama.ui.canvas_image_cache import get_resized_photo, load_rgba_image
from App_Organigrama.ui.modals import NodeEditorDialog


GridPoint = tuple[float, float]
NODE_PROXIMITY_RADIUS = 34.0


class CanvasNodeController:
    def _open_node_dialog_at(self, grid_x: int, grid_y: int) -> None:
        def save(name: str, role: str, color: str) -> None:
            node = self.document.add_node(name, role, grid_x, grid_y, color)
            self._mark_recent_node(node.id)
            self._set_selection(node_id=node.id)
            self._mark_document_changed()

        NodeEditorDialog(self, f"Nueva persona ({grid_x}, {grid_y})", save)

    def _open_node_dialog(self, node: OrgNode) -> None:
        def save(name: str, role: str, color: str) -> None:
            layout_dirty = node.name != name or node.role != role
            self.document.update_node(node.id, name, role, color)
            self._mark_recent_node(node.id)
            self._set_selection(node_id=node.id)
            self._mark_document_changed(
                routes_dirty=False,
                layout_dirty=layout_dirty,
            )

        NodeEditorDialog(
            self,
            "Editar persona",
            save,
            name=node.name,
            role=node.role,
            selected_color=node.color,
        )

    def _delete_selected(self, _event: tk.Event[tk.Canvas] | None = None) -> None:
        if self.selected_node_id is not None:
            node_id = self.selected_node_id
            self.document.remove_node(node_id)
            self.node_history = [item for item in self.node_history if item != node_id]
            self.last_node_id = self.node_history[-1] if self.node_history else None
            self.pending_connection_source_id = None
            self.pending_source_port = None
            self._set_selection()
            self._mark_document_changed()
            return
        if self.selected_connection_id is not None:
            removed = self.document.remove_connection(self.selected_connection_id)
            self.pending_connection_source_id = None
            self.pending_source_port = None
            self._set_selection()
            if removed:
                self._mark_document_changed()
            else:
                self.request_redraw()
        if self.selected_blocked_point is not None:
            blocked_point = self.selected_blocked_point
            self.pending_connection_source_id = None
            self.pending_source_port = None
            self._set_selection()
            if self.document.remove_blocked_point(blocked_point):
                self._mark_document_changed()
            else:
                self.request_redraw()

    def _select_or_add_blocked_point(self, screen_x: int, screen_y: int) -> None:
        existing = self._blocked_point_at_screen(screen_x, screen_y)
        if existing is not None:
            self.preview_obstacle = existing
            self._set_selection(blocked_point=existing)
            self.request_redraw()
            return
        obstacle = self._screen_to_subgrid(screen_x, screen_y)
        if self._obstacle_hits_node(obstacle):
            return
        self.document.toggle_blocked_point(obstacle)
        self.preview_obstacle = obstacle
        self._set_selection(blocked_point=obstacle)
        self._mark_document_changed()

    def _obstacle_hits_node(self, obstacle: GridPoint) -> bool:
        world_x, world_y = self.rendering_engine.grid_to_world(*obstacle)
        for node in self.document.nodes.values():
            box = self._get_node_layout(node, include_logo=False).box
            if box.left <= world_x <= box.right and box.top <= world_y <= box.bottom:
                return True
        return False

    def _node_at_screen(self, screen_x: int, screen_y: int) -> OrgNode | None:
        for node in self.document.nodes.values():
            layout = self._get_node_layout(node, include_logo=False)
            left, top = self._world_to_screen(layout.box.left, layout.box.top)
            right, bottom = self._world_to_screen(layout.box.right, layout.box.bottom)
            if left <= screen_x <= right and top <= screen_y <= bottom:
                return node
        return None

    def _node_near_screen(self, screen_x: int, screen_y: int) -> OrgNode | None:
        max_distance = max(18.0, NODE_PROXIMITY_RADIUS * self.zoom)
        closest_node: OrgNode | None = None
        closest_distance = max_distance
        for node in self.document.nodes.values():
            layout = self._get_node_layout(node, include_logo=False)
            left, top = self._world_to_screen(layout.box.left, layout.box.top)
            right, bottom = self._world_to_screen(layout.box.right, layout.box.bottom)
            dx = max(left - screen_x, 0, screen_x - right)
            dy = max(top - screen_y, 0, screen_y - bottom)
            distance = math.hypot(dx, dy)
            if distance <= closest_distance:
                closest_distance = distance
                closest_node = node
        return closest_node

    def _is_near_port_marker(
        self,
        node: OrgNode,
        port: str,
        screen_x: int,
        screen_y: int,
    ) -> bool:
        point = self._port_screen_position(node.id, port)
        if point is None:
            return False
        radius = max(16.0, 18.0 * self.zoom)
        return math.hypot(screen_x - point[0], screen_y - point[1]) <= radius

    def _port_screen_position(
        self,
        node_id: str,
        port: str,
    ) -> tuple[float, float] | None:
        node = self.document.nodes.get(node_id)
        if node is None:
            return None
        return self._world_to_screen(*self.rendering_engine.get_node_port(node, port))

    def _blocked_point_at_screen(
        self,
        screen_x: int,
        screen_y: int,
    ) -> GridPoint | None:
        return find_blocked_point_at_screen(
            self.document.blocked_points,
            screen_x,
            screen_y,
            self.zoom,
            self.rendering_engine,
            self._world_to_screen,
        )

    def _mark_recent_node(self, node_id: str) -> None:
        if node_id not in self.document.nodes:
            return
        self.node_history = [item for item in self.node_history if item != node_id]
        self.node_history.append(node_id)
        self.last_node_id = node_id

    def _load_logo_source(self) -> Image.Image | None:
        return load_rgba_image(NODE_LOGO_PATH)

    def _load_cross_cursor_source(self) -> Image.Image | None:
        return load_rgba_image(CROSS_CURSOR_PATH)

    def _invalidate_layout_cache(self) -> None:
        self._node_layout_cache.clear()

    def _get_node_layout(self, node: OrgNode, include_logo: bool) -> NodeLayout:
        cache_key = (node.id, include_logo)
        if cache_key not in self._node_layout_cache:
            self._node_layout_cache[cache_key] = self.rendering_engine.layout_node(
                node,
                include_logo=include_logo,
            )
        return self._node_layout_cache[cache_key]

    def _get_logo_image(self, size: int) -> ImageTk.PhotoImage | None:
        return get_resized_photo(self.logo_source_image, self.logo_cache, size)

    def _get_cross_cursor_image(self, size: int) -> ImageTk.PhotoImage | None:
        return get_resized_photo(
            self.cross_cursor_source_image,
            self.cross_cursor_cache,
            size,
            crop_alpha=True,
        )


__all__ = ["CanvasNodeController"]
