from dataclasses import dataclass


PRIMARY_BLUE = "#09519F"
SECONDARY_BLUE = "#3C8AC9"
LIGHT_BLUE = "#9DC3E6"
NEUTRAL_GRAY = "#797E85"

NODE_COLOR_CHOICES: tuple[tuple[str, str], ...] = (
    ("Secretarios", PRIMARY_BLUE),
    ("Directores", SECONDARY_BLUE),
    ("Coordinadores, Jefes o Encargados de Departamento", LIGHT_BLUE),
    ("Personal Administrativo", NEUTRAL_GRAY),
)

HIERARCHY_LEVEL_BY_COLOR = {
    color: level
    for level, (_label, color) in enumerate(NODE_COLOR_CHOICES)
}
HIERARCHY_LABEL_BY_COLOR = {
    color: label
    for label, color in NODE_COLOR_CHOICES
}


def is_inverse_hierarchy(source_color: str, target_color: str) -> bool:
    """Return whether a connection points from a lower to a higher hierarchy."""
    source_level = HIERARCHY_LEVEL_BY_COLOR.get(source_color)
    target_level = HIERARCHY_LEVEL_BY_COLOR.get(target_color)
    if source_level is None or target_level is None:
        return False
    return source_level > target_level


@dataclass(frozen=True, slots=True)
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
