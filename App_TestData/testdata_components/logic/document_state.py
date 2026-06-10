"""Typed document state used by the business layer."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any, Deque, Optional, TypedDict

import fitz
from PIL import ImageTk

from App_TestData.testdata_components.constants import UNDO_REDO_STACK_LIMIT


class RectangleData(TypedDict, total=False):
    """Mutable rectangle metadata stored for each redaction box."""

    id: int
    order: int
    page: int
    x1: float
    y1: float
    x2: float
    y2: float
    classification: str
    concept_id: Optional[int]
    category: str
    concept_name: str
    rows: int
    paragraphs: int
    legal_basis: str
    reason: str
    object: str
    articles: str
    law: str
    description: str
    label: str
    display_text: str
    rect_tag: str
    final_number: str
    canvas_rect_id: Optional[int]
    canvas_text_id: Optional[int]
    rect: fitz.Rect


CommitteeData = dict[str, str]
HistoryItem = str | dict[str, Any]


@dataclass(slots=True)
class DocumentState:
    """Own all mutable document data independently from UI widgets."""

    current_pdf_path: Optional[str] = None
    pdf_document: Optional[fitz.Document] = None
    pdf_page_image: Optional[ImageTk.PhotoImage] = None
    current_page: int = 0
    current_zoom: Optional[float] = None
    censored_rectangles: list[RectangleData] = field(default_factory=list)
    undo_stack: Deque[RectangleData] = field(
        default_factory=lambda: deque(maxlen=UNDO_REDO_STACK_LIMIT)
    )
    redo_stack: Deque[RectangleData] = field(
        default_factory=lambda: deque(maxlen=UNDO_REDO_STACK_LIMIT)
    )
    next_rectangle_id: int = 1
    selected_rect_id: Optional[int] = None
    reserved_history: list[HistoryItem] = field(default_factory=list)
    confidential_history: list[HistoryItem] = field(default_factory=list)
    other_law_history: list[HistoryItem] = field(default_factory=list)
    committee_data: CommitteeData = field(default_factory=dict)

    def reset_for_new_job(self) -> None:
        """Clear every document-specific value before a new file is selected."""
        if self.pdf_document is not None:
            self.pdf_document.close()

        self.current_pdf_path = None
        self.pdf_document = None
        self.pdf_page_image = None
        self.current_page = 0
        self.current_zoom = None
        self.censored_rectangles.clear()
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.next_rectangle_id = 1
        self.selected_rect_id = None
        self.reserved_history.clear()
        self.confidential_history.clear()
        self.other_law_history.clear()
        self.committee_data.clear()
