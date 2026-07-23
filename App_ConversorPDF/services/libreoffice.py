from __future__ import annotations

import os
from pathlib import Path
import sys


WINDOWS_SOFFICE_RELATIVE_PATHS = (
    Path("vendor") / "libreoffice" / "program" / "soffice.exe",
    Path("vendor") / "LibreOffice" / "program" / "soffice.exe",
)
MACOS_SOFFICE_RELATIVE_PATHS = (
    Path("vendor") / "LibreOffice" / "Contents" / "MacOS" / "soffice",
    Path("vendor") / "libreoffice" / "Contents" / "MacOS" / "soffice",
    Path("vendor") / "LibreOffice.app" / "Contents" / "MacOS" / "soffice",
)
WINDOWS_INSTALL_PATHS = (
    Path("C:/Program Files/LibreOffice/program/soffice.exe"),
    Path("C:/Program Files (x86)/LibreOffice/program/soffice.exe"),
)
MACOS_INSTALL_PATHS = (
    Path("/Applications/LibreOffice.app/Contents/MacOS/soffice"),
)


def _app_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _frozen_root() -> Path:
    return Path(sys.executable).resolve().parent


def _frozen_resources_root() -> Path:
    executable_path = Path(sys.executable).resolve()
    return executable_path.parent.parent / "Resources"


def _existing_path(candidates: list[Path]) -> Path | None:
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def _all_relative_soffice_paths() -> tuple[Path, ...]:
    return WINDOWS_SOFFICE_RELATIVE_PATHS + MACOS_SOFFICE_RELATIVE_PATHS


def _all_install_soffice_paths() -> tuple[Path, ...]:
    return WINDOWS_INSTALL_PATHS + MACOS_INSTALL_PATHS


def _macos_contents_dir_from_soffice_path(soffice_path: Path) -> Path | None:
    if soffice_path.name != "soffice" or soffice_path.parent.name != "MacOS":
        return None

    contents_dir = soffice_path.parent.parent
    if contents_dir.name != "Contents":
        return None
    return contents_dir


def get_libreoffice_python_path(soffice_path: Path | None = None) -> Path | None:
    soffice_path = soffice_path or get_soffice_path()
    if soffice_path is None:
        return None

    windows_python = soffice_path.parent / "python.exe"
    if windows_python.is_file():
        return windows_python

    contents_dir = _macos_contents_dir_from_soffice_path(soffice_path)
    if contents_dir is None:
        return None

    framework_dir = contents_dir / "Frameworks" / "LibreOfficePython.framework"
    candidates = [
        framework_dir / "LibreOfficePython",
        framework_dir / "Versions" / "Current" / "LibreOfficePython",
    ]
    return _existing_path(candidates)


def build_libreoffice_subprocess_env(soffice_path: Path | None = None) -> dict[str, str]:
    soffice_path = soffice_path or get_soffice_path()
    env = os.environ.copy()
    if soffice_path is None:
        return env

    contents_dir = _macos_contents_dir_from_soffice_path(soffice_path)
    if contents_dir is None:
        return env

    macos_dir = contents_dir / "MacOS"
    frameworks_dir = contents_dir / "Frameworks"
    resources_dir = contents_dir / "Resources"
    python_framework_dir = frameworks_dir / "LibreOfficePython.framework"
    current_python_path = env.get("PYTHONPATH", "")
    python_paths = [str(frameworks_dir), str(resources_dir)]
    if current_python_path:
        python_paths.append(current_python_path)

    env["PATH"] = str(macos_dir) + os.pathsep + env.get("PATH", "")
    env["PYTHONHOME"] = str(python_framework_dir)
    env["PYTHONPATH"] = os.pathsep.join(python_paths)
    env["PYTHONEXECUTABLE"] = str(python_framework_dir / "LibreOfficePython")
    env["UNO_PATH"] = str(macos_dir)
    env["URE_BOOTSTRAP"] = f"vnd.sun.star.pathname:{resources_dir / 'fundamentalrc'}"
    env["DYLD_FRAMEWORK_PATH"] = str(frameworks_dir)
    env["DYLD_LIBRARY_PATH"] = os.pathsep.join((str(frameworks_dir), str(macos_dir)))
    env["SAL_USE_VCLPLUGIN"] = "svp"
    return env


def get_soffice_path() -> Path | None:
    candidates: list[Path] = []
    relative_paths = _all_relative_soffice_paths()

    if getattr(sys, "frozen", False):
        frozen_root = _frozen_root()
        frozen_resources_root = _frozen_resources_root()
        for relative_path in relative_paths:
            candidates.append(frozen_root / relative_path)
        for relative_path in relative_paths:
            candidates.append(frozen_root / "_internal" / relative_path)
        for relative_path in relative_paths:
            candidates.append(frozen_resources_root / "App_ConversorPDF" / relative_path)
        for relative_path in relative_paths:
            candidates.append(frozen_resources_root / relative_path)
        if hasattr(sys, "_MEIPASS"):
            meipass_root = Path(sys._MEIPASS)
            for relative_path in relative_paths:
                candidates.append(meipass_root / relative_path)
    else:
        app_root = _app_root()
        project_root = _project_root()
        for relative_path in relative_paths:
            candidates.append(app_root / relative_path)
        for relative_path in relative_paths:
            candidates.append(project_root / relative_path)

    candidates.extend(_all_install_soffice_paths())
    return _existing_path(candidates)


def require_soffice_path() -> Path:
    soffice_path = get_soffice_path()
    if soffice_path is None:
        checked_locations = [
            "vendor/libreoffice/program/soffice.exe",
            "_internal/vendor/libreoffice/program/soffice.exe",
            "vendor/LibreOffice/Contents/MacOS/soffice",
            "_internal/vendor/LibreOffice/Contents/MacOS/soffice",
            "Contents/Resources/App_ConversorPDF/vendor/LibreOffice/Contents/MacOS/soffice",
            "C:/Program Files/LibreOffice/program/soffice.exe",
            "C:/Program Files (x86)/LibreOffice/program/soffice.exe",
            "/Applications/LibreOffice.app/Contents/MacOS/soffice",
        ]
        raise FileNotFoundError(
            "No se encontro LibreOffice para convertir documentos. "
            "Verifica que exista LibreOffice en una de estas rutas: "
            + "; ".join(checked_locations)
        )
    return soffice_path
