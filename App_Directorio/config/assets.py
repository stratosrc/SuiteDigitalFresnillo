from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = PACKAGE_ROOT / "assets"
DIRECTORY_ICON_PATH = ASSETS_DIR / "logo2.png"

__all__ = ["ASSETS_DIR", "DIRECTORY_ICON_PATH", "PACKAGE_ROOT"]
