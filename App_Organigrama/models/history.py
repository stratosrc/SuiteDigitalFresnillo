"""Undo and redo history for organigram documents."""

from __future__ import annotations

from copy import deepcopy

from App_Organigrama.models.document import OrgGridDocument


class DocumentHistory:
    def __init__(self, document: OrgGridDocument, limit: int = 100) -> None:
        self.limit = max(1, limit)
        self.undo_stack: list[OrgGridDocument] = []
        self.redo_stack: list[OrgGridDocument] = []
        self.current = deepcopy(document)
        self.saved_state = deepcopy(document.to_dict())

    @property
    def can_undo(self) -> bool:
        return bool(self.undo_stack)

    @property
    def can_redo(self) -> bool:
        return bool(self.redo_stack)

    @property
    def is_dirty(self) -> bool:
        return self.current.to_dict() != self.saved_state

    def reset(self, document: OrgGridDocument, *, mark_saved: bool = True) -> None:
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.current = deepcopy(document)
        if mark_saved:
            self.saved_state = deepcopy(document.to_dict())

    def record(self, document: OrgGridDocument) -> bool:
        if document.to_dict() == self.current.to_dict():
            return False
        self.undo_stack.append(deepcopy(self.current))
        if len(self.undo_stack) > self.limit:
            del self.undo_stack[0]
        self.current = deepcopy(document)
        self.redo_stack.clear()
        return True

    def undo(self) -> OrgGridDocument | None:
        if not self.undo_stack:
            return None
        self.redo_stack.append(deepcopy(self.current))
        self.current = self.undo_stack.pop()
        return deepcopy(self.current)

    def redo(self) -> OrgGridDocument | None:
        if not self.redo_stack:
            return None
        self.undo_stack.append(deepcopy(self.current))
        self.current = self.redo_stack.pop()
        return deepcopy(self.current)

    def mark_saved(self, document: OrgGridDocument) -> None:
        self.current = deepcopy(document)
        self.saved_state = deepcopy(document.to_dict())


__all__ = ["DocumentHistory"]
