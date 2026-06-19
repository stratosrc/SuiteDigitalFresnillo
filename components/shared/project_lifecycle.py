"""Shared project lifecycle, atomic persistence, and recent-file tracking."""

from __future__ import annotations

from collections.abc import Callable
import json
import os
from pathlib import Path
import tempfile
from tkinter import messagebox
from typing import Any

RECENT_FILES_LIMIT = 8


def app_data_dir() -> Path:
    root = Path(
        os.environ.get("LOCALAPPDATA")
        or os.environ.get("APPDATA")
        or (Path.home() / ".local" / "share")
    )
    path = root / "SuiteDigitalFresnillo"
    path.mkdir(parents=True, exist_ok=True)
    return path


def stable_fingerprint(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def atomic_write_text(
    target_path: str | Path,
    content: str,
    *,
    encoding: str = "utf-8",
) -> Path:
    """Write a text file through a sibling temporary file and atomic replace."""
    target = Path(target_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding=encoding,
            newline="",
            prefix=f".{target.stem}-",
            suffix=f"{target.suffix}.tmp",
            dir=target.parent,
            delete=False,
        ) as temporary:
            temporary.write(content)
            temporary.flush()
            os.fsync(temporary.fileno())
            temporary_path = Path(temporary.name)
        temporary_path.replace(target)
    except Exception:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        raise
    return target


def atomic_write_json(target_path: str | Path, payload: Any) -> Path:
    return atomic_write_text(
        target_path,
        json.dumps(payload, ensure_ascii=False, indent=2),
    )


class RecentFilesStore:
    def __init__(self, app_id: str, limit: int = RECENT_FILES_LIMIT) -> None:
        self.app_id = app_id
        self.limit = max(1, limit)
        self.path = app_data_dir() / "recent_files.json"

    def list(self) -> list[Path]:
        payload = self._load()
        raw_items = payload.get(self.app_id, [])
        items: list[Path] = []
        for raw_item in raw_items:
            path = Path(str(raw_item))
            if path.is_file() and path not in items:
                items.append(path)
        return items[: self.limit]

    def add(self, path: str | Path) -> None:
        resolved = Path(path).resolve()
        payload = self._load()
        items = [
            str(resolved),
            *(
                item
                for item in payload.get(self.app_id, [])
                if Path(str(item)) != resolved
            ),
        ][: self.limit]
        payload[self.app_id] = items
        atomic_write_json(self.path, payload)

    def remove(self, path: str | Path) -> None:
        target = Path(path).resolve()
        payload = self._load()
        payload[self.app_id] = [
            item
            for item in payload.get(self.app_id, [])
            if Path(str(item)) != target
        ]
        atomic_write_json(self.path, payload)

    def _load(self) -> dict[str, list[str]]:
        if not self.path.is_file():
            return {}
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            return {}
        return payload if isinstance(payload, dict) else {}


class ProjectLifecycle:
    """Track saved state and coordinate common project confirmations."""

    def __init__(
        self,
        app_id: str,
        *,
        snapshot: Callable[[], Any],
        save: Callable[[], bool],
    ) -> None:
        self.app_id = app_id
        self.snapshot = snapshot
        self.save = save
        self.recent_files = RecentFilesStore(app_id)
        self.current_path: Path | None = None
        self._saved_fingerprint = stable_fingerprint(snapshot())

    @property
    def is_dirty(self) -> bool:
        return stable_fingerprint(self.snapshot()) != self._saved_fingerprint

    def reset(self, *, path: str | Path | None = None, mark_saved: bool = True) -> None:
        self.current_path = Path(path) if path is not None else None
        if mark_saved:
            self._saved_fingerprint = stable_fingerprint(self.snapshot())

    def mark_saved(self, path: str | Path | None = None) -> None:
        if path is not None:
            self.current_path = Path(path)
            self.recent_files.add(self.current_path)
        self._saved_fingerprint = stable_fingerprint(self.snapshot())

    def confirm_discard(self, parent, action: str = "continuar") -> bool:
        if not self.is_dirty:
            return True
        answer = messagebox.askyesnocancel(
            "Cambios sin guardar",
            f"Hay cambios sin guardar. ¿Deseas guardarlos antes de {action}?",
            parent=parent,
        )
        if answer is None:
            return False
        if answer is False:
            return True
        return bool(self.save()) and not self.is_dirty


__all__ = [
    "ProjectLifecycle",
    "RecentFilesStore",
    "atomic_write_json",
    "atomic_write_text",
    "stable_fingerprint",
]
