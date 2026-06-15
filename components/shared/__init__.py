"""Shared helpers reused across desktop applications."""

from .app_registry import (
    APPLICATIONS,
    ApplicationDefinition,
    get_application,
    get_launcher_applications,
    run_application,
)

__all__ = [
    "APPLICATIONS",
    "ApplicationDefinition",
    "get_application",
    "get_launcher_applications",
    "run_application",
]
