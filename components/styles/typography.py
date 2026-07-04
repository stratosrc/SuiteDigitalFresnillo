"""Shared typography tokens."""

import sys


FONT_FAMILY = "Helvetica Neue" if sys.platform == "darwin" else "Arial"
CTK_FONT_FAMILY = FONT_FAMILY
PDF_FONT_REGULAR = "Helvetica"
PDF_FONT_BOLD = "Helvetica-Bold"
PYMUPDF_FONT_REGULAR = "helv"
