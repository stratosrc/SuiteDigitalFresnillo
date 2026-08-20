# Suite Digital Fresnillo

**Versión 1.1.3**

Suite de escritorio para apoyar flujos administrativos de la Presidencia Municipal de Fresnillo. Integra testado de documentos, organigramas, directorios institucionales y conversión de archivos a PDF.

## Módulos

- **Test Data y versiones públicas**: testado visual de PDFs, conceptos legales y personalizados, proyectos `.td`, resumen para Comité y exportación Estándar o Compacta.
- **Organigrama**: edición de nodos y conexiones, rutas manuales, proyectos `.og` y exportación a PDF o imagen.
- **Directorio**: captura de áreas y personal, edición virtualizada para directorios grandes, proyectos `.dir` y exportación a PDF.
- **Conversor a PDF**: imágenes, documentos, hojas de cálculo, presentaciones y PDFs; selección de páginas/hojas y combinación de archivos.

## Instalación para desarrollo

Requiere Python 3.12 a 3.14. Desde la raíz del proyecto:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python main.py
```

También puede abrirse un módulo directamente:

```powershell
python main.py --app testdata
python main.py --app organigrama
python main.py --app directorio
python main.py --app conversor_pdf
```

## Estructura

```text
SuiteDigitalFresnillo/
|-- App_TestData/       # Testado y versiones públicas
|-- App_Organigrama/    # Editor de organigramas
|-- App_Directorio/     # Directorios institucionales
|-- App_ConversorPDF/   # Conversión y LibreOffice integrado
|-- components/         # Componentes e infraestructura compartida
|-- docs/               # Documentación operativa y técnica
|-- installer/          # Proyecto de Inno Setup
|-- tests/              # Pruebas automatizadas
|-- convertidor.spec    # Configuración de PyInstaller
|-- main.py             # Punto de entrada
`-- pyproject.toml      # Dependencias y herramientas
```

La explicación de responsabilidades y módulos está en [Arquitectura](docs/ARCHITECTURE.md).

## Calidad

```powershell
python -m ruff check .
python -m compileall -q App_TestData App_Organigrama App_Directorio App_ConversorPDF components
python -m pytest
```

## Compilar

```powershell
python -m PyInstaller --clean --noconfirm convertidor.spec
& "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe" installer\SuiteFresnillo.iss
```

El instalador esperado es `installer_output/SuiteDigitalFresnillo-Setup-1.1.3.exe`. Python y LibreOffice quedan incluidos en la distribución.

## Documentación

- [Índice de documentación](docs/README.md)
- [Guía de usuario](docs/USER_GUIDE.md)
- [Desarrollo](docs/DEVELOPMENT.md)
- [Compilación y publicación](docs/BUILD_AND_RELEASE.md)
- [Registro de cambios](docs/CHANGELOG.md)
- [Plan de pruebas manuales](docs/QA.md)

## Notas

- Test Data guarda el PDF original dentro del proyecto portátil `.td`.
- Los rangos del Conversor aceptan valores como `1`, `2-4` o vacío.
- Los archivos existentes no se sobrescriben automáticamente.
- No debe moverse `App_ConversorPDF/vendor/LibreOffice` sin actualizar el empaquetado y el resolvedor de rutas.
