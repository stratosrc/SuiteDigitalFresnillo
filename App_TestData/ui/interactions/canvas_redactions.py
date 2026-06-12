"""Canvas interaction handlers for rectangle drawing and manipulation."""

from App_TestData.config.settings import (
    DRAFT_RECT_OUTLINE_COLOR,
    DRAFT_RECT_OUTLINE_WIDTH,
    MIN_DRAG_DISTANCE,
    RECTANGLE_FILL_COLOR_ACTIVE,
    RECTANGLE_FONT_NAME,
    RECTANGLE_FONT_SIZE,
    RECTANGLE_OUTLINE_COLOR_NORMAL,
    RECTANGLE_OUTLINE_COLOR_SELECTED,
    RECTANGLE_OUTLINE_WIDTH_NORMAL,
    RECTANGLE_OUTLINE_WIDTH_SELECTED,
    RECTANGLE_TEXT_COLOR,
)
from App_TestData.domain.legal_text import build_censorship_text
from App_TestData.domain.redaction_editing import build_rectangle_metadata
from App_TestData.ui.dialogs.concept_dialog import ConceptDialog

RESIZE_HANDLE_DISTANCE = 10


def setup_canvas_events(app):
    """Bind pointer and keyboard events to the PDF canvas."""
    app.pdf_canvas.bind("<ButtonPress-1>", lambda event: on_button_press(app, event))
    app.pdf_canvas.bind("<B1-Motion>", lambda event: on_move_press(app, event))
    app.pdf_canvas.bind("<ButtonRelease-1>", lambda event: on_button_release(app, event))
    app.pdf_canvas.bind("<Motion>", lambda event: on_pointer_motion(app, event))
    app.bind("<Delete>", lambda _event: _delete_selected_from_key(app))
    app.bind("<BackSpace>", lambda _event: _delete_selected_from_key(app))


def on_button_press(app, event):
    """Start drawing, moving, or resizing a rectangle."""
    if not app.pdf_document:
        return

    canvas_x = app.pdf_canvas.canvasx(event.x)
    canvas_y = app.pdf_canvas.canvasy(event.y)
    rectangle, mode, corner = _hit_test_rectangle(app, canvas_x, canvas_y)

    if rectangle:
        _select_rectangle(app, rectangle)
        app.current_rect = None
        app.drag_mode = mode
        app.active_rect_data = rectangle
        app.active_resize_corner = corner
        app.drag_start_x = canvas_x
        app.drag_start_y = canvas_y
        app.drag_original_coords = app.pdf_manager.pdf_rect_to_canvas(rectangle)
        return

    _select_rectangle(app, None)
    app.drag_mode = "draw"
    app.start_x = canvas_x
    app.start_y = canvas_y
    app.current_rect = app.pdf_canvas.create_rectangle(
        app.start_x,
        app.start_y,
        app.start_x,
        app.start_y,
        outline=DRAFT_RECT_OUTLINE_COLOR,
        width=DRAFT_RECT_OUTLINE_WIDTH,
        tags=("draft_rect",),
    )


def on_move_press(app, event):
    """Update the active drag interaction."""
    if not app.pdf_document:
        return

    current_x = app.pdf_canvas.canvasx(event.x)
    current_y = app.pdf_canvas.canvasy(event.y)
    if app.drag_mode == "move" and app.active_rect_data:
        _move_active_rectangle(app, current_x, current_y)
    elif app.drag_mode == "resize" and app.active_rect_data:
        _resize_active_rectangle(app, current_x, current_y)
    elif app.drag_mode == "draw" and app.current_rect:
        app.pdf_canvas.coords(app.current_rect, app.start_x, app.start_y, current_x, current_y)


def on_button_release(app, event):
    """Complete the active interaction."""
    if not app.pdf_document:
        return

    if app.drag_mode in {"move", "resize"}:
        _normalize_active_rectangle(app)
        _reset_drag_state(app)
        return

    if app.drag_mode != "draw" or not app.current_rect:
        _reset_drag_state(app)
        return

    end_x = app.pdf_canvas.canvasx(event.x)
    end_y = app.pdf_canvas.canvasy(event.y)
    if abs(app.start_x - end_x) < MIN_DRAG_DISTANCE and abs(app.start_y - end_y) < MIN_DRAG_DISTANCE:
        app.pdf_canvas.delete(app.current_rect)
        app.current_rect = None
        _reset_drag_state(app)
        return

    dialog = ConceptDialog(app, app.catalogue_items)
    app.wait_window(dialog)
    if not dialog.result:
        app.pdf_canvas.delete(app.current_rect)
        app.current_rect = None
        _reset_drag_state(app)
        return

    rectangle = _build_rectangle_data(app, dialog.result, end_x, end_y)
    _commit_current_rectangle(app, rectangle)
    app.censored_rectangles.append(rectangle)
    app.undo_stack.append(rectangle)
    app.redo_stack.clear()
    _select_rectangle(app, rectangle)
    app.current_rect = None
    _reset_drag_state(app)


