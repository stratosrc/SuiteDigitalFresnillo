"""State models used by the PDF conversion workspace."""

from dataclasses import dataclass, field
from pathlib import Path
import tkinter as tk


@dataclass(slots=True)
class SourceFileItem:
    path: Path
    sheet_var: tk.StringVar | None = None
    split_var: tk.BooleanVar | None = None
    output_names: list[str] = field(default_factory=list)
