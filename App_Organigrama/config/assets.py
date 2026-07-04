from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = PACKAGE_ROOT / "assets"
BANNER_LOGO_PATH = ASSETS_DIR / "LogoBanner.png"
CROSS_CURSOR_PATH = ASSETS_DIR / "cross_cursor.png"
HORIZONTAL_ICON_PATH = ASSETS_DIR / "horizontal.png"
NODE_LOGO_PATH = ASSETS_DIR / "logo_personal.png"
REDO_ICON_PATH = ASSETS_DIR / "redo.png"
TOOLBAR_LOGO_PATH = ASSETS_DIR / "logo_tool_bar.png"
UNDO_ICON_PATH = ASSETS_DIR / "undo.png"
VERTICAL_ICON_PATH = ASSETS_DIR / "vertical.png"
WATERMARK_LOGO_PATH = ASSETS_DIR / "logo_marca_agua.png"

__all__ = [
    "ASSETS_DIR",
    "BANNER_LOGO_PATH",
    "CROSS_CURSOR_PATH",
    "HORIZONTAL_ICON_PATH",
    "NODE_LOGO_PATH",
    "PACKAGE_ROOT",
    "REDO_ICON_PATH",
    "TOOLBAR_LOGO_PATH",
    "UNDO_ICON_PATH",
    "VERTICAL_ICON_PATH",
    "WATERMARK_LOGO_PATH",
]