def on_pointer_motion(app, event):
    """Update the cursor based on the hovered rectangle area."""
    if not app.pdf_document or app.drag_mode:
        return

    canvas_x = app.pdf_canvas.canvasx(event.x)
    canvas_y = app.pdf_canvas.canvasy(event.y)
    rectangle, mode, corner = _hit_test_rectangle(app, canvas_x, canvas_y)
    if not rectangle:
        app.pdf_canvas.configure(cursor="")
    elif mode == "resize":
        app.pdf_canvas.configure(cursor=_cursor_for_corner(corner))
    else:
        app.pdf_canvas.configure(cursor="fleur")


def _build_rectangle_data(app, result, end_x, end_y):
    rectangle_id = app.next_rectangle_id
    app.next_rectangle_id += 1
    pdf_x1, pdf_y1, pdf_x2, pdf_y2 = app.pdf_manager.canvas_to_pdf_rect(app.start_x, app.start_y, end_x, end_y)
    classification = result["classification"]

    if classification == "general":
        concept_id = result["concept_id"]
        concept_name = _get_concept_name(app, concept_id)
        description = build_censorship_text(
            f"#{concept_id}",
            concept_name,
            result["rows"],
            result["paragraphs"],
        )
    elif classification == "other_law":
        concept_id = None
        concept_name = result.get("object", "")
        description = ""
    else:
        concept_id = None
        concept_name = (
            "Información Reservada"
            if classification == "reserved"
            else "Información Confidencial"
        )
        description = ""

    rectangle = {
        "id": rectangle_id,
        "order": rectangle_id,
        "page": app.current_page,
        "x1": pdf_x1,
        "y1": pdf_y1,
        "x2": pdf_x2,
        "y2": pdf_y2,
        "classification": classification,
        "concept_id": concept_id,
        "category": app.catalogue_categories.get(concept_id, "normal") if concept_id else classification,
        "concept_name": concept_name,
        "rows": result["rows"],
        "paragraphs": result["paragraphs"],
        "legal_basis": result.get("legal_basis", ""),
        "reason": result.get("reason", ""),
        "object": result.get("object", ""),
        "articles": result.get("articles", ""),
        "law": result.get("law", ""),
        "description": description,
        "rect_tag": f"rect-{rectangle_id}",
        "canvas_rect_id": app.current_rect,
        "canvas_text_id": None,
    }
    rectangle.update(build_rectangle_metadata(rectangle))
    return rectangle


def _commit_current_rectangle(app, rectangle):
    canvas_x1, canvas_y1, canvas_x2, canvas_y2 = app.pdf_manager.pdf_rect_to_canvas(rectangle)
    app.pdf_canvas.coords(app.current_rect, canvas_x1, canvas_y1, canvas_x2, canvas_y2)
    app.pdf_canvas.itemconfig(
        app.current_rect,
        fill=RECTANGLE_FILL_COLOR_ACTIVE,
        outline=RECTANGLE_OUTLINE_COLOR_SELECTED,
        width=RECTANGLE_OUTLINE_WIDTH_SELECTED,
        tags=(rectangle["rect_tag"], "censored_rect"),
    )
    rectangle["canvas_text_id"] = app.pdf_canvas.create_text(
        (canvas_x1 + canvas_x2) / 2,
        (canvas_y1 + canvas_y2) / 2,
        text=rectangle.get("display_text", rectangle["concept_name"]),
        fill=RECTANGLE_TEXT_COLOR,
        font=(RECTANGLE_FONT_NAME, RECTANGLE_FONT_SIZE, "bold"),
        tags=(rectangle["rect_tag"], "censored_text"),
    )


