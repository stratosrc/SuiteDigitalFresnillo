"""Canonical application registry shared by the launcher and CLI entry points."""

from dataclasses import dataclass
from importlib import import_module
from importlib.util import find_spec
import os


@dataclass(frozen=True, slots=True)
class ApplicationDefinition:
    app_id: str
    name: str
    package_name: str
    icon_path: str
    description: str

    @property
    def module_path(self) -> str:
        return self.package_name

    @property
    def is_available(self) -> bool:
        return find_spec(self.package_name) is not None

    def to_launcher_config(self) -> dict[str, str | bool]:
        return {
            "app_id": self.app_id,
            "name": self.name,
            "module_path": self.module_path,
            "icon_path": self.icon_path,
            "description": self.description,
            "available": self.is_available,
        }


APPLICATIONS: tuple[ApplicationDefinition, ...] = (
    ApplicationDefinition(
        app_id="testdata",
        name="Test Data",
        package_name="App_TestData",
        icon_path="components/assets/censor_icon.png",
        description="Modulo de test data y\nversiones publicas",
    ),
    ApplicationDefinition(
        app_id="organigrama",
        name="Organigrama",
        package_name="App_Organigrama",
        icon_path="components/assets/organization_icon.png",
        description="Gestion del diseno y estructura institucional",
    ),
    ApplicationDefinition(
        app_id="directorio",
        name="Directorio",
        package_name="App_Directorio",
        icon_path="components/assets/directorio.png",
        description="Gestion y diseno del\nDirectorio de Area",
    ),
)


def _enabled_applications() -> tuple[ApplicationDefinition, ...]:
    if os.environ.get("SUITE_LEGACY_MAC") == "1":
        return tuple(definition for definition in APPLICATIONS if definition.app_id != "testdata")
    return APPLICATIONS


def get_application(app_id: str) -> ApplicationDefinition | None:
    normalized_app_id = app_id.strip().lower()
    for definition in _enabled_applications():
        if definition.app_id == normalized_app_id:
            return definition
    return None


def get_launcher_applications() -> list[dict[str, str | bool]]:
    return [definition.to_launcher_config() for definition in _enabled_applications()]


def run_application(app_id: str) -> None:
    definition = get_application(app_id)
    if definition is None:
        raise KeyError(app_id)
    if not definition.is_available:
        raise ModuleNotFoundError(definition.package_name)

    module = import_module(definition.module_path)
    main = getattr(module, "main", None)
    if not callable(main):
        raise AttributeError(f"{definition.module_path} does not expose a callable main()")
    main()


__all__ = [
    "APPLICATIONS",
    "ApplicationDefinition",
    "get_application",
    "get_launcher_applications",
    "run_application",
]
