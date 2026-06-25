"""Coordinate transforms and layout projection for the organigram canvas."""

from __future__ import annotations

import typing

from App_Organigrama.rendering.engine import Box, NodeLayout

GridPoint = typing.Tuple[float, float]


def world_to_screen(world_x: float, world_y: float, pan_x: float, pan_y: float, zoom: float) -> tuple[float, float]:
    """Convert world coordinates into screen coordinates."""
    return (pan_x + (world_x * zoom), pan_y + (world_y * zoom))


def screen_to_grid(screen_x: int, screen_y: int, pan_x: float, pan_y: float, zoom: float, rendering_engine) -> tuple[int, int]:
    """Convert screen coordinates into integer grid coordinates."""
    world_x = (screen_x - pan_x) / zoom
    world_y = (screen_y - pan_y) / zoom
    return rendering_engine.world_to_grid(world_x, world_y)


def screen_to_subgrid(screen_x: int, screen_y: int, pan_x: float, pan_y: float, zoom: float, rendering_engine) -> GridPoint:
    """Convert screen coordinates into half-step grid coordinates."""
    world_x = (screen_x - pan_x) / zoom
    world_y = (screen_y - pan_y) / zoom
    return (
        round((world_x / rendering_engine.base_cell_width) * 2) / 2,
        round((world_y / rendering_engine.base_cell_height) * 2) / 2,
    )


def scale_box(box: Box, pan_x: float, pan_y: float, zoom: float) -> Box:
    """Scale a world box into a screen box."""
    left, top = world_to_screen(box.left, box.top, pan_x, pan_y, zoom)
    right, bottom = world_to_screen(box.right, box.bottom, pan_x, pan_y, zoom)
    return type(box)(left=left, top=top, right=right, bottom=bottom)


def to_screen_layout(layout: NodeLayout, pan_x: float, pan_y: float, zoom: float) -> NodeLayout:
    """Project a node layout from world space into screen space."""
    scaled_box = scale_box(layout.box, pan_x, pan_y, zoom)
    scaled_visual_box = scale_box(layout.visual_box, pan_x, pan_y, zoom)
    scaled_lines = []
    for line in layout.lines:
        line_top_world = layout.box.top + line.top
        _screen_x, screen_top = world_to_screen(layout.center_x, line_top_world, pan_x, pan_y, zoom)
        scaled_lines.append(
            type(line)(
                text=line.text,
                top=screen_top,
                font_size=line.font_size * zoom,
                line_height=line.line_height * zoom,
                is_bold=line.is_bold,
                align=line.align,
                is_underlined=line.is_underlined,
            )
        )
    scaled_style = type(layout.style)(
        width=layout.style.width * zoom,
        min_height=layout.style.min_height * zoom,
        name_font_size=layout.style.name_font_size * zoom,
        role_font_size=layout.style.role_font_size * zoom,
        name_line_height=layout.style.name_line_height * zoom,
        role_line_height=layout.style.role_line_height * zoom,
        text_padding_x=layout.style.text_padding_x * zoom,
        text_padding_top=layout.style.text_padding_top * zoom,
        text_padding_bottom=layout.style.text_padding_bottom * zoom,
        text_gap=layout.style.text_gap * zoom,
        logo_radius=layout.style.logo_radius * zoom,
        logo_center_offset_y=layout.style.logo_center_offset_y * zoom,
        connection_line_width=layout.style.connection_line_width * zoom,
    )
    screen_center_x, screen_center_y = world_to_screen(layout.center_x, layout.center_y, pan_x, pan_y, zoom)
    logo_center_x, logo_center_y = world_to_screen(layout.logo_center_x, layout.logo_center_y, pan_x, pan_y, zoom)
    return NodeLayout(
        center_x=screen_center_x,
        center_y=screen_center_y,
        box=scaled_box,
        visual_box=scaled_visual_box,
        lines=tuple(scaled_lines),
        style=scaled_style,
        logo_center_x=logo_center_x,
        logo_center_y=logo_center_y,
        logo_image_size=layout.logo_image_size * zoom,
    )


def offset_screen_layout(layout: NodeLayout, delta_x: float, delta_y: float) -> NodeLayout:
    """Move an already-projected screen layout."""
    shifted_box = type(layout.box)(
        left=layout.box.left + delta_x,
        top=layout.box.top + delta_y,
        right=layout.box.right + delta_x,
        bottom=layout.box.bottom + delta_y,
    )
    shifted_visual_box = type(layout.visual_box)(
        left=layout.visual_box.left + delta_x,
        top=layout.visual_box.top + delta_y,
        right=layout.visual_box.right + delta_x,
        bottom=layout.visual_box.bottom + delta_y,
    )
    shifted_lines = tuple(
        type(line)(
            text=line.text,
            top=line.top + delta_y,
            font_size=line.font_size,
            line_height=line.line_height,
            is_bold=line.is_bold,
            align=line.align,
            is_underlined=line.is_underlined,
        )
        for line in layout.lines
    )
    return NodeLayout(
        center_x=layout.center_x + delta_x,
        center_y=layout.center_y + delta_y,
        box=shifted_box,
        visual_box=shifted_visual_box,
        lines=shifted_lines,
        style=layout.style,
        logo_center_x=layout.logo_center_x + delta_x,
        logo_center_y=layout.logo_center_y + delta_y,
        logo_image_size=layout.logo_image_size,
    )
