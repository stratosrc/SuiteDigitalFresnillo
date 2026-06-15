from collections.abc import Callable
import math
import tkinter as tk

import customtkinter as ctk
from PIL import Image, ImageTk

from App_Organigrama.models.document import OrgGridDocument, OrgNode
from App_Organigrama.rendering.engine import NodeLayout, RenderingEngine
from App_Organigrama.routing.manhattan_router import ConnectionRoute, ManhattanRouter
from App_Organigrama.config.assets import CROSS_CURSOR_PATH, NODE_LOGO_PATH
from App_Organigrama.ui.canvas_hit_testing import (
    find_blocked_point_at_screen,
    find_connection_at_screen,
    nearest_port,
)
from App_Organigrama.ui.canvas_image_cache import get_resized_photo, load_rgba_image
from App_Organigrama.ui.canvas_selection import draw_connection_selection_overlay, draw_node_selection_overlay
from App_Organigrama.ui.canvas_shapes import create_rounded_rectangle
from App_Organigrama.ui.canvas_viewport import (
    offset_screen_layout,
    scale_box,
    screen_to_grid,
    screen_to_subgrid,
    to_screen_layout,
    world_to_screen,
)
from App_Organigrama.ui.modals import NodeEditorDialog
from App_Organigrama.ui.theme import (
    BORDER_COLOR,
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
    SURFACE_BACKGROUND,
    TEXT_LIGHT,
)


GridPoint = tuple[float, float]
SELECTION_BLINK_INTERVAL_MS = 420
CUSTOM_CURSOR_SIZE = 32


