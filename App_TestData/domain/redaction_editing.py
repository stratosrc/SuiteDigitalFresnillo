"""Pure rectangle editing helpers."""

from App_TestData.domain.legal_text import build_censorship_text
from App_TestData.domain.redaction_history import make_history_action, redo_last_action, undo_last_action


CLASSIFICATION_DISPLAY_NAMES = {
    "reserved": "Información Reservada",
    "confidential": "Información Confidencial",
}


def get_classification_display_name(classification: str) -> str:
    """Return the stable user-facing name for a classified redaction."""
    return CLASSIFICATION_DISPLAY_NAMES.get(classification, classification)


def delete_selected_rectangle(rectangles, selected_rect_id):
    """Remove the selected rectangle from the collection."""
    if not selected_rect_id:
        return list(rectangles), None, None, None

    removed_rectangle = next(
        (item for item in rectangles if item["id"] == selected_rect_id),
        None,
    )
    if removed_rectangle is None:
        return list(rectangles), None, None, None

    remaining_rectangles = [item for item in rectangles if item["id"] != selected_rect_id]
    action = make_history_action("delete", rectangle=removed_rectangle)
    return remaining_rectangles, None, removed_rectangle, action


def undo_last_rectangle(rectangles, undo_stack, redo_stack):
    """Undo the last recorded redaction action."""
    return undo_last_action(rectangles, undo_stack, redo_stack)


def redo_last_rectangle(rectangles, undo_stack, redo_stack):
    """Redo the last redaction action removed through undo."""
    return redo_last_action(rectangles, undo_stack, redo_stack)


def refresh_rectangle_metadata(rectangles):
    """Update derived label and description fields for every rectangle."""
    for rectangle in iter_rectangles_in_order(rectangles):
        metadata = build_rectangle_metadata(rectangle)
        rectangle.update(metadata)


def iter_rectangles_in_order(rectangles):
    """Return rectangles ordered by their stable creation sequence."""
    return sorted(rectangles, key=lambda item: item["order"])


def build_rectangle_metadata(rectangle):
    """Build the user-visible metadata associated with a rectangle."""
    classification = rectangle.get("classification", "general")
    concept_id = rectangle.get("concept_id")

    if classification == "reserved":
        label_text = "Reservada"
    elif classification == "confidential":
        label_text = "Confidencial"
    elif classification == "other_law":
        label_text = "Otra"
    elif classification == "custom":
        label_text = "P"
    else:
        label_text = f"#{concept_id}"

    display_text = rectangle.get("concept_name", label_text)
    description = rectangle.get("description", "")
    if classification == "general":
        description = build_censorship_text(
            label_text,
            rectangle.get("concept_name", ""),
            rectangle.get("rows", 1),
            rectangle.get("paragraphs", 1),
        )

    return {
        "label": label_text,
        "description": description,
        "display_text": display_text,
    }
