"""Atomic creation helpers for generated files."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
import tempfile
from typing import TypeVar


T = TypeVar("T")


class OutputCancelled(RuntimeError):
    """Raised when a generated temporary output must not be committed."""


def write_atomic_output(
    target_path: str | Path,
    writer: Callable[[Path], T],
    *,
    should_commit: Callable[[], bool] | None = None,
) -> Path:
    """Generate a sibling temporary file and replace the destination on success."""
    target = Path(target_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix=f".{target.stem}-",
            suffix=target.suffix or ".tmp",
            dir=target.parent,
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
        temporary_path.unlink(missing_ok=True)
        writer(temporary_path)
        if not temporary_path.is_file() or temporary_path.stat().st_size == 0:
            raise RuntimeError("La operación no generó un archivo de salida válido.")
        if should_commit is not None and not should_commit():
            raise OutputCancelled("La operación fue cancelada.")
        temporary_path.replace(target)
    except Exception:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        raise
    return target


__all__ = ["OutputCancelled", "write_atomic_output"]
