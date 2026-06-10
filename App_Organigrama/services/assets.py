import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets"
WINDOWS_FONT_DIR = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"

BANNER_LOGO_PATH = ASSETS_DIR / "LogoBanner.png"
HORIZONTAL_ICON_PATH = ASSETS_DIR / "horizontal.png"
NODE_LOGO_PATH = ASSETS_DIR / "logo_personal.png"
TOOLBAR_LOGO_PATH = ASSETS_DIR / "logo_tool_bar.png"
VERTICAL_ICON_PATH = ASSETS_DIR / "vertical.png"
WATERMARK_LOGO_PATH = ASSETS_DIR / "logo_marca_agua.png"

SEGOE_UI_FONT_PATH = WINDOWS_FONT_DIR / "segoeui.ttf"
SEGOE_UI_BOLD_FONT_PATH = WINDOWS_FONT_DIR / "segoeuib.ttf"
