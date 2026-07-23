"""Small, toolkit-independent viewport culling helpers."""

from __future__ import annotations


VIEWPORT_OVERSCAN_PX = 180.0


def screen_box_intersects_viewport(
    left: float,
    top: float,
    right: float,
    bottom: float,
    viewport_width: float,
    viewport_height: float,
    *,
    overscan: float = VIEWPORT_OVERSCAN_PX,
) -> bool:
    """Return whether a screen-space rectangle touches the visible region."""
    return not (
        right < -overscan
        or bottom < -overscan
        or left > viewport_width + overscan
        or top > viewport_height + overscan
    )


def screen_points_intersect_viewport(
    points: list[tuple[float, float]],
    viewport_width: float,
    viewport_height: float,
    *,
    overscan: float = VIEWPORT_OVERSCAN_PX,
) -> bool:
    """Cull a polyline by its screen-space bounding box."""
    if not points:
        return False
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return screen_box_intersects_viewport(
        min(xs),
        min(ys),
        max(xs),
        max(ys),
        viewport_width,
        viewport_height,
        overscan=overscan,
    )


__all__ = [
    "VIEWPORT_OVERSCAN_PX",
    "screen_box_intersects_viewport",
    "screen_points_intersect_viewport",
]