class OrgGridCanvas(ctk.CTkFrame):
    def __init__(
        self,
        master: tk.Misc,
        document: OrgGridDocument,
        rendering_engine: RenderingEngine,
        router: ManhattanRouter,
        on_selection_change: Callable[[bool], None] | None = None,
        on_zoom_change: Callable[[int], None] | None = None,
        on_document_change: Callable[[], None] | None = None,
        on_context_change: Callable[[str], None] | None = None,
        **kwargs: object,
    ) -> None:
        super().__init__(
            master,
            fg_color=SURFACE_BACKGROUND,
            border_color=BORDER_COLOR,
            border_width=1,
            **kwargs,
        )
        self.document = document
        self.rendering_engine = rendering_engine
        self.router = router
        self.on_selection_change = on_selection_change
        self.on_zoom_change = on_zoom_change
        self.on_document_change = on_document_change
        self.on_context_change = on_context_change

        self.zoom = 1.0
        self.min_zoom = 0.25
        self.max_zoom = 2.0
        self.pan_x = 560.0
        self.pan_y = 320.0
        self.block_mode = False
        self.selected_node_id: str | None = None
        self.selected_connection_id: str | None = None
        self.selected_blocked_point: GridPoint | None = None
        self.selection_blink_visible = True
        self.selection_blink_after_id: str | None = None
        self.pending_connection_source_id: str | None = None
        self.pending_source_port: str | None = None
        self.hover_port: tuple[str, str] | None = None
        self.preview_obstacle: GridPoint | None = None
        self.last_hover_cell: tuple[int, int] | None = None
        self.node_history: list[str] = []
        self.last_node_id: str | None = None
        self.route_cache: list[ConnectionRoute] = []
        self._routes_dirty = True
        self._node_layout_cache: dict[tuple[str, bool], NodeLayout] = {}
        self.drag_press: tuple[int, int, float, float] | None = None
        self.dragged = False
        self.drag_node_id: str | None = None
        self.drag_screen_point: tuple[int, int] | None = None
        self.redraw_after_id: str | None = None
        self.logo_source_image = self._load_logo_source()
        self.logo_cache: dict[int, ImageTk.PhotoImage] = {}
        self.cross_cursor_source_image = self._load_cross_cursor_source()
        self.cross_cursor_cache: dict[int, ImageTk.PhotoImage] = {}
        self.custom_cursor_canvas_id: int | None = None
        self.custom_cursor_position: tuple[int, int] | None = None
        self.custom_cursor_visible = False

        self.canvas = tk.Canvas(self, bg=SURFACE_BACKGROUND, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self._bind_events()
        self._emit_context_change()

    def _bind_events(self) -> None:
        self.canvas.bind("<Configure>", lambda _event: self.request_redraw())
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<ButtonPress-3>", self._on_right_click)
        self.canvas.bind("<Double-Button-1>", self._on_double_click)
        self.canvas.bind("<Motion>", self._on_motion)
        self.canvas.bind("<Leave>", self._on_leave)
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Delete>", self._delete_selected)
        self.canvas.bind("<BackSpace>", self._delete_selected)
        self.canvas.bind("<Escape>", self._cancel_connection)
        self.canvas.focus_set()

    def set_document(self, document: OrgGridDocument) -> None:
        self.document = document
        self.selected_node_id = None
        self.selected_connection_id = None
        self.selected_blocked_point = None
        self._sync_selection_blink()
        self.pending_connection_source_id = None
        self.pending_source_port = None
        self.hover_port = None
        self.preview_obstacle = None
        self.node_history = []
        self.last_node_id = None
        self.route_cache = []
        self._routes_dirty = True
        self._invalidate_layout_cache()
        self._update_custom_cursor(visible=False)
        self.after_idle(self.fit_document_to_content_top)
        self._emit_selection_change()

    def set_block_mode(self, enabled: bool) -> None:
        self.block_mode = enabled
        self.preview_obstacle = None
        if enabled:
            self.pending_connection_source_id = None
            self.pending_source_port = None
            self.hover_port = None
        self._update_custom_cursor(visible=enabled)
        self.request_redraw()
        self._emit_context_change()

    def set_show_logos(self, enabled: bool) -> None:
        self.document.show_logos = enabled
        self._invalidate_layout_cache()
        self._emit_document_change()
        self.request_redraw()

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
            node = min(self.document.nodes.values(), key=lambda item: (item.grid_y, item.grid_x, item.id))
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
        route_points = [list(route.points) for route in routes]
        bounds = self.rendering_engine.compute_document_bounds(
            self.document,
            route_points,
            include_blocked_points=False,
        )

        canvas_width = max(self.canvas.winfo_width(), 1)
        content_width = max(bounds.width * self.zoom, 1.0)
        self.pan_x = ((canvas_width - content_width) / 2) - (bounds.left * self.zoom)
        self.pan_y = self.rendering_engine.content_top_margin - (bounds.top * self.zoom)
        self.route_cache = routes
        self._routes_dirty = False
        self.request_redraw()

    def delete_selected_item(self) -> None:
        self._delete_selected()

    def redraw(self) -> None:
        self.redraw_after_id = None
        self.canvas.delete("all")
        self.custom_cursor_canvas_id = None
        if self._routes_dirty:
            self.route_cache = self.router.route_document(self.document)
            self._routes_dirty = False
        self._draw_grid()
        self._draw_connections(self.route_cache)
        self._draw_preview_routes()
        draw_connection_selection_overlay(self)
        self._draw_nodes()
        self._draw_blocked_points()
        self._draw_hover_port()
        self._draw_ghost()
        draw_node_selection_overlay(self)
        self._draw_custom_cursor()

    def request_redraw(self) -> None:
        if self.redraw_after_id is not None:
            return
        self.redraw_after_id = self.after(16, self.redraw)

    def _redraw_selection_overlay(self) -> None:
        self.canvas.delete("selection-overlay")
        draw_connection_selection_overlay(self)
        if self.canvas.find_withtag("node"):
            self.canvas.tag_lower("connection-selection-overlay", "node")
        draw_node_selection_overlay(self)
        self.canvas.tag_raise("node-selection-overlay")

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
            for grid_x, grid_y in route.points:
                world_x, world_y = self.rendering_engine.grid_to_world(grid_x, grid_y)
                screen_x, screen_y = self._world_to_screen(world_x, world_y)
                points.extend((screen_x, screen_y))
            self.canvas.create_line(
                *points,
                fill=PRIMARY_BUTTON,
                width=max(2, int(self.rendering_engine.base_line_width * self.zoom)),
                capstyle="butt",
                joinstyle="miter",
                tags=("connection", f"connection:{route.connection.id}"),
            )

    def _draw_nodes(self) -> None:
        for node in self.document.nodes.values():
            layout = self._get_node_layout(node, include_logo=self.document.show_logos)
            screen_layout = self._to_screen_layout(layout)
            if node.id == self.drag_node_id and self.drag_screen_point is not None:
                delta_x = self.drag_screen_point[0] - screen_layout.center_x
                delta_y = self.drag_screen_point[1] - screen_layout.center_y
                screen_layout = self._offset_screen_layout(screen_layout, delta_x, delta_y)
            selected = node.id == self.selected_node_id
            pending_connection_source = node.id == self.pending_connection_source_id
            outline = node.color
            if pending_connection_source:
                outline = SELECTION_COLOR
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
            self._draw_port_indicator(self.pending_connection_source_id, pending_port, PORT_ACTIVE_COLOR, "port-active")

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
        self.canvas.create_oval(
            center_x - max(2, int(radius * 0.28)),
            center_y - max(2, int(radius * 0.28)),
            center_x + max(2, int(radius * 0.28)),
            center_y + max(2, int(radius * 0.28)),
            fill=PORT_MARKER_OUTLINE,
            outline="",
            tags=tag,
        )

    def _draw_ghost(self) -> None:
        if self.block_mode and self.preview_obstacle is not None:
            world_x, world_y = self.rendering_engine.grid_to_world(self.preview_obstacle[0], self.preview_obstacle[1])
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

        if self.last_hover_cell is None:
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

    def _on_press(self, event: tk.Event[tk.Canvas]) -> None:
        self.canvas.focus_set()
        self.dragged = False
        self.drag_press = (event.x, event.y, self.pan_x, self.pan_y)
        if self.block_mode:
            self.drag_press = None
            self._select_or_add_blocked_point(event.x, event.y)
            return

        node = self._node_at_screen(event.x, event.y)
        self.drag_node_id = node.id if node is not None else None
        self.drag_screen_point = (event.x, event.y) if node is not None else None
        if node is not None:
            self._set_selection(node_id=node.id)
            self._emit_context_change("Arrastra para mover")

    def _on_drag(self, event: tk.Event[tk.Canvas]) -> None:
        if self.drag_press is None:
            return

        start_x, start_y, initial_pan_x, initial_pan_y = self.drag_press
        dx = event.x - start_x
        dy = event.y - start_y
        if abs(dx) < 4 and abs(dy) < 4:
            return

        self.dragged = True
        self._emit_context_change("Arrastra para mover" if self.drag_node_id is not None else "Arrastra para desplazar el lienzo")
        if self.drag_node_id is not None:
            self.drag_screen_point = (event.x, event.y)
        else:
            self.pan_x = initial_pan_x + dx
            self.pan_y = initial_pan_y + dy
        self.request_redraw()

    def _on_release(self, event: tk.Event[tk.Canvas]) -> None:
        if self.drag_press is None:
            return

        self.drag_press = None
        drag_node_id = self.drag_node_id
        self.drag_node_id = None
        self.drag_screen_point = None
        if self.dragged:
            if drag_node_id is not None:
                grid_x, grid_y = self._screen_to_grid(event.x, event.y)
                if self.document.move_node(drag_node_id, grid_x, grid_y):
                    self._mark_recent_node(drag_node_id)
                    self._mark_document_changed()
                self._set_selection(node_id=drag_node_id)
            self.request_redraw()
            self._emit_context_change()
            return

        self._handle_click(event.x, event.y)

    def _on_right_click(self, event: tk.Event[tk.Canvas]) -> None:
        if self.block_mode:
            return

        node = self._node_at_screen(event.x, event.y)
        if node is None:
            if self._connection_at_screen(event.x, event.y) is not None:
                self._cancel_connection()
            return

        self._set_selection(node_id=node.id)
        port = self._nearest_port(node, event.x, event.y)
        if self.pending_connection_source_id is None:
            self.pending_connection_source_id = node.id
            self.pending_source_port = port
            self._emit_context_change()
        else:
            new_connection = self.document.add_connection(
                self.pending_connection_source_id,
                node.id,
                source_port=self.pending_source_port or "bottom",
                target_port=port,
            )
            self.pending_connection_source_id = None
            self.pending_source_port = None
            self.hover_port = None
            if new_connection is not None:
                self._set_selection(connection_id=new_connection.id)
                self._mark_document_changed()
        self._emit_context_change()
        self.request_redraw()

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

    def _on_motion(self, event: tk.Event[tk.Canvas]) -> None:
        if self.drag_press is not None:
            return

        if self.block_mode:
            self._update_custom_cursor(event.x, event.y, visible=True)
            self.preview_obstacle = self._screen_to_subgrid(event.x, event.y)
            self.request_redraw()
            self._emit_context_change()
            return

        node = self._node_at_screen(event.x, event.y)
        self.hover_port = (node.id, self._nearest_port(node, event.x, event.y)) if node is not None else None
        self._update_custom_cursor(event.x, event.y, visible=self.hover_port is not None)
        if node is not None:
            self.last_hover_cell = None
            self.request_redraw()
            self._emit_context_change()
            return

        grid_x, grid_y = self._screen_to_grid(event.x, event.y)
        hover_cell = (grid_x, grid_y)
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

    def _open_node_dialog_at(self, grid_x: int, grid_y: int) -> None:
        def save(nombre: str, cargo: str, color: str) -> None:
            node = self.document.add_node(nombre, cargo, grid_x, grid_y, color)
            self._mark_recent_node(node.id)
            self._set_selection(node_id=node.id)
            self._mark_document_changed()

        NodeEditorDialog(self, f"Nueva persona ({grid_x}, {grid_y})", save)

    def _open_node_dialog(self, node: OrgNode) -> None:
        def save(nombre: str, cargo: str, color: str) -> None:
            layout_dirty = node.nombre != nombre or node.cargo != cargo
            self.document.update_node(node.id, nombre, cargo, color)
            self._mark_recent_node(node.id)
            self._set_selection(node_id=node.id)
            self._mark_document_changed(routes_dirty=False, layout_dirty=layout_dirty)

        NodeEditorDialog(
            self,
            "Editar persona",
            save,
            nombre=node.nombre,
            cargo=node.cargo,
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
        world_x, world_y = self.rendering_engine.grid_to_world(obstacle[0], obstacle[1])
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

    def _blocked_point_at_screen(self, screen_x: int, screen_y: int) -> GridPoint | None:
        return find_blocked_point_at_screen(
            self.document.blocked_points,
            screen_x,
            screen_y,
            self.zoom,
            self.rendering_engine,
            self._world_to_screen,
        )

    def _connection_at_screen(self, screen_x: int, screen_y: int) -> ConnectionRoute | None:
        return find_connection_at_screen(
            self.route_cache,
            screen_x,
            screen_y,
            self.rendering_engine,
            self._world_to_screen,
        )

    def _nearest_port(self, node: OrgNode, screen_x: int, screen_y: int) -> str:
        layout = self._get_node_layout(node, include_logo=False)
        return nearest_port(node, screen_x, screen_y, layout, self.zoom, self._world_to_screen)

    def _world_to_screen(self, world_x: float, world_y: float) -> tuple[float, float]:
        return world_to_screen(world_x, world_y, self.pan_x, self.pan_y, self.zoom)

    def _screen_to_grid(self, screen_x: int, screen_y: int) -> tuple[int, int]:
        return screen_to_grid(screen_x, screen_y, self.pan_x, self.pan_y, self.zoom, self.rendering_engine)

    def _screen_to_subgrid(self, screen_x: int, screen_y: int) -> GridPoint:
        return screen_to_subgrid(screen_x, screen_y, self.pan_x, self.pan_y, self.zoom, self.rendering_engine)

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
        if (
            self.selected_node_id is not None
            or self.selected_connection_id is not None
            or self.selected_blocked_point is not None
        ):
            if self.selection_blink_after_id is None:
                self.selection_blink_visible = True
                self._schedule_selection_blink()
            return

        if self.selection_blink_after_id is not None:
            self.after_cancel(self.selection_blink_after_id)
            self.selection_blink_after_id = None
        self.selection_blink_visible = True

    def _schedule_selection_blink(self) -> None:
        self.selection_blink_after_id = self.after(SELECTION_BLINK_INTERVAL_MS, self._toggle_selection_blink)

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
        self._update_custom_cursor(visible=self.block_mode)
        self.request_redraw()
        self._emit_context_change()

    def _emit_selection_change(self) -> None:
        if self.on_selection_change is not None:
            has_selection = (
                self.selected_node_id is not None
                or self.selected_connection_id is not None
                or self.selected_blocked_point is not None
            )
            self.on_selection_change(has_selection)

    def _emit_document_change(self) -> None:
        if self.on_document_change is not None:
            self.on_document_change()

    def _emit_context_change(self, message: str | None = None) -> None:
        if self.on_context_change is not None:
            self.on_context_change(message or self._context_message())

    def _context_message(self) -> str:
        if self.block_mode:
            return "Clic para marcar o quitar obstaculo"
        if self.pending_connection_source_id is not None:
            return "Clic derecho en el nodo destino para conectar"
        if self.hover_port is not None:
            return "Clic derecho en dos nodos para conectar"
        if self.selected_node_id is not None:
            return "Arrastra para mover. Doble clic para editar"
        if self.selected_connection_id is not None:
            return "Conexion seleccionada. Supr para eliminar"
        if self.selected_blocked_point is not None:
            return "Obstaculo seleccionado. Supr para eliminar"
        return "Clic para crear nodo"

    def _mark_document_changed(self, routes_dirty: bool = True, layout_dirty: bool = True) -> None:
        if layout_dirty:
            self._invalidate_layout_cache()
        if routes_dirty:
            self._routes_dirty = True
        self._emit_document_change()
        self.request_redraw()

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
        return get_resized_photo(self.cross_cursor_source_image, self.cross_cursor_cache, size, crop_alpha=True)

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
            self.canvas.itemconfigure(self.custom_cursor_canvas_id, image=cursor_image, state="normal")
        self.canvas.tag_raise(self.custom_cursor_canvas_id)

    def _to_screen_layout(self, layout: NodeLayout) -> NodeLayout:
        return to_screen_layout(layout, self.pan_x, self.pan_y, self.zoom)

    def _scale_box(self, box):
        return scale_box(box, self.pan_x, self.pan_y, self.zoom)

    def _offset_screen_layout(self, layout: NodeLayout, delta_x: float, delta_y: float) -> NodeLayout:
        return offset_screen_layout(layout, delta_x, delta_y)

    def destroy(self) -> None:
        if self.selection_blink_after_id is not None:
            self.after_cancel(self.selection_blink_after_id)
            self.selection_blink_after_id = None
        if self.redraw_after_id is not None:
            self.after_cancel(self.redraw_after_id)
            self.redraw_after_id = None
        self.custom_cursor_canvas_id = None
        super().destroy()


__all__ = ["OrgGridCanvas"]
