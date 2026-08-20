# Compilación y publicación

## 1. Verificar la versión

Para una publicación, los siguientes valores deben coincidir:

- `components/version.py`
- `pyproject.toml`
- `convertidor.spec`
- `installer/SuiteFresnillo.iss`
- `docs/CHANGELOG.md`

La versión actual es **1.1.3**.

## 2. Ejecutar calidad

```powershell
python -m ruff check .
python -m compileall -q App_TestData App_Organigrama App_Directorio App_ConversorPDF components
python -m pytest
```

## 3. Crear la distribución

```powershell
python -m PyInstaller --clean --noconfirm convertidor.spec
```

La salida es `dist/SuiteFresnillo/SuiteFresnillo.exe`. La carpeta completa es necesaria; no debe copiarse únicamente el EXE.

## 4. Crear el instalador

Con Inno Setup 6 instalado:

```powershell
& "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe" installer\SuiteFresnillo.iss
```

Si se instaló para todos los usuarios, `ISCC.exe` puede estar en `C:\Program Files (x86)\Inno Setup 6`.

Salida esperada:

```text
installer_output/SuiteDigitalFresnillo-Setup-1.1.3.exe
```

## 5. Validación de publicación

- Probar el ejecutable compilado.
- Instalar en una máquina virtual limpia sin Python ni LibreOffice.
- Abrir los cuatro módulos.
- Convertir al menos un DOCX, XLSX y PPTX.
- Crear PDFs de Test Data en calidad Estándar y Compacta.
- Guardar y volver a abrir proyectos `.td`, `.og` y `.dir`.
- Desinstalar y confirmar accesos directos y procesos.
- Calcular y publicar el SHA-256 del instalador.
- Firmar digitalmente el instalador cuando exista un certificado de firma de código.

Los directorios `build/`, `dist/` e `installer_output/` son artefactos locales y no se versionan.

## 6. Verificar metadatos y hash

```powershell
$installer = Get-Item .\installer_output\SuiteDigitalFresnillo-Setup-1.1.3.exe
$installer.VersionInfo | Select-Object ProductVersion,FileVersion
Get-FileHash $installer.FullName -Algorithm SHA256
Get-AuthenticodeSignature $installer.FullName
```

Publicar nombre, tamaño, versión, SHA-256 y estado de firma. No reutilizar el hash de una compilación anterior.

## 7. Firma y entrega

La firma debe aplicarse con certificado de firma de código y timestamp confiable antes de la distribución final. Tras firmar, recalcular SHA-256 y repetir la prueba de instalación. Conservar el instalador, hash, changelog y evidencia de QA como conjunto de release.

Consulta también [COMPATIBILITY.md](COMPATIBILITY.md), [SECURITY_AND_PRIVACY.md](SECURITY_AND_PRIVACY.md) y [QA.md](QA.md).
