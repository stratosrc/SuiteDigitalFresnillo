"""Shared typography tokens."""

import os


FONT_FAMILY = "Segoe UI"
CTK_FONT_FAMILY = FONT_FAMILY
SEGOE_UI_FONT_FILE = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts", "segoeui.ttf")
SEGOE_UI_BOLD_FONT_FILE = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts", "segoeuib.ttf")
