from __future__ import annotations

from dataclasses import dataclass


PRIMARY_BLUE = "#09519F"
SECONDARY_BLUE = "#3C8AC9"
LIGHT_BLUE = "#9DC3E6"
NEUTRAL_GRAY = "#797E85"

NODE_COLOR_CHOICES: tuple[tuple[str, str], ...] = (
    ("Azul institucional", PRIMARY_BLUE),
    ("Azul medio", SECONDARY_BLUE),
    ("Azul claro", LIGHT_BLUE),
    ("Gris institucional", NEUTRAL_GRAY),
)


@dataclass(frozen=True)
class HierarchyStyle:
    width_scale: float
    min_height_scale: float
    name_font_scale: float
    role_font_scale: float


DEFAULT_HIERARCHY_STYLE = HierarchyStyle(
    width_scale=1.0,
    min_height_scale=1.0,
    name_font_scale=1.0,
    role_font_scale=1.0,
)

HIERARCHY_STYLE_BY_COLOR: dict[str, HierarchyStyle] = {
    PRIMARY_BLUE: HierarchyStyle(1.08, 1.08, 1.08, 1.04),
    SECONDARY_BLUE: HierarchyStyle(1.04, 1.03, 1.03, 1.01),
    LIGHT_BLUE: HierarchyStyle(1.0, 1.0, 1.0, 1.0),
    NEUTRAL_GRAY: HierarchyStyle(0.98, 0.98, 0.96, 0.96),
}
