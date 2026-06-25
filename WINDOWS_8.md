# Edicion para Windows 8

Esta versión conserva Test Data, Organigrama y Directorio. El Conversor y
LibreOffice fueron retirados.

La compilación debe realizarse con **Python 3.8.10 de 64 bits**:

```bat
python --version
python -c "import struct; print(struct.calcsize('P') * 8)"
build_win8.bat
```

El instalador generado queda en:

```text
installer_output\SuiteDigitalFresnillo-Windows8-Setup-1.1.0.exe
```

El instalador incluye KB2999226 para Windows 8.0. Si agrega esa actualización,
es obligatorio reiniciar Windows antes de abrir la aplicación.
