from pathlib import Path
import sys


VENDOR_PYTHON_DIR = Path(__file__).resolve().parent / "vendor" / "python"
if VENDOR_PYTHON_DIR.exists():
    vendor_path = str(VENDOR_PYTHON_DIR)
    if vendor_path not in sys.path:
        sys.path.insert(0, vendor_path)

from .application import AppConversorPDF, main  # noqa: E402

__all__ = ["AppConversorPDF", "main"]
