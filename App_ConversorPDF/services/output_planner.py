"""Plan converter outputs from user page or sheet selections."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


class TextValue(Protocol):
    """Minimal interface implemented by Tk string variables."""

    def get(self) -> str:
        """Return the current text value."""


class BooleanValue(Protocol):
    """Minimal interface implemented by Tk boolean variables."""

    def get(self) -> bool:
        """Return the current boolean value."""


class SourceItem(Protocol):
    """Input data required to build planned PDF outputs."""

    path: Path
    sheet_var: TextValue | None
    split_var: BooleanValue | None


@dataclass(frozen=True, slots=True)
class PlannedOutput:
    """One PDF output requested by the converter UI."""

    source: SourceItem
    selection: str | None
    filename: str


def build_output_plan(items: list[SourceItem]) -> list[PlannedOutput]:
    """Create output entries while preserving the source-list order."""
    outputs: list[PlannedOutput] = []
    for item in items:
        selection = normalize_selection(item.sheet_var.get()) if item.sheet_var is not None else None
        if selection is None:
            outputs.append(PlannedOutput(item, None, f"{item.path.stem}.pdf"))
            continue
        if item.split_var is not None and item.split_var.get():
            for single_page in expand_selection(selection):
                outputs.append(
                    PlannedOutput(
                        item,
                        single_page,
                        f"{item.path.stem}_{safe_filename(single_page)}.pdf",
                    )
                )
            continue
        outputs.append(
            PlannedOutput(
                item,
                selection,
                f"{item.path.stem}_{safe_filename(selection)}.pdf",
            )
        )
    return outputs


def normalize_selection(raw_value: str) -> str | None:
    """Normalize valid numeric ranges without rejecting named sheets."""
    normalized_parts: list[str] = []
    for part in _selection_parts(raw_value):
        if "-" not in part:
            normalized_parts.append(part)
            continue
        start, end, *extra = (value.strip() for value in part.split("-"))
        if extra or not start.isdigit() or not end.isdigit():
            normalized_parts.append(part)
            continue
        start_number = int(start)
        end_number = int(end)
        normalized_parts.append(
            part if start_number > end_number else f"{start_number}-{end_number}"
        )
    return ",".join(normalized_parts) or None


def expand_selection(raw_value: str) -> list[str]:
    """Expand numeric ranges while retaining nonnumeric sheet names."""
    expanded: list[str] = []
    for part in _selection_parts(raw_value):
        if "-" not in part:
            expanded.append(part)
            continue
        start, end, *extra = (value.strip() for value in part.split("-"))
        if extra or not start.isdigit() or not end.isdigit():
            expanded.append(part)
            continue
        start_number = int(start)
        end_number = int(end)
        if start_number > end_number:
            expanded.append(part)
            continue
        expanded.extend(str(number) for number in range(start_number, end_number + 1))
    return expanded or [raw_value]


def safe_filename(value: str) -> str:
    """Remove characters that Windows does not allow in file names."""
    safe_value = "".join(character for character in value if character not in '<>:"/\\|?*')
    return safe_value.strip() or "hoja"


def _selection_parts(raw_value: str) -> list[str]:
    return [part.strip() for part in raw_value.replace(";", ",").split(",") if part.strip()]


__all__ = [
    "PlannedOutput",
    "build_output_plan",
    "expand_selection",
    "normalize_selection",
    "safe_filename",
]
