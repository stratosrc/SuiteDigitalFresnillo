"""Undo/redo actions for redaction rectangles."""

from copy import deepcopy


def make_history_action(action_type, **payload):
    """Build a history action decoupled from the live UI dictionaries."""
    return {"type": action_type, **deepcopy(payload)}


def undo_last_action(rectangles, undo_stack, redo_stack):
    """Undo the last recorded redaction action."""
    if not undo_stack:
        return list(rectangles), list(undo_stack), list(redo_stack), None

    restored_redo_stack = list(redo_stack)
    updated_undo_stack = list(undo_stack[:-1])
    action = undo_stack[-1]
    updated_rectangles, affected_rectangle = _apply_inverse_action(rectangles, action)
    restored_redo_stack.append(action)
    return updated_rectangles, updated_undo_stack, restored_redo_stack, affected_rectangle


def redo_last_action(rectangles, undo_stack, redo_stack):
    """Redo the last redaction action removed through undo."""
    if not redo_stack:
        return list(rectangles), list(undo_stack), list(redo_stack), None

    action = redo_stack[-1]
    updated_redo_stack = list(redo_stack[:-1])
    updated_rectangles, affected_rectangle = _apply_action(rectangles, action)
    updated_undo_stack = list(undo_stack)
    updated_undo_stack.append(action)
    return updated_rectangles, updated_undo_stack, updated_redo_stack, affected_rectangle


def _apply_inverse_action(rectangles, action):
    action_type = action.get("type")
    if action_type == "create":
        rectangle = action["rectangle"]
        return _remove_rectangle(rectangles, rectangle["id"]), rectangle
    if action_type == "delete":
        rectangle = action["rectangle"]
        return _upsert_rectangle(rectangles, rectangle), rectangle
    if action_type == "update":
        before = action["before"]
        return _upsert_rectangle(rectangles, before), before
    return list(rectangles), None


def _apply_action(rectangles, action):
    action_type = action.get("type")
    if action_type == "create":
        rectangle = action["rectangle"]
        return _upsert_rectangle(rectangles, rectangle), rectangle
    if action_type == "delete":
        rectangle = action["rectangle"]
        return _remove_rectangle(rectangles, rectangle["id"]), rectangle
    if action_type == "update":
        after = action["after"]
        return _upsert_rectangle(rectangles, after), after
    return list(rectangles), None


def _remove_rectangle(rectangles, rectangle_id):
    return [item for item in rectangles if item["id"] != rectangle_id]


def _upsert_rectangle(rectangles, rectangle):
    updated_rectangles = [item for item in rectangles if item["id"] != rectangle["id"]]
    restored = deepcopy(rectangle)
    restored["canvas_rect_id"] = None
    restored["canvas_text_id"] = None
    updated_rectangles.append(restored)
    updated_rectangles.sort(key=lambda item: item["order"])
    return updated_rectangles
