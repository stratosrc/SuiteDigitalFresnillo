from components.shared.app_registry import get_launcher_applications
from components.version import VERSION


WINDOW_TITLE = f"Suite Digital {VERSION} - Presidencia Fresnillo"
WINDOW_SUBTITLE = "Unidad de Transparencia y Acceso a la Información Pública"
WINDOW_SIZE = (850, 600)
WINDOW_MIN_SIZE = (720, 520)

BANNER_RELATIVE_PATH = "components/assets/logo_banner.png"
BANNER_HEIGHT = 80
FOOTER_TEXT = "Gestión Institucional | Período de Administración 2024-2027"
LEGAL_NOTICE_TEXT = (
    "© 2026 H. Ayuntamiento de Fresnillo, Zacatecas, México. Administración 2024-2027 "
    "Todos los derechos reservados.\n"
    "Este software es una obra protegida por las leyes nacionales e internacionales en "
    "materia de derechos de autor y propiedad intelectual. Fue desarrollado por la Unidad "
    "de Transparencia del H. Ayuntamiento de Fresnillo, Zacatecas, Administración 2024-2027 "
    "para uso institucional y administrativo. \nQueda prohibida su reproducción, distribución, "
    "modificación, ingeniería inversa, comercialización o cualquier otro uso no autorizado, "
    "total o parcial, sin el consentimiento previo y por escrito del titular de los derechos.\n"
    "Sistema desarrollado por la Unidad de Transparencia del H. Ayuntamiento de Fresnillo, "
    "Zacatecas, México. Administración 2024-2027."
)

APPLICATIONS_CONFIG = get_launcher_applications()
