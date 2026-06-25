"""Geometry helpers for directional connection arrows."""

from __future__ import annotations

import typing

import math
from typing import Sequence


Point = typing.Tuple[float, float]


def build_arrow_triangle(
    route_points: Sequence[Point],
    *,
    length: float,
    width: float,
    target_gap: float,
) -> tuple[Point, Point, Point] | None:
    """Build a triangle pointing toward the final route point."""
    segment = _last_distinct_segment(route_points)
    if segment is None:
        return None

    start, end = segment
    delta_x = end[0] - start[0]
    delta_y = end[1] - start[1]
    distance = math.hypot(delta_x, delta_y)
    if distance <= 0:
        return None

    direction_x = delta_x / distance
    direction_y = delta_y / distance
    effective_gap = min(target_gap, max(0.0, distance * 0.35))
    effective_length = min(length, max(3.0, distance - effective_gap))

    tip = (
        end[0] - (direction_x * effective_gap),
        end[1] - (direction_y * effective_gap),
    )
    base_center = (
        tip[0] - (direction_x * effective_length),
        tip[1] - (direction_y * effective_length),
    )
    perpendicular_x = -direction_y
    perpendicular_y = direction_x
    half_width = width / 2
    return (
        tip,
        (
            base_center[0] + (perpendicular_x * half_width),
            base_center[1] + (perpendicular_y * half_width),
        ),
        (
            base_center[0] - (perpendicular_x * half_width),
            base_center[1] - (perpendicular_y * half_width),
        ),
    )


def flatten_points(points: Sequence[Point]) -> tuple[float, ...]:
    """Flatten coordinate pairs for Tkinter polygon APIs."""
    return tuple(coordinate for point in points for coordinate in point)


def _last_distinct_segment(route_points: Sequence[Point]) -> tuple[Point, Point] | None:
    if len(route_points) < 2:
        return None
    end = route_points[-1]
    for start in reversed(route_points[:-1]):
        if start != end:
            return start, end
    return None


__all__ = ["Point", "build_arrow_triangle", "flatten_points"]
