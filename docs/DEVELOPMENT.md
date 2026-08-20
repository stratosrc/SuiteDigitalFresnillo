# Desarrollo

## Requisitos

- Windows 10/11 de 64 bits.
- Python 3.12, 3.13 o 3.14.
- Git.
- Inno Setup 6 únicamente para generar el instalador.

## Preparación

Desde la raíz del repositorio:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Ejecución

```powershell
python main.py
python main.py --app testdata
python main.py --app organigrama
python main.py --app directorio
python main.py --app conversor_pdf
```

## Verificación automática

```powershell
python -m ruff check .
python -m compileall -q App_TestData App_Organigrama App_Directorio App_ConversorPDF components
python -m pytest
```

Antes de publicar también debe completarse [QA.md](QA.md).

GitHub Actions repite análisis, bytecode y pruebas en Windows/Python 3.12. También realiza un smoke build de PyInstaller sin LibreOffice para controlar tiempo y tamaño en CI.

## Flujo recomendado de cambio

1. Localizar la responsabilidad en [ARCHITECTURE.md](ARCHITECTURE.md).
2. Escribir o ajustar una prueba de regresión.
3. Implementar en la capa más baja posible.
4. Ejecutar pruebas dirigidas.
5. Ejecutar la verificación completa.
6. Realizar QA visual si cambia UI/PDF.
7. Actualizar documentación y changelog.

## Depuración

Ejecuta un solo módulo con `--app` para obtener errores en consola. Para problemas de empaquetado revisa `build/convertidor/warn-convertidor.txt`. Consulta [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

## Convenciones

- Mantener reglas de negocio fuera de widgets y diálogos.
- Dividir controladores cuando mezclen construcción visual, persistencia y tareas de fondo.
- Mantener funciones pequeñas cuando representen una operación reutilizable; no unir archivos solo por su tamaño si tienen una responsabilidad propia.
- Usar `pathlib.Path` y escritura atómica para archivos del usuario.
- Agregar pruebas para regresiones, serialización y cálculos que no dependan de una ventana real.
- No editar el código incluido en `App_ConversorPDF/vendor` salvo al actualizar explícitamente la dependencia.

## Referencias

- [APIs internas](API_REFERENCE.md)
- [Formatos y migraciones](DATA_FORMATS.md)
- [Cómo extender](EXTENDING.md)
- [Rendimiento](PERFORMANCE.md)
