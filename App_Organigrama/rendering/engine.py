import textwrap
from dataclasses import dataclass

from App_Organigrama.models.document import OrgGridDocument, OrgNode
from App_Organigrama.rendering.palette import DEFAULT_HIERARCHY_STYLE, HIERARCHY_STYLE_BY_COLOR


HORIZONTAL_ORIENTATION = "horizontal"
VERTICAL_ORIENTATION = "vertical"


@dataclass(frozen=True, slots=True)
class PageLayout:
    width: float
    height: float
    margin_left: float
    margin_top: float
    margin_right: float
    margin_bottom: float
    header_height: float


@dataclass(frozen=True, slots=True)
class NodeStyle:
    width: float
    min_height: float
    name_font_size: float
    role_font_size: float
    name_line_height: float
    role_line_height: float
    text_padding_x: float
    text_padding_top: float
    text_padding_bottom: float
    text_gap: float
    logo_radius: float
    logo_center_offset_y: float
    connection_line_width: float


@dataclass(frozen=True, slots=True)
class NodeTextLine:
    text: str
    top: float
    font_size: float
    line_height: float
    is_bold: bool


@dataclass(frozen=True, slots=True)
class Box:
    left: float
    top: float
    right: float
    bottom: float

    @property
    def width(self) -> float:
        return self.right - self.left

    @property
    def height(self) -> float:
        return self.bottom - self.top


@dataclass(frozen=True, slots=True)
class NodeLayout:
    center_x: float
    center_y: float
    box: Box
    visual_box: Box
    lines: tuple[NodeTextLine, ...]
    style: NodeStyle
    logo_center_x: float
    logo_center_y: float
    logo_image_size: float


@dataclass(frozen=True, slots=True)
class DocumentBounds:
    left: float
    top: float
    right: float
    bottom: float

    @property
    def width(self) -> float:
        return max(0.0, self.right - self.left)

    @property
    def height(self) -> float:
        return max(0.0, self.bottom - self.top)

    @classmethod
    def from_box(cls, box: Box) -> "DocumentBounds":
        return cls(left=box.left, top=box.top, right=box.right, bottom=box.bottom)

    def include_box(self, box: Box) -> "DocumentBounds":
        return DocumentBounds(
            left=min(self.left, box.left),
            top=min(self.top, box.top),
            right=max(self.right, box.right),
            bottom=max(self.bottom, box.bottom),
        )

    def include_point(self, x: float, y: float) -> "DocumentBounds":
        return DocumentBounds(
            left=min(self.left, x),
            top=min(self.top, y),
            right=max(self.right, x),
            bottom=max(self.bottom, y),
        )


