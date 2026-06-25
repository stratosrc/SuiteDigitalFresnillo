"""Shared project lifecycle, atomic persistence, and recovery."""

from __future__ import annotations

from typing import Callable
import json
import os
from pathlib import Path
import shutil
import tempfile
import time
from tkinter import messagebox
from typing import Any

from components.shared.confirmation import ask_save_discard_cancel
from components.shared.protected_storage import (
    ProtectedStorageUnavailable,
    protect_bytes,
    unprotect_bytes,
)


RECENT_FILES_LIMIT = 8
AUTOSAVE_INTERVAL_MS = 20_000


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


def atomic_write_bytes(target_path: str | Path, content: bytes) -> Path:
    target = Path(target_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
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


class RecentFilesStore:
    def __init__(self, app_id: str, limit: int = RECENT_FILES_LIMIT) -> None:
        self.app_id = app_id
        self.limit = max(1, limit)
        self.path = app_data_dir() / "recent_files.json"

    def list(self) -> list[Path]:
        payload = self._load()
        items: list[Path] = []
        for raw_item in payload.get(self.app_id, []):
            path = Path(str(raw_item))
            if path.is_file() and path not in items:
                items.append(path)
        return items[: self.limit]

    def add(self, path: str | Path) -> None:
        resolved = Path(path).resolve()
        payload = self._load()
        payload[self.app_id] = [
            str(resolved),
            *(
                item
                for item in payload.get(self.app_id, [])
                if Path(str(item)) != resolved
            ),
        ][: self.limit]
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
    def __init__(
        self,
        app_id: str,
        *,
        snapshot: Callable[[], Any],
        save: Callable[[], bool],
        prepare_recovery: Callable[[Any, Path], Any] | None = None,
    ) -> None:
        self.app_id = app_id
        self.snapshot = snapshot
        self.save = save
        self.prepare_recovery = prepare_recovery
        self.recent_files = RecentFilesStore(app_id)
        self.current_path: Path | None = None
        self._saved_fingerprint = stable_fingerprint(snapshot())
        self.recovery_dir = app_data_dir() / "recovery" / app_id
        self.recovery_path = self.recovery_dir / "recovery.bin"
        self.legacy_recovery_path = app_data_dir() / "recovery" / f"{app_id}.json"
        self._autosave_owner = None
        self._autosave_after_id: str | None = None

    @property
    def is_dirty(self) -> bool:
        return stable_fingerprint(self.snapshot()) != self._saved_fingerprint

    def reset(self, *, path: str | Path | None = None, mark_saved: bool = True) -> None:
        self.current_path = Path(path) if path is not None else None
        if mark_saved:
            self._saved_fingerprint = stable_fingerprint(self.snapshot())
            self.clear_recovery()

    def mark_saved(self, path: str | Path | None = None) -> None:
        if path is not None:
            self.current_path = Path(path)
        self._saved_fingerprint = stable_fingerprint(self.snapshot())
        self.clear_recovery()
        if self.current_path is not None:
            try:
                self.recent_files.add(self.current_path)
            except (OSError, TypeError, ValueError):
                pass

    def confirm_discard(self, parent, action: str = "continuar") -> bool:
        if not self.is_dirty:
            return True
        answer = ask_save_discard_cancel(parent, action)
        if answer == "cancel":
            return False
        if answer == "discard":
            self.clear_recovery()
            return True
        return bool(self.save()) and not self.is_dirty

    def start_autosave(self, owner, restore: Callable[[Any, Path | None], None]) -> None:
        self._autosave_owner = owner
        self.legacy_recovery_path.unlink(missing_ok=True)
        if not self.recovery_path.is_file():
            shutil.rmtree(self.recovery_dir, ignore_errors=True)
        self.offer_recovery(owner, restore)
        self._schedule_autosave()

    def stop_autosave(self) -> None:
        if self._autosave_owner is not None and self._autosave_after_id is not None:
            try:
                self._autosave_owner.after_cancel(self._autosave_after_id)
            except Exception:
                pass
        self._autosave_after_id = None
        self._autosave_owner = None

    def offer_recovery(self, parent, restore: Callable[[Any, Path | None], None]) -> bool:
        if not self.recovery_path.is_file():
            return False
        try:
            protected_payload = self.recovery_path.read_bytes()
            payload = json.loads(unprotect_bytes(protected_payload).decode("utf-8"))
            snapshot = payload["snapshot"]
            path = Path(payload["path"]) if payload.get("path") else None
        except (
            OSError,
            KeyError,
            TypeError,
            ValueError,
            json.JSONDecodeError,
            ProtectedStorageUnavailable,
        ):
            self.clear_recovery()
            return False
        if not messagebox.askyesno(
            "Recuperar trabajo",
            "Se encontró un autoguardado de una sesión anterior. ¿Deseas recuperarlo?",
            parent=parent,
        ):
            self.clear_recovery()
            return False
        restore(snapshot, path)
        self.current_path = path
        self._saved_fingerprint = stable_fingerprint({})
        return True

    def clear_recovery(self) -> None:
        self.recovery_path.unlink(missing_ok=True)
        shutil.rmtree(self.recovery_dir, ignore_errors=True)
        self.legacy_recovery_path.unlink(missing_ok=True)

    def _schedule_autosave(self) -> None:
        if self._autosave_owner is not None:
            self._autosave_after_id = self._autosave_owner.after(
                AUTOSAVE_INTERVAL_MS,
                self._autosave_tick,
            )

    def _autosave_tick(self) -> None:
        self._autosave_after_id = None
        if self.is_dirty:
            try:
                snapshot = self.snapshot()
                if self.prepare_recovery is not None:
                    snapshot = self.prepare_recovery(snapshot, self.recovery_dir)
                payload = json.dumps(
                    {
                        "app": self.app_id,
                        "saved_at": time.time(),
                        "path": str(self.current_path) if self.current_path else None,
                        "snapshot": snapshot,
                    },
                    ensure_ascii=False,
                    separators=(",", ":"),
                ).encode("utf-8")
                atomic_write_bytes(
                    self.recovery_path,
                    protect_bytes(payload),
                )
            except (
                OSError,
                TypeError,
                ValueError,
                ProtectedStorageUnavailable,
            ):
                pass
        self._schedule_autosave()


__all__ = [
    "ProjectLifecycle",
    "RecentFilesStore",
    "atomic_write_json",
    "atomic_write_bytes",
    "atomic_write_text",
    "stable_fingerprint",
]
