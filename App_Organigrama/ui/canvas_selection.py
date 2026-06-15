"""Selection overlay drawing for the organigram canvas."""

from __future__ import annotations

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
    route = next(
        (route for route in view.route_cache if route.connection.id == view.selected_connection_id),
        None,
    )
    if route is None:
        return

    points: list[float] = []
    for grid_x, grid_y in route.points:
        world_x, world_y = view.rendering_engine.grid_to_world(grid_x, grid_y)
        screen_x, screen_y = view._world_to_screen(world_x, world_y)
        points.extend((screen_x, screen_y))
    view.canvas.create_line(
        *points,
        fill=SELECTION_COLOR,
        width=max(4, int(view.rendering_engine.base_line_width * view.zoom * 2.0)),
        capstyle="butt",
        joinstyle="miter",
        tags="selection-overlay",
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
        tags="selection-overlay",
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
        tags="selection-overlay",
    )
