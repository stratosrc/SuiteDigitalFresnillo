"""Pure rectangle editing helpers."""

from App_TestData.domain.legal_text import build_censorship_text


def delete_selected_rectangle(rectangles, selected_rect_id):
    """Remove the selected rectangle from the collection."""
    if not selected_rect_id:
        return list(rectangles), None, None

    removed_rectangle = next(
        (item for item in rectangles if item["id"] == selected_rect_id),
        None,
    )
    if removed_rectangle is None:
        return list(rectangles), None, None

    remaining_rectangles = [item for item in rectangles if item["id"] != selected_rect_id]
    return remaining_rectangles, None, removed_rectangle


def undo_last_rectangle(rectangles, undo_stack, redo_stack):
    """Remove the last rectangle recorded in the undo stack."""
    if not undo_stack:
        return list(rectangles), list(undo_stack), list(redo_stack), None

    restored_redo_stack = list(redo_stack)
    updated_undo_stack = list(undo_stack[:-1])
    removed_rectangle = undo_stack[-1]
    remaining_rectangles = [item for item in rectangles if item["id"] != removed_rectangle["id"]]
    restored_redo_stack.append(removed_rectangle)
    return remaining_rectangles, updated_undo_stack, restored_redo_stack, removed_rectangle


def redo_last_rectangle(rectangles, undo_stack, redo_stack):
    """Restore the last rectangle removed through undo."""
    if not redo_stack:
        return list(rectangles), list(undo_stack), list(redo_stack), None

    restored_rectangle = redo_stack[-1]
    updated_redo_stack = list(redo_stack[:-1])
    updated_rectangles = list(rectangles)
    if all(item["id"] != restored_rectangle["id"] for item in updated_rectangles):
        updated_rectangles.append(restored_rectangle)
        updated_rectangles.sort(key=lambda item: item["order"])

    updated_undo_stack = list(undo_stack)
    updated_undo_stack.append(restored_rectangle)
    return updated_rectangles, updated_undo_stack, updated_redo_stack, restored_rectangle


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
