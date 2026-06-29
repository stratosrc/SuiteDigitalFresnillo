from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from fastapi import HTTPException

from .config import RUNTIME_DIR


def cleanup_tree(path: Path) -> None:
    shutil.rmtree(path, ignore_errors=True)


def session_dir(session_id: str) -> Path:
    safe_id = "".join(ch for ch in session_id if ch.isalnum() or ch in "-_")
    if not safe_id:
        raise HTTPException(status_code=400, detail="Sesion invalida.")
    path = RUNTIME_DIR / safe_id
    if not path.exists():
        raise HTTPException(status_code=404, detail="Sesion no encontrada.")
    return path


def make_work_dir(prefix: str) -> Path:
    return Path(tempfile.mkdtemp(prefix=prefix, dir=RUNTIME_DIR))
