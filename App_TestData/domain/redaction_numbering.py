"""Shared numbering rules for TestData redaction rectangles."""

from __future__ import annotations

from copy import deepcopy
from typing import Iterable

from App_TestData.domain.document_state import RectangleData


def assign_redaction_numbers(rectangles: Iterable[RectangleData]) -> list[RectangleData]:
    """Return rectangles with stable labels/final numbers assigned by classification."""
    copied_rectangles = deepcopy(list(rectangles))
    ordered_rectangles = sorted(
        enumerate(copied_rectangles),
        key=lambda item: item[1].get("order", item[0]),
    )
    ordered_rectangles = [rectangle for _, rectangle in ordered_rectangles]
    concept_counters: dict[int, int] = {}
    reserved_counter = 0
    confidential_counter = 0
    other_law_counter = 0

    for rect_data in ordered_rectangles:
        classification = rect_data.get("classification", "general")
        if classification == "reserved":
            reserved_counter += 1
            final_number = f"#reservada.{reserved_counter}"
        elif classification == "confidential":
            confidential_counter += 1
            final_number = f"#confidencial.{confidential_counter}"
        elif classification == "other_law":
            other_law_counter += 1
            final_number = f"Otra.{other_law_counter}"
        else:
            concept_id = int(rect_data.get("concept_id") or 1)
            concept_counters[concept_id] = concept_counters.get(concept_id, 0) + 1
            final_number = f"#{concept_id}.{concept_counters[concept_id]}"
        rect_data["label"] = final_number
        rect_data["final_number"] = final_number

    return ordered_rectangles
