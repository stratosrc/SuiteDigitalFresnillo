APP_TITLE = "Conversor a PDF"
APP_DESCRIPTION = "Conversor a PDF"

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tif", ".tiff"}
DOCUMENT_EXTENSIONS = {".doc", ".docx", ".rtf", ".odt", ".xls", ".xlsx", ".ods", ".csv", ".ppt", ".pptx", ".odp"}
SHEET_EXTENSIONS = {".xls", ".xlsx", ".ods", ".csv"}
SUPPORTED_EXTENSIONS = IMAGE_EXTENSIONS | DOCUMENT_EXTENSIONS

__all__ = [
    "APP_DESCRIPTION",
    "APP_TITLE",
    "DOCUMENT_EXTENSIONS",
    "IMAGE_EXTENSIONS",
    "SHEET_EXTENSIONS",
    "SUPPORTED_EXTENSIONS",
]
