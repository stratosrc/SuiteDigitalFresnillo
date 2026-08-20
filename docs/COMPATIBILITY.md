# Compatibilidad

## Plataformas

| Plataforma | Estado |
|---|---|
| Windows 11 x64 | Objetivo principal. |
| Windows 10 x64 | Soportado y obligatorio en QA. |
| Windows 8.1 o anterior | No soportado. |
| macOS/Linux | No soportado oficialmente: instalador, DPAPI y distribución están orientados a Windows. |

## Python

`pyproject.toml` declara `>=3.12,<3.15`. CI usa 3.12; 3.13 está soportado; 3.14 debe verificarse antes de compilar una publicación. Otras versiones no están soportadas.

## Requisitos mínimos

x64, 4 GB RAM, 2.5 GB libres durante instalación y pantalla 1280×720. Archivos grandes pueden requerir más memoria/espacio temporal.

## Formatos

| Módulo | Entrada | Salida |
|---|---|---|
| Test Data | PDF, `.td` | PDF, `.td` |
| Organigrama | `.og` | `.og`, PDF, PNG, JPG/JPEG |
| Directorio | `.dir` | `.dir`, PDF |
| Conversor | JPG/JPEG, PNG, WEBP, BMP, GIF, TIF/TIFF, DOC/DOCX, RTF, ODT, XLS/XLSX, ODS, CSV, PPT/PPTX, ODP, PDF | PDF |

Formatos Office dependen de LibreOffice; archivos dañados, protegidos o con funciones incompatibles pueden fallar o variar visualmente.
