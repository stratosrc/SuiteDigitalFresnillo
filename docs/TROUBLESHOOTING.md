# Solución de problemas

## Diagnóstico de desarrollo

```powershell
python --version
python -m pip check
python -m ruff check .
python -m compileall -q App_TestData App_Organigrama App_Directorio App_ConversorPDF components
python -m pytest
```

Para aislar un módulo: `python main.py --app testdata|organigrama|directorio|conversor_pdf`.

## La aplicación no abre

- Ejecutar desde la raíz que contiene `main.py`.
- Usar Python 3.12–3.14 y activar `.venv`.
- Reinstalar con `python -m pip install -e ".[dev]"`.
- Si falta `_tkinter`, reparar Python incluyendo Tcl/Tk.

## Windows bloquea el EXE

Verificar origen institucional, SHA-256, versión y cuarentena del antivirus. No desactivar permanentemente la protección; la solución de distribución es firmar el instalador.

## No se encuentra LibreOffice

Debe existir `App_ConversorPDF/vendor/LibreOffice/program/soffice.exe` en desarrollo o `_internal/vendor/libreoffice/program/soffice.exe` en el compilado. No basta copiar `soffice.exe`.

## Falla una conversión Office

- Comprobar que LibreOffice abra el archivo.
- Cerrar instancias que lo bloqueen.
- Evitar documentos dañados o con contraseña.
- Revisar permisos, espacio y selección de páginas/hojas.
- La exportación de hojas tiene timeout de 180 segundos.
- Tras cancelar, confirmar que no quede `soffice.exe`.

## No abre un proyecto

- `.td`: debe ser ZIP, contener `project.json`/`source.pdf`, usar versión compatible y pasar SHA-256.
- `.td` legado: necesita el PDF en `pdf_path`.
- `.og`: debe identificar Organigrama o contener campos reconocibles.
- `.dir`: exige `app: directorio`, `version: 1` y objeto `directory`.

Consulta [DATA_FORMATS.md](DATA_FORMATS.md) antes de editar.

## No aparece autosave

Solo se ofrece si existe un snapshot distinto, transcurrió el ciclo de autosave y el mismo usuario puede descifrar DPAPI. Revisar `%LOCALAPPDATA%\SuiteDigitalFresnillo\recovery`.

## PDF de Test Data grande

Usar calidad Compacta, revisar escaneos de alta resolución y comparar legibilidad. PDFs con muchas imágenes únicas pueden seguir siendo grandes.

## Rectángulos desalineados

Registrar página y rotación; no modificar el PDF fuente después de guardar. Ejecutar `test_testdata_pdf_rotation.py` y `test_redaction_label_rotation.py`.

## Directorio lento

Mantener una sola área expandida y comparar con las muestras de 300/900 personas. No quitar virtualización sin medir.

## Rutas inesperadas en Organigrama

Revisar obstáculos y `manual_points`; restablecer la ruta para volver al router automático. Evitar nodos demasiado próximos.

## Reporte útil

Incluir versión, Windows, fuente/EXE/instalador, módulo, pasos, mensaje exacto, muestra anonimizada, resultado de pruebas y hash del instalador.
