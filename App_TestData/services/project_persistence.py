"""JSON persistence for in-progress Test Data jobs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from App_TestData.domain.document_state import DocumentState, RectangleData


PROJECT_APP_ID = "testdata"
PROJECT_VERSION = 1
_TRANSIENT_RECTANGLE_FIELDS = {"canvas_rect_id", "canvas_text_id", "rect"}


def calculate_file_hash(file_path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(file_path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def save_project(state: DocumentState, target_path: str | Path) -> Path:
    target = Path(target_path)
    payload = {
        "app": PROJECT_APP_ID,
        "version": PROJECT_VERSION,
        "pdf_path": state.current_pdf_path,
        "pdf_sha256": calculate_file_hash(state.current_pdf_path) if state.current_pdf_path else "",
        "current_page": state.current_page,
        "current_zoom": state.current_zoom,
        "rectangles": [_serialize_rectangle(rectangle) for rectangle in state.censored_rectangles],
        "reserved_history": list(state.reserved_history),
        "confidential_history": list(state.confidential_history),
        "other_law_history": list(state.other_law_history),
        "committee_data": dict(state.committee_data),
    }
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return target


def load_project(source_path: str | Path) -> dict[str, Any]:
    source = Path(source_path)
    payload = json.loads(source.read_text(encoding="utf-8"))
    if payload.get("app", PROJECT_APP_ID) != PROJECT_APP_ID:
        raise ValueError("Este archivo no es un proyecto de TestData.")
    if payload.get("version") != PROJECT_VERSION:
        raise ValueError("Version de proyecto no compatible.")
    return payload


def deserialize_rectangles(items: list[dict[str, Any]]) -> list[RectangleData]:
    rectangles: list[RectangleData] = []
    for item in items:
        rectangle = dict(item)
        rectangle["canvas_rect_id"] = None
        rectangle["canvas_text_id"] = None
        rectangles.append(rectangle)
    return rectangles


def _serialize_rectangle(rectangle: RectangleData) -> dict[str, Any]:
    return {
        key: value
        for key, value in rectangle.items()
        if key not in _TRANSIENT_RECTANGLE_FIELDS
    }
