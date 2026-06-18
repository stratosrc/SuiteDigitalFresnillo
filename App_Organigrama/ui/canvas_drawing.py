"""Drawing layer for the organization chart canvas."""

from __future__ import annotations

import math

from App_Organigrama.models.document import OrgGridDocument
from App_Organigrama.rendering.connection_arrows import (
    build_arrow_triangle,
    flatten_points,
)
from App_Organigrama.routing.manhattan_router import ConnectionRoute
from App_Organigrama.ui.canvas_shapes import create_rounded_rectangle
from App_Organigrama.ui.theme import (
    GHOST_AVAILABLE_FILL,
    GHOST_OCCUPIED_FILL,
    GRID_AXIS,
    GRID_LINE,
    OBSTACLE_COLOR,
    OBSTACLE_PREVIEW_COLOR,
    PORT_ACTIVE_COLOR,
    PORT_HOVER_COLOR,
    PORT_MARKER_OUTLINE,
    PRIMARY_BUTTON,
    ROUTE_PREVIEW_COLOR,
    SELECTION_COLOR,
    TEXT_LIGHT,
)


class CanvasDrawingMixin:
    """Render canvas content without owning document interaction state."""

    def _draw_grid(self) -> None:
        width = max(self.canvas.winfo_width(), 1)
        height = max(self.canvas.winfo_height(), 1)
        cell_width = self.rendering_engine.base_cell_width * self.zoom
        cell_height = self.rendering_engine.base_cell_height * self.zoom
        start_column = math.floor((-self.pan_x) / cell_width) - 1
        end_column = math.ceil((width - self.pan_x) / cell_width) + 1
        start_row = math.floor((-self.pan_y) / cell_height) - 1
        end_row = math.ceil((height - self.pan_y) / cell_height) + 1

        for column in range(start_column, end_column + 1):
            x = self.pan_x + (column * cell_width)
            color = GRID_AXIS if column == 0 else GRID_LINE
            self.canvas.create_line(x, 0, x, height, fill=color, tags="grid")

        for row in range(start_row, end_row + 1):
            y = self.pan_y + (row * cell_height)
            color = GRID_AXIS if row == 0 else GRID_LINE
            self.canvas.create_line(0, y, width, y, fill=color, tags="grid")

    def _draw_connections(self, routes: list[ConnectionRoute]) -> None:
        for route in routes:
            points: list[float] = []
            screen_points: list[tuple[float, float]] = []
            for grid_x, grid_y in route.points:
                world_x, world_y = self.rendering_engine.grid_to_world(grid_x, grid_y)
                screen_x, screen_y = self._world_to_screen(world_x, world_y)
                screen_points.append((screen_x, screen_y))
                points.extend((screen_x, screen_y))
            connection_tags = ("connection", f"connection:{route.connection.id}")
            self.canvas.create_line(
                *points,
                fill=PRIMARY_BUTTON,
                width=max(2, int(self.rendering_engine.base_line_width * self.zoom)),
                capstyle="butt",
                joinstyle="miter",
                tags=connection_tags,
            )
            arrow = build_arrow_triangle(
                screen_points,
                length=max(8.0, 12.0 * self.zoom),
                width=max(8.0, 11.0 * self.zoom),
                target_gap=max(7.0, 10.0 * self.zoom),
            )
            if arrow is not None:
                self.canvas.create_polygon(
                    *flatten_points(arrow),
                    fill=PRIMARY_BUTTON,
                    outline=PRIMARY_BUTTON,
                    tags=connection_tags,
                )

    def _draw_connection_drag_preview(self) -> None:
        if self.connection_drag_source_id is None or self.connection_drag_screen_point is None:
            return
        source_port = self.connection_drag_source_port or "bottom"
        start = self._port_screen_position(self.connection_drag_source_id, source_port)
        if start is None:
            return

        end = self.connection_drag_screen_point
        if self.hover_port is not None:
            hover_node_id, hover_port = self.hover_port
            target = self._port_screen_position(hover_node_id, hover_port)
            if target is not None:
                end = (int(target[0]), int(target[1]))

        self.canvas.create_line(
            start[0],
            start[1],
            end[0],
            end[1],
            fill=ROUTE_PREVIEW_COLOR,
            width=max(2, int(2 * self.zoom)),
            dash=(8, 5),
            arrow="last",
            tags=("connection-drag-preview", "ghost"),
        )

    def _draw_nodes(self) -> None:
        for node in self.document.nodes.values():
            layout = self._get_node_layout(node, include_logo=self.document.show_logos)
            screen_layout = self._to_screen_layout(layout)
            if node.id == self.drag_node_id and self.drag_screen_point is not None:
                delta_x = self.drag_screen_point[0] - screen_layout.center_x
                delta_y = self.drag_screen_point[1] - screen_layout.center_y
                screen_layout = self._offset_screen_layout(screen_layout, delta_x, delta_y)
            pending_connection_source = node.id == self.pending_connection_source_id
            outline = SELECTION_COLOR if pending_connection_source else node.color
            outline_width = 3 if pending_connection_source else 1
            tag = ("node", f"node:{node.id}")
            create_rounded_rectangle(
                self.canvas,
                screen_layout.box.left,
                screen_layout.box.top,
                screen_layout.box.right,
                screen_layout.box.bottom,
                radius=max(0, int(12 * self.zoom)),
                fill=node.color,
                outline=outline,
                width=outline_width,
                tags=tag,
            )
            if self.document.show_logos:
                radius = screen_layout.style.logo_radius
                self.canvas.create_oval(
                    screen_layout.logo_center_x - radius,
                    screen_layout.logo_center_y - radius,
                    screen_layout.logo_center_x + radius,
                    screen_layout.logo_center_y + radius,
                    fill=node.color,
                    outline=TEXT_LIGHT,
                    width=1,
                    tags=tag,
                )
                logo_image = self._get_logo_image(int(screen_layout.logo_image_size))
                if logo_image is not None:
                    self.canvas.create_image(
                        screen_layout.logo_center_x,
                        screen_layout.logo_center_y,
                        image=logo_image,
                        tags=tag,
                    )

            for line in screen_layout.lines:
                self.canvas.create_text(
                    screen_layout.center_x,
                    line.top,
                    text=line.text,
                    fill=TEXT_LIGHT,
                    font=(
                        "Segoe UI",
                        max(6, int(line.font_size)),
                        "bold" if line.is_bold else "normal",
                    ),
                    anchor="n",
                    tags=tag,
                )

    def _draw_blocked_points(self) -> None:
        size = max(5, int(7 * self.zoom))
        width = max(2, int(2 * self.zoom))
        for grid_x, grid_y in self.document.blocked_points:
            world_x, world_y = self.rendering_engine.grid_to_world(grid_x, grid_y)
            center_x, center_y = self._world_to_screen(world_x, world_y)
            self.canvas.create_line(
                center_x - size,
                center_y - size,
                center_x + size,
                center_y + size,
                fill=OBSTACLE_COLOR,
                width=width,
                tags="blocked-point",
            )
            self.canvas.create_line(
                center_x - size,
                center_y + size,
                center_x + size,
                center_y - size,
                fill=OBSTACLE_COLOR,
                width=width,
                tags="blocked-point",
            )

    def _draw_preview_routes(self) -> None:
        if not self.block_mode or self.preview_obstacle is None:
            return

        preview_points = list(self.document.blocked_points)
        if self.document.has_blocked_point(self.preview_obstacle):
            preview_points = [item for item in preview_points if item != self.preview_obstacle]
        elif not self._obstacle_hits_node(self.preview_obstacle):
            preview_points.append(self.preview_obstacle)
        else:
            return

        preview_document = OrgGridDocument(
            title=self.document.title,
            period=self.document.period,
            page_orientation=self.document.page_orientation,
            show_logos=self.document.show_logos,
            nodes=self.document.nodes,
            connections=self.document.connections,
            blocked_points=preview_points,
        )
        preview_routes = self.router.route_document(preview_document)
        current_routes = {route.connection.id: route.points for route in self.route_cache}
        for route in preview_routes:
            if current_routes.get(route.connection.id) == route.points:
                continue
            screen_points: list[float] = []
            for grid_x, grid_y in route.points:
                world_x, world_y = self.rendering_engine.grid_to_world(grid_x, grid_y)
                screen_x, screen_y = self._world_to_screen(world_x, world_y)
                screen_points.extend((screen_x, screen_y))
            self.canvas.create_line(
                *screen_points,
                fill=ROUTE_PREVIEW_COLOR,
                width=max(2, int(self.rendering_engine.base_line_width * self.zoom * 1.35)),
                dash=(10, 6),
                tags=("route-preview", f"route-preview:{route.connection.id}"),
            )

    def _draw_hover_port(self) -> None:
        if self.pending_connection_source_id is not None:
            pending_port = self.pending_source_port or "bottom"
            self._draw_port_indicator(
                self.pending_connection_source_id,
                pending_port,
                PORT_ACTIVE_COLOR,
                "port-active",
            )

        if self.hover_port is None:
            return

        node_id, port = self.hover_port
        if (node_id, port) == (self.pending_connection_source_id, self.pending_source_port):
            return
        self._draw_port_indicator(node_id, port, PORT_HOVER_COLOR, "port-hover")

    def _draw_port_indicator(self, node_id: str, port: str, color: str, tag: str) -> None:
        node = self.document.nodes.get(node_id)
        if node is None:
            return

        world_x, world_y = self.rendering_engine.get_node_port(node, port)
        center_x, center_y = self._world_to_screen(world_x, world_y)
        radius = max(9, int(12 * self.zoom))
        width = max(3, int(4 * self.zoom))
        glow_radius = radius + max(5, int(5 * self.zoom))
        self.canvas.create_oval(
            center_x - glow_radius,
            center_y - glow_radius,
            center_x + glow_radius,
            center_y + glow_radius,
            fill=color,
            outline="",
            stipple="gray50",
            tags=tag,
        )
        self.canvas.create_oval(
            center_x - radius,
            center_y - radius,
            center_x + radius,
            center_y + radius,
            fill=color,
            outline=PORT_MARKER_OUTLINE,
            width=width,
            tags=tag,
        )
        center_radius = max(2, int(radius * 0.28))
        self.canvas.create_oval(
            center_x - center_radius,
            center_y - center_radius,
            center_x + center_radius,
            center_y + center_radius,
            fill=PORT_MARKER_OUTLINE,
            outline="",
            tags=tag,
        )

    def _draw_ghost(self) -> None:
        if self.block_mode and self.preview_obstacle is not None:
            world_x, world_y = self.rendering_engine.grid_to_world(*self.preview_obstacle)
            center_x, center_y = self._world_to_screen(world_x, world_y)
            size = max(8, int(12 * self.zoom))
            width = max(2, int(2 * self.zoom))
            hits_node = self._obstacle_hits_node(self.preview_obstacle)
            removing = self.preview_obstacle in self.document.blocked_points
            color = OBSTACLE_COLOR if hits_node else OBSTACLE_PREVIEW_COLOR
            label = "No disponible" if hits_node else ("Quitar bloqueo" if removing else "Bloquear")
            self.canvas.create_oval(
                center_x - size,
                center_y - size,
                center_x + size,
                center_y + size,
                fill=color,
                outline=TEXT_LIGHT,
                width=width,
                stipple="gray25",
                tags="ghost",
            )
            self.canvas.create_text(
                center_x,
                center_y + size + max(10, int(10 * self.zoom)),
                text=label,
                fill=color,
                font=("Segoe UI", max(6, int(8 * self.zoom)), "bold"),
                tags="ghost",
            )
            return

        if self.last_hover_cell is None or self._connection_at_hover_cell() is not None:
            return

        grid_x, grid_y = self.last_hover_cell
        occupied = self.document.get_node_at(grid_x, grid_y) is not None
        world_x, world_y = self.rendering_engine.grid_to_world(grid_x, grid_y)
        center_x, center_y = self._world_to_screen(world_x, world_y)
        width = self.rendering_engine.base_node_width * self.zoom
        min_height = self.rendering_engine.base_node_min_height * self.zoom
        x1 = center_x - (width / 2)
        y1 = center_y - (min_height / 2)
        x2 = center_x + (width / 2)
        y2 = center_y + (min_height / 2)
        fill = GHOST_OCCUPIED_FILL if occupied else GHOST_AVAILABLE_FILL
        outline = OBSTACLE_COLOR if occupied else PRIMARY_BUTTON
        self.canvas.create_rectangle(
            x1,
            y1,
            x2,
            y2,
            fill=fill,
            outline=outline,
            width=2,
            dash=(6, 4),
            stipple="gray25",
            tags="ghost",
        )
        self.canvas.create_text(
            center_x,
            center_y,
            text="Ocupado" if occupied else "Nuevo nodo",
            fill=outline,
            font=("Segoe UI", max(6, int(8 * self.zoom)), "bold"),
            tags="ghost",
        )


__all__ = ["CanvasDrawingMixin"]
