from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = PACKAGE_ROOT / "assets"
CONVERTER_LOGO_PATH = ASSETS_DIR / "logo2.png"
UPLOAD_ICON_PATH = ASSETS_DIR / "upload.png"
UPLOAD_ICON_HOVER_PATH = ASSETS_DIR / "upload_hover.png"
DOWNLOAD_ICON_PATH = ASSETS_DIR / "download.png"
DOWNLOAD_ICON_HOVER_PATH = ASSETS_DIR / "download_hover.png"
DOWNLOAD_ITEM_ICON_PATH = ASSETS_DIR / "dl.png"

APP_TITLE = "Conversor de archivos a PDF"
APP_DESCRIPTION = "Conversor de archivos a PDF"

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tif", ".tiff"}
DOCUMENT_EXTENSIONS = {".doc", ".docx", ".rtf", ".odt", ".xls", ".xlsx", ".ods", ".csv", ".ppt", ".pptx", ".odp"}
SHEET_EXTENSIONS = {".xls", ".xlsx", ".ods", ".csv"}
SUPPORTED_EXTENSIONS = IMAGE_EXTENSIONS | DOCUMENT_EXTENSIONS

__all__ = [
    "APP_DESCRIPTION",
    "APP_TITLE",
    "ASSETS_DIR",
    "CONVERTER_LOGO_PATH",
    "DOWNLOAD_ICON_HOVER_PATH",
    "DOWNLOAD_ICON_PATH",
    "DOWNLOAD_ITEM_ICON_PATH",
    "DOCUMENT_EXTENSIONS",
    "IMAGE_EXTENSIONS",
    "SHEET_EXTENSIONS",
    "SUPPORTED_EXTENSIONS",
    "UPLOAD_ICON_HOVER_PATH",
    "UPLOAD_ICON_PATH",
]
