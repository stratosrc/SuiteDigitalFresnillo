"""Selection overlay drawing for the organigram canvas."""

from __future__ import annotations

from App_Organigrama.rendering.connection_arrows import build_arrow_triangle, flatten_points
from App_Organigrama.ui.canvas_shapes import create_rounded_rectangle
from App_Organigrama.ui.theme import SELECTION_COLOR

GridPoint = tuple[float, float]


def draw_connection_selection_overlay(view) -> None:
    """Draw selected connection below nodes."""
    if not view.selection_blink_visible:
        return

    if view.selected_connection_id is not None:
        draw_selected_connection_overlay(view)


def draw_node_selection_overlay(view) -> None:
    """Draw selected nodes and blocked points above nodes."""
    if not view.selection_blink_visible:
        return

    if view.selected_node_id is not None:
        draw_selected_node_overlay(view)

    if view.selected_blocked_point is not None:
        draw_selected_blocked_point_overlay(view)


def draw_selection_overlay(view) -> None:
    """Draw the current canvas selection overlay."""
    draw_connection_selection_overlay(view)
    draw_node_selection_overlay(view)


def draw_selected_connection_overlay(view) -> None:
    route = view._selected_connection_route()
    if route is None:
        return

    points: list[float] = []
    screen_points: list[tuple[float, float]] = []
    for grid_x, grid_y in route.points:
        world_x, world_y = view.rendering_engine.grid_to_world(grid_x, grid_y)
        screen_x, screen_y = view._world_to_screen(world_x, world_y)
        screen_points.append((screen_x, screen_y))
        points.extend((screen_x, screen_y))
    view.canvas.create_line(
        *points,
        fill=SELECTION_COLOR,
        width=max(4, int(view.rendering_engine.base_line_width * view.zoom * 2.0)),
        capstyle="butt",
        joinstyle="miter",
        tags=("selection-overlay", "connection-selection-overlay"),
    )
    arrow = build_arrow_triangle(
        screen_points,
        length=max(9.0, 14.0 * view.zoom),
        width=max(9.0, 13.0 * view.zoom),
        target_gap=max(7.0, 10.0 * view.zoom),
    )
    if arrow is not None:
        view.canvas.create_polygon(
            *flatten_points(arrow),
            fill=SELECTION_COLOR,
            outline=SELECTION_COLOR,
            tags=("selection-overlay", "connection-selection-overlay"),
        )


def draw_selected_node_overlay(view) -> None:
    node = view.document.nodes.get(view.selected_node_id)
    if node is None:
        return

    layout = view._get_node_layout(node, include_logo=view.document.show_logos)
    screen_layout = view._to_screen_layout(layout)
    if node.id == view.drag_node_id and view.drag_screen_point is not None:
        delta_x = view.drag_screen_point[0] - screen_layout.center_x
        delta_y = view.drag_screen_point[1] - screen_layout.center_y
        screen_layout = view._offset_screen_layout(screen_layout, delta_x, delta_y)

    create_rounded_rectangle(
        view.canvas,
        screen_layout.box.left,
        screen_layout.box.top,
        screen_layout.box.right,
        screen_layout.box.bottom,
        radius=max(0, int(12 * view.zoom)),
        fill="",
        outline=SELECTION_COLOR,
        width=max(3, int(3 * view.zoom)),
        tags=("selection-overlay", "node-selection-overlay"),
    )


def draw_selected_blocked_point_overlay(view) -> None:
    grid_x, grid_y = view.selected_blocked_point
    world_x, world_y = view.rendering_engine.grid_to_world(grid_x, grid_y)
    center_x, center_y = view._world_to_screen(world_x, world_y)
    size = max(9, int(11 * view.zoom))
    view.canvas.create_oval(
        center_x - size,
        center_y - size,
        center_x + size,
        center_y + size,
        outline=SELECTION_COLOR,
        width=max(3, int(3 * view.zoom)),
        tags=("selection-overlay", "node-selection-overlay"),
    )