class RenderingEngine:
    """Single source of truth for node sizing, text wrapping and coordinate mapping."""

    content_top_margin: float = 10.0
    base_cell_width: float = 250.0
    base_cell_height: float = 260.0
    base_node_width: float = 210.0
    base_node_min_height: float = 87.0
    base_logo_radius: float = 44.0
    base_line_width: float = 2.1
    base_text_padding_x: float = 22.0
    base_text_padding_top: float = 27.0
    base_text_padding_bottom: float = 5.0
    base_text_gap: float = 5.0
    base_name_font_size: float = 14.0
    base_role_font_size: float = 12.0

    def normalize_orientation(self, orientation: str) -> str:
        return VERTICAL_ORIENTATION if orientation == VERTICAL_ORIENTATION else HORIZONTAL_ORIENTATION

    def get_page_layout(self, orientation: str) -> PageLayout:
        normalized = self.normalize_orientation(orientation)
        if normalized == VERTICAL_ORIENTATION:
            return PageLayout(
                width=612.0,
                height=792.0,
                margin_left=12.0,
                margin_top=16.0,
                margin_right=12.0,
                margin_bottom=12.0,
                header_height=132.0,
            )

        return PageLayout(
            width=792.0,
            height=612.0,
            margin_left=12.0,
            margin_top=16.0,
            margin_right=12.0,
            margin_bottom=12.0,
            header_height=112.0,
        )

    def world_to_grid(self, world_x: float, world_y: float) -> tuple[int, int]:
        return (
            round(world_x / self.base_cell_width),
            round(world_y / self.base_cell_height),
        )

    def grid_to_world(self, grid_x: float, grid_y: float) -> tuple[float, float]:
        return (grid_x * self.base_cell_width, grid_y * self.base_cell_height)

    def get_node_style(self, color: str) -> NodeStyle:
        hierarchy = HIERARCHY_STYLE_BY_COLOR.get(color, DEFAULT_HIERARCHY_STYLE)
        name_font_size = self.base_name_font_size * hierarchy.name_font_scale
        role_font_size = self.base_role_font_size * hierarchy.role_font_scale
        return NodeStyle(
            width=self.base_node_width * hierarchy.width_scale,
            min_height=self.base_node_min_height * hierarchy.min_height_scale,
            name_font_size=name_font_size,
            role_font_size=role_font_size,
            name_line_height=name_font_size * 1.15,
            role_line_height=role_font_size * 1.22,
            text_padding_x=self.base_text_padding_x,
            text_padding_top=self.base_text_padding_top,
            text_padding_bottom=self.base_text_padding_bottom,
            text_gap=self.base_text_gap,
            logo_radius=self.base_logo_radius,
            logo_center_offset_y=-17.0,
            connection_line_width=self.base_line_width,
        )

    def layout_node(self, node: OrgNode, include_logo: bool = True) -> NodeLayout:
        style = self.get_node_style(node.color)
        center_x, center_y = self.grid_to_world(node.grid_x, node.grid_y)
        name_lines = self.wrap_text(node.nombre or "ASIGNAR NOMBRE", style.name_font_size, style.width, style.text_padding_x)
        role_lines = self.wrap_text(node.cargo, style.role_font_size, style.width, style.text_padding_x)

        cursor_y = style.text_padding_top
        lines: list[NodeTextLine] = []
        for line in name_lines:
            lines.append(
                NodeTextLine(
                    text=line,
                    top=cursor_y,
                    font_size=style.name_font_size,
                    line_height=style.name_line_height,
                    is_bold=True,
                )
            )
            cursor_y += style.name_line_height

        if name_lines and role_lines:
            cursor_y += style.text_gap

        for line in role_lines:
            lines.append(
                NodeTextLine(
                    text=line,
                    top=cursor_y,
                    font_size=style.role_font_size,
                    line_height=style.role_line_height,
                    is_bold=False,
                )
            )
            cursor_y += style.role_line_height

        content_height = max(0.0, cursor_y - style.text_padding_top)
        height = max(style.min_height, style.text_padding_top + content_height + style.text_padding_bottom)
        box = Box(
            left=center_x - (style.width / 2),
            top=center_y - (height / 2),
            right=center_x + (style.width / 2),
            bottom=center_y + (height / 2),
        )
        logo_center_x = center_x
        logo_center_y = box.top + style.logo_center_offset_y
        logo_image_size = style.logo_radius * 1.35
        visual_top = min(box.top, logo_center_y - style.logo_radius) if include_logo else box.top
        visual_box = Box(left=box.left, top=visual_top, right=box.right, bottom=box.bottom)
        return NodeLayout(
            center_x=center_x,
            center_y=center_y,
            box=box,
            visual_box=visual_box,
            lines=tuple(lines),
            style=style,
            logo_center_x=logo_center_x,
            logo_center_y=logo_center_y,
            logo_image_size=logo_image_size,
        )

    def get_node_box(self, node: OrgNode, include_logo: bool = True) -> Box:
        layout = self.layout_node(node, include_logo=include_logo)
        return layout.visual_box if include_logo else layout.box

    def get_node_port(self, node: OrgNode, port: str) -> tuple[float, float]:
        layout = self.layout_node(node, include_logo=False)
        if port == "top":
            return (layout.center_x, layout.box.top)
        if port == "bottom":
            return (layout.center_x, layout.box.bottom)
        if port == "left":
            return (layout.box.left, layout.center_y)
        return (layout.box.right, layout.center_y)

    def get_node_port_grid_position(self, node: OrgNode, port: str) -> tuple[float, float]:
        port_x, port_y = self.get_node_port(node, port)
        return (port_x / self.base_cell_width, port_y / self.base_cell_height)

    def get_obstacle_box(self, grid_x: float, grid_y: float) -> Box:
        center_x, center_y = self.grid_to_world(grid_x, grid_y)
        radius = 12.0
        return Box(
            left=center_x - radius,
            top=center_y - radius,
            right=center_x + radius,
            bottom=center_y + radius,
        )

    def wrap_text(
        self,
        text: str,
        font_size: float,
        node_width: float,
        horizontal_padding: float,
    ) -> list[str]:
        normalized_text = (text or "").strip()
        if not normalized_text:
            return []

        usable_width = max(20.0, node_width - (horizontal_padding * 2))
        estimated_char_width = max(4.5, font_size * 0.56)
        characters_per_line = max(8, int(usable_width / estimated_char_width))

        wrapped_lines: list[str] = []
        for paragraph in normalized_text.splitlines():
            paragraph_lines = textwrap.wrap(
                paragraph,
                width=characters_per_line,
                break_long_words=False,
                replace_whitespace=False,
            )
            wrapped_lines.extend(paragraph_lines or [paragraph])
        return wrapped_lines

    def compute_document_bounds(
        self,
        document: OrgGridDocument,
        routes: list[list[tuple[float, float]]] | None = None,
        include_blocked_points: bool = True,
    ) -> DocumentBounds:
        bounds: DocumentBounds | None = None

        for node in document.nodes.values():
            node_box = self.get_node_box(node, include_logo=document.show_logos)
            bounds = DocumentBounds.from_box(node_box) if bounds is None else bounds.include_box(node_box)

        if include_blocked_points:
            for point_x, point_y in document.blocked_points:
                obstacle_box = self.get_obstacle_box(point_x, point_y)
                bounds = DocumentBounds.from_box(obstacle_box) if bounds is None else bounds.include_box(obstacle_box)

        if routes:
            for route in routes:
                for point_x, point_y in route:
                    world_x, world_y = self.grid_to_world(point_x, point_y)
                    bounds = (
                        DocumentBounds(left=world_x, top=world_y, right=world_x, bottom=world_y)
                        if bounds is None
                        else bounds.include_point(world_x, world_y)
                    )

        if bounds is None:
            return DocumentBounds(left=0.0, top=0.0, right=0.0, bottom=0.0)
        return bounds
