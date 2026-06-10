"""Shared path resolution helpers for development and frozen builds."""

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def is_frozen() -> bool:
    return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")


def base_path() -> Path:
    if is_frozen():
        return Path(sys._MEIPASS)
    return PROJECT_ROOT


def resource_path(*path_parts: str) -> Path:
    return (base_path().joinpath(*path_parts)).resolve()


def build_path(relative_path: str) -> Path:
    return resource_path(relative_path)
