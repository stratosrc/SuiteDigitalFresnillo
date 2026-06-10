WINDOW_TITLE = "Suite Digital - Presidencia Fresnillo"
WINDOW_SUBTITLE = "Unidad de Transparencia y Acceso a la Información Pública"
WINDOW_SIZE = (850, 600)
WINDOW_MIN_SIZE = (720, 520)

BANNER_RELATIVE_PATH = "components/assets/logo_banner.png"
BANNER_HEIGHT = 80
FOOTER_TEXT = "Gestión Institucional | Período de Administración 2024-2027"

APPLICATIONS_CONFIG = [
    {
        "app_id": "testdata",
        "name": "Test Data",
        "icon_path": "components/assets/censor_icon.png",
        "script_path": "App_TestData/App.py",
        "module_path": "App_TestData.App",
        "description": "Módulo de test data y\nversiones públicas",
    },
    {
        "app_id": "organigrama",
        "name": "Organigrama",
        "icon_path": "components/assets/organization_icon.png",
        "script_path": "App_Organigrama/App.py",
        "module_path": "App_Organigrama.App",
        "description": "Gestión del diseño y estructura institucional",
    },
]