def _hit_test_rectangle(app, canvas_x, canvas_y):
    for rectangle in reversed(app.censored_rectangles):
        if rectangle["page"] != app.current_page:
            continue
        x1, y1, x2, y2 = app.pdf_manager.pdf_rect_to_canvas(rectangle)
        left, right = sorted((x1, x2))
        top, bottom = sorted((y1, y2))
        corner = _corner_at_point(canvas_x, canvas_y, left, top, right, bottom)
        if corner:
            return rectangle, "resize", corner
        if left <= canvas_x <= right and top <= canvas_y <= bottom:
            return rectangle, "move", None
    return None, None, None


def _corner_at_point(x, y, left, top, right, bottom):
    corners = {
        "nw": (left, top),
        "ne": (right, top),
        "sw": (left, bottom),
        "se": (right, bottom),
    }
    for name, (corner_x, corner_y) in corners.items():
        if abs(x - corner_x) <= RESIZE_HANDLE_DISTANCE and abs(y - corner_y) <= RESIZE_HANDLE_DISTANCE:
            return name
    return None


def _move_active_rectangle(app, current_x, current_y):
    x1, y1, x2, y2 = app.drag_original_coords
    delta_x = current_x - app.drag_start_x
    delta_y = current_y - app.drag_start_y
    _update_rect_from_canvas_coords(app, app.active_rect_data, x1 + delta_x, y1 + delta_y, x2 + delta_x, y2 + delta_y)


def _resize_active_rectangle(app, current_x, current_y):
    x1, y1, x2, y2 = app.drag_original_coords
    if "n" in app.active_resize_corner:
        y1 = current_y
    if "s" in app.active_resize_corner:
        y2 = current_y
    if "w" in app.active_resize_corner:
        x1 = current_x
    if "e" in app.active_resize_corner:
        x2 = current_x
    if abs(x1 - x2) < MIN_DRAG_DISTANCE or abs(y1 - y2) < MIN_DRAG_DISTANCE:
        return
    _update_rect_from_canvas_coords(app, app.active_rect_data, x1, y1, x2, y2)


def _update_rect_from_canvas_coords(app, rectangle, x1, y1, x2, y2):
    pdf_x1, pdf_y1, pdf_x2, pdf_y2 = app.pdf_manager.canvas_to_pdf_rect(x1, y1, x2, y2)
    rectangle.update({"x1": pdf_x1, "y1": pdf_y1, "x2": pdf_x2, "y2": pdf_y2})
    canvas_x1, canvas_y1, canvas_x2, canvas_y2 = app.pdf_manager.pdf_rect_to_canvas(rectangle)
    app.pdf_canvas.coords(rectangle["canvas_rect_id"], canvas_x1, canvas_y1, canvas_x2, canvas_y2)
    app.pdf_canvas.coords(rectangle["canvas_text_id"], (canvas_x1 + canvas_x2) / 2, (canvas_y1 + canvas_y2) / 2)


def _normalize_active_rectangle(app):
    if not app.active_rect_data:
        return
    x1, y1, x2, y2 = app.pdf_manager.pdf_rect_to_canvas(app.active_rect_data)
    _update_rect_from_canvas_coords(app, app.active_rect_data, x1, y1, x2, y2)


def _select_rectangle(app, rectangle):
    app.selected_rect_id = rectangle["id"] if rectangle else None
    _refresh_selection_visual(app)
    app._sync_delete_button_state()
    app.pdf_canvas.focus_set()


def _refresh_selection_visual(app):
    for rectangle in app.censored_rectangles:
        canvas_rect_id = rectangle.get("canvas_rect_id")
        if not canvas_rect_id or rectangle["page"] != app.current_page:
            continue
        is_selected = rectangle["id"] == app.selected_rect_id
        app.pdf_canvas.itemconfigure(
            canvas_rect_id,
            outline=RECTANGLE_OUTLINE_COLOR_SELECTED if is_selected else RECTANGLE_OUTLINE_COLOR_NORMAL,
            width=RECTANGLE_OUTLINE_WIDTH_SELECTED if is_selected else RECTANGLE_OUTLINE_WIDTH_NORMAL,
        )


def _delete_selected_from_key(app):
    app._handle_rectangle_action("delete")


def _reset_drag_state(app):
    app.drag_mode = None
    app.active_rect_data = None
    app.active_resize_corner = None
    app.drag_start_x = None
    app.drag_start_y = None
    app.drag_original_coords = None
    app.pdf_canvas.configure(cursor="")


def _cursor_for_corner(_corner):
    return "sizing"


def _get_concept_name(app, concept_id):
    return app.catalogue_name_by_id.get(concept_id, str(concept_id))
