"""Pure zoom helpers for the PDF viewer."""

from App_TestData.config.settings import ZOOM_MAX, ZOOM_MIN, ZOOM_STEP


def get_next_zoom(current_zoom: float | None, action: str) -> float | None:
    """Return the next zoom value for the requested action."""
    base_zoom = current_zoom or 1.0
    if action == "in":
        return round(min(ZOOM_MAX, base_zoom + ZOOM_STEP), 2)
    if action == "out":
        return round(max(ZOOM_MIN, base_zoom - ZOOM_STEP), 2)
    return None


def get_auto_zoom(pdf_width: float, canvas_width: float) -> float:
    """Calculate an automatic zoom that fits the current canvas width."""
    if pdf_width <= 0:
        raise ValueError("Invalid PDF page width")
    return min(ZOOM_MAX, max(ZOOM_MIN, canvas_width / pdf_width))


def format_zoom_percentage(zoom: float | None) -> str:
    """Format a zoom value as the label shown in the UI."""
    return f"{int(round((zoom or 1.0) * 100))}%"
