import os


APP_BG = "#f5f7fa"
SURFACE_BG = "#ffffff"
SURFACE_ALT_BG = "#eef3f7"
DARK_BG = "#131C46"
DARK_BG_ACTIVE = "#202C66"
DARK_BG_PRESSED = "#1c313a"
TEXT_DARK = "#263238"
TEXT_MUTED = "#607d8b"
TEXT_LIGHT = "#ffffff"
BORDER_BG = "#c7d2da"
SUCCESS_BG = "#2e7d32"
SUCCESS_BG_ACTIVE = "#388e3c"
DANGER_BG = "#c62828"
DANGER_BG_ACTIVE = "#d32f2f"
CANVAS_BG = "#999999"
SELECTED_OUTLINE = "#22C55E"
PLACEHOLDER_TEXT = "#888888"
GRID_AXIS = "#d7e1ea"
GRID_LINE = "#edf2f6"
GHOST_AVAILABLE_FILL = "#9DC3E6"
GHOST_OCCUPIED_FILL = "#f3a8a8"
BUTTON_BG = "#131C46"
BUTTON_BG_ACTIVE = "#4B4B4B"
BUTTON_BG_PRESSED = "#2C2C2C"
BUTTON_BG2= "#3B8ED0"

PRIMARY_BLUE = "#09519F"
SECONDARY_BLUE = "#3C8AC9"
LIGHT_BLUE = "#9DC3E6"
NEUTRAL_GRAY = "#797E85"

FONT_FAMILY = "Segoe UI"
SEGOE_UI_FONT_FILE = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts", "segoeui.ttf")
SEGOE_UI_BOLD_FONT_FILE = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts", "segoeuib.ttf")
HEADER_LOGO_SIZE = (280, 110)
HEADER_HEIGHT = 134
FOOTER_HEIGHT = 58
WINDOW_PAD = 24
SECTION_GAP = 12
CONTROL_GAP = 8
BUTTON_RADIUS = 0

CTK_FONT_FAMILY = FONT_FAMILY
CTK_RADIUS = BUTTON_RADIUS
CTK_ENTRY_HEIGHT = 30
CTK_COMPACT_BUTTON_SIZE = 24


def apply_ctk_style(ctk):
    ctk.set_appearance_mode("Light")
    ctk.set_default_color_theme("blue")


def styles(app):
    try:
        app.configure(fg_color=APP_BG)
    except Exception:
        app.configure(bg=APP_BG)
