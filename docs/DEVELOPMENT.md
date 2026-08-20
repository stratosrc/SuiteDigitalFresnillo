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

## Convenciones

- Mantener reglas de negocio fuera de widgets y diálogos.
- Dividir controladores cuando mezclen construcción visual, persistencia y tareas de fondo.
- Mantener funciones pequeñas cuando representen una operación reutilizable; no unir archivos solo por su tamaño si tienen una responsabilidad propia.
- Usar `pathlib.Path` y escritura atómica para archivos del usuario.
- Agregar pruebas para regresiones, serialización y cálculos que no dependan de una ventana real.
- No editar el código incluido en `App_ConversorPDF/vendor` salvo al actualizar explícitamente la dependencia.
