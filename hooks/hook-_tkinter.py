"""PyInstaller hook for local Python 3.8 builds.

The Windows 8 build is made with a portable/local Python 3.8 installation.
PyInstaller 5 may fail to infer Tcl/Tk locations from that layout, so this
hook collects the standard Tcl/Tk folders directly from ``sys.base_prefix``.
"""

from __future__ import annotations

import sys
from pathlib import Path

python_base = Path(sys.base_prefix)
tcl_root = python_base / "tcl" / "tcl8.6"
tk_root = python_base / "tcl" / "tk8.6"


def _collect_tree(source: Path, destination: str):
    if not source.exists():
        return []
    files = []
    for path in source.rglob("*"):
        if not path.is_file():
            continue
        if path.name in {"tclConfig.sh", "tkConfig.sh"} or path.suffix == ".lib":
            continue
        if "demos" in path.relative_to(source).parts:
            continue
        files.append((str(path), str(Path(destination) / path.relative_to(source).parent)))
    return files


datas = []
datas += _collect_tree(tcl_root, "tcl")
datas += _collect_tree(tk_root, "tk")
