"""Helpers for persistent manual Manhattan connection routes."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass


GridPoint = tuple[float, float]


@dataclass(frozen=True, slots=True)
class GridBox:
    left: float
    top: float
    right: float
    bottom: float


def build_manual_route(
    start: GridPoint,
    end: GridPoint,
    manual_points: Sequence[GridPoint],
    source_port: str,
    target_port: str,
) -> list[GridPoint]:
    """Reconnect stored intermediate points to current node ports."""
    if not manual_points:
        return [start, end]

    points = [start, *(normalize_point(point) for point in manual_points), end]
    first = points[1]
    points[1] = (
        (first[0], start[1])
        if source_port in {"left", "right"}
        else (start[0], first[1])
    )
    last = points[-2]
    points[-2] = (
        (last[0], end[1])
        if target_port in {"left", "right"}
        else (end[0], last[1])
    )
    return simplify_orthogonal_route(points)


def move_intermediate_segment(
    route_points: Sequence[GridPoint],
    segment_index: int,
    pointer: GridPoint,
) -> list[GridPoint]:
    """Move an intermediate segment along its perpendicular axis."""
    if not is_movable_segment(route_points, segment_index):
        raise ValueError("Solo se pueden mover segmentos intermedios.")

    points = [normalize_point(point) for point in route_points]
    start = points[segment_index]
    end = points[segment_index + 1]
    pointer_x, pointer_y = normalize_point(pointer)
    if start[1] == end[1]:
        points[segment_index] = (start[0], pointer_y)
        points[segment_index + 1] = (end[0], pointer_y)
    elif start[0] == end[0]:
        points[segment_index] = (pointer_x, start[1])
        points[segment_index + 1] = (pointer_x, end[1])
    else:
        raise ValueError("La conexión debe conservar segmentos ortogonales.")
    return simplify_orthogonal_route(points)


def route_crosses_boxes(
    route_points: Sequence[GridPoint],
    boxes: Sequence[GridBox],
    epsilon: float = 1e-6,
) -> bool:
    """Return whether an orthogonal route enters the interior of any box."""
    for start, end in zip(route_points, route_points[1:]):
        x1, y1 = normalize_point(start)
        x2, y2 = normalize_point(end)
        for box in boxes:
            left = box.left + epsilon
            right = box.right - epsilon
            top = box.top + epsilon
            bottom = box.bottom - epsilon
            if x1 == x2:
                segment_top, segment_bottom = sorted((y1, y2))
                if left < x1 < right and max(segment_top, top) < min(segment_bottom, bottom):
                    return True
            elif y1 == y2:
                segment_left, segment_right = sorted((x1, x2))
                if top < y1 < bottom and max(segment_left, left) < min(segment_right, right):
                    return True
            else:
                raise ValueError("La conexión debe conservar segmentos ortogonales.")
    return False


def is_movable_segment(
    route_points: Sequence[GridPoint],
    segment_index: int,
) -> bool:
    """Return whether a segment excludes both node-adjacent route ends."""
    return (
        len(route_points) >= 4
        and 1 <= segment_index <= len(route_points) - 3
        and route_points[segment_index] != route_points[segment_index + 1]
    )


def simplify_orthogonal_route(points: Sequence[GridPoint]) -> list[GridPoint]:
    """Remove duplicate and collinear points without changing route shape."""
    normalized: list[GridPoint] = []
    for point in points:
        current = normalize_point(point)
        if not normalized or normalized[-1] != current:
            normalized.append(current)

    if len(normalized) <= 2:
        return normalized

    simplified = [normalized[0]]
    for index in range(1, len(normalized) - 1):
        previous = simplified[-1]
        current = normalized[index]
        following = normalized[index + 1]
        same_x = previous[0] == current[0] == following[0]
        same_y = previous[1] == current[1] == following[1]
        if not same_x and not same_y:
            simplified.append(current)
    simplified.append(normalized[-1])
    return simplified


def normalize_point(point: GridPoint) -> GridPoint:
    """Snap route coordinates to the half-grid used by the router."""
    return (round(float(point[0]) * 2) / 2, round(float(point[1]) * 2) / 2)


__all__ = [
    "GridBox",
    "GridPoint",
    "build_manual_route",
    "is_movable_segment",
    "move_intermediate_segment",
    "normalize_point",
    "route_crosses_boxes",
    "simplify_orthogonal_route",
]
