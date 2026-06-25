"""Hit-testing helpers for the organigram canvas."""

from __future__ import annotations

import typing

import math

from App_Organigrama.models.document import OrgNode
from App_Organigrama.rendering.engine import RenderingEngine
from App_Organigrama.routing.manhattan_router import ConnectionRoute

GridPoint = typing.Tuple[float, float]
ScreenPoint = typing.Tuple[float, float]


def distance_to_segment(
    screen_x: int,
    screen_y: int,
    start: ScreenPoint,
    end: ScreenPoint,
) -> float:
    """Return the distance from a screen point to a segment."""
    ax, ay = start
    bx, by = end
    dx = bx - ax
    dy = by - ay
    if dx == 0 and dy == 0:
        return math.hypot(screen_x - ax, screen_y - ay)

    projection = max(0.0, min(1.0, ((screen_x - ax) * dx + (screen_y - ay) * dy) / ((dx * dx) + (dy * dy))))
    point_x = ax + (projection * dx)
    point_y = ay + (projection * dy)
    return math.hypot(screen_x - point_x, screen_y - point_y)


def find_blocked_point_at_screen(
    blocked_points: list[GridPoint],
    screen_x: int,
    screen_y: int,
    zoom: float,
    rendering_engine: RenderingEngine,
    world_to_screen,
) -> GridPoint | None:
    """Find the closest blocked point under the pointer."""
    hit_radius = max(10.0, 12.0 * zoom)
    closest_point: GridPoint | None = None
    closest_distance = hit_radius
    for blocked_point in blocked_points:
        world_x, world_y = rendering_engine.grid_to_world(blocked_point[0], blocked_point[1])
        center_x, center_y = world_to_screen(world_x, world_y)
        distance = math.hypot(screen_x - center_x, screen_y - center_y)
        if distance <= closest_distance:
            closest_distance = distance
            closest_point = blocked_point
    return closest_point


def find_connection_at_screen(
    routes: list[ConnectionRoute],
    screen_x: int,
    screen_y: int,
    rendering_engine: RenderingEngine,
    world_to_screen,
    max_distance: float = 10.0,
) -> ConnectionRoute | None:
    """Find the closest connection route under the pointer."""
    best_route: ConnectionRoute | None = None
    best_distance = max_distance
    for route in routes:
        points = [
            world_to_screen(*rendering_engine.grid_to_world(point[0], point[1]))
            for point in route.points
        ]
        for start, end in zip(points, points[1:]):
            distance = distance_to_segment(screen_x, screen_y, start, end)
            if distance < best_distance:
                best_distance = distance
                best_route = route
    return best_route


def find_movable_segment_at_screen(
    route: ConnectionRoute,
    screen_x: int,
    screen_y: int,
    rendering_engine: RenderingEngine,
    world_to_screen,
    max_distance: float = 10.0,
) -> int | None:
    """Find a movable intermediate segment, excluding both node-adjacent ends."""
    if len(route.points) < 4:
        return None

    points = [
        world_to_screen(*rendering_engine.grid_to_world(point[0], point[1]))
        for point in route.points
    ]
    best_index: int | None = None
    best_distance = max_distance
    for index in range(1, len(points) - 2):
        distance = distance_to_segment(screen_x, screen_y, points[index], points[index + 1])
        if distance < best_distance:
            best_distance = distance
            best_index = index
    return best_index


def find_bend_point_at_screen(
    route: ConnectionRoute,
    screen_x: int,
    screen_y: int,
    rendering_engine: RenderingEngine,
    world_to_screen,
    max_distance: float = 10.0,
) -> int | None:
    """Find an internal route bend under the pointer."""
    best_index: int | None = None
    best_distance = max_distance
    for index, point in enumerate(route.points[1:-1], start=1):
        point_x, point_y = world_to_screen(*rendering_engine.grid_to_world(*point))
        distance = math.hypot(screen_x - point_x, screen_y - point_y)
        if distance <= best_distance:
            best_distance = distance
            best_index = index
    return best_index


def nearest_port(
    node: OrgNode,
    screen_x: int,
    screen_y: int,
    layout,
    zoom: float,
    world_to_screen,
) -> str:
    """Return the closest node port to a screen point."""
    center_x, center_y = world_to_screen(layout.center_x, layout.center_y)
    half_width = (layout.box.width * zoom) / 2
    half_height = (layout.box.height * zoom) / 2
    distances = {
        "top": abs(screen_y - (center_y - half_height)),
        "bottom": abs(screen_y - (center_y + half_height)),
        "left": abs(screen_x - (center_x - half_width)),
        "right": abs(screen_x - (center_x + half_width)),
    }
    return min(distances, key=distances.get)
