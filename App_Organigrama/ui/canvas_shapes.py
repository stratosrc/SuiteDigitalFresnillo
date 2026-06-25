from __future__ import annotations

import tkinter as tk


def create_rounded_rectangle(
    canvas: tk.Canvas,
    left: float,
    top: float,
    right: float,
    bottom: float,
    radius: int,
    **options: object,
) -> int:
    radius = min(radius, int((right - left) / 2), int((bottom - top) / 2))
    if radius <= 0:
        return canvas.create_rectangle(left, top, right, bottom, **options)

    points = [
        left + radius,
        top,
        right - radius,
        top,
        right,
        top,
        right,
        top + radius,
        right,
        bottom - radius,
        right,
        bottom,
        right - radius,
        bottom,
        left + radius,
        bottom,
        left,
        bottom,
        left,
        bottom - radius,
        left,
        top + radius,
        left,
        top,
    ]
    return canvas.create_polygon(points, smooth=True, splinesteps=12, **options)
