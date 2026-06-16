from __future__ import annotations

from pathlib import Path
import sys


SOFFICE_RELATIVE_PATHS = (
    Path("vendor") / "libreoffice" / "program" / "soffice.exe",
    Path("vendor") / "LibreOffice" / "program" / "soffice.exe",
)
WINDOWS_INSTALL_PATHS = (
    Path("C:/Program Files/LibreOffice/program/soffice.exe"),
    Path("C:/Program Files (x86)/LibreOffice/program/soffice.exe"),
)


def _app_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _frozen_root() -> Path:
    return Path(sys.executable).resolve().parent


def _existing_path(candidates: list[Path]) -> Path | None:
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def get_soffice_path() -> Path | None:
    candidates: list[Path] = []

    if getattr(sys, "frozen", False):
        frozen_root = _frozen_root()
        for relative_path in SOFFICE_RELATIVE_PATHS:
            candidates.append(frozen_root / relative_path)
        for relative_path in SOFFICE_RELATIVE_PATHS:
            candidates.append(frozen_root / "_internal" / relative_path)
        if hasattr(sys, "_MEIPASS"):
            meipass_root = Path(sys._MEIPASS)
            for relative_path in SOFFICE_RELATIVE_PATHS:
                candidates.append(meipass_root / relative_path)
    else:
        app_root = _app_root()
        project_root = _project_root()
        for relative_path in SOFFICE_RELATIVE_PATHS:
            candidates.append(app_root / relative_path)
        for relative_path in SOFFICE_RELATIVE_PATHS:
            candidates.append(project_root / relative_path)

    candidates.extend(WINDOWS_INSTALL_PATHS)
    return _existing_path(candidates)


def require_soffice_path() -> Path:
    soffice_path = get_soffice_path()
    if soffice_path is None:
        checked_locations = [
            "vendor/libreoffice/program/soffice.exe",
            "_internal/vendor/libreoffice/program/soffice.exe",
            "C:/Program Files/LibreOffice/program/soffice.exe",
            "C:/Program Files (x86)/LibreOffice/program/soffice.exe",
        ]
        raise FileNotFoundError(
            "No se encontro LibreOffice para convertir documentos. "
            "Verifica que exista soffice.exe en una de estas rutas: "
            + "; ".join(checked_locations)
        )
    return soffice_path
